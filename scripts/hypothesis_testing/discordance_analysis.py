import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
import os
import json

def run_discordance_analysis():
    print("Running Dual-Model Discordance Analysis...")
    
    # Load models
    with open("models/xgboost_rg_classifier.pkl", "rb") as f:
        rg_model = pickle.load(f)
    with open("results/spillover_model.pkl", "rb") as f:
        sp_model = pickle.load(f)
        
    with open("models/encoder_mappings.json", "r") as f:
        enc = json.load(f)
        
    # Reverse mappings for context
    rev_genome = {v: k for k, v in enc["genome_type"].items()}
    rev_family = {v: k for k, v in enc["taxonomic_family"].items()}

    # Load dataset
    df = pd.read_csv("data/processed/rg_dataset_encoded.csv")
    
    # We need the full feature set without NaNs for the RG model, or let XGBoost handle NaNs.
    # XGBoost handles NaNs natively for the RG model.
    feature_cols = enc["_feature_cols"]
    
    results = []
    
    for idx, row in df.iterrows():
        name = row["name"]
        known_rg = int(row["rg_label"]) + 1 # 1-indexed
        
        # RG model features
        rg_features = row[feature_cols].to_frame().T
        # XGBoost predict_proba
        rg_proba = rg_model.predict_proba(rg_features)[0]
        prob_rg3_rg4 = rg_proba[2] + rg_proba[3] # Index 2 is RG3, Index 3 is RG4
        
        # Spillover features translation
        is_dna = row["is_dna"]
        is_env = row["is_enveloped"]
        is_seg = row["is_segmented"]
        is_vec = row["is_vector_borne"]
        infects = row["infects_humans"]
        hb = row["host_breadth"]
        gen_enc = row["genome_type_enc"]
        gen_str = rev_genome.get(gen_enc, "")
        
        sp_dict = {
            "vIsTypeSpecies": 0, "ReverseZoonoses": 0, "vGenomeAveLength": 12016.0,
            "vGenomeMinLength": 12017.0, "vGenomeMaxLength": 12450.0,
            "vWOKcites": 11.0, "vPubMedCites": 9.0, "vCytoReplicTF": 1, "vSSoDS": 1,
            "human_host": 0
        }
        sp_dict["vDNAoRNA"] = 0 if is_dna == 1 else 1
        sp_dict["vEnvelope"] = 0 if is_env == 1 else (1 if not pd.isna(is_env) else 0)
        sp_dict["vSegmentedTF"] = 1 if is_seg == 1 else 0
        sp_dict["vVectorYNna"] = 1 if is_vec == 1 else 0
        sp_dict["IsHoSa"] = int(infects) if not pd.isna(infects) else 0
        sp_dict["host_count"] = float(hb) if not pd.isna(hb) else 1.0
        sp_dict["vSSoDS"] = 0 if str(gen_str).startswith("ds") else 1
        sp_dict["human_host"] = sp_dict["IsHoSa"]
        
        cols = ['vIsTypeSpecies','ReverseZoonoses','IsHoSa','vGenomeAveLength',
                'vGenomeMinLength','vGenomeMaxLength','vWOKcites','vPubMedCites',
                'vCytoReplicTF','vSegmentedTF','vVectorYNna','vSSoDS','vDNAoRNA',
                'vEnvelope','host_count','human_host']
        sp_row = pd.DataFrame([sp_dict], columns=cols)
        
        sp_prob = sp_model.predict_proba(sp_row)[0][1] # Probability of spillover
        
        discordance = sp_prob - prob_rg3_rg4
        
        if sp_prob >= 0.5 and prob_rg3_rg4 >= 0.5:
            quadrant = "High spillover / High severity"
        elif sp_prob >= 0.5 and prob_rg3_rg4 < 0.5:
            quadrant = "High spillover / Low severity"
        elif sp_prob < 0.5 and prob_rg3_rg4 >= 0.5:
            quadrant = "Low spillover / High severity"
        else:
            quadrant = "Low spillover / Low severity"
            
        results.append({
            "name": name,
            "taxonomic_family": rev_family.get(row["taxonomic_family_enc"], "Unknown"),
            "genome_type": gen_str,
            "known_rg": known_rg,
            "spillover_probability": sp_prob,
            "rg3_rg4_probability": prob_rg3_rg4,
            "discordance_score": discordance,
            "discordance_quadrant": quadrant
        })

    res_df = pd.DataFrame(results)
    
    # Save CSV
    os.makedirs("results/tables", exist_ok=True)
    res_df.to_csv("results/tables/dual_model_discordance_scores.csv", index=False)
    
    # Plot
    os.makedirs("results/figures", exist_ok=True)
    plt.figure(figsize=(10, 8))
    
    # Colors for quadrants
    colors = {
        "High spillover / High severity": "#e74c3c",
        "High spillover / Low severity": "#f39c12",
        "Low spillover / High severity": "#9b59b6",
        "Low spillover / Low severity": "#3498db"
    }
    
    for quad, group in res_df.groupby("discordance_quadrant"):
        plt.scatter(group["spillover_probability"], group["rg3_rg4_probability"], 
                    label=quad, alpha=0.6, color=colors[quad], edgecolor='k')

    # Add quadrant lines
    plt.axvline(0.5, color='gray', linestyle='--', alpha=0.5)
    plt.axhline(0.5, color='gray', linestyle='--', alpha=0.5)
    
    # Highlight specific pathogens
    highlights = ["Severe acute respiratory syndrome-related coronavirus", "Marburg marburgvirus", "Dengue virus", "Influenza A virus"]
    for h in highlights:
        match = res_df[res_df['name'].str.contains(h, case=False, na=False)]
        if not match.empty:
            pt = match.iloc[0]
            plt.annotate(pt['name'], (pt['spillover_probability'], pt['rg3_rg4_probability']),
                         xytext=(5, 5), textcoords='offset points', fontsize=9, fontweight='bold')
    
    plt.xlabel("Predicted Spillover Probability (Ecological Risk)")
    plt.ylabel("Predicted RG3/RG4 Probability (Containment Severity)")
    plt.title("Dual-Model Discordance Map: Emergence vs Containment")
    plt.legend()
    plt.grid(True, alpha=0.2)
    
    plt.tight_layout()
    plt.savefig("results/figures/dual_model_discordance_map.png", dpi=300)
    plt.savefig("results/figures/dual_model_discordance_map.pdf")
    plt.close()
    print("Discordance map and tables saved to results/figures and results/tables.")

if __name__ == "__main__":
    run_discordance_analysis()
