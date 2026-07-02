"""
从 PrimeKG 的 kg.csv 中筛选与 100 种社区药店常见药物相关的数据。
输出精简数据集到 data/processed/primekg_core100_drug_dataset.csv
"""

import re
import sys
import time
from pathlib import Path

import pandas as pd


# ── 路径配置 ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "kg.csv"
OUT_PATH = PROJECT_ROOT / "data" / "processed" / "primekg_core100_drug_dataset.csv"

# ── 100 种核心药物 ───────────────────────────────────────
CORE_DRUGS = [
    # 心血管
    "Nifedipine", "Amlodipine", "Valsartan", "Irbesartan", "Losartan",
    "Telmisartan", "Enalapril", "Lisinopril", "Captopril", "Metoprolol",
    "Bisoprolol", "Atenolol", "Hydrochlorothiazide", "Furosemide", "Spironolactone",
    # 解热镇痛
    "Ibuprofen", "Aspirin", "Diclofenac", "Celecoxib", "Naproxen",
    "Meloxicam", "Indomethacin", "Acetaminophen", "Tramadol", "Codeine",
    # 抗凝/抗血小板
    "Warfarin", "Rivaroxaban", "Apixaban", "Dabigatran", "Clopidogrel",
    "Ticagrelor", "Heparin", "Enoxaparin",
    # 糖尿病
    "Metformin", "Glipizide", "Gliclazide", "Glimepiride", "Acarbose",
    "Insulin", "Sitagliptin", "Empagliflozin", "Dapagliflozin", "Liraglutide",
    # 调脂
    "Atorvastatin", "Rosuvastatin", "Simvastatin", "Pravastatin", "Ezetimibe",
    "Fenofibrate",
    # 消化系统
    "Omeprazole", "Pantoprazole", "Lansoprazole", "Famotidine", "Ranitidine",
    "Domperidone", "Metoclopramide", "Lactulose", "Loperamide",
    # 抗感染
    "Amoxicillin", "Clavulanate", "Azithromycin", "Clarithromycin", "Cefuroxime",
    "Cefixime", "Levofloxacin", "Ciprofloxacin", "Metronidazole", "Doxycycline",
    # 抗过敏/呼吸
    "Loratadine", "Cetirizine", "Fexofenadine", "Chlorpheniramine", "Diphenhydramine",
    "Montelukast", "Salbutamol", "Budesonide", "Theophylline",
    # 内分泌
    "Levothyroxine", "Methimazole", "Prednisone", "Dexamethasone", "Hydrocortisone",
    # 精神神经
    "Sertraline", "Fluoxetine", "Paroxetine", "Escitalopram", "Amitriptyline",
    "Diazepam", "Alprazolam", "Zolpidem",
    # 其他
    "Allopurinol", "Colchicine", "Febuxostat", "Calcium carbonate", "Vitamin D",
    "Ferrous sulfate", "Folic acid", "Potassium chloride", "Magnesium",
    "Isosorbide mononitrate",
]

# PrimeKG 中药物名称与核心药物名不一致的别名 → 核心药物名
DRUG_ALIASES: dict[str, str] = {
    "Acetylsalicylic acid": "Aspirin",
    "Clavulanic acid":      "Clavulanate",
}

# 合并：所有需要匹配的名称 → 对应的核心药物名
_all_match_names: dict[str, str] = {d: d for d in CORE_DRUGS}
for alias, canonical in DRUG_ALIASES.items():
    _all_match_names[alias] = canonical

# 预编译正则，按长度降序
_sorted_names = sorted(_all_match_names.keys(), key=len, reverse=True)
DRUG_PATTERNS: list[tuple[str, re.Pattern]] = [
    (name, re.compile(r"\b" + re.escape(name) + r"\b", re.IGNORECASE))
    for name in _sorted_names
]

# 需要保留的实体类型组合 → keep_reason
# (x_type, y_type) → reason
KEEP_TYPE_PAIRS = {
    ("drug", "drug"):             "drug_drug",
    ("drug", "disease"):          "drug_disease",
    ("disease", "drug"):          "drug_disease",
    ("drug", "effect/phenotype"): "drug_effect",
    ("effect/phenotype", "drug"): "drug_effect",
}


def match_core_drugs(name: str) -> list[str]:
    """返回 name 中命中的所有核心药物名（使用规范名）。"""
    hits = []
    for matched_name, pat in DRUG_PATTERNS:
        if pat.search(name):
            canonical = _all_match_names[matched_name]
            hits.append(canonical)
    return hits


def process_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    """处理一个 chunk，返回命中行（含新增列）。"""
    records = []

    for row in chunk.itertuples(index=False):
        x_type = row.x_type
        y_type = row.y_type

        # 第一层：关系类型筛选
        reason = KEEP_TYPE_PAIRS.get((x_type, y_type))
        if reason is None:
            continue

        # 第二层：核心药物匹配
        x_hits = match_core_drugs(row.x_name) if x_type == "drug" else []
        y_hits = match_core_drugs(row.y_name) if y_type == "drug" else []

        all_hits = x_hits + y_hits
        if not all_hits:
            continue

        # 去重（同一药物可能被多次命中，如 "Aspirin" 和 "aspirin"）
        unique_hits = list(dict.fromkeys(all_hits))

        record = row._asdict()
        record["keep_reason"] = reason
        record["matched_core_drug"] = ";".join(unique_hits)
        records.append(record)

    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records)


def main() -> None:
    # 检查源文件
    if not RAW_PATH.exists():
        print(f"错误: 找不到原始数据文件 {RAW_PATH}")
        print("请确认 data/raw/kg.csv 存在。")
        sys.exit(1)

    # 创建输出目录
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    print(f"源文件: {RAW_PATH}  ({RAW_PATH.stat().st_size / 1024 / 1024:.1f} MB)")
    print(f"输出到: {OUT_PATH}")
    print("开始分块扫描 ...")

    total_rows = 0
    chunks_processed = 0
    results: list[pd.DataFrame] = []
    t0 = time.time()

    for chunk in pd.read_csv(RAW_PATH, chunksize=500_000, low_memory=False):
        total_rows += len(chunk)
        chunks_processed += 1

        hit = process_chunk(chunk)
        if not hit.empty:
            results.append(hit)

        if chunks_processed % 5 == 0:
            elapsed = time.time() - t0
            print(f"  已扫描 {total_rows:>10,} 行  |  用时 {elapsed:.0f}s")

    elapsed = time.time() - t0
    print(f"  扫描完成，共 {total_rows:,} 行，用时 {elapsed:.1f}s")

    # 合并 & 去重
    if results:
        df = pd.concat(results, ignore_index=True)
        df.drop_duplicates(
            subset=["x_index", "y_index", "relation"],
            keep="first",
            inplace=True,
        )
        df.reset_index(drop=True, inplace=True)
    else:
        df = pd.DataFrame()
        print("\n警告: 没有命中任何数据，请检查药物名或数据内容。")

    # 写出
    df.to_csv(OUT_PATH, index=False)

    # ── 统计报告 ──────────────────────────────────────────
    matched_drugs = set()
    if not df.empty:
        for cell in df["matched_core_drug"]:
            for d in cell.split(";"):
                matched_drugs.add(d)

    unmatched = [d for d in CORE_DRUGS if d not in matched_drugs]

    out_size = OUT_PATH.stat().st_size
    if out_size > 1024 * 1024:
        size_str = f"{out_size / 1024 / 1024:.2f} MB"
    else:
        size_str = f"{out_size / 1024:.1f} KB"

    print("\n" + "=" * 60)
    print("数据清洗完成")
    print("=" * 60)
    print(f"原始扫描总行数      : {total_rows:,}")
    print(f"最终保留行数        : {len(df):,}")
    print(f"输出文件路径        : {OUT_PATH}")
    print(f"输出文件大小        : {size_str}")

    print(f"\n成功命中核心药物 ({len(matched_drugs)}/{len(CORE_DRUGS)}):")
    for d in sorted(matched_drugs):
        print(f"  [OK] {d}")

    if unmatched:
        print(f"\n未命中核心药物 ({len(unmatched)}):")
        for d in unmatched:
            print(f"  [MISS] {d}")
    else:
        print("\n所有核心药物均有命中！")

    if not df.empty:
        print("\nkeep_reason 分布:")
        for reason, cnt in df["keep_reason"].value_counts().items():
            print(f"  {reason:<20s} {cnt:>10,}")

    print()


if __name__ == "__main__":
    main()
