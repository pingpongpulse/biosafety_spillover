import os
import pandas as pd
import pickle
import shap
import matplotlib.pyplot as plt

os.makedirs(os.path.join('results', 'figures'), exist_ok=True)

model_path = os.path.join('models', 'xgboost_rg_classifier.pkl')
data_path = os.path.join('data', 'processed', 'smote_dataset.csv')
features_path = os.path.join('data', 'processed', 'rg_dataset_features.csv')

if not os.path.exists(model_path):
    raise FileNotFoundError('Missing model file: models/xgboost_rg_classifier.pkl')
if not os.path.exists(data_path):
    raise FileNotFoundError('Missing dataset file: data/processed/smote_dataset.csv')
if not os.path.exists(features_path):
    raise FileNotFoundError('Missing feature dataset: data/processed/rg_dataset_features.csv')

model = pickle.load(open(model_path, 'rb'))
df = pd.read_csv(data_path)
orig = pd.read_csv(features_path)
X = df.drop(columns=['rg_label'])

explainer = shap.TreeExplainer(model)

case_studies = ['SARS-CoV-2', 'Ebola virus', 'Escherichia coli']

for pathogen in case_studies:
    matches = orig[orig['name'].str.contains(pathogen, case=False, na=False)]
    if matches.empty:
        print(f'Not found: {pathogen}')
        continue
    idx = matches.index[0]
    if idx >= len(X):
        print(f'Index out of range for: {pathogen}')
        continue
    instance = X.iloc[[idx]]
    shap_vals = explainer.shap_values(instance)
    pred = model.predict(instance)[0]
    rg = pred + 1
    print(f'{pathogen}: Predicted RG{rg}')
    if isinstance(shap_vals, list):
        sv = shap_vals[pred][0]
        base_value = explainer.expected_value[pred] if isinstance(explainer.expected_value, list) else explainer.expected_value
    else:
        if len(shap_vals.shape) == 3: # (n_samples, n_features, n_classes)
            sv = shap_vals[0, :, pred]
        else:
            sv = shap_vals[0]
        base_value = explainer.expected_value[pred] if isinstance(explainer.expected_value, (list, tuple, type(shap_vals))) and len(explainer.expected_value) > 1 else explainer.expected_value

    explanation = shap.Explanation(
        values=sv,
        base_values=base_value,
        data=instance.iloc[0],
        feature_names=X.columns.tolist()
    )

    shap.waterfall_plot(explanation, show=False)
    plt.title(f'SHAP Explanation: {pathogen} (Predicted RG{rg})', fontweight='bold')
    plt.tight_layout()
    safe_name = pathogen.replace(' ', '_').replace('-', '_').replace('/', '_')
    filename = os.path.join('results', 'figures', f'shap_case_{safe_name}.png')
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    print(f'Saved: {filename}')
