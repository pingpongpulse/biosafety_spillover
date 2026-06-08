import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import f1_score
from imblearn.over_sampling import SMOTE
import warnings
import json
import os

warnings.filterwarnings('ignore')

def run_lfo_validation():
    print("Running Leave-Family-Out Validation...")
    
    with open("models/encoder_mappings.json", "r") as f:
        enc = json.load(f)
        
    df = pd.read_csv("data/processed/rg_dataset_encoded.csv")
    feature_cols = enc["_feature_cols"]
    
    # We remove family from the training features for this test to see if other traits generalize
    train_cols = [c for c in feature_cols if c != "taxonomic_family_enc"]
    
    X = df[train_cols].copy()
    y = df['rg_label'].values
    groups = df['taxonomic_family_enc'].values
    
    # Simple median/mode imputation for CV
    for c in X.columns:
        if c == "host_breadth":
            X[c] = X[c].fillna(X[c].median())
        else:
            X[c] = X[c].fillna(X[c].mode()[0])
            
    logo = LeaveOneGroupOut()
    
    f1_scores = []
    
    # Due to small sizes of some families, we only evaluate on families with at least 5 members
    # and we skip families where it's impossible to evaluate (e.g. RG4 only appears in Filoviridae and Arenaviridae, 
    # if we leave them out, the model might not predict RG4 well, but that's exactly what we want to test).
    
    valid_groups = df['taxonomic_family_enc'].value_counts()
    valid_groups = valid_groups[valid_groups >= 5].index.tolist()
    
    for train_idx, test_idx in logo.split(X, y, groups):
        group_id = groups[test_idx[0]]
        if group_id not in valid_groups:
            continue
            
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Apply SMOTE to training fold
        smote = SMOTE(k_neighbors=3, random_state=42)
        try:
            X_train_sm, y_train_sm = smote.fit_resample(X_train, y_train)
        except ValueError:
            # Skip if a class is entirely missing from train fold (e.g., if the left-out family contained ALL RG4s)
            continue
            
        model = xgb.XGBClassifier(
            max_depth=4, min_child_weight=5, reg_alpha=0.1, reg_lambda=2.0,
            n_estimators=400, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
            tree_method='hist', random_state=42, n_jobs=-1
        )
        
        model.fit(X_train_sm, y_train_sm)
        preds = model.predict(X_test)
        
        score = f1_score(y_test, preds, average='macro')
        f1_scores.append(score)
        
    avg_f1 = np.mean(f1_scores)
    
    print(f"Leave-Family-Out Cross-Validation Macro-F1: {avg_f1:.4f}")
    print("\nConclusion: If LFO F1 is significantly lower than the standard CV F1 (0.68), it indicates the model heavily relies on memorizing taxonomic lineage priors to assign Risk Groups, supporting the hypothesis that biosafety severity is highly lineage-bound.")

if __name__ == "__main__":
    run_lfo_validation()
