import pandas as pd
import numpy as np
import pickle, os
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import confusion_matrix

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

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
y_pred = cross_val_predict(model, X, y, cv=cv)

cm = confusion_matrix(y, y_pred)
cm_norm = cm.astype('float') / cm.sum(axis=1)[:,np.newaxis]
labels = ['RG1','RG2','RG3','RG4']

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14,6))

sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=labels, yticklabels=labels,
            linewidths=0.5, linecolor='white', ax=ax1)
ax1.set_title('Confusion Matrix (Raw Counts)', fontsize=13, fontweight='bold')
ax1.set_xlabel('Predicted Risk Group')
ax1.set_ylabel('True Risk Group')

sns.heatmap(cm_norm, annot=True, fmt='.2f', cmap='Blues',
            xticklabels=labels, yticklabels=labels,
            linewidths=0.5, linecolor='white', ax=ax2)
ax2.set_title('Confusion Matrix (Normalized)', fontsize=13, fontweight='bold')
ax2.set_xlabel('Predicted Risk Group')
ax2.set_ylabel('True Risk Group')

plt.suptitle('BioRiskNet — WHO Risk Group Classifier (5-fold CV)',
             fontsize=13, fontweight='bold', y=1.01)
plt.tight_layout()
os.makedirs('results/figures', exist_ok=True)
plt.savefig('results/figures/confusion_matrix.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: results/figures/confusion_matrix.png")