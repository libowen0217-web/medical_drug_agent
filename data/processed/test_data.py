import pandas as pd
from pathlib import Path

path = Path(__file__).resolve().parent / "primekg_core100_drug_dataset.csv"

df = pd.read_csv(path, low_memory=False)

print("数据行数和列数：")
print(df.shape)

print("\nkeep_reason 统计：")
print(df["keep_reason"].value_counts())

print("\n节点类型组合统计：")
print(pd.crosstab(df["x_type"], df["y_type"]))

print("\nrelation 统计：")
print(df["relation"].value_counts().head(30))

print("\ndisplay_relation 统计：")
print(df["display_relation"].value_counts().head(30))

print("\n命中的核心药物数量：")
matched = set()

for item in df["matched_core_drug"].dropna():
    for drug in str(item).split(";"):
        drug = drug.strip()
        if drug:
            matched.add(drug)

print(len(matched))
print(sorted(matched))

print("\n前20行示例：")
print(
    df[
        [
            "x_name",
            "x_type",
            "display_relation",
            "y_name",
            "y_type",
            "keep_reason",
            "matched_core_drug",
        ]
    ].head(20)
)