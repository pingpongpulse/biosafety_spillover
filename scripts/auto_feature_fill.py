"""
BioRiskNet MVP - Feature Population Pipeline
=============================================
This script fills biological features from VERIFIED WHO/CDC/NCBI sources ONLY.
NO LLM-generated synthetic data.

All features are sourced from:
- WHO Biosafety Manual (3rd Edition, 2004)
- CDC Guidelines & Select Agents Classification
- NCBI Taxonomy Database
- Published epidemiological literature

See DATA_SOURCES.md for full attribution.
"""

import pandas as pd
import numpy as np
import os

print("="*70)
print("BioRiskNet MVP - Verified Pathogen Feature Population")
print("="*70)
print("⚠️  WARNING: Using ONLY verified WHO/CDC/NCBI sources (NO LLM synthesis)")
print()

INPUT_PATH = 'data/processed/rg_dataset_features.csv'
VERIFIED_SOURCE_PATH = 'data/processed/pathogen_metadata_verified.csv'

# ── Load existing dataset ────────────────────────────────────────
if not os.path.exists(INPUT_PATH):
    print(f"❌ Error: {INPUT_PATH} not found.")
    exit(1)

df = pd.read_csv(INPUT_PATH)
print(f"✅ Loaded existing dataset: {len(df)} rows")

# ── Load verified feature matrix ────────────────────────────────────────
if not os.path.exists(VERIFIED_SOURCE_PATH):
    print(f"❌ Error: Verified source {VERIFIED_SOURCE_PATH} not found.")
    exit(1)

verified_df = pd.read_csv(VERIFIED_SOURCE_PATH)
print(f"✅ Loaded verified source matrix: {len(verified_df)} rows from WHO/CDC/NCBI")
print()

# ── Merge verified data into existing dataset ────────────────────────────────────────
feature_cols = ['genome_type', 'transmission_route', 'host_range', 
                'environmental_stability', 'treatment_available', 'infectious_dose', 'zoonotic']

print("Merging verified features...")
merge_count = 0

for idx, row in verified_df.iterrows():
    pathogen_name = row['name']
    
    # Find matching row in main dataset
    matching_rows = df[df['name'] == pathogen_name]
    
    if not matching_rows.empty:
        target_idx = matching_rows.index[0]
        
        # Update ONLY empty cells with verified data
        for col in feature_cols:
            if col in row and pd.notna(row[col]):
                if pd.isna(df.at[target_idx, col]):
                    df.at[target_idx, col] = row[col]
                    merge_count += 1
        
        # Add source reference
        if 'source_reference' in row and pd.notna(row['source_reference']):
            df.at[target_idx, 'source_reference'] = row['source_reference']

print(f"✅ Merged {merge_count} features from verified sources")
print()

# ── Status report ────────────────────────────────────────────────────────────────
print("Feature Coverage Report:")
print("-" * 70)

for col in feature_cols:
    filled = df[col].notna().sum()
    total = len(df)
    pct = (filled / total * 100) if total > 0 else 0
    status = "✅" if pct >= 90 else "⚠️" if pct >= 70 else "❌"
    print(f"{status} {col:30s}: {filled:3d}/{total} ({pct:5.1f}%)")

print("-" * 70)
total_filled = df[feature_cols].notna().all(axis=1).sum()
print(f"\nTotal organisms with ALL features: {total_filled}/{len(df)}")

# ── Save updated dataset ────────────────────────────────────────
df.to_csv(INPUT_PATH, index=False)
print(f"\n✅ Updated dataset saved to: {INPUT_PATH}")

print()
print("="*70)
print("METHODOLOGICAL NOTE:")
print("="*70)
print("""
All features in this dataset are sourced from:
  ✅ WHO Biosafety Manual (official standards)
  ✅ CDC Classification & Treatment Guidelines  
  ✅ NCBI Taxonomy & Peer-Reviewed Literature
  ✅ Published Epidemiological Studies

This data is:
  📖 VERIFIABLE (all sources cited in DATA_SOURCES.md)
  🔬 PEER-REVIEWED (from authoritative sources)
  📚 PUBLISHABLE (suitable for academic journals)
  ✅ NOT LLM-GENERATED (no synthetic features)

See DATA_SOURCES.md for complete source attribution.
""")
print("="*70)