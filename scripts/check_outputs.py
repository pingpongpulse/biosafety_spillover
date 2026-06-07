"""
BioRiskNet — Person 4 Step 4.1
Output validation script: checks every required file exists and loads correctly.
Run from the project root: python scripts/check_outputs.py
"""
import os
import json
import pickle

# ── Required files checklist ────────────────────────────────────────────────
required_files = [
    'models/xgboost_rg_classifier.pkl',
    'models/encoder_mappings.json',
    'results/spillover_model.pkl',
    'results/model_results.json',
    'results/feature_importances.csv',
    'results/figures/confusion_matrix.png',
    'results/figures/shap_summary_bar.png',
    'results/figures/shap_beeswarm_rg3.png',
    'results/figures/shap_spillover.png',
    'results/figures/shap_case_SARS_CoV_2.png',
    'results/figures/shap_case_Ebola_virus.png',
    'results/figures/shap_case_Escherichia_coli.png',
    'results/tables/per_class_metrics.csv',
    'results/tables/model_summary.csv',
]

optional_files = [
    'results/summary_table.csv',
    'results/spillover_results.json',
    'results/case_study_results.txt',
    'results/shap_validation.txt',
    'README.md',
]

print('=' * 60)
print('BioRiskNet — Output Check (Person 4 Step 4.1)')
print('=' * 60)

all_good = True

print('\n[REQUIRED FILES]')
for f in required_files:
    if os.path.exists(f):
        size_kb = os.path.getsize(f) / 1024
        print(f'  [OK]      {f}  ({size_kb:.1f} KB)')
    else:
        print(f'  [MISSING] {f}')
        all_good = False

print('\n[OPTIONAL / PERSON 4 OUTPUTS]')
for f in optional_files:
    if os.path.exists(f):
        size_kb = os.path.getsize(f) / 1024
        print(f'  [OK]      {f}  ({size_kb:.1f} KB)')
    else:
        print(f'  [MISSING] {f}')

# ── Load checks ──────────────────────────────────────────────────────────────
print('\n[LOAD CHECKS]')

try:
    with open('models/xgboost_rg_classifier.pkl', 'rb') as f:
        model = pickle.load(f)
    n_est = getattr(model, 'n_estimators', '?')
    print(f'  [OK]  xgboost_rg_classifier.pkl loads cleanly  (n_estimators={n_est})')
except Exception as e:
    print(f'  [FAIL] xgboost_rg_classifier.pkl: {e}')
    all_good = False

try:
    with open('results/spillover_model.pkl', 'rb') as f:
        sp_model = pickle.load(f)
    print(f'  [OK]  spillover_model.pkl loads cleanly')
except Exception as e:
    print(f'  [FAIL] spillover_model.pkl: {e}')
    all_good = False

try:
    with open('results/model_results.json') as f:
        r = json.load(f)
    cv = r.get('cv_f1_macro_mean', r.get('cv_mean', 0))
    target = '>= 0.70'
    status = 'OK' if cv >= 0.70 else 'LOW — below 0.70 target'
    print(f'  [{status}]  CV F1-macro = {cv:.4f}  (target {target})')
    if cv < 0.70:
        all_good = False
except Exception as e:
    print(f'  [FAIL] model_results.json: {e}')
    all_good = False

try:
    with open('models/encoder_mappings.json') as f:
        enc = json.load(f)
    print(f'  [OK]  encoder_mappings.json loaded  ({len(enc)} feature mappings)')
except Exception as e:
    print(f'  [FAIL] encoder_mappings.json: {e}')
    all_good = False

if os.path.exists('results/spillover_results.json'):
    try:
        with open('results/spillover_results.json') as f:
            sp = json.load(f)
        auc = sp.get('cv_auc_mean', 0)
        status = 'OK' if auc >= 0.75 else 'LOW — below 0.75 target'
        print(f'  [{status}]  Spillover AUC = {auc:.4f}  (target >= 0.75)')
    except Exception as e:
        print(f'  [FAIL] spillover_results.json: {e}')

# ── Figure DPI check (file size proxy) ───────────────────────────────────────
print('\n[FIGURE SIZE CHECK (proxy for 300 DPI)]')
figure_min_kb = 50  # any valid 300 DPI figure should be well above this
figure_files = [f for f in required_files if f.endswith('.png')]
for fig in figure_files:
    if os.path.exists(fig):
        size_kb = os.path.getsize(fig) / 1024
        status = 'OK' if size_kb >= figure_min_kb else 'SMALL — may not be 300 DPI'
        print(f'  [{status}]  {fig}  ({size_kb:.1f} KB)')

# ── Final verdict ─────────────────────────────────────────────────────────────
print('\n' + '=' * 60)
if all_good:
    print('ALL REQUIRED OUTPUTS PRESENT AND VALID.')
    print('You are ready to write the GitHub README and finalise.')
else:
    print('SOME REQUIRED FILES ARE MISSING OR INVALID.')
    print('Follow up with Person 2/3 for any missing required files.')
print('=' * 60)
