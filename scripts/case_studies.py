"""
BioRiskNet v2 — case_studies.py
Person 4 Step 4.3: Viral pathogen case studies.

Uses ACTUAL ROWS from rg_dataset_encoded.csv — exact same feature encoding
as training. This avoids the synthetic feature vector problem.

Viruses selected for complete feature coverage:
  RG3: Severe acute respiratory syndrome coronavirus 2 (SARS-CoV-2)
  RG4: Orthomarburgvirus marburgense (Marburg virus — Filoviridae, ssRNA-, fully encoded)
  RG2: Alphainfluenzavirus influenzae (H1N1)pdm09 (Orthomyxoviridae, ssRNA-, fully encoded)

Run: python scripts/case_studies.py
"""
import pickle, json, os
import pandas as pd
import numpy as np

# ── Load model and encodings ──────────────────────────────────────────────────
model_path = os.path.join('models', 'xgboost_rg_classifier.pkl')
with open(model_path, 'rb') as f:
    model = pickle.load(f)

with open(os.path.join('models', 'encoder_mappings.json')) as f:
    enc = json.load(f)

feature_cols = enc.get('_feature_cols', [])

# ── Load encoded dataset ──────────────────────────────────────────────────────
df_enc  = pd.read_csv('data/processed/rg_dataset_encoded.csv')
df_real = pd.read_csv('data/processed/rg_dataset_real_features.csv')

# ── Select case study organisms ───────────────────────────────────────────────
# Strategy: pick organisms with the best feature coverage in the encoded dataset
# for each target RG. Prefer organisms with taxonomic_family_enc AND genome_type_enc.

CASE_STUDY_TARGETS = {
    # RG3 — SARS-CoV-2 (use actual row; NaN features are handled by XGBoost default routing)
    'SARS-CoV-2 (RG3)': {
        'search': 'SARS-CoV-2',
        'known_rg': 3,
        'display_name': 'SARS-CoV-2',
    },
    # RG4 — Marburg virus: fully encoded (Filoviridae=16, ssRNA-=5)
    'Marburg virus (RG4)': {
        'search': 'Orthomarburgvirus marburgense',
        'known_rg': 4,
        'display_name': 'Marburg virus (Orthomarburgvirus marburgense)',
    },
    # RG2 — Influenza A H1N1: fully encoded (Orthomyxoviridae=29, ssRNA-=5)
    'Influenza A H1N1 (RG2)': {
        'search': 'Alphainfluenzavirus influenzae (H1N1)pdm09',
        'known_rg': 2,
        'display_name': 'Influenza A virus (H1N1)pdm09',
    },
}

print('=' * 75)
print('BioRiskNet v2 — Viral Pathogen Case Studies (Person 4 Step 4.3)')
print('Dataset: 934 viral organisms | Features: ICTV + Olival + Virus-Host DB')
print('Method: Real encoded rows from training dataset (exact feature vectors)')
print('=' * 75)

results  = []
match_count = 0

for label, cfg in CASE_STUDY_TARGETS.items():
    search      = cfg['search']
    known_rg    = cfg['known_rg']
    display_name= cfg['display_name']

    # Find organism in encoded dataset (exact first, then partial)
    row = df_enc[df_enc['name'] == search]
    if row.empty:
        row = df_enc[df_enc['name'].str.contains(search.split()[0], case=False, na=False)]
    if row.empty:
        print(f"[NOT FOUND] {search}")
        continue

    row = row.iloc[[0]]  # take first match

    # Feature vector — exact same as training
    X         = row[feature_cols].copy()
    raw_pred  = model.predict(X)[0]
    pred_rg   = int(raw_pred) + 1    # 0-indexed back to RG1-4
    proba     = model.predict_proba(X)[0]
    confidence= proba[raw_pred]
    off       = abs(pred_rg - known_rg)
    is_match  = off == 0
    if is_match:
        match_count += 1

    # Feature completeness for this row
    n_features = int(X.notna().sum().sum())
    n_total    = len(feature_cols)

    # Look up real feature values for display
    real_row = df_real[df_real['name'].str.contains(search.split()[0], case=False, na=False)]
    family   = real_row.iloc[0]['taxonomic_family'] if not real_row.empty else 'N/A'
    genome   = real_row.iloc[0]['genome_type']      if not real_row.empty else 'N/A'

    match_str = 'CORRECT' if is_match else f'off by {off}'
    print(f"\nOrganism:   {display_name}")
    print(f"Family:     {family}  |  Genome: {genome}  |  Features: {n_features}/{n_total} present")
    print(f"Predicted:  RG{pred_rg}  (confidence: {confidence:.1%})")
    print(f"Known:      RG{known_rg}")
    print(f"Match:      {'YES [PASS]' if is_match else f'NO [FAIL] — {match_str}'}")

    results.append({
        'Pathogen':         display_name,
        'Predicted_RG':     pred_rg,
        'Known_RG':         known_rg,
        'Match':            'YES' if is_match else 'NO',
        'Off_By':           off,
        'Confidence':       round(float(confidence), 3),
        'Taxonomic_Family': family,
        'Genome_Type':      genome,
        'Features_Present': f'{n_features}/{n_total}',
    })

print('\n' + '=' * 75)
print(f'SUMMARY: {match_count}/{len(results)} match known Risk Group')
print(f'Threshold >=2/3: {"MET" if match_count >= 2 else "NOT MET"}')

# ── Feature coverage diagnostic ───────────────────────────────────────────────
print('\n[Feature coverage per case study]')
for cfg in CASE_STUDY_TARGETS.values():
    row = df_enc[df_enc['name'].str.contains(
        cfg['search'].split()[0], case=False, na=False)]
    if not row.empty:
        vals = row.iloc[0][feature_cols]
        coverage = {c: ('NaN' if pd.isna(v) else v) for c, v in vals.items()}
        print(f"\n  {cfg['display_name']}:")
        for c, v in coverage.items():
            print(f"    {c:<25}: {v}")

# ── Save ───────────────────────────────────────────────────────────────────────
os.makedirs('results', exist_ok=True)
if results:
    pd.DataFrame(results).to_csv('results/case_study_results.csv', index=False)
    print('\nSaved: results/case_study_results.csv')
