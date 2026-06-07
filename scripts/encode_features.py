"""
BioRiskNet v2 — encode_features.py
Encodes real viral biological features for XGBoost training.
ALL 9 features retained after improved Olival matching (37-45% coverage).
XGBoost handles NaN natively — NO LLM imputation.

Input:  data/processed/rg_dataset_real_features.csv
Output: data/processed/rg_dataset_encoded.csv
        models/encoder_mappings.json  (updated)
"""
import pandas as pd
import numpy as np
import json, os
from sklearn.preprocessing import LabelEncoder

df = pd.read_csv('data/processed/rg_dataset_real_features.csv')
print(f"Loaded: {df.shape[0]} viral organisms, {df.shape[1]} columns")
print(f"RG distribution: {df['rg_label'].value_counts().sort_index().to_dict()}")

# ── Feature selection ──────────────────────────────────────────────────────────
# ALL 9 FEATURES RETAINED — Olival matching improved to 37-45% coverage
# genome_type (84.5%), is_dna (84.5%), is_enveloped (83.5%)  <- ICTV / family lookup
# taxonomic_family (84.5%)                                    <- ICTV
# is_segmented (37.9%), is_vector_borne (36.8%), is_zoonotic (37.9%) <- Olival 2017
# host_breadth (45.5%), infects_humans (12.5%)               <- Virus-Host DB

CATEGORICAL_FEATURES = ['genome_type', 'taxonomic_family']
BINARY_FEATURES      = ['is_dna', 'is_enveloped', 'is_segmented',
                         'is_vector_borne', 'is_zoonotic', 'infects_humans']
NUMERICAL_FEATURES   = ['host_breadth']

print(f"\n[Feature Coverage Report]")
all_feat = CATEGORICAL_FEATURES + BINARY_FEATURES + NUMERICAL_FEATURES
for col in all_feat:
    if col in df.columns:
        n = df[col].notna().sum()
        pct = 100 * n / len(df)
        print(f"  {col:<22}: {n:4d}/{len(df)} ({pct:.1f}%)")
    else:
        print(f"  {col:<22}: MISSING from dataset")

encoder_mappings = {}

# ── Categorical: LabelEncoder (genome_type, taxonomic_family) ─────────────────
for col in CATEGORICAL_FEATURES:
    if col not in df.columns:
        print(f"WARNING: {col} not in dataset — skipping")
        continue
    enc_col = col + '_enc'
    df[col] = df[col].fillna('unknown')
    le = LabelEncoder()
    df[enc_col] = le.fit_transform(df[col].astype(str))
    encoder_mappings[col] = dict(zip(
        le.classes_.tolist(),
        le.transform(le.classes_).tolist()
    ))
    n_cats = len(le.classes_)
    print(f"\nEncoded {col} -> {enc_col}  ({n_cats} categories)")
    if n_cats <= 20:
        print(f"  Mapping: {encoder_mappings[col]}")

# ── Binary: 0/1/NaN — NaN stays NaN for XGBoost to handle natively ───────────
for col in BINARY_FEATURES:
    if col not in df.columns:
        print(f"WARNING: {col} not in dataset — skipping")
        continue
    n_nan = df[col].isna().sum()
    print(f"Binary {col:<22}: {df[col].notna().sum()} filled, {n_nan} NaN (XGBoost handles)")

# ── Numerical: host_breadth — keep raw, NaN stays NaN ────────────────────────
for col in NUMERICAL_FEATURES:
    if col in df.columns:
        n_nan = df[col].isna().sum()
        print(f"Numerical {col:<20}: {df[col].notna().sum()} filled, {n_nan} NaN")

# ── Build encoded feature list ─────────────────────────────────────────────────
enc_feature_cols = []
for col in CATEGORICAL_FEATURES:
    enc_col = col + '_enc'
    if enc_col in df.columns:
        enc_feature_cols.append(enc_col)
for col in BINARY_FEATURES + NUMERICAL_FEATURES:
    if col in df.columns:
        enc_feature_cols.append(col)

print(f"\nFinal encoded feature set ({len(enc_feature_cols)} features):")
for c in enc_feature_cols:
    print(f"  {c}")

# ── Convert RG labels to 0-indexed for XGBoost ───────────────────────────────
# XGBoost needs 0-indexed: RG1->0, RG2->1, RG3->2, RG4->3
df['rg_label_raw'] = df['rg_label'].astype(int)
df['rg_label']     = df['rg_label'].astype(int) - 1

print(f"\nRG label encoding: RG1->0, RG2->1, RG3->2, RG4->3")
print(f"Class counts (0-indexed): {dict(df['rg_label'].value_counts().sort_index())}")

# ── Save encoded dataset ───────────────────────────────────────────────────────
cols_to_save = ['name', 'rg_label', 'rg_label_raw'] + enc_feature_cols
df_out = df[cols_to_save].copy()
os.makedirs('data/processed', exist_ok=True)
df_out.to_csv('data/processed/rg_dataset_encoded.csv', index=False)
print(f"\nSaved: data/processed/rg_dataset_encoded.csv  ({df_out.shape})")

# ── Save encoder mappings ──────────────────────────────────────────────────────
encoder_mappings['_feature_cols']    = enc_feature_cols
encoder_mappings['_dropped']         = []
encoder_mappings['_drop_reason']     = 'All features retained: Olival matching improved to 37-45% coverage'
encoder_mappings['_xgb_label_note']  = 'rg_label is 0-indexed: 0=RG1, 1=RG2, 2=RG3, 3=RG4'
encoder_mappings['_nan_handling']    = 'NaN left as NaN — XGBoost native handling'
encoder_mappings['_dataset_note']    = '934 viral pathogens. Real features from ICTV/Virus-Host DB/Olival 2017. Zero LLM imputation.'

os.makedirs('models', exist_ok=True)
with open('models/encoder_mappings.json', 'w') as f:
    json.dump(encoder_mappings, f, indent=2)
print("Saved: models/encoder_mappings.json")

print("\n[Next Step]")
print("  Run: python scripts/apply_smote.py")