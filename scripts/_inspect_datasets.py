import pandas as pd

# ICTV
ictv = pd.read_excel('data/raw/ICTV_Master_Species_List_2025_MSL41.v1.xlsx',
                     sheet_name=None, nrows=0)
print('ICTV sheets:', list(ictv.keys()))
sheet = [s for s in ictv if 'msl' in s.lower() or 'species' in s.lower() or 'master' in s.lower()]
sname = sheet[0] if sheet else list(ictv.keys())[0]
df = pd.read_excel('data/raw/ICTV_Master_Species_List_2025_MSL41.v1.xlsx',
                   sheet_name=sname, nrows=5)
print(f'Sheet: {sname}  cols: {df.columns.tolist()}')
print(df.head(3).to_string())

print()
# virushostdb
vhdb = pd.read_csv('data/raw/virushostdb.tsv', sep='\t', nrows=5)
print('virushostdb columns:', vhdb.columns.tolist())
print(vhdb.head(3).to_string())

print()
# virus_genome_type unique genome_type values
vgt = pd.read_csv('data/raw/virus_genome_type.tsv', sep='\t')
print('genome_type unique:', vgt['genome_type'].unique().tolist())
print('Total rows in vgt:', len(vgt))
print('Virus col sample:', vgt['virus'].dropna().head(5).tolist())
