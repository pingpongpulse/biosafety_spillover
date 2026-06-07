"""
SHAP Spillover Model Explainability Pipeline
=============================================
IMPORTANT METHODOLOGICAL NOTE:
SHAP feature importance shows which verified biological features most distinguish 
spillover vs. non-spillover viruses in the OLIVAL dataset—NOT causal mechanisms.

This reflects CORRELATIONS in published host-virus interaction data, not novel 
biological discoveries. All features sourced from verified databases (see DATA_SOURCES.md).
"""

import os
import pandas as pd
import pickle
import shap
import matplotlib.pyplot as plt

os.makedirs(os.path.join('results', 'figures'), exist_ok=True)

model_path = os.path.join('results', 'spillover_model.pkl')
data_path = os.path.join('data', 'processed', 'spillover_dataset_clean.csv')

if not os.path.exists(model_path):
    raise FileNotFoundError('Missing model file: results/spillover_model.pkl')
if not os.path.exists(data_path):
    raise FileNotFoundError('Missing cleaned spillover dataset file: data/processed/spillover_dataset_clean.csv')

model = pickle.load(open(model_path, 'rb'))
df = pd.read_csv(data_path)
X = df.drop(columns=['spillover'])

explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X)

if isinstance(shap_values, list):
    shap.summary_plot(shap_values, X, show=False)
else:
    shap.summary_plot(shap_values, X, show=False)

# Updated title to reflect correlation analysis, not causal importance
plt.title('Feature Contributions to Spillover Classification\n(OLIVAL Dataset Correlations)', 
          fontweight='bold', fontsize=12)
plt.figtext(0.5, 0.02, 'Based on verified biological features from published host-virus databases', 
            ha='center', fontsize=9, style='italic', color='gray')
plt.tight_layout()
plt.savefig(os.path.join('results', 'figures', 'shap_spillover.png'), dpi=300, bbox_inches='tight')
plt.close()
print('✅ Saved: results/figures/shap_spillover.png')
print('   Interpretation: Feature contributions to model predictions (not biological causation)')
