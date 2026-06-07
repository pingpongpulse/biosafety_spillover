"""
BioRiskNet — Person 4 Step 4.3
Real pathogen case studies: load trained XGBoost model, run 3 known pathogens,
compare predictions to actual WHO Risk Group.

Encoding values come directly from models/encoder_mappings.json:
  genome_type:            DNA=0 RNA=1 dsDNA=2 dsRNA=3 none=4 prion=5 protein=6 ssDNA=7 ssRNA+=8 ssRNA-=9
  transmission_route:     airborne=0 contact=1 droplet=2 fecal-oral=3 inhalation=4 none=5 tick=6 vector=7 water=8 waterborne=9
  host_range:             broad=0 human-only=1 narrow=2
  environmental_stability:high=0 low=1 medium=2 none=3
  treatment_available:    no=0 partial=1 yes=2
  infectious_dose:        high=0 low=1 medium=2 none=3
  zoonotic:               no=0 yes=1

Run from project root: python scripts/case_studies.py > results/case_study_results.txt
"""
import pickle
import pandas as pd
import json
import os

# Load model
model_path = os.path.join('models', 'xgboost_rg_classifier.pkl')
if not os.path.exists(model_path):
    raise FileNotFoundError(f'Model not found at {model_path}. Run train_model.py first.')

with open(model_path, 'rb') as f:
    model = pickle.load(f)

# Load encoder mappings (for reference / verification)
with open(os.path.join('models', 'encoder_mappings.json')) as f:
    enc = json.load(f)

feature_cols = [
    'genome_type_enc', 'transmission_route_enc', 'host_range_enc',
    'environmental_stability_enc', 'treatment_available_enc',
    'infectious_dose_enc', 'zoonotic_enc'
]

# ── Case study definitions ───────────────────────────────────────────────────
# Values verified against models/encoder_mappings.json
case_studies = {
    'SARS-CoV-2': {
        # ssRNA+ virus, airborne, broad host range, medium env stability,
        # partial treatment (antivirals), low infectious dose, zoonotic
        'genome_type_enc':              enc['genome_type']['ssRNA+'],      # 8
        'transmission_route_enc':       enc['transmission_route']['airborne'],  # 0
        'host_range_enc':               enc['host_range']['broad'],        # 0
        'environmental_stability_enc':  enc['environmental_stability']['medium'],  # 2
        'treatment_available_enc':      enc['treatment_available']['partial'],  # 1
        'infectious_dose_enc':          enc['infectious_dose']['low'],     # 1
        'zoonotic_enc':                 enc['zoonotic']['yes'],            # 1
    },
    'Ebola virus': {
        # ssRNA- virus, contact transmission, narrow host range, low env stability,
        # partial treatment (mAbs approved 2020), low infectious dose, zoonotic
        'genome_type_enc':              enc['genome_type']['ssRNA-'],      # 9
        'transmission_route_enc':       enc['transmission_route']['contact'],  # 1
        'host_range_enc':               enc['host_range']['narrow'],       # 2
        'environmental_stability_enc':  enc['environmental_stability']['low'],  # 1
        'treatment_available_enc':      enc['treatment_available']['partial'],  # 1
        'infectious_dose_enc':          enc['infectious_dose']['low'],     # 1
        'zoonotic_enc':                 enc['zoonotic']['yes'],            # 1
    },
    'Escherichia coli K12': {
        # dsDNA bacterium, fecal-oral, broad host range, medium env stability,
        # yes treatment (antibiotics), high infectious dose, not zoonotic
        'genome_type_enc':              enc['genome_type']['dsDNA'],       # 2
        'transmission_route_enc':       enc['transmission_route']['fecal-oral'],  # 3
        'host_range_enc':               enc['host_range']['broad'],        # 0
        'environmental_stability_enc':  enc['environmental_stability']['medium'],  # 2
        'treatment_available_enc':      enc['treatment_available']['yes'],  # 2
        'infectious_dose_enc':          enc['infectious_dose']['high'],    # 0
        'zoonotic_enc':                 enc['zoonotic']['no'],             # 0
    },
}

# Known WHO Risk Group for each pathogen
known_rg = {
    'SARS-CoV-2':          3,   # WHO RG3 / BSL-3 (select agent handling)
    'Ebola virus':         4,   # WHO RG4 / BSL-4
    'Escherichia coli K12': 1,  # WHO RG1 (non-pathogenic lab strain)
}

# Biological rationale for each prediction
rationale = {
    'SARS-CoV-2': (
        'Airborne ssRNA+ virus with broad host range and partial treatment availability. '
        'Low infectious dose and high community transmissibility place it at RG3 per WHO/CDC guidelines.'
    ),
    'Ebola virus': (
        'Filovirus (ssRNA-) with high fatality rate, low infectious dose via direct contact, '
        'and narrow host range. Historically no approved treatment — now partial. '
        'BSL-4 / RG4 due to life-threatening disease and no fully effective prophylaxis.'
    ),
    'Escherichia coli K12': (
        'dsDNA bacterium, fecal-oral transmission, broad host range. K12 strain is '
        'the standard non-pathogenic lab strain. Fully antibiotic-treatable. WHO RG1.'
    ),
}

# ── Run predictions ───────────────────────────────────────────────────────────
print('=' * 70)
print('BioRiskNet — Case Study Results (Person 4 Step 4.3)')
print('=' * 70)
print()
print(f'{"Pathogen":<25} {"Predicted RG":<15} {"Known RG":<12} {"Match":<20}')
print('-' * 70)

results = []
match_count = 0

for name, features in case_studies.items():
    X = pd.DataFrame([features], columns=feature_cols)
    raw_pred = model.predict(X)[0]
    pred_rg = int(raw_pred) + 1        # convert 0-indexed back to 1–4
    proba = model.predict_proba(X)[0]  # confidence scores for all 4 classes
    confidence = proba[raw_pred]

    known = known_rg[name]
    off = abs(pred_rg - known)
    match_str = 'CORRECT' if off == 0 else f'off by {off}'
    if off == 0:
        match_count += 1

    print(f'{name:<25} RG{pred_rg:<14} RG{known:<11} {match_str}')
    results.append({
        'Pathogen': name,
        'Predicted_RG': pred_rg,
        'Known_RG': known,
        'Match': 'YES' if off == 0 else 'NO',
        'Off_By': off,
        'Confidence': round(float(confidence), 3),
    })

print()
print(f'Summary: {match_count}/{len(case_studies)} predictions match known Risk Group')
print(f'Procedure book threshold: >=2/3 correct')
threshold_met = match_count >= 2
print(f'Threshold met: {"YES — results are valid" if threshold_met else "NO — investigate model"}')

# ── Per-pathogen detail ───────────────────────────────────────────────────────
print()
print('=' * 70)
print('DETAILED BREAKDOWN')
print('=' * 70)
for r in results:
    name = r['Pathogen']
    print(f'\nPathogen:     {name}')
    print(f'Predicted:    RG{r["Predicted_RG"]}   (confidence: {r["Confidence"]:.1%})')
    print(f'Known:        RG{r["Known_RG"]}')
    match_sym = '[PASS]' if r["Match"] == "YES" else '[FAIL]'
    print(f'Match:        {r["Match"]} {match_sym}')
    print(f'Rationale:    {rationale[name]}')

# ── Save CSV ──────────────────────────────────────────────────────────────────
os.makedirs('results', exist_ok=True)
df_out = pd.DataFrame(results)
df_out.to_csv('results/case_study_results.csv', index=False)
print()
print('Saved: results/case_study_results.txt  (this console output)')
print('Saved: results/case_study_results.csv')

# ── Encoder reference (for paper methods section) ─────────────────────────────
print()
print('=' * 70)
print('ENCODER MAPPINGS USED (from models/encoder_mappings.json)')
print('=' * 70)
for feature, mapping in enc.items():
    print(f'  {feature}: {mapping}')
