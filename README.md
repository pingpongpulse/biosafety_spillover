# BioRiskNet

## Metadata-Driven WHO Risk Group Classification and Zoonotic Spillover Scoring with SHAP Explainability

**Course:** Biosafety and Ethics | 4-Person Team Project  
**Target:** PLOS ONE / Bioinformatics Advances  

---

## What Is BioRiskNet?

BioRiskNet is a dual-objective machine learning framework that predicts pathogen biosafety risk from biological metadata alone, without requiring genome sequences.

| Model | Task | Dataset | Key Metric |
|---|---|---|---|
| **RG Classifier** | Predict WHO Risk Group 1–4 | ABSA + ePATHogen + BMBL (~1000 organisms) | F1-macro = 0.708 ± 0.008 (5-fold CV) |
| **Spillover Scorer** | Predict zoonotic spillover probability | Olival 2017 (~586 viruses) | AUC-ROC (5-fold CV) |

SHAP TreeExplainer is used to explain every prediction at the individual pathogen level.

---

## Key Results

- **F1-macro (5-fold CV): 0.708 ± 0.008** — exceeds the 0.70 paper target
- **Per-class F1:** RG1=0.758, RG2=0.604, RG3=0.645, RG4=0.825
- **Top 3 predictive features (by SHAP importance):**
  1. `genome_type` (26.4%) — RNA viruses systematically score higher
  2. `zoonotic` (18.2%) — zoonotic origin strongly correlates with higher RG
  3. `treatment_available` (14.8%) — codified WHO criterion for RG3/RG4
- **Case studies:** SARS-CoV-2, Ebola virus, E. coli K12 predictions vs known RG

---

## Setup

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/biorisknet.git
cd biorisknet

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate      # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

---

## Run in Order

```bash
# Person 1 — Data Collection & Merging
python scripts/download_olival.py        # 1. Download Olival 2017 virus-host data
python scripts/clean_epathogen.py        # 2. Clean ePATHogen risk group database
python scripts/scrape_absa.py            # 3. Scrape ABSA risk group database
python scripts/extract_bmbl.py           # 4. Extract WHO BMBL PDF tables
python scripts/merge_datasets.py         # 5. Merge all sources → rg_dataset.csv

# Person 2 — ML Model Training
python scripts/encode_features.py        # 6. Label-encode biological features
python scripts/apply_smote.py            # 7. SMOTE class balancing
python scripts/train_model.py            # 8. Train XGBoost RG classifier
python scripts/plot_confusion.py         # 9. Generate confusion matrix figure

# Person 3 — Spillover Model & SHAP
python scripts/train_spillover.py        # 10. Train zoonotic spillover model
python scripts/shap_global.py            # 11. SHAP global feature importance plots
python scripts/shap_case_studies.py      # 12. SHAP waterfall plots for 3 pathogens
python scripts/shap_spillover.py         # 13. SHAP analysis for spillover model

# Person 4 — Validation & Results
python scripts/check_outputs.py          # 14. Validate all required outputs exist
python scripts/case_studies.py > results/case_study_results.txt  # 15. Case study predictions
python scripts/build_results_tables.py   # 16. Build summary and per-class tables
```

---

## Project Structure

```
biorisknet/
├── data/
│   ├── raw/                    # Source datasets (not tracked in git)
│   │   ├── olival_viruses.csv
│   │   ├── olival_associations.csv
│   │   ├── absa_raw.csv
│   │   ├── epathogen_clean.csv
│   │   └── bmbl_extracted.csv
│   └── processed/              # Cleaned and encoded datasets
│       ├── rg_dataset.csv
│       ├── rg_dataset_features.csv
│       ├── rg_dataset_encoded.csv
│       └── smote_dataset.csv
├── models/
│   ├── xgboost_rg_classifier.pkl
│   └── encoder_mappings.json
├── results/
│   ├── model_results.json
│   ├── spillover_model.pkl
│   ├── spillover_results.json
│   ├── feature_importances.csv
│   ├── summary_table.csv
│   ├── case_study_results.txt
│   ├── shap_validation.txt
│   ├── figures/
│   │   ├── confusion_matrix.png
│   │   ├── shap_summary_bar.png
│   │   ├── shap_beeswarm_rg3.png
│   │   ├── shap_spillover.png
│   │   ├── shap_case_SARS_CoV_2.png
│   │   ├── shap_case_Ebola_virus.png
│   │   └── shap_case_Escherichia_coli.png
│   └── tables/
│       ├── model_summary.csv
│       └── per_class_metrics.csv
└── scripts/                    # All analysis scripts (run in order above)
```

---

## Datasets

| Dataset | Source | License |
|---|---|---|
| Olival 2017 virus-host associations | https://github.com/ecohealthalliance/HP3 | CC-BY |
| ePATHogen Risk Group Database | https://ePathogen.phac-aspc.gc.ca | Public |
| ABSA Risk Group Database | https://absa.org/biosafety-resources/risk-group-database/ | Public |
| WHO BMBL 6th Edition | https://www.cdc.gov/labs/BMBL.html | Public domain |

> **Note:** Raw data files are excluded from this repository via `.gitignore`.
> Run `scripts/download_olival.py` to retrieve the Olival dataset automatically.
> ePATHogen and ABSA must be downloaded manually (see procedure book).

---

## Methods Summary

- **Class imbalance:** SMOTE with `k_neighbors=3` applied to all classes before training
- **Model:** XGBoost (`n_estimators=300, max_depth=6, learning_rate=0.05`)
- **Validation:** 5-fold stratified cross-validation, `random_state=42`
- **Explainability:** SHAP TreeExplainer — global summary, beeswarm per class, individual waterfall plots
- **Feature encoding:** Scikit-learn `LabelEncoder` — mappings saved to `models/encoder_mappings.json`

---

## Citation

If you use BioRiskNet in your work, please cite:

> [Authors]. BioRiskNet: Metadata-Driven WHO Risk Group Classification and Zoonotic
> Spillover Scoring with SHAP Explainability. *Bioinformatics Advances*, 2026.

---

## Requirements

See `requirements.txt`. Key dependencies:

```
pandas>=1.5
scikit-learn>=1.2
xgboost>=1.7
shap>=0.42
imbalanced-learn>=0.10
matplotlib>=3.6
seaborn>=0.12
pdfplumber>=0.9
biopython>=1.80
requests>=2.28
beautifulsoup4>=4.11
```
