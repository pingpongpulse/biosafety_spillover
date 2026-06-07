"""
BioRiskNet v2 — apply_smote.py
Applies SMOTE to balance the 934-virus real-feature dataset.

Key changes from v1:
  - Feature columns updated to real biological features
  - NaN imputation BEFORE SMOTE (SMOTE cannot handle NaN)
  - Imputation uses median for numerical, mode for binary
  - k_neighbors=3 (safe for RG4 with 26 real samples)
  - Imputation strategy recorded in output for transparency

Input:  data/processed/rg_dataset_encoded.csv
Output: data/processed/smote_dataset.csv
        results/figures/smote_chart.png
"""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from imblearn.over_sampling import SMOTE
from collections import Counter

df = pd.read_csv('data/processed/rg_dataset_encoded.csv')

# Read feature cols dynamically from encoder_mappings if available
# Fallback: detect from column names
import json
try:
    with open('models/encoder_mappings.json') as f:
        enc = json.load(f)
    feature_cols = enc.get('_feature_cols', [])
    print(f"Feature cols from encoder_mappings.json: {feature_cols}")
except Exception:
    feature_cols = [c for c in df.columns if c not in ['name', 'rg_label', 'rg_label_raw', 'ncbi_tax_id',
                                                         'agent_type', 'feature_sources', 'source_count',
                                                         'n_real_features']]
    print(f"Feature cols detected from CSV: {feature_cols}")

# Keep only features that exist in the dataframe
feature_cols = [c for c in feature_cols if c in df.columns]
print(f"Using {len(feature_cols)} features: {feature_cols}")

X = df[feature_cols].copy()
y = df['rg_label'].copy()

print(f"\nBefore SMOTE: {dict(Counter(y))}")
print(f"Dataset shape: {X.shape}")

# ── NaN Imputation BEFORE SMOTE ────────────────────────────────────────────────
# SMOTE cannot handle NaN. We impute with the most conservative strategy:
#   - Binary features (0/1): impute with MODE (most common value)
#   - Numerical features (host_breadth): impute with MEDIAN
#   - Categorical encoded (integers): impute with MODE
# This is ONLY for the SMOTE step. The imputed values are NOT the real data.
# The real NaN structure is preserved in rg_dataset_encoded.csv and rg_dataset_real_features.csv

print("\n[NaN Imputation for SMOTE — using mode/median of real observations]")
imputation_log = {}
for col in feature_cols:
    n_nan = X[col].isna().sum()
    if n_nan == 0:
        continue
    if col == 'host_breadth':
        fill_val = X[col].median()
        strategy = 'median'
    else:
        fill_val = X[col].mode()[0] if not X[col].mode().empty else 0
        strategy = 'mode'
    X[col] = X[col].fillna(fill_val)
    imputation_log[col] = {'n_filled': int(n_nan), 'fill_value': float(fill_val), 'strategy': strategy}
    print(f"  {col:<25}: filled {n_nan} NaN with {strategy}={fill_val:.2f}")

# Ensure integer dtypes for binary features
for col in feature_cols:
    if col != 'host_breadth':
        X[col] = X[col].astype(int)

# ── SMOTE ──────────────────────────────────────────────────────────────────────
# k_neighbors=3: safe for RG4 which has only 26 real samples
# In 5-fold CV, each fold trains on ~80% of data => ~21 RG4 samples per fold
# k_neighbors=3 << 21, so no error
print(f"\n[Applying SMOTE: k_neighbors=3]")
smote     = SMOTE(random_state=42, k_neighbors=3)
X_res, y_res = smote.fit_resample(X, y)

print(f"After SMOTE:  {dict(Counter(y_res))}")
print(f"Dataset grew from {len(X)} to {len(X_res)} rows")
print(f"Balance check: all classes equal = {len(set(Counter(y_res).values())) == 1}")

# ── Save ───────────────────────────────────────────────────────────────────────
out = pd.DataFrame(X_res, columns=feature_cols)
out['rg_label'] = y_res
os.makedirs('data/processed', exist_ok=True)
out.to_csv('data/processed/smote_dataset.csv', index=False)
print("Saved: data/processed/smote_dataset.csv")

# Save imputation log for transparency
with open('data/processed/smote_imputation_log.json', 'w') as f:
    json.dump(imputation_log, f, indent=2)
print("Saved: data/processed/smote_imputation_log.json")

# ── Plot: Before vs After SMOTE ───────────────────────────────────────────────
os.makedirs('results/figures', exist_ok=True)
n_classes  = len(set(y))
labels     = [f'RG{i+1}' for i in range(n_classes)]
colors     = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444'][:n_classes]
before     = [Counter(y).get(i, 0)     for i in range(n_classes)]
after      = [Counter(y_res).get(i, 0) for i in range(n_classes)]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
for ax, counts, title in [(ax1, before, 'Before SMOTE (Real Data)'),
                           (ax2, after,  'After SMOTE (Balanced)')]:
    bars = ax.bar(labels, counts, color=colors, edgecolor='white')
    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.set_xlabel('WHO Risk Group')
    ax.set_ylabel('Count')
    for bar, v in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width() / 2,
                v + max(counts) * 0.02, str(v),
                ha='center', fontweight='bold', fontsize=10)

plt.suptitle('Viral Pathogen Dataset: Class Distribution Before vs After SMOTE',
             fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('results/figures/smote_chart.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: results/figures/smote_chart.png")

print("\n[Next Step]")
print("  Run: python scripts/train_model.py")