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

plt.title('SHAP Feature Importance — Zoonotic Spillover Model', fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join('results', 'figures', 'shap_spillover.png'), dpi=300, bbox_inches='tight')
plt.close()
print('Saved: results/figures/shap_spillover.png')
