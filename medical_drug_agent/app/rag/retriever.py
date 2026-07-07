from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from medical_drug_agent.app.constants import RAG_CHROMA_PATH, RAG_MODEL_PATH


COLLECTION_NAME = "rag_docs"
logger = logging.getLogger(__name__)


@dataclass
class RAGEvidence:
    content: str
    source: str
    section: str
    score: float
    relative_path: str = ""
    chunk_id: str = ""
    is_placeholder: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "source": self.source,
            "section": self.section,
            "score": self.score,
            "relative_path": self.relative_path,
            "chunk_id": self.chunk_id,
            "is_placeholder": self.is_placeholder,
        }


class RAGRetriever:
    """Retrieve evidence chunks from the local Chroma markdown index."""

    def __init__(
        self,
        persist_dir: Path = RAG_CHROMA_PATH,
        model_path: Path = RAG_MODEL_PATH,
        collection_name: str = COLLECTION_NAME,
    ) -> None:
        self.persist_dir = Path(persist_dir)
        self.model_path = Path(model_path)
        self.collection_name = collection_name
        self._client = None
        self._collection = None
        self._model = None

    def retrieve(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        query_text = str(query or "").strip()
        if not query_text:
            raise ValueError("query 不能为空")
        if top_k <= 0:
            raise ValueError("top_k 必须大于 0")

        collection = self._get_collection()
        model = self._get_model()
        query_embedding = model.encode([query_text], normalize_embeddings=True).tolist()[0]
        result = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]

        evidences: list[dict[str, Any]] = []
        for document, metadata, distance in zip(documents, metadatas, distances):
            meta = metadata or {}
            score = self._distance_to_score(distance)
            evidences.append(
                RAGEvidence(
                    content=document or "",
                    source=str(meta.get("source") or ""),
                    section=str(meta.get("section") or ""),
                    score=score,
                    relative_path=str(meta.get("relative_path") or ""),
                    chunk_id=str(meta.get("chunk_id") or ""),
                    is_placeholder=is_placeholder_evidence(document or ""),
                ).to_dict()
            )
        return evidences

    def _get_collection(self):
        if self._collection is not None:
            return self._collection

        if not self.persist_dir.exists():
            raise FileNotFoundError(f"RAG 向量库不存在，请先运行 scripts/build_rag_index.py：{self.persist_dir}")

        try:
            import chromadb
        except ImportError as exc:  # pragma: no cover - depends on optional local environment
            raise RuntimeError("缺少 RAG 依赖 chromadb，请先安装 requirements.txt。") from exc

        self._client = chromadb.PersistentClient(path=str(self.persist_dir))
        self._collection = self._client.get_collection(self.collection_name)
        return self._collection

    def _get_model(self):
        if self._model is not None:
            return self._model

        if not self.model_path.exists():
            raise FileNotFoundError(f"RAG 向量模型不存在：{self.model_path}")

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:  # pragma: no cover - depends on optional local environment
            raise RuntimeError("缺少 RAG 依赖 sentence-transformers，请先安装 requirements.txt。") from exc

        self._model = SentenceTransformer(str(self.model_path))
        return self._model

    @staticmethod
    def _distance_to_score(distance: Any) -> float:
        try:
            value = float(distance)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(1.0, 1.0 - value))


_DEFAULT_RETRIEVER: RAGRetriever | None = None


def _get_default_retriever() -> RAGRetriever:
    global _DEFAULT_RETRIEVER
    if _DEFAULT_RETRIEVER is None:
        _DEFAULT_RETRIEVER = RAGRetriever()
    return _DEFAULT_RETRIEVER


def retrieve(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Module-level RAG retrieval entry point.

    This function intentionally reuses ``RAGRetriever`` and does not perform
    any text encode/decode conversion, so Chinese content is returned exactly
    as stored in Chroma.
    """
    query_text = str(query or "").strip()
    if not query_text:
        logger.warning("RAG retrieve skipped: query is empty.")
        return []

    try:
        return _get_default_retriever().retrieve(query_text, top_k=top_k)
    except FileNotFoundError as exc:
        logger.warning("RAG vector store is unavailable: %s", exc)
        return []
    except RuntimeError as exc:
        logger.warning("RAG dependencies or model loading failed: %s", exc)
        return []
    except Exception as exc:
        logger.exception("RAG retrieve failed: %s", exc)
        return []


def is_placeholder_evidence(content: str) -> bool:
    return "待补充" in str(content or "")
