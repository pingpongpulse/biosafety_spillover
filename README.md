# BioRiskNet v2

## Viral Pathogen Risk Classification & Zoonotic Spillover Prediction
**100% Verified Biological Metadata | Zero Imputation**

**Course:** Biosafety and Ethics | 4-Person Team Project  
**Target:** PLOS ONE / Bioinformatics Advances  
**Branch:** `v2-real-features`

---

## What Is BioRiskNet?

BioRiskNet is an explainable machine learning framework that evaluates whether verified biological metadata can predict WHO biosafety Risk Groups for viral pathogens. It explicitly tests whether the biological features driving laboratory containment severity are the same as those driving zoonotic spillover potential.

**The Pipeline:**
1. Merges pathogen labels from ePATHogen, ABSA, and WHO BMBL.
2. Extracts 9 biological features from **ICTV MSL 2025**, **Virus-Host DB**, and **Olival 2017** using NCBI Entrez fuzzy matching.
3. Classifies 934 viral pathogens into WHO Risk Groups 1–4 using an XGBoost classifier and SMOTE class balancing.
4. Uses SHAP TreeExplainer to compare biosafety severity predictors against zoonotic spillover predictors.

---

## Key Scientific Findings

1. **Biosafety Severity ≠ Spillover Potential:** `is_vector_borne` carries **0.0% weight** in risk group classification, but is a primary predictor in spillover models. This quantitatively demonstrates that ecological emergence risk and laboratory biosafety severity are partially independent biological constructs.
2. **RNA vs DNA drives Risk:** `is_dna` (RNA/DNA genome status) is the single strongest predictor of WHO Risk Group (42.7% importance), reflecting that RNA viruses disproportionately occupy RG3 and RG4.
3. **Clinical Limitations:** Genome architecture alone cannot distinguish Influenza A (RG2) from Marburg virus (RG4). The model systematically over-predicts risk for RG2 respiratory viruses due to the absence of clinical variables (Case Fatality Rate, treatment/vaccine availability) in public metadata databases.

---

## v2 Results (Real Data)

| Metric | Value | Notes |
|---|---|---|
| Dataset Size | **934 viral organisms** | Filtered for ≥2 real biological features |
| Feature Set | **9 biological features** | Genome type, family, DNA/RNA, envelope, segmentation, vector-borne, zoonotic, infects humans, host breadth |
| F1-macro | **0.682 ± 0.021** | 5-fold stratified CV |
| Accuracy | **0.684 ± 0.022** | 5-fold stratified CV |
| RG4 F1 | **0.82** | Extreme-risk pathogens have the clearest biological fingerprint |
| Case Studies | **2/3 Correct** | SARS-CoV-2 (RG3) ✅, Marburg (RG4) ✅, Influenza A (RG4 ≠ RG2) ❌ |

---

## Setup

```bash
# Clone the repo and switch to v2 branch
git clone https://github.com/pingpongpulse/biosafety_spillover.git
cd biosafety_spillover
git checkout v2-real-features

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate      # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

---

## Full Pipeline Execution Order

```bash
# Person 1 — Data Collection & Real Feature Building
python scripts/download_olival.py        # 1. Download Olival 2017 virus-host data
python scripts/clean_epathogen.py        # 2. Clean ePATHogen risk group database
python scripts/scrape_absa.py            # 3. Scrape ABSA risk group database
python scripts/extract_bmbl.py           # 4. Extract WHO BMBL PDF tables
python scripts/merge_datasets.py         # 5. Merge all sources
python scripts/build_real_features.py    # 6. Build v2 matrix (ICTV/VH-DB/Olival/NCBI)

# Person 2 — ML Pipeline (GPU-Accelerated)
python scripts/encode_features.py        # 7. Label-encode biological features
python scripts/apply_smote.py            # 8. NaN-aware SMOTE class balancing
python scripts/train_model.py            # 9. Train XGBoost RG classifier
python scripts/plot_confusion.py         # 10. Generate confusion matrix figure
python scripts/build_results_tables.py   # 11. Build summary and per-class tables

# Person 3 — Spillover Model & Explainability
python scripts/train_spillover.py        # 12. Train zoonotic spillover model
python scripts/shap_global.py            # 13. SHAP global feature importance plots
python scripts/shap_case_studies.py      # 14. SHAP waterfall plots for Marburg/SARS-CoV-2
python scripts/shap_spillover.py         # 15. SHAP analysis for spillover model

# Person 4 — Validation & Results
python scripts/check_outputs.py          # 16. Validate all required v2 outputs exist
python scripts/case_studies.py           # 17. Run case study predictions
```

---

## Datasets & Provenance

| Dataset | Source | Features Extracted |
|---|---|---|
| **ICTV MSL 2025** | ictv.global | `genome_type`, `taxonomic_family` |
| **Virus-Host DB** | genome.jp/ftp | `host_breadth`, `infects_humans` |
| **Olival 2017** | ecohealthalliance/HP3 | `is_enveloped`, `is_segmented`, `is_vector_borne`, `is_zoonotic` |
| **NCBI Entrez** | biopython/Entrez | Cross-database tax ID resolution |

> **Note:** Raw data files are tracked in this `v2-real-features` branch to ensure full reproducibility, but larger raw databases may require manual download if run from scratch.

---

## Citation

If you use BioRiskNet in your work, please cite:

> [Authors]. BioRiskNet: Verified Viral Metadata Reveals Diverging Biological Drivers of Zoonotic Spillover and WHO Biosafety Severity. *Biosafety and Ethics Course Project*, 2026.
