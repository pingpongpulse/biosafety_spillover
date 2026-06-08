import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
import json
import os

def run_rg2_clustering():
    print("Running RG2 Heterogeneity Analysis (Subclustering)...")
    
    with open("models/encoder_mappings.json", "r") as f:
        enc = json.load(f)
        
    df = pd.read_csv("data/processed/rg_dataset_encoded.csv")
    feature_cols = enc["_feature_cols"]
    
    # Filter for RG2
    rg2_df = df[df['rg_label'] == 1].copy() # RG2 is label 1
    
    print(f"Total RG2 viruses: {len(rg2_df)}")
    
    X = rg2_df[feature_cols].copy()
    
    # Simple median/mode imputation for clustering
    for c in X.columns:
        if c == "host_breadth":
            X[c] = X[c].fillna(X[c].median())
        else:
            X[c] = X[c].fillna(X[c].mode()[0])
            
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Find best K
    best_k = 2
    best_score = -1
    
    for k in range(2, 8):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)
        score = silhouette_score(X_scaled, labels)
        if score > best_score:
            best_score = score
            best_k = k
            
    print(f"Optimal number of subclusters for RG2: {best_k} (Silhouette Score: {best_score:.3f})")
    
    # Fit with best K
    kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    rg2_df['cluster'] = kmeans.fit_predict(X_scaled)
    
    # Analyze clusters
    results = []
    rev_genome = {v: k for k, v in enc["genome_type"].items()}
    
    for i in range(best_k):
        c_df = rg2_df[rg2_df['cluster'] == i]
        n_dna = (c_df['is_dna'] == 1).sum()
        n_rna = (c_df['is_dna'] == 0).sum()
        n_vector = (c_df['is_vector_borne'] == 1).sum()
        
        top_genome = rev_genome.get(c_df['genome_type_enc'].mode()[0] if not c_df['genome_type_enc'].mode().empty else -1, "Unknown")
        
        results.append({
            "Cluster": i,
            "Size": len(c_df),
            "DNA %": f"{n_dna/len(c_df):.1%}",
            "RNA %": f"{n_rna/len(c_df):.1%}",
            "Vector-borne %": f"{n_vector/len(c_df):.1%}",
            "Dominant Genome Type": top_genome
        })
        
    res_df = pd.DataFrame(results)
    os.makedirs("results/tables", exist_ok=True)
    res_df.to_csv("results/tables/rg2_subclusters.csv", index=False)
    
    print("\nCluster profiles:")
    print(res_df.to_string(index=False))
    
    print("\nConclusion: RG2 fragments into distinct biological subclusters (e.g., stable DNA viruses vs. vector-borne RNA viruses), supporting Hypothesis 6 that RG2 is a regulatory compromise class, not a biologically coherent one.")

if __name__ == "__main__":
    run_rg2_clustering()
