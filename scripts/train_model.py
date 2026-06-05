import pandas as pd
import numpy as np
import xgboost as xgb
import pickle, json, os
from sklearn.model_selection import StratifiedKFold, cross_val_score, cross_val_predict
from sklearn.metrics import classification_report

df = pd.read_csv('data/processed/smote_dataset.csv')

feature_cols = [
    'genome_type_enc', 'transmission_route_enc', 'host_range_enc',
    'environmental_stability_enc', 'treatment_available_enc',
    'infectious_dose_enc', 'zoonotic_enc'
]

X = df[feature_cols]
y = df['rg_label']

print(f"Training data: {X.shape[0]} rows, {X.shape[1]} features")
print(f"Label distribution: {dict(y.value_counts().sort_index())}")

model = xgb.XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    eval_metric='mlogloss',
    random_state=42,
    num_class=4,
    verbosity=0
)

# 5-fold cross-validation
print("\nRunning 5-fold CV...")
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_f1  = cross_val_score(model, X, y, cv=cv, scoring='f1_macro')
cv_acc = cross_val_score(model, X, y, cv=cv, scoring='accuracy')

print(f"F1-macro  per fold: {[round(s,3) for s in cv_f1]}")
print(f"F1-macro  mean:     {cv_f1.mean():.3f} +/- {cv_f1.std():.3f}")
print(f"Accuracy  mean:     {cv_acc.mean():.3f} +/- {cv_acc.std():.3f}")

# Train final model on all data
print("\nTraining final model...")
model.fit(X, y)

# Full classification report
y_cv_pred = cross_val_predict(model, X, y, cv=cv)
print("\nClassification Report:")
print(classification_report(y, y_cv_pred, target_names=['RG1','RG2','RG3','RG4']))

# Save model
os.makedirs('models', exist_ok=True)
with open('models/xgboost_rg_classifier.pkl', 'wb') as f:
    pickle.dump(model, f)
print("Saved: models/xgboost_rg_classifier.pkl")

# Save metrics
os.makedirs('results', exist_ok=True)
results = {
    'cv_f1_macro_mean': round(float(cv_f1.mean()), 4),
    'cv_f1_macro_std':  round(float(cv_f1.std()),  4),
    'cv_f1_macro_scores': cv_f1.tolist(),
    'cv_accuracy_mean': round(float(cv_acc.mean()), 4),
    'cv_accuracy_std':  round(float(cv_acc.std()),  4),
    'training_samples': int(len(X)),
    'feature_names': feature_cols,
    'class_labels': ['RG1','RG2','RG3','RG4'],
    'model_params': {'n_estimators':300,'max_depth':6,'learning_rate':0.05}
}
with open('results/model_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print("Saved: results/model_results.json")

# Feature importance
fi = pd.DataFrame({'feature': feature_cols, 'importance': model.feature_importances_})
fi = fi.sort_values('importance', ascending=False)
print("\nFeature importances:")
print(fi.to_string(index=False))
fi.to_csv('results/feature_importances.csv', index=False)
print("Saved: results/feature_importances.csv")