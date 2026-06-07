"""
BioRiskNet v2 — build_real_features.py
Person 1 replacement for auto_feature_fill.py.

Builds a REAL, LLM-free feature matrix for viral pathogens by merging:
  1. ePATHogen      → agent_type filter (keep Virus rows only)
  2. ICTV MSL 2025  → genome type, family (Genome column)
  3. Virus-Host DB  → host_breadth, infects_humans
  4. virus_genome_type.tsv → Baltimore group, NCBI tax_id lookup for matching
  5. Olival 2017    → envelope, segmented, vector_borne, zoonotic (subset)
  6. NCBI Entrez API→ resolve virus names to NCBI tax_ids for better matching

Output: data/processed/rg_dataset_real_features.csv
  - Only viral pathogens
  - 0% LLM-imputed data
  - Minimum 2 real features per organism (beyond agent_type) enforced

Run from project root:
  python scripts/build_real_features.py
"""

from __future__ import annotations

import time
import json
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd
from difflib import SequenceMatcher

# ── Biopython Entrez for NCBI queries ─────────────────────────────────────────
from Bio import Entrez
Entrez.email = "biorisknet.project@gmail.com"  # required by NCBI
NCBI_SLEEP   = 0.34   # ~3 requests/sec (safe without API key)
NCBI_CACHE   = Path("data/raw/ncbi_taxid_cache.json")

# ── Paths ─────────────────────────────────────────────────────────────────────
RG_DATASET       = Path("data/processed/rg_dataset.csv")
EPATHO_RAW       = Path("data/raw/epathogen_raw.csv")
ICTV_MSL         = Path("data/raw/ICTV_Master_Species_List_2025_MSL41.v1.xlsx")
VIRUSHOSTDB      = Path("data/raw/virushostdb.tsv")
VIRUS_GENOME_TYPE= Path("data/raw/virus_genome_type.tsv")
OLIVAL_VIRUSES   = Path("data/raw/olival_viruses.csv")
OLIVAL_ASSOC     = Path("data/raw/olival_associations.csv")
OUTPUT_PATH      = Path("data/processed/rg_dataset_real_features.csv")

MIN_REAL_FEATURES_BEYOND_AGENT_TYPE = 2  # strict threshold

# ── Genome type normaliser ─────────────────────────────────────────────────────
GENOME_MAP = {
    # dsDNA
    "I: dsDNA": "dsDNA", "dsDNA": "dsDNA",
    # ssDNA
    "II: ssDNA": "ssDNA", "ssDNA": "ssDNA",
    "II: ssDNA(+)": "ssDNA", "II: ssDNA(-)": "ssDNA",
    "II: ssDNA(+/-)": "ssDNA",  "ssDNA(+/-)": "ssDNA",
    # dsRNA
    "III: dsRNA": "dsRNA", "dsRNA": "dsRNA",
    # ssRNA positive
    "IV: ssRNA(+)": "ssRNA+", "+ssRNA": "ssRNA+", "ssRNA(+)": "ssRNA+",
    # ssRNA negative
    "V: ssRNA(-)": "ssRNA-", "ssRNA(-)": "ssRNA-",
    # ambisense / mixed
    "IV/V: ssRNA(+/-)": "ssRNA_amb", "IV/V: ssRNA": "ssRNA_amb",
    # retro
    "VII: dsDNA-RT": "dsDNA_RT",
    "VI: ssRNA-RT": "ssRNA_RT",
    # generic
    "RNA": "RNA", "Other RNA viruses": "RNA", "Others": "other",
}

# Envelope status by virus family (from ICTV/ViralZone — experimentally verified)
# 1 = enveloped, 0 = non-enveloped, -1 = unknown
FAMILY_ENVELOPE = {
    # Enveloped RNA viruses
    "Flaviviridae": 1, "Togaviridae": 1, "Coronaviridae": 1,
    "Rhabdoviridae": 1, "Paramyxoviridae": 1, "Filoviridae": 1,
    "Orthomyxoviridae": 1, "Bunyaviridae": 1, "Arenaviridae": 1,
    "Phenuiviridae": 1, "Nairoviridae": 1, "Hantaviridae": 1,
    "Peribunyaviridae": 1, "Retroviridae": 1, "Hepadnaviridae": 1,
    "Arteriviridae": 1, "Reoviridae": 0,  # exception: non-enveloped dsRNA
    # Enveloped DNA viruses
    "Herpesviridae": 1, "Poxviridae": 1, "Asfarviridae": 1,
    "Alloherpesviridae": 1, "Malacoherpesviridae": 1,
    # Non-enveloped RNA viruses
    "Picornaviridae": 0, "Caliciviridae": 0, "Astroviridae": 0,
    "Nodaviridae": 0, "Virgaviridae": 0,
    # Non-enveloped DNA viruses
    "Adenoviridae": 0, "Papillomaviridae": 0, "Polyomaviridae": 0,
    "Parvoviridae": 0, "Anelloviridae": 0, "Circoviridae": 0,
    "Genomoviridae": 0,
}

# ── Helpers ───────────────────────────────────────────────────────────────────

# Common biological words that don't help discriminate virus names
BIO_STOPWORDS = {
    'virus', 'human', 'the', 'of', 'and', 'a', 'an', 'strain', 'type',
    'subtype', 'species', 'infection', 'disease', 'syndrome',
}

# Known aliases: maps old/abbrev names (Olival 2017 era) to current ePATHogen names
# Key  = Olival name fragment (lowercase)
# Value= substring expected in RG dataset name (lowercase)
VIRUS_ALIASES: dict[str, str] = {
    'sars coronavirus':                'severe acute respiratory syndrome coronavirus',
    'mers coronavirus':                'middle east respiratory syndrome',
    'nipah virus':                     'nipah henipavirus',
    'hendra virus':                    'hendra henipavirus',
    'rabies virus':                    'rabies lyssavirus',
    'hiv-1':                           'human immunodeficiency virus 1',
    'hiv-2':                           'human immunodeficiency virus 2',
    'human immunodeficiency virus 1':  'human immunodeficiency virus 1',
    'human immunodeficiency virus 2':  'human immunodeficiency virus 2',
    'hepatitis c virus':               'hepacivirus c',
    'hepatitis b virus':               'hepatitis b virus',
    'hepatitis a virus':               'hepatovirus a',
    'hepatitis e virus':               'orthohepevirus a',
    'influenza a virus':               'influenza a virus',
    'influenza b virus':               'influenza b virus',
    'ebola virus':                     'ebola virus',
    'marburg virus':                   'marburg marburgvirus',
    'west nile virus':                 'west nile virus',
    'dengue virus':                    'dengue virus',
    'yellow fever virus':              'yellow fever virus',
    'zika virus':                      'zika virus',
    'chikungunya virus':               'chikungunya virus',
    'rift valley fever virus':         'rift valley fever phlebovirus',
    'hantaan virus':                   'hantaan orthohantavirus',
    'sin nombre virus':                'sin nombre orthohantavirus',
    'lassa virus':                     'lassa mammarenavirus',
    'junin virus':                     'junin mammarenavirus',
    'machupo virus':                   'machupo mammarenavirus',
    'lymphocytic choriomeningitis':    'lymphocytic choriomeningitis mammarenavirus',
    'crimean-congo hemorrhagic fever': 'crimean-congo hemorrhagic fever orthonairovirus',
    'venezuelan equine encephalitis':  'venezuelan equine encephalitis virus',
    'eastern equine encephalitis':     'eastern equine encephalitis virus',
    'western equine encephalitis':     'western equine encephalitis virus',
    'japanese encephalitis':           'japanese encephalitis virus',
    'tick-borne encephalitis':         'tick-borne encephalitis virus',
    'varicella-zoster virus':          'human alphaherpesvirus 3',
    'herpes simplex virus 1':          'human alphaherpesvirus 1',
    'herpes simplex virus 2':          'human alphaherpesvirus 2',
    'cytomegalovirus':                 'human betaherpesvirus 5',
    'epstein-barr virus':              'human gammaherpesvirus 4',
    'human herpesvirus 8':             'human gammaherpesvirus 8',
    'smallpox virus':                  'variola virus',
    'monkeypox virus':                 'monkeypox virus',
    'vaccinia virus':                  'vaccinia virus',
    'poliovirus':                      'enterovirus c',
    'human rhinovirus':                'rhinovirus',
    'coxsackievirus':                  'enterovirus',
    'rotavirus':                       'rotavirus',
    'norovirus':                       'norovirus',
    'human papillomavirus':            'alphapapillomavirus',
    'human t-lymphotropic virus':      'primate t-lymphotropic virus',
    'avian influenza':                 'influenza a virus',
    'h5n1':                            'influenza a virus',
    'h1n1':                            'influenza a virus',
}


def normalise(name: str) -> str:
    """Lower-case, strip punctuation for matching."""
    if not isinstance(name, str):
        return ""
    return re.sub(r"[^a-z0-9 ]", " ", name.lower()).strip()


def token_containment_score(query: str, candidate: str) -> float:
    """
    Fraction of the SHORTER name's meaningful tokens found in the LONGER name.
    Handles cases like 'Rabies virus' matching 'Rabies lyssavirus' (score=1.0)
    and 'Influenza A virus' matching 'Influenza A virus H1N1' (score=1.0).
    """
    q_tokens = set(normalise(query).split()) - BIO_STOPWORDS
    c_tokens = set(normalise(candidate).split()) - BIO_STOPWORDS
    if not q_tokens or not c_tokens:
        return 0.0
    shorter = q_tokens if len(q_tokens) <= len(c_tokens) else c_tokens
    longer  = c_tokens if len(q_tokens) <= len(c_tokens) else q_tokens
    return len(shorter & longer) / len(shorter)


def alias_score(query: str, candidate: str) -> float:
    """Check if query matches candidate via the VIRUS_ALIASES dictionary."""
    q_low = normalise(query)
    c_low = normalise(candidate)
    for alias_key, alias_target in VIRUS_ALIASES.items():
        alias_key_n    = normalise(alias_key)
        alias_target_n = normalise(alias_target)
        # Forward: query contains alias_key AND candidate contains alias_target
        if alias_key_n in q_low and alias_target_n in c_low:
            return 1.0
        # Reverse: candidate contains alias_key AND query contains alias_target
        if alias_key_n in c_low and alias_target_n in q_low:
            return 1.0
    return 0.0


def combined_match_score(query: str, candidate: str) -> float:
    """Combined score: max of SequenceMatcher, token-containment, and alias."""
    seq = SequenceMatcher(None, normalise(query), normalise(candidate)).ratio()
    tok = token_containment_score(query, candidate)
    ali = alias_score(query, candidate)
    return max(seq, tok, ali)


def best_fuzzy_match(query: str, candidates: list[str],
                     threshold: float = 0.72) -> str | None:
    """Return best matching candidate above threshold using combined scoring."""
    best_score = 0.0
    best_match = None
    for c in candidates:
        score = combined_match_score(query, c)
        if score > best_score:
            best_score = score
            best_match = c
    return best_match if best_score >= threshold else None


def load_ncbi_cache() -> dict:
    if NCBI_CACHE.exists():
        with open(NCBI_CACHE) as f:
            return json.load(f)
    return {}


def save_ncbi_cache(cache: dict) -> None:
    NCBI_CACHE.parent.mkdir(parents=True, exist_ok=True)
    with open(NCBI_CACHE, "w") as f:
        json.dump(cache, f, indent=2)


def query_ncbi_taxid(name: str, cache: dict) -> int | None:
    """Query NCBI Taxonomy for the tax_id of a virus name. Uses cache."""
    if name in cache:
        return cache[name]
    try:
        handle = Entrez.esearch(db="taxonomy", term=f"{name}[organism]", retmax=1)
        record = Entrez.read(handle)
        handle.close()
        time.sleep(NCBI_SLEEP)
        if record["IdList"]:
            tax_id = int(record["IdList"][0])
            cache[name] = tax_id
            return tax_id
    except Exception as e:
        print(f"  NCBI query failed for '{name}': {e}")
    cache[name] = None
    return None


def parse_genome_type(raw: str | float) -> str:
    if isinstance(raw, float) or not raw:
        return "unknown"
    key = str(raw).strip()
    return GENOME_MAP.get(key, "other")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    print("=" * 65)
    print("BioRiskNet v2 — build_real_features.py")
    print("=" * 65)

    # ── Step 1: Load RG dataset and filter to viruses ──────────────────────
    print("\n[Step 1] Loading RG dataset and filtering to viruses...")
    rg = pd.read_csv(RG_DATASET)
    epatho_raw = pd.read_csv(EPATHO_RAW)

    # Get virus names from ePATHogen
    virus_df = epatho_raw[epatho_raw["Agent type"] == "Virus"][["Name"]].copy()
    virus_df = virus_df.rename(columns={"Name": "epathogen_name"})
    virus_set = set(virus_df["epathogen_name"].str.strip())

    # Match against RG dataset (exact first, then fuzzy)
    rg_virus = rg[rg["name"].isin(virus_set)].copy()
    rg_other = rg[~rg["name"].isin(virus_set)].copy()

    # Try fuzzy match for remaining RG entries that might be viruses
    virus_name_list = list(virus_set)
    fuzzy_matched = []
    for name in rg_other["name"]:
        m = best_fuzzy_match(name, virus_name_list, threshold=0.80)
        if m:
            fuzzy_matched.append(name)

    rg_virus_fuzzy = rg_other[rg_other["name"].isin(fuzzy_matched)]
    rg_viruses = pd.concat([rg_virus, rg_virus_fuzzy], ignore_index=True)
    rg_viruses["agent_type"] = "Virus"

    print(f"  Viruses found: {len(rg_viruses)} (exact: {len(rg_virus)}, fuzzy: {len(rg_virus_fuzzy)})")
    print(f"  RG distribution: {rg_viruses['rg_label'].value_counts().sort_index().to_dict()}")

    # ── Step 2: Load ICTV MSL ──────────────────────────────────────────────
    print("\n[Step 2] Loading ICTV Master Species List...")
    ictv = pd.read_excel(ICTV_MSL, sheet_name="MSL")
    ictv = ictv[["Family", "Genus", "Species", "Genome"]].dropna(subset=["Species"])
    ictv["genome_type_ictv"] = ictv["Genome"].apply(parse_genome_type)
    ictv["Species_norm"] = ictv["Species"].str.lower().str.strip()
    ictv_species_dict = ictv.set_index("Species_norm").to_dict("index")
    ictv_family_dict  = ictv.groupby("Family")["genome_type_ictv"].agg(
        lambda x: x.mode()[0] if len(x) > 0 else "unknown"
    ).to_dict()
    print(f"  ICTV loaded: {len(ictv)} species, {ictv['Family'].nunique()} families")

    # ── Step 3: Load Virus-Host DB ─────────────────────────────────────────
    print("\n[Step 3] Loading Virus-Host DB...")
    vhdb = pd.read_csv(VIRUSHOSTDB, sep="\t", low_memory=False)
    vhdb.columns = vhdb.columns.str.strip().str.lower().str.replace(" ", "_")
    # compute host_breadth per virus tax_id
    host_breadth = (
        vhdb.groupby("virus_tax_id")["host_name"]
        .nunique()
        .reset_index()
        .rename(columns={"host_name": "host_breadth"})
    )
    # infects humans
    human_viruses = vhdb[
        vhdb["host_name"].str.contains("Homo sapiens", case=False, na=False)
    ]["virus_tax_id"].unique()
    host_breadth["infects_humans"] = host_breadth["virus_tax_id"].isin(human_viruses).astype(int)
    print(f"  Virus-Host DB: {len(vhdb)} associations, {host_breadth['virus_tax_id'].nunique()} unique viruses")

    # ── Step 4: Load virus_genome_type.tsv ────────────────────────────────
    print("\n[Step 4] Loading virus_genome_type.tsv...")
    vgt = pd.read_csv(VIRUS_GENOME_TYPE, sep="\t", low_memory=False)
    vgt.columns = vgt.columns.str.strip()
    vgt["genome_type_vgt"] = vgt["genome_type"].apply(parse_genome_type)
    # Build name → tax_id lookup from this file
    vgt_name_to_taxid = {}
    for _, row in vgt.iterrows():
        if pd.notna(row.get("species")) and pd.notna(row.get("virus_tax_id")):
            vgt_name_to_taxid[str(row["species"]).lower().strip()] = int(row["virus_tax_id"])
    print(f"  vgt loaded: {len(vgt)} entries, genome types: {vgt['genome_type_vgt'].value_counts().to_dict()}")

    # ── Step 5: Load Olival ────────────────────────────────────────────────
    print("\n[Step 5] Loading Olival 2017...")
    olival = pd.read_csv(OLIVAL_VIRUSES)
    olival_assoc = pd.read_csv(OLIVAL_ASSOC)

    # Host breadth from Olival associations
    olival_host_breadth = (
        olival_assoc.groupby("vVirusNameCorrected")["hHostNameFinal"]
        .nunique()
        .reset_index()
        .rename(columns={"hHostNameFinal": "olival_host_breadth"})
    )
    olival = olival.merge(olival_host_breadth, on="vVirusNameCorrected", how="left")

    olival_names = olival["vVirusNameCorrected"].tolist()
    olival_lookup = olival.set_index("vVirusNameCorrected").to_dict("index")
    print(f"  Olival loaded: {len(olival)} viruses")

    # ── Step 6: NCBI Entrez — resolve tax IDs ─────────────────────────────
    print("\n[Step 6] NCBI Entrez — resolving tax IDs for virus names...")
    ncbi_cache = load_ncbi_cache()

    # Prioritise names NOT already in vgt species lookup
    names_needing_ncbi = [
        n for n in rg_viruses["name"]
        if normalise(n) not in vgt_name_to_taxid and n not in ncbi_cache
    ]
    print(f"  Names to query NCBI: {len(names_needing_ncbi)} (others already cached or in vgt)")

    for i, virus_name in enumerate(names_needing_ncbi):
        if i > 0 and i % 50 == 0:
            print(f"    {i}/{len(names_needing_ncbi)} NCBI queries done...")
            save_ncbi_cache(ncbi_cache)
        query_ncbi_taxid(virus_name, ncbi_cache)

    save_ncbi_cache(ncbi_cache)
    print(f"  NCBI cache total: {len(ncbi_cache)} entries")

    # Build name → tax_id combined lookup (vgt + NCBI)
    def resolve_taxid(name: str) -> int | None:
        # 1. Try vgt species exact match
        k = normalise(name)
        if k in vgt_name_to_taxid:
            return vgt_name_to_taxid[k]
        # 2. Try NCBI cache
        if name in ncbi_cache and ncbi_cache[name]:
            return int(ncbi_cache[name])
        # 3. Try fuzzy match in vgt species keys
        m = best_fuzzy_match(name, list(vgt_name_to_taxid.keys()), threshold=0.82)
        if m:
            return vgt_name_to_taxid[m]
        return None

    # ── Step 7: Build feature row for each virus ──────────────────────────
    print("\n[Step 7] Building feature matrix...")

    rows = []
    for _, row in rg_viruses.iterrows():
        name = row["name"]
        rg   = row["rg_label"]

        feat = {
            "name":            name,
            "rg_label":        rg,
            "agent_type":      "Virus",
            "genome_type":     None,
            "is_dna":          None,
            "is_enveloped":    None,
            "is_segmented":    None,
            "is_vector_borne": None,
            "is_zoonotic":     None,
            "host_breadth":    None,
            "infects_humans":  None,
            "taxonomic_family":None,
            "_sources":        [],
        }

        # ── A: Resolve NCBI tax_id ─────────────────────────────────────────
        tax_id = resolve_taxid(name)
        feat["ncbi_tax_id"] = tax_id

        # ── B: Virus-Host DB features (by tax_id) ────────────────────────
        if tax_id:
            hb_row = host_breadth[host_breadth["virus_tax_id"] == tax_id]
            if not hb_row.empty:
                feat["host_breadth"]   = int(hb_row.iloc[0]["host_breadth"])
                feat["infects_humans"] = int(hb_row.iloc[0]["infects_humans"])
                feat["_sources"].append("virushostdb")

        # ── C: virus_genome_type.tsv (by tax_id) ─────────────────────────
        if tax_id:
            vgt_row = vgt[vgt["virus_tax_id"] == tax_id]
            if not vgt_row.empty:
                gt = vgt_row.iloc[0]["genome_type_vgt"]
                if gt != "unknown":
                    feat["genome_type"]    = gt
                    feat["taxonomic_family"]= vgt_row.iloc[0].get("family", None)
                    feat["_sources"].append("vgt")

        # ── D: ICTV MSL (by species name fuzzy match) ────────────────────
        m = best_fuzzy_match(name, list(ictv_species_dict.keys()), threshold=0.78)
        if m:
            ictv_row = ictv_species_dict[m]
            if not feat["genome_type"]:
                feat["genome_type"] = ictv_row["genome_type_ictv"]
            if not feat["taxonomic_family"]:
                feat["taxonomic_family"] = ictv_row["Family"]
            feat["_sources"].append("ictv")
        elif feat.get("taxonomic_family") and feat["taxonomic_family"] in ictv_family_dict:
            # Fall back to family-level genome type
            if not feat["genome_type"] or feat["genome_type"] == "unknown":
                feat["genome_type"] = ictv_family_dict[feat["taxonomic_family"]]

        # ── E: Envelope from family lookup ────────────────────────────────
        fam = feat.get("taxonomic_family")
        if fam and fam in FAMILY_ENVELOPE:
            feat["is_enveloped"] = FAMILY_ENVELOPE[fam]

        # ── F: Olival (by name fuzzy match) ──────────────────────────────
        olival_match = best_fuzzy_match(name, olival_names, threshold=0.65)
        if olival_match:
            olr = olival_lookup[olival_match]
            if feat["is_enveloped"] is None and "vEnvelope" in olr:
                env = olr["vEnvelope"]
                if not pd.isna(env):
                    feat["is_enveloped"] = int(bool(env))
            if feat["is_segmented"] is None and "vSegmentedTF" in olr:
                seg = olr["vSegmentedTF"]
                if not pd.isna(seg):
                    feat["is_segmented"] = int(bool(seg))
            if feat["is_vector_borne"] is None and "vVectorYNna" in olr:
                vec = olr["vVectorYNna"]
                if not pd.isna(vec):
                    try:
                        feat["is_vector_borne"] = int(str(vec).strip() in ["1", "1.0", "True", "yes"])
                    except Exception:
                        pass
            if feat["is_zoonotic"] is None and "IsZoonotic" in olr:
                zon = olr["IsZoonotic"]
                if not pd.isna(zon):
                    feat["is_zoonotic"] = int(bool(zon))
            if feat["host_breadth"] is None and "olival_host_breadth" in olr:
                hb = olr["olival_host_breadth"]
                if not pd.isna(hb):
                    feat["host_breadth"] = int(hb)
            feat["_sources"].append("olival")

        # ── G: Derived features ───────────────────────────────────────────
        if feat["genome_type"]:
            feat["is_dna"] = 1 if "dna" in feat["genome_type"].lower() else 0

        feat["source_count"] = len(set(feat["_sources"]))
        feat["feature_sources"] = "|".join(sorted(set(feat["_sources"])))
        rows.append(feat)

    df = pd.DataFrame(rows)
    df = df.drop(columns=["_sources"])

    # ── Step 8: Apply strict feature threshold ─────────────────────────────
    print("\n[Step 8] Applying strict coverage filter...")
    real_feature_cols = [
        "genome_type", "is_dna", "is_enveloped", "is_segmented",
        "is_vector_borne", "is_zoonotic", "host_breadth", "infects_humans",
        "taxonomic_family",
    ]
    df["n_real_features"] = df[real_feature_cols].notna().sum(axis=1)
    df_strict = df[df["n_real_features"] >= MIN_REAL_FEATURES_BEYOND_AGENT_TYPE].copy()

    print(f"  Before filter: {len(df)} viruses")
    print(f"  After filter (>= {MIN_REAL_FEATURES_BEYOND_AGENT_TYPE} real features): {len(df_strict)}")
    print(f"  RG distribution: {df_strict['rg_label'].value_counts().sort_index().to_dict()}")
    print(f"  Feature completeness:")
    for col in real_feature_cols:
        n = df_strict[col].notna().sum()
        pct = 100 * n / len(df_strict)
        print(f"    {col:<22}: {n:4d} / {len(df_strict)}  ({pct:.1f}%)")

    # ── Step 9: Save ──────────────────────────────────────────────────────
    df_strict.to_csv(OUTPUT_PATH, index=False)
    print(f"\n[Done] Saved {len(df_strict)} viral organisms to {OUTPUT_PATH}")
    print(f"  Full dataset (no filter) also available for inspection:")
    df.to_csv(OUTPUT_PATH.parent / "rg_dataset_real_features_full.csv", index=False)

    print("\n[Source Coverage]")
    for src in ["virushostdb", "vgt", "ictv", "olival"]:
        n = df_strict["feature_sources"].str.contains(src, na=False).sum()
        print(f"  {src:<15}: {n} viruses matched")

    print("\n[Next Steps]")
    print("  Run: python scripts/encode_features.py")
    print("  (uses data/processed/rg_dataset_real_features.csv as input)")


if __name__ == "__main__":
    main()
