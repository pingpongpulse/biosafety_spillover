import pandas as pd
import pickle, json, os
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import classification_report

df = pd.read_csv('data/processed/smote_dataset.csv')
feature_cols = [
    'genome_type_enc', 'transmission_route_enc', 'host_range_enc',
    'environmental_stability_enc', 'treatment_available_enc',
    'infectious_dose_enc', 'zoonotic_enc'
]
X = df[feature_cols]
y = df['rg_label']

with open('models/xgboost_rg_classifier.pkl','rb') as f:
    model = pickle.load(f)
with open('results/model_results.json') as f:
    metrics = json.load(f)

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
y_pred = cross_val_predict(model, X, y, cv=cv)

report = classification_report(y, y_pred,
    target_names=['RG1','RG2','RG3','RG4'], output_dict=True)

rows = []
for rg in ['RG1','RG2','RG3','RG4']:
    r = report[rg]
    rows.append({'Risk Group': rg,
                 'Precision': round(r['precision'],3),
                 'Recall':    round(r['recall'],3),
                 'F1-Score':  round(r['f1-score'],3),
                 'Support':   int(r['support'])})
m = report['macro avg']
rows.append({'Risk Group': 'Macro Avg',
             'Precision': round(m['precision'],3),
             'Recall':    round(m['recall'],3),
             'F1-Score':  round(m['f1-score'],3),
             'Support':   int(m['support'])})

os.makedirs('results/tables', exist_ok=True)
t1 = pd.DataFrame(rows)
t1.to_csv('results/tables/per_class_metrics.csv', index=False)
print("Table 1 saved: results/tables/per_class_metrics.csv")
print(t1.to_string(index=False))

summary = pd.DataFrame([
    ['Model', 'XGBoost (Gradient Boosted Trees)'],
    ['Task', 'Multi-class classification (RG1–RG4)'],
    ['Input', '7 biological metadata features'],
    ['Training samples', str(metrics['training_samples'])],
    ['Validation', '5-fold stratified cross-validation'],
    ['Class balancing', 'SMOTE (k_neighbors=3)'],
    ['F1-macro (CV)', f"{metrics['cv_f1_macro_mean']:.3f} ± {metrics['cv_f1_macro_std']:.3f}"],
    ['Accuracy (CV)', f"{metrics['cv_accuracy_mean']:.3f} ± {metrics['cv_accuracy_std']:.3f}"],
], columns=['Parameter','Value'])

summary.to_csv('results/tables/model_summary.csv', index=False)
print("\nTable 2 saved: results/tables/model_summary.csv")
print(summary.to_string(index=False))