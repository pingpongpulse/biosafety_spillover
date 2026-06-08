import pandas as pd
import numpy as np
import pickle
import json
import os

def run_counterfactuals():
    print("Running Counterfactual Case Studies...")
    
    with open("models/xgboost_rg_classifier.pkl", "rb") as f:
        rg_model = pickle.load(f)
    with open("models/encoder_mappings.json", "r") as f:
        enc = json.load(f)
        
    df = pd.read_csv("data/processed/rg_dataset_encoded.csv")
    feature_cols = enc["_feature_cols"]
    
    results = []
    
    def evaluate_case(virus_name, feature_to_change, new_value, description):
        match = df[df['name'].str.contains(virus_name, case=False, na=False)]
        if match.empty:
            return
            
        row = match.iloc[0].copy()
        
        # Baseline predict
        feats_base = row[feature_cols].to_frame().T.astype(float)
        prob_base = rg_model.predict_proba(feats_base)[0]
        rg34_base = prob_base[2] + prob_base[3]
        pred_base = np.argmax(prob_base) + 1
        
        # Counterfactual predict
        row[feature_to_change] = new_value
        feats_cf = row[feature_cols].to_frame().T.astype(float)
        prob_cf = rg_model.predict_proba(feats_cf)[0]
        rg34_cf = prob_cf[2] + prob_cf[3]
        pred_cf = np.argmax(prob_cf) + 1
        
        results.append({
            "Virus": match.iloc[0]['name'],
            "Scenario": description,
            "Base Predicted RG": pred_base,
            "Base Prob(RG3/4)": rg34_base,
            "Counterfactual RG": pred_cf,
            "Counterfactual Prob(RG3/4)": rg34_cf,
            "Shift": rg34_cf - rg34_base
        })
        
    # Case 1: Influenza A (H1N1)
    # What if it wasn't an RNA virus? (Testing RNA Prior)
    evaluate_case("California/7/2009", "is_dna", 1, "Change from RNA to DNA")
    
    # Case 2: Marburg
    # What if we removed enveloped status?
    evaluate_case("Marburg marburgvirus", "is_enveloped", 0, "Remove Enveloped Status")
    
    # Case 3: Dengue
    # What if we removed vector-borne status? (Testing vector importance for RG)
    evaluate_case("Dengue virus", "is_vector_borne", 0, "Remove Vector-borne Status")
    
    # Case 4: Severe acute respiratory syndrome-related coronavirus
    # What if we changed its family to Filoviridae? (Testing lineage-bound hypothesis)
    filo_enc = enc["taxonomic_family"].get("Filoviridae", 0)
    evaluate_case("Severe acute respiratory syndrome", "taxonomic_family_enc", filo_enc, "Change Family to Filoviridae")
    
    res_df = pd.DataFrame(results)
    os.makedirs("results/tables", exist_ok=True)
    res_df.to_csv("results/tables/counterfactual_case_studies.csv", index=False)
    
    print("\nCounterfactual Case Studies:")
    print(res_df.to_string(index=False))

if __name__ == "__main__":
    run_counterfactuals()
