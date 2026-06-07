# ============================================================================
# BioRiskNet MVP - One-Day Execution Pipeline (All 4 Persons)
# ============================================================================
# NO REBASE. Pure sequential execution with verified biological data.
# Timeline: ~6 hours total (can run in parallel with some coordination)
#
# IMPORTANT: All biological features sourced from WHO/CDC/NCBI verified sources
# See DATA_SOURCES.md for complete attribution
# ============================================================================

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "BioRiskNet MVP - One-Day Pipeline Execution" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Branch: $(git branch --show-current)" -ForegroundColor Green
Write-Host "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Green
Write-Host ""
Write-Host "⚠️  IMPORTANT: All data sourced from WHO/CDC/NCBI (NO LLM synthesis)" -ForegroundColor Yellow
Write-Host ""

# Track execution times
$startTime = Get-Date

# ============================================================================
# PERSON 1: Data Engineer - Data Collection & Consolidation
# ============================================================================
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta
Write-Host "PERSON 1: DATA ENGINEER - Data Collection (ETA: 2 hours)" -ForegroundColor Magenta
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta
Write-Host ""
Write-Host "[1/4] Downloading Olival Dataset (virus-host associations)..." -ForegroundColor Cyan
python scripts/download_olival.py
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Download failed" -ForegroundColor Red; exit 1 }
Write-Host ""

Write-Host "[2/4] Merging Risk Group Labels & Consolidating Data..." -ForegroundColor Cyan
python scripts/merge_datasets.py
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Merge failed" -ForegroundColor Red; exit 1 }
Write-Host ""

Write-Host "[3/4] Populating Features from Verified WHO/CDC/NCBI Sources..." -ForegroundColor Cyan
python scripts/auto_feature_fill.py
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Feature population failed" -ForegroundColor Red; exit 1 }
Write-Host ""

Write-Host "✅ PERSON 1 COMPLETE" -ForegroundColor Green
Write-Host "   Output: data/processed/rg_dataset_features.csv" -ForegroundColor Green
Write-Host ""
$person1Time = (Get-Date) - $startTime
Write-Host "   Time: $($person1Time.TotalMinutes.ToString('F1')) minutes" -ForegroundColor Gray

# ============================================================================
# PERSON 2: ML Engineer - Encoding & XGBoost Training
# ============================================================================
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Blue
Write-Host "PERSON 2: ML ENGINEER - Classification Pipeline (ETA: 1.5 hours)" -ForegroundColor Blue
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Blue
Write-Host ""
Write-Host "[1/3] Encoding Categorical Features to Numeric Tensors..." -ForegroundColor Cyan
python scripts/encode_features.py
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Encoding failed" -ForegroundColor Red; exit 1 }
Write-Host ""

Write-Host "[2/3] Applying SMOTE Balancing & Training XGBoost Classifier..." -ForegroundColor Cyan
python scripts/train_model.py
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Model training failed" -ForegroundColor Red; exit 1 }
Write-Host ""

Write-Host "[3/3] Generating Confusion Matrix (5-Fold Cross-Validation)..." -ForegroundColor Cyan
python scripts/plot_confusion.py
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Confusion matrix failed" -ForegroundColor Red; exit 1 }
Write-Host ""

Write-Host "✅ PERSON 2 COMPLETE" -ForegroundColor Green
Write-Host "   Output: results/xgboost_model.pkl, results/figures/confusion_matrix.png" -ForegroundColor Green
Write-Host ""
$person2Time = (Get-Date) - $startTime
Write-Host "   Time: $($person2Time.TotalMinutes.ToString('F1')) minutes total" -ForegroundColor Gray

# ============================================================================
# PERSON 3: Explainability Engineer - Spillover Model & SHAP
# ============================================================================
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta
Write-Host "PERSON 3: EXPLAINABILITY - Spillover Modeling & SHAP (ETA: 1.5 hours)" -ForegroundColor Magenta
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Magenta
Write-Host ""
Write-Host "[1/3] Training Zoonotic Spillover Binary Classifier..." -ForegroundColor Cyan
python scripts/train_spillover.py
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Spillover model failed" -ForegroundColor Red; exit 1 }
Write-Host ""

Write-Host "[2/3] Generating SHAP Spillover Feature Importance Plot..." -ForegroundColor Cyan
python scripts/shap_spillover.py
if ($LASTEXITCODE -ne 0) { Write-Host "❌ SHAP spillover failed" -ForegroundColor Red; exit 1 }
Write-Host ""

Write-Host "[3/3] Generating SHAP Risk Group Global & RG3 Attribution Charts..." -ForegroundColor Cyan
python scripts/shap_global.py
if ($LASTEXITCODE -ne 0) { Write-Host "❌ SHAP global failed" -ForegroundColor Red; exit 1 }
Write-Host ""

Write-Host "✅ PERSON 3 COMPLETE" -ForegroundColor Green
Write-Host "   Output: 4 PNG explainability charts in results/figures/" -ForegroundColor Green
Write-Host ""
$person3Time = (Get-Date) - $startTime
Write-Host "   Time: $($person3Time.TotalMinutes.ToString('F1')) minutes total" -ForegroundColor Gray

# ============================================================================
# PERSON 4: Validation & QA - System Verification
# ============================================================================
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host "PERSON 4: VALIDATION & QA - System Integration (ETA: 1 hour)" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
Write-Host ""
Write-Host "[1/3] Auditing Workspace Integrity & Verifying Artifacts..." -ForegroundColor Cyan
python scripts/check_outputs.py
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Audit failed" -ForegroundColor Red; exit 1 }
Write-Host ""

Write-Host "[2/3] Benchmarking on High-Consequence Pathogens (Nipah/Lassa)..." -ForegroundColor Cyan
python scripts/shap_case_studies.py
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Case studies failed" -ForegroundColor Red; exit 1 }
Write-Host ""

Write-Host "[3/3] Compiling Performance Summary Table for Manuscript..." -ForegroundColor Cyan
python scripts/build_results_tables.py
if ($LASTEXITCODE -ne 0) { Write-Host "❌ Summary table failed" -ForegroundColor Red; exit 1 }
Write-Host ""

Write-Host "✅ PERSON 4 COMPLETE" -ForegroundColor Green
Write-Host "   Output: CSV tables in results/tables/, ready for manuscript" -ForegroundColor Green
Write-Host ""

# ============================================================================
# FINAL STATUS
# ============================================================================
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "✅ ALL PIPELINE STAGES COMPLETE" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

$totalTime = (Get-Date) - $startTime
Write-Host "Total Execution Time: $($totalTime.TotalMinutes.ToString('F1')) minutes" -ForegroundColor Green
Write-Host ""

Write-Host "📊 DELIVERABLES GENERATED:" -ForegroundColor Cyan
Write-Host ""
Write-Host "Data & Features:" -ForegroundColor White
Write-Host "  ✅ data/processed/rg_dataset_features.csv (verified features)" 
Write-Host "  ✅ data/processed/smote_dataset.csv (balanced training set)"
Write-Host "  ✅ data/processed/spillover_smote.csv (spillover training set)"
Write-Host ""
Write-Host "Models & Encoders:" -ForegroundColor White
Write-Host "  ✅ results/xgboost_model.pkl (multi-class RG classifier)"
Write-Host "  ✅ results/spillover_model.pkl (binary spillover classifier)"
Write-Host "  ✅ results/encoders.pkl (feature encoders)"
Write-Host ""
Write-Host "Explainability & Analysis:" -ForegroundColor White
Write-Host "  ✅ results/figures/confusion_matrix.png"
Write-Host "  ✅ results/figures/shap_spillover.png"
Write-Host "  ✅ results/figures/shap_summary_bar.png"
Write-Host "  ✅ results/figures/shap_beeswarm_rg3.png"
Write-Host ""
Write-Host "Validation & Reporting:" -ForegroundColor White
Write-Host "  ✅ results/tables/case_studies_results.csv (Nipah/Lassa benchmarks)"
Write-Host "  ✅ results/tables/summary_table.csv (performance metrics)"
Write-Host ""
Write-Host "Documentation:" -ForegroundColor White
Write-Host "  ✅ DATA_SOURCES.md (all sources cited & verifiable)"
Write-Host ""

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "📋 NEXT STEPS:" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1️⃣  Review all outputs in results/ and data/processed/" -ForegroundColor White
Write-Host "2️⃣  Verify DATA_SOURCES.md contains proper citations" -ForegroundColor White
Write-Host "3️⃣  Check plot interpretations match methodology notes" -ForegroundColor White
Write-Host "4️⃣  Commit all changes to Koundinya branch:" -ForegroundColor White
Write-Host ""
Write-Host "     git add ." -ForegroundColor Gray
Write-Host "     git commit -m 'BioRiskNet MVP: Verified data pipeline (WHO/CDC sources)'" -ForegroundColor Gray
Write-Host "     git push origin Koundinya" -ForegroundColor Gray
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
