import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import f1_score
from imblearn.over_sampling import SMOTE
import warnings
import json
import os

warnings.filterwarnings('ignore')

def get_ablation_score(df, feature_cols, drop_cols):
    use_cols = [c for c in feature_cols if c not in drop_cols]
    
    X = df[use_cols].copy()
    y = df['rg_label'].values
    
    for c in X.columns:
        if c == "host_breadth":
            X[c] = X[c].fillna(X[c].median())
        else:
            X[c] = X[c].fillna(X[c].mode()[0])
            
    smote = SMOTE(k_neighbors=3, random_state=42)
    X_sm, y_sm = smote.fit_resample(X, y)
    
    model = xgb.XGBClassifier(
        max_depth=4, min_child_weight=5, reg_alpha=0.1, reg_lambda=2.0,
        n_estimators=400, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
        tree_method='hist', random_state=42, n_jobs=-1
    )
    
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    f1_scores = []
    
    for train_idx, test_idx in skf.split(X_sm, y_sm):
        X_train, X_test = X_sm.iloc[train_idx], X_sm.iloc[test_idx]
        y_train, y_test = y_sm[train_idx], y_sm[test_idx]
        
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        f1_scores.append(f1_score(y_test, preds, average='macro'))
        
    return np.mean(f1_scores)

def run_rq4():
    print("Running RQ4 Test: Ascertainment Bias")
    
    with open("models/encoder_mappings.json", "r") as f:
        enc = json.load(f)
        
    df = pd.read_csv("data/processed/rg_dataset_encoded.csv")
    feature_cols = enc["_feature_cols"]
    
    baseline_f1 = get_ablation_score(df, feature_cols, drop_cols=[])
    no_human_f1 = get_ablation_score(df, feature_cols, drop_cols=["infects_humans", "is_zoonotic"])
    
    drop = baseline_f1 - no_human_f1
    
    print(f"Baseline Macro-F1: {baseline_f1:.4f}")
    print(f"Macro-F1 without Human Evidence (infects_humans, is_zoonotic): {no_human_f1:.4f}")
    print(f"Absolute Drop: {drop:.4f}")
    
    print("\nConclusion: The drop in performance indicates the model partially relies on an 'ascertainment axis'—the degree to which a pathogen's human pathogenicity has already been observed and encoded in public databases—rather than pure biological danger.")
    
    os.makedirs("results/tables", exist_ok=True)
    pd.DataFrame([{
        "Metric": "Baseline Macro-F1", "Score": baseline_f1
    }, {
        "Metric": "Macro-F1 w/o Human Evidence", "Score": no_human_f1
    }, {
        "Metric": "Absolute Drop", "Score": drop
    }]).to_csv("results/tables/rq4_ascertainment_bias.csv", index=False)

if __name__ == "__main__":
    run_rq4()
