import pandas as pd
import json, os
from sklearn.preprocessing import LabelEncoder

df = pd.read_csv('data/processed/rg_dataset_features.csv')

cat_cols = [
    'genome_type', 'transmission_route', 'host_range',
    'environmental_stability', 'treatment_available',
    'infectious_dose', 'zoonotic'
]

encoder_mappings = {}

for col in cat_cols:
    le = LabelEncoder()
    df[col + '_enc'] = le.fit_transform(df[col].astype(str))
    encoder_mappings[col] = dict(zip(le.classes_, le.transform(le.classes_).tolist()))
    print(f"{col}: {encoder_mappings[col]}")

feature_cols = [c + '_enc' for c in cat_cols]
encoded = df[feature_cols].copy()
encoded['rg_label_raw'] = df['rg_label'].astype(int)
encoded['rg_label'] = df['rg_label'].astype(int) - 1  # XGBoost needs 0-indexed

encoded.to_csv('data/processed/rg_dataset_encoded.csv', index=False)
print(f"\nSaved encoded dataset: {encoded.shape}")

os.makedirs('models', exist_ok=True)
with open('models/encoder_mappings.json', 'w') as f:
    json.dump(encoder_mappings, f, indent=2)

# IMPORTANT: Person 3 needs encoder_mappings.json for case studies
print("Saved: models/encoder_mappings.json — share this with Person 3")