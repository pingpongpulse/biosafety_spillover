import pandas as pd
import matplotlib.pyplot as plt
import os
from imblearn.over_sampling import SMOTE
from collections import Counter

df = pd.read_csv('data/processed/rg_dataset_encoded.csv')

feature_cols = [
    'genome_type_enc', 'transmission_route_enc', 'host_range_enc',
    'environmental_stability_enc', 'treatment_available_enc',
    'infectious_dose_enc', 'zoonotic_enc'
]

X = df[feature_cols]
y = df['rg_label']

print(f"Before SMOTE: {dict(Counter(y))}")

smote = SMOTE(random_state=42, k_neighbors=3)
X_res, y_res = smote.fit_resample(X, y)

print(f"After SMOTE:  {dict(Counter(y_res))}")
print(f"Dataset grew from {len(X)} to {len(X_res)} rows")

out = pd.DataFrame(X_res, columns=feature_cols)
out['rg_label'] = y_res
out.to_csv('data/processed/smote_dataset.csv', index=False)
print("Saved: data/processed/smote_dataset.csv")

# Plot
os.makedirs('results/figures', exist_ok=True)
labels = ['RG1','RG2','RG3','RG4']
colors = ['#3B82F6','#10B981','#F59E0B','#EF4444']
before = [Counter(y).get(i,0) for i in range(4)]
after  = [Counter(y_res).get(i,0) for i in range(4)]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12,5))
for ax, counts, title in [(ax1,before,'Before SMOTE'),(ax2,after,'After SMOTE')]:
    bars = ax.bar(labels, counts, color=colors, edgecolor='white')
    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.set_xlabel('WHO Risk Group')
    ax.set_ylabel('Count')
    for bar, v in zip(bars, counts):
        ax.text(bar.get_x()+bar.get_width()/2, v+30, str(v), ha='center', fontweight='bold')

plt.suptitle('Class Distribution Before vs After SMOTE', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('results/figures/smote_chart.png', dpi=300, bbox_inches='tight')
plt.close()
print("Saved: results/figures/smote_chart.png")