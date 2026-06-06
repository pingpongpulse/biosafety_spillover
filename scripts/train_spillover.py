import os
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from imblearn.over_sampling import SMOTE
import pickle

os.makedirs(os.path.join('results', 'figures'), exist_ok=True)

viruses_path = os.path.join('data', 'raw', 'olival_viruses.csv')
assoc_path = os.path.join('data', 'raw', 'olival_associations.csv')

if not os.path.exists(viruses_path) or not os.path.exists(assoc_path):
    raise FileNotFoundError('Missing Olival raw data files. Please place olival_viruses.csv and olival_associations.csv in data/raw/')

viruses = pd.read_csv(viruses_path)
assoc = pd.read_csv(assoc_path)
print('Loaded Olival data: viruses', viruses.shape, 'associations', assoc.shape)
print('Viruses columns:', viruses.columns.tolist())
print('Associations columns:', assoc.columns.tolist())

# Create binary spillover label.
if 'IsZoonotic' in viruses.columns:
    viruses['spillover'] = (viruses['IsZoonotic'] == 1).astype(int)
else:
    human_host_col = None
    for col in assoc.columns:
        if 'human' in col.lower() or 'homo' in col.lower():
            human_host_col = col
            break
    if human_host_col is not None:
        human_viruses = assoc[assoc[human_host_col].str.contains('Homo sapiens', case=False, na=False)]['vVirusNameCorrected'].unique()
        viruses['spillover'] = viruses['vVirusNameCorrected'].isin(human_viruses).astype(int)
    else:
        raise ValueError('Cannot infer spillover label from Olival data. Please inspect raw columns.')

print('Spillover distribution:', viruses['spillover'].value_counts().to_dict())

# Derive features from the Olival dataset.
viruses['host_count'] = assoc.groupby('vVirusNameCorrected')['hHostNameFinal'].nunique().reindex(viruses['vVirusNameCorrected']).fillna(0).astype(int).values
viruses['human_host'] = viruses['vVirusNameCorrected'].isin(
    assoc[assoc['hHostNameFinal'].str.contains('Homo sapiens', case=False, na=False)]['vVirusNameCorrected'].unique()
).astype(int)

feature_candidates = [
    'vIsTypeSpecies', 'ReverseZoonoses', 'IsHoSa',
    'vGenomeAveLength', 'vGenomeMinLength', 'vGenomeMaxLength',
    'vWOKcites', 'vPubMedCites',
    'vCytoReplicTF', 'vSegmentedTF',
    'vVectorYNna', 'vSSoDS', 'vDNAoRNA', 'vEnvelope',
    'host_count', 'human_host'
]

available = [c for c in feature_candidates if c in viruses.columns]
print('Available features:', available)

if not available:
    raise ValueError('No candidate features found in the Olival virus dataset.')

spillover_df = viruses[available + ['spillover']].copy()

# Encode non-numeric features so the model can train.
numeric_fill_zero = ['vGenomeAveLength', 'vGenomeMinLength', 'vGenomeMaxLength', 'vWOKcites', 'vPubMedCites', 'host_count']
for col in numeric_fill_zero:
    if col in spillover_df.columns:
        spillover_df[col] = spillover_df[col].fillna(0)

for col in spillover_df.columns:
    if col == 'spillover':
        continue
    if pd.api.types.is_bool_dtype(spillover_df[col]):
        spillover_df[col] = spillover_df[col].astype(int)
    elif not pd.api.types.is_numeric_dtype(spillover_df[col]):
        spillover_df[col] = spillover_df[col].fillna('unknown').astype(str)
        le = LabelEncoder()
        spillover_df[col] = le.fit_transform(spillover_df[col])
        print(f'Encoded {col}: {dict(zip(le.classes_, le.transform(le.classes_)))}')

spillover_df = spillover_df.dropna()
print('Dataset after dropna:', spillover_df.shape)

X = spillover_df[available]
y = spillover_df['spillover']

if len(y.unique()) < 2:
    raise ValueError('Spillover target has only one class after cleaning.')

smote = SMOTE(random_state=42, k_neighbors=3)
X_res, y_res = smote.fit_resample(X, y)
print('After SMOTE:', dict(pd.Series(y_res).value_counts()))

model = xgb.XGBClassifier(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.05,
    eval_metric='logloss',
    random_state=42
)

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
auc_scores = cross_val_score(model, X_res, y_res, cv=cv, scoring='roc_auc')
print(f'Spillover AUC: {auc_scores.mean():.3f} +/- {auc_scores.std():.3f}')

model.fit(X_res, y_res)

os.makedirs('results', exist_ok=True)
with open(os.path.join('results', 'spillover_model.pkl'), 'wb') as f:
    pickle.dump(model, f)

results = {
    'feature_columns': available,
    'n_samples': int(len(spillover_df)),
    'class_distribution': {int(k): int(v) for k, v in dict(pd.Series(y).value_counts()).items()},
    'smote_distribution': {int(k): int(v) for k, v in dict(pd.Series(y_res).value_counts()).items()},
    'cv_auc_mean': float(auc_scores.mean()),
    'cv_auc_std': float(auc_scores.std())
}
with open(os.path.join('results', 'spillover_results.json'), 'w', encoding='utf-8') as f:
    import json
    json.dump(results, f, indent=2)

spillover_df.to_csv(os.path.join('data', 'processed', 'spillover_dataset_clean.csv'), index=False)
print('Saved results/spillover_model.pkl and results/spillover_results.json')
print('Saved cleaned spillover dataset to data/processed/spillover_dataset_clean.csv')
