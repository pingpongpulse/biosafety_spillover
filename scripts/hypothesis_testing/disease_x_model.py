import pandas as pd
import numpy as np
import xgboost as xgb
from imblearn.over_sampling import SMOTE
import shap
import matplotlib.pyplot as plt
import os
import json

def run_disease_x():
    print("Training the Disease X Downgrade Model...")
    
    with open("models/encoder_mappings.json", "r") as f:
        enc = json.load(f)
        
    df = pd.read_csv("data/processed/rg_dataset_encoded.csv")
    feature_cols = enc["_feature_cols"]
    
    # We remove lineage and known-human-infection to simulate a completely unknown virus
    disease_x_cols = [c for c in feature_cols if c not in ["taxonomic_family_enc", "infects_humans"]]
    
    X = df[disease_x_cols].copy()
    y = df['rg_label'].values
    
    # Impute missing values for SMOTE
    for c in X.columns:
        if c == "host_breadth":
            X[c] = X[c].fillna(X[c].median())
        else:
            X[c] = X[c].fillna(X[c].mode()[0])
            
    smote = SMOTE(k_neighbors=3, random_state=42)
    X_sm, y_sm = smote.fit_resample(X, y)
    
    model = xgb.XGBClassifier(
        max_depth=3, min_child_weight=5, reg_alpha=0.1, reg_lambda=2.0,
        n_estimators=100, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
        tree_method='hist', random_state=42, n_jobs=-1
    )
    
    # Fit the model
    model.fit(X_sm, y_sm)
    
    # Now we simulate the downgrade logic using SHAP
    # Let's take Marburg as our "Disease X" structural template
    marburg_row = df[df['name'].str.contains("Marburg", case=False, na=False)].iloc[0]
    marburg_X = marburg_row[disease_x_cols].to_frame().T.astype(float)
    
    # Fill Nans for Marburg
    for c in marburg_X.columns:
        if pd.isna(marburg_X[c].iloc[0]):
            marburg_X[c] = X[c].median()
    
    # Calculate SHAP values
    explainer = shap.TreeExplainer(model)
    shap_values = explainer(marburg_X)
    
    # XGBClassifier multi-class returns shape (n_samples, n_features, n_classes)
    # Class index 3 is RG4
    rg4_shap = shap_values[:, :, 3]
    
    # Generate SHAP Waterfall Plot for RG4
    plt.figure(figsize=(10, 6))
    shap.plots.waterfall(rg4_shap[0], show=False)
    plt.title("Disease X Downgrade/Upgrade Pathway (Prob of RG4)")
    plt.tight_layout()
    
    os.makedirs("results/figures", exist_ok=True)
    plt.savefig("results/figures/disease_x_waterfall.png", dpi=300, bbox_inches='tight')
    plt.close()
    

    # Also save the waterfall values to CSV
    base_value = rg4_shap[0].base_values
    features = disease_x_cols
    values = rg4_shap[0].values
    data = marburg_X.iloc[0].values
    
    out_df = pd.DataFrame({
        "Feature": features,
        "Value": data,
        "SHAP_Contribution": values
    }).sort_values(by="SHAP_Contribution", ascending=False)
    
    print(f"Disease X Baseline (Expected output value for RG4): {base_value:.4f}")
    print("Feature Contributions:")
    print(out_df.to_string(index=False))
    
    os.makedirs("results/tables", exist_ok=True)
    out_df.to_csv("results/tables/disease_x_downgrade_weights.csv", index=False)
    
    print("\nSaved waterfall plot and decision tree to results/figures/")

if __name__ == "__main__":
    run_disease_x()
