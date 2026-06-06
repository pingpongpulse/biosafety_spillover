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
plt.title('SHAP Feature Importance — All Risk Groups', fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join('results', 'figures', 'shap_summary_bar.png'), dpi=300, bbox_inches='tight')
plt.close()
print('Saved: results/figures/shap_summary_bar.png')

if isinstance(shap_values, list) and len(shap_values) >= 3:
    shap_rg3 = shap_values[2]
else:
    shap_rg3 = shap_values

shap.summary_plot(shap_rg3, X, show=False)
plt.title('SHAP Beeswarm — Drivers of Risk Group 3 Classification', fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join('results', 'figures', 'shap_beeswarm_rg3.png'), dpi=300, bbox_inches='tight')
plt.close()
print('Saved: results/figures/shap_beeswarm_rg3.png')
