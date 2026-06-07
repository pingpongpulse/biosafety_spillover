"""
BioRiskNet v2 — train_model.py
Trains XGBoost RG classifier on REAL biological features (no LLM data).
GPU-accelerated via RTX 4050 (CUDA 13.1).

Input:  data/processed/smote_dataset.csv
Output: models/xgboost_rg_classifier.pkl
        results/model_results.json
        results/feature_importances.csv
"""
import pandas as pd
import numpy as np
import xgboost as xgb
import pickle, json, os
from sklearn.model_selection import StratifiedKFold, cross_val_score, cross_val_predict
from sklearn.metrics import classification_report

# ── Detect GPU ─────────────────────────────────────────────────────────────────
try:
    import subprocess
    result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
    GPU_AVAILABLE = result.returncode == 0
except Exception:
    GPU_AVAILABLE = False

DEVICE      = 'cuda' if GPU_AVAILABLE else 'cpu'
TREE_METHOD = 'hist'
print(f"Device: {DEVICE.upper()}  (RTX 4050 Laptop)" if GPU_AVAILABLE else "Device: CPU")

# ── Load data ──────────────────────────────────────────────────────────────────
df = pd.read_csv('data/processed/smote_dataset.csv')

# Dynamically detect feature columns — all columns except the label
# This ensures taxonomic_family_enc and future features are always included
NON_FEATURE_COLS = {'rg_label', 'rg_label_raw', 'name', 'ncbi_tax_id',
                    'agent_type', 'feature_sources', 'source_count', 'n_real_features'}
feature_cols = [c for c in df.columns if c not in NON_FEATURE_COLS]

X = df[feature_cols]
y = df['rg_label']

print(f"\nTraining data: {X.shape[0]} rows, {X.shape[1]} features")
print(f"Features used: {feature_cols}")
print(f"Label distribution: {dict(y.value_counts().sort_index())}")

# ── Model — anti-overfit settings for ~900–1500 viral organisms ───────────────
# max_depth=4 (not 6): prevents memorizing noise on small dataset
# min_child_weight=5:  no split on fewer than 5 samples
# subsample=0.8:       trains on 80% random rows per tree
# colsample_bytree=0.8: uses 80% of features per tree
model = xgb.XGBClassifier(
    n_estimators=150,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    min_child_weight=5,
    reg_alpha=0.1,         # L1 regularisation
    reg_lambda=1.0,        # L2 regularisation
    eval_metric='mlogloss',
    random_state=42,
    device=DEVICE,
    tree_method=TREE_METHOD,
    verbosity=0,
)

# ── 5-fold CV ──────────────────────────────────────────────────────────────────
print("\nRunning 5-fold stratified CV...")
cv      = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_f1   = cross_val_score(model, X, y, cv=cv, scoring='f1_macro',   n_jobs=1)
cv_acc  = cross_val_score(model, X, y, cv=cv, scoring='accuracy',   n_jobs=1)

print(f"F1-macro per fold: {[round(s,3) for s in cv_f1]}")
print(f"F1-macro mean:     {cv_f1.mean():.3f} +/- {cv_f1.std():.3f}")
print(f"Accuracy mean:     {cv_acc.mean():.3f} +/- {cv_acc.std():.3f}")

if cv_f1.std() > 0.08:
    print("WARNING: High CV variance — model may be unstable. Consider reducing max_depth further.")

# ── Train final model on all data ─────────────────────────────────────────────
print("\nTraining final model on full dataset...")
model.fit(X, y)

# ── Full classification report ────────────────────────────────────────────────
y_cv_pred = cross_val_predict(model, X, y, cv=cv)
n_classes  = len(y.unique())
class_names= ['RG1','RG2','RG3','RG4'][:n_classes]
print("\nClassification Report (5-fold CV predictions):")
print(classification_report(y, y_cv_pred, target_names=class_names))

# ── Save model ────────────────────────────────────────────────────────────────
os.makedirs('models', exist_ok=True)
with open('models/xgboost_rg_classifier.pkl', 'wb') as f:
    pickle.dump(model, f)
print("Saved: models/xgboost_rg_classifier.pkl")

# ── Save metrics ───────────────────────────────────────────────────────────────
os.makedirs('results', exist_ok=True)
results = {
    'cv_f1_macro_mean':   round(float(cv_f1.mean()),  4),
    'cv_f1_macro_std':    round(float(cv_f1.std()),   4),
    'cv_f1_macro_scores': [round(float(s), 4) for s in cv_f1],
    'cv_accuracy_mean':   round(float(cv_acc.mean()), 4),
    'cv_accuracy_std':    round(float(cv_acc.std()),  4),
    'training_samples':   int(len(X)),
    'feature_names':      feature_cols,
    'class_labels':       class_names,
    'device':             DEVICE,
    'model_params': {
        'n_estimators': 150, 'max_depth': 4,
        'learning_rate': 0.05, 'min_child_weight': 5,
    },
    'dataset_note': 'Viral pathogens only. Real biological features from ICTV/Virus-Host DB/Olival. Zero LLM imputation.'
}
with open('results/model_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print("Saved: results/model_results.json")

# ── Feature importances ────────────────────────────────────────────────────────
fi = pd.DataFrame({
    'feature':    feature_cols,
    'importance': model.feature_importances_,
})
fi = fi.sort_values('importance', ascending=False)
print("\nFeature importances (real biological features):")
print(fi.to_string(index=False))
fi.to_csv('results/feature_importances.csv', index=False)
print("Saved: results/feature_importances.csv")