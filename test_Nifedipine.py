import pandas as pd

df = pd.read_csv("data/processed/primekg_core100_drug_dataset.csv", low_memory=False)

nifedipine = df[
    df["x_name"].astype(str).str.contains("Nifedipine", case=False, na=False) |
    df["y_name"].astype(str).str.contains("Nifedipine", case=False, na=False)
]

print("Nifedipine 相关关系数量：", len(nifedipine))
print(nifedipine["keep_reason"].value_counts())
print(nifedipine["display_relation"].value_counts())

print(
    nifedipine[
        ["x_name", "x_type", "display_relation", "y_name", "y_type", "keep_reason"]
    ].head(50)
)