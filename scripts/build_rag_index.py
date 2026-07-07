from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

PROJECT_ROOT_FOR_IMPORT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT_FOR_IMPORT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_FOR_IMPORT))

from medical_drug_agent.app.constants import PROJECT_ROOT, RAG_CHROMA_PATH, RAG_DOCS_DIR, RAG_MODEL_PATH


COLLECTION_NAME = "rag_docs"
SUPPORTED_SUFFIXES = {".md", ".txt"}
DEFAULT_CHUNK_SIZE = 900
DEFAULT_CHUNK_OVERLAP = 120


@dataclass(frozen=True)
class DocumentChunk:
    content: str
    source: str
    relative_path: str
    chunk_id: str
    section: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build local Chroma index for RAG markdown documents.")
    parser.add_argument("--docs-dir", type=Path, default=RAG_DOCS_DIR, help="Directory containing .md/.txt RAG docs.")
    parser.add_argument("--persist-dir", type=Path, default=RAG_CHROMA_PATH, help="Chroma persistence directory.")
    parser.add_argument("--model-path", type=Path, default=RAG_MODEL_PATH, help="Local SentenceTransformer model path.")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE, help="Maximum chunk size in characters.")
    parser.add_argument("--chunk-overlap", type=int, default=DEFAULT_CHUNK_OVERLAP, help="Overlap size for long chunks.")
    parser.add_argument("--append", action="store_true", help="Append to an existing collection instead of rebuilding it.")
    return parser.parse_args()


def iter_document_paths(docs_dir: Path) -> Iterable[Path]:
    if not docs_dir.exists():
        raise FileNotFoundError(f"RAG 文档目录不存在：{docs_dir}")
    for path in sorted(docs_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES:
            yield path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig").strip()


def split_front_matter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text

    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, flags=re.DOTALL)
    if not match:
        return {}, text

    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata, match.group(2).strip()


def split_by_headings(body: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, list[str]]] = []
    current_title = "正文"
    current_lines: list[str] = []

    for line in body.splitlines():
        heading_match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if heading_match:
            if current_lines:
                sections.append((current_title, current_lines))
            current_title = heading_match.group(2).strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_title, current_lines))

    return [(title, "\n".join(lines).strip()) for title, lines in sections if "\n".join(lines).strip()]


def split_long_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    safe_overlap = max(0, min(overlap, chunk_size // 2))
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = end - safe_overlap
    return [chunk for chunk in chunks if chunk]


def chunk_document(path: Path, docs_dir: Path, chunk_size: int, overlap: int) -> list[DocumentChunk]:
    text = read_text(path)
    if not text:
        return []

    front_matter, body = split_front_matter(text)
    if not body.strip():
        return []

    relative_path = path.relative_to(docs_dir).as_posix()
    source = front_matter.get("source_name") or front_matter.get("doc_title") or front_matter.get("drug_name_zh") or path.name

    chunks: list[DocumentChunk] = []
    chunk_index = 0
    for section_title, section_text in split_by_headings(body):
        for part in split_long_text(section_text, chunk_size=chunk_size, overlap=overlap):
            chunks.append(
                DocumentChunk(
                    content=part,
                    source=source,
                    relative_path=relative_path,
                    chunk_id=f"{relative_path}::chunk-{chunk_index}",
                    section=section_title,
                )
            )
            chunk_index += 1
    return chunks


def build_chunks(docs_dir: Path, chunk_size: int, overlap: int) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    for path in iter_document_paths(docs_dir):
        chunks.extend(chunk_document(path, docs_dir=docs_dir, chunk_size=chunk_size, overlap=overlap))
    return chunks


def build_index(
    docs_dir: Path = RAG_DOCS_DIR,
    persist_dir: Path = RAG_CHROMA_PATH,
    model_path: Path = RAG_MODEL_PATH,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    append: bool = False,
) -> dict[str, int | str]:
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:  # pragma: no cover - depends on optional local environment
        raise RuntimeError("缺少 RAG 依赖，请先安装 chromadb 和 sentence-transformers。") from exc

    docs_dir = docs_dir.resolve()
    persist_dir = persist_dir.resolve()
    model_path = model_path.resolve()

    if not model_path.exists():
        raise FileNotFoundError(f"向量模型目录不存在：{model_path}")

    chunks = build_chunks(docs_dir=docs_dir, chunk_size=chunk_size, overlap=chunk_overlap)
    if not chunks:
        raise ValueError(f"未从 RAG 文档目录中读取到有效 chunk：{docs_dir}")

    persist_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(persist_dir))

    if not append:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine", "description": "local markdown RAG documents"},
    )

    model = SentenceTransformer(str(model_path))
    embeddings = model.encode(
        [chunk.content for chunk in chunks],
        normalize_embeddings=True,
        show_progress_bar=True,
    ).tolist()

    collection.add(
        ids=[chunk.chunk_id for chunk in chunks],
        documents=[chunk.content for chunk in chunks],
        embeddings=embeddings,
        metadatas=[
            {
                "source": chunk.source,
                "relative_path": chunk.relative_path,
                "chunk_id": chunk.chunk_id,
                "section": chunk.section,
            }
            for chunk in chunks
        ],
    )

    return {
        "docs_dir": str(docs_dir.relative_to(PROJECT_ROOT) if docs_dir.is_relative_to(PROJECT_ROOT) else docs_dir),
        "persist_dir": str(persist_dir.relative_to(PROJECT_ROOT) if persist_dir.is_relative_to(PROJECT_ROOT) else persist_dir),
        "model_path": str(model_path.relative_to(PROJECT_ROOT) if model_path.is_relative_to(PROJECT_ROOT) else model_path),
        "chunk_count": len(chunks),
    }


def main() -> int:
    args = parse_args()
    if args.persist_dir.exists() and not args.append:
        print(
            "提示：检测到 Chroma 索引目录已存在。"
            "如果仍检索到旧乱码内容，请先删除 data/vector_db/chroma 后重新运行本脚本。"
            "当前脚本会重建 rag_docs collection。"
        )
    try:
        result = build_index(
            docs_dir=args.docs_dir,
            persist_dir=args.persist_dir,
            model_path=args.model_path,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            append=args.append,
        )
    except Exception as exc:
        print(f"RAG index build failed: {exc}")
        return 1

    print("RAG index build complete:")
    for key, value in result.items():
        print(f"- {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
