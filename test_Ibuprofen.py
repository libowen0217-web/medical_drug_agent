import pandas as pd

df = pd.read_csv("data/processed/primekg_core100_drug_dataset.csv", low_memory=False)

ibuprofen = df[
    df["x_name"].astype(str).str.contains("Ibuprofen", case=False, na=False) |
    df["y_name"].astype(str).str.contains("Ibuprofen", case=False, na=False)
]

print("Ibuprofen 相关关系数量：", len(ibuprofen))
print(ibuprofen["keep_reason"].value_counts())
print(ibuprofen["display_relation"].value_counts())

print(
    ibuprofen[
        ["x_name", "x_type", "display_relation", "y_name", "y_type", "keep_reason"]
    ].head(50)
)