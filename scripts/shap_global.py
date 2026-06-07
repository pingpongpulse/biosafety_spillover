"""
SHAP Risk Group Model Explainability Pipeline
==============================================
IMPORTANT METHODOLOGICAL NOTE:
SHAP feature importance shows which verified biological features most distinguish 
between WHO Risk Groups in our dataset—NOT causal drivers of pathogenicity.

This reflects CORRELATIONS in WHO/CDC biosafety standards and published features,
not novel biological mechanisms. All features sourced from verified databases 
(see DATA_SOURCES.md).

Interpretation: SHAP identifies which verified features co-occur with official 
RG classifications, not which features CAUSE higher risk.
"""

import os
import pandas as pd
import pickle
import shap
import matplotlib.pyplot as plt

os.makedirs(os.path.join('results', 'figures'), exist_ok=True)

model_path = os.path.join('results', 'xgboost_model.pkl')
data_path = os.path.join('data', 'processed', 'smote_dataset.csv')

if not os.path.exists(model_path):
    raise FileNotFoundError('Missing model file: results/xgboost_model.pkl')
if not os.path.exists(data_path):
    raise FileNotFoundError('Missing dataset file: data/processed/smote_dataset.csv')

model = pickle.load(open(model_path, 'rb'))
df = pd.read_csv(data_path)
X = df.drop(columns=['rg_label'])

explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X)

if isinstance(shap_values, list):
    shap.summary_plot(
        shap_values,
        X,
        plot_type='bar',
        class_names=['RG1', 'RG2', 'RG3', 'RG4'],
        show=False
    )
else:
    shap.summary_plot(shap_values, X, plot_type='bar', show=False)

# Updated title to reflect correlation analysis, not causal importance
plt.title('Feature Contributions Across WHO Risk Groups\n(Verified Biosafety Feature Matrix)', 
          fontweight='bold', fontsize=12)
plt.figtext(0.5, 0.02, 'Feature contributions reflect WHO/CDC biosafety standards; not novel biological discoveries', 
            ha='center', fontsize=9, style='italic', color='gray')
plt.tight_layout()
plt.savefig(os.path.join('results', 'figures', 'shap_summary_bar.png'), dpi=300, bbox_inches='tight')
plt.close()
print('✅ Saved: results/figures/shap_summary_bar.png')
print('   Interpretation: Feature contributions to RG classification correlations')

if isinstance(shap_values, list) and len(shap_values) >= 3:
    shap_rg3 = shap_values[2]
else:
    shap_rg3 = shap_values

shap.summary_plot(shap_rg3, X, show=False)
plt.title('Feature Contributions — Risk Group 3 Classification Patterns\n(SHAP Analysis of Verified Features)', 
          fontweight='bold', fontsize=12)
plt.figtext(0.5, 0.02, 'Shows which verified features distinguish RG3 pathogens in our dataset', 
            ha='center', fontsize=9, style='italic', color='gray')
plt.tight_layout()
plt.savefig(os.path.join('results', 'figures', 'shap_beeswarm_rg3.png'), dpi=300, bbox_inches='tight')
plt.close()
print('✅ Saved: results/figures/shap_beeswarm_rg3.png')
print('   Interpretation: Which verified features distinguish RG3 classification')
