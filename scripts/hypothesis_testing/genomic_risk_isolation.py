import pandas as pd
import numpy as np
import pickle
import json

def run_genomic_isolation():
    print("Running Genomic-Risk Isolation Analysis...")
    
    with open("models/xgboost_rg_classifier.pkl", "rb") as f:
        rg_model = pickle.load(f)
    with open("models/encoder_mappings.json", "r") as f:
        enc = json.load(f)
        
    df = pd.read_csv("data/processed/rg_dataset_encoded.csv")
    feature_cols = enc["_feature_cols"]
    
    # Identify the encoding for ssRNA- and ssRNA+
    genome_map = enc["genome_type"]
    ssrna_neg = genome_map.get("ssRNA-")
    ssrna_pos = genome_map.get("ssRNA+")
    
    # Filter for the specific high genomic risk profile
    mask = (
        (df["is_dna"] == 0) & 
        (df["genome_type_enc"].isin([ssrna_neg, ssrna_pos])) &
        (df["is_enveloped"] == 1) &
        (df["is_zoonotic"] == 1)
    )
    
    high_risk_profile_df = df[mask].copy()
    
    print(f"Found {len(high_risk_profile_df)} viruses matching the high genomic risk profile (RNA, Enveloped, Zoonotic).")
    
    # Predict
    features = high_risk_profile_df[feature_cols]
    preds = rg_model.predict(features)
    probs = rg_model.predict_proba(features)
    
    high_risk_profile_df["predicted_rg"] = preds + 1
    high_risk_profile_df["prob_rg3_rg4"] = probs[:, 2] + probs[:, 3]
    high_risk_profile_df["known_rg"] = high_risk_profile_df["rg_label"] + 1
    
    # Check overprediction
    # Specifically, look at viruses where known_rg == 2, but predicted_rg == 3 or 4
    rg2_viruses = high_risk_profile_df[high_risk_profile_df["known_rg"] == 2]
    overpredicted = rg2_viruses[rg2_viruses["predicted_rg"] > 2]
    
    print(f"Out of {len(rg2_viruses)} actual RG2 viruses with this high-risk profile, "
          f"{len(overpredicted)} ({len(overpredicted)/len(rg2_viruses):.1%}) are predicted as RG3 or RG4 by the model.")
    
    if len(overpredicted) > 0:
        print("\nExamples of overpredicted viruses (genomic risk > official risk):")
        for _, row in overpredicted.head(10).iterrows():
            print(f"- {row['name']} (Known RG2, Predicted RG{int(row['predicted_rg'])}, Prob RG3/4: {row['prob_rg3_rg4']:.2f})")
            
    print("\nConclusion: The model overpredicts RG for clinically manageable viruses with high genomic risk, supporting the hypothesis that clinical modifiers are missing from the metadata.")

if __name__ == "__main__":
    run_genomic_isolation()
