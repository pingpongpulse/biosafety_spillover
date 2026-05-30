from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def normalize_rg(val: object) -> float:
    val_str = str(val).strip().upper()
    mapping = {
        "RG1": 1,
        "RG2": 2,
        "RG3": 3,
        "RG4": 4,
        "RISK GROUP 1": 1,
        "RISK GROUP 2": 2,
        "RISK GROUP 3": 3,
        "RISK GROUP 4": 4,
        "1": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "BSL-1": 1,
        "BSL-2": 2,
        "BSL-3": 3,
        "BSL-4": 4,
        "BSL 1": 1,
        "BSL 2": 2,
        "BSL 3": 3,
        "BSL 4": 4,
    }
    return float(mapping.get(val_str, np.nan))


def _load_csv(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        print(f"SKIP (missing): {path.as_posix()}")
        return None
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        print(f"SKIP (empty): {path.as_posix()}")
        return pd.DataFrame()


def main() -> None:
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Load datasets (skip gracefully if missing)
    absa = _load_csv(raw_dir / "absa_raw.csv")
    epatho = _load_csv(raw_dir / "epathogen_clean.csv")
    bmbl = _load_csv(raw_dir / "bmbl_extracted.csv")

    olival_v = _load_csv(raw_dir / "olival_viruses.csv")
    olival_a = _load_csv(raw_dir / "olival_associations.csv")

    # Standardize & collect RG label frames
    rg_frames: list[pd.DataFrame] = []

    if absa is not None and {"organism", "risk_group"}.issubset(absa.columns):
        tmp = absa.rename(columns={"organism": "name", "risk_group": "rg_label"})
        rg_frames.append(tmp[["name", "rg_label"]])

    if epatho is not None:
        # From clean_epathogen.py we expect 'Organism' + 'Risk Group'
        if {"Organism", "Risk Group"}.issubset(epatho.columns):
            tmp = epatho.rename(columns={"Organism": "name", "Risk Group": "rg_label"})
            rg_frames.append(tmp[["name", "rg_label"]])
        else:
            # best-effort
            cols = {c.lower(): c for c in epatho.columns}
            org = cols.get("organism")
            rg = cols.get("risk group") or cols.get("risk_group")
            if org and rg:
                tmp = epatho.rename(columns={org: "name", rg: "rg_label"})
                rg_frames.append(tmp[["name", "rg_label"]])

    if bmbl is not None and {"organism", "bsl_level"}.issubset(bmbl.columns):
        tmp = bmbl.rename(columns={"organism": "name", "bsl_level": "rg_label"})
        rg_frames.append(tmp[["name", "rg_label"]])

    if not rg_frames:
        raise SystemExit(
            "No Risk Group sources loaded.\n"
            "Expected at least one of: data/raw/absa_raw.csv, data/raw/epathogen_clean.csv, data/raw/bmbl_extracted.csv"
        )

    combined_rg = pd.concat(rg_frames, ignore_index=True)
    combined_rg["rg_label"] = combined_rg["rg_label"].apply(normalize_rg)
    combined_rg = combined_rg.dropna(subset=["rg_label"])
    combined_rg["rg_label"] = combined_rg["rg_label"].astype(int)

    # Where sources disagree, take the max (more conservative)
    combined_rg["name"] = combined_rg["name"].astype(str).str.strip()
    combined_rg = combined_rg[combined_rg["name"] != ""]
    combined_rg = combined_rg.groupby("name", as_index=False)["rg_label"].max()

    print("Risk Group dataset shape:", combined_rg.shape)
    print("Label distribution:")
    print(combined_rg["rg_label"].value_counts().sort_index())

    feature_cols = [
        "genome_type",
        "transmission_route",
        "host_range",
        "environmental_stability",
        "treatment_available",
        "infectious_dose",
        "zoonotic",
    ]
    for col in feature_cols:
        combined_rg[col] = np.nan

    rg_out = processed_dir / "rg_dataset.csv"
    combined_rg.to_csv(rg_out, index=False)
    print(f"Saved: {rg_out.as_posix()}")

    if olival_v is not None:
        spill_out = processed_dir / "spillover_dataset.csv"
        olival_v.to_csv(spill_out, index=False)
        print(f"Saved: {spill_out.as_posix()}")
    else:
        print("NOTE: Olival viruses file missing; spillover_dataset.csv not created.")

    # Keep associations too, as Person 3 may need it
    if olival_a is not None:
        assoc_out = processed_dir / "spillover_associations.csv"
        olival_a.to_csv(assoc_out, index=False)
        print(f"Saved: {assoc_out.as_posix()}")

    print("DONE — hand off to Person 2 now")


if __name__ == "__main__":
    main()
