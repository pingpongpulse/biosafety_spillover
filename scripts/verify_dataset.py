import pandas as pd

df = pd.read_csv('data/processed/rg_dataset_features.csv')

print(f"Shape: {df.shape}")
assert df.shape == (7765, 9), f"WRONG SHAPE: {df.shape} — tell Person 1"

print(f"Missing values: {df.isnull().sum().sum()}")
assert df.isnull().sum().sum() == 0, "MISSING VALUES — tell Person 1"

print(f"RG labels: {sorted(df['rg_label'].unique())}")
assert sorted(df['rg_label'].unique()) == [1,2,3,4], "BAD LABELS"

print("\nClass distribution:")
for rg, count in df['rg_label'].value_counts().sort_index().items():
    print(f"  RG{rg}: {count}  {'#' * int(count/50)}")

print("\nVERIFICATION PASSED")