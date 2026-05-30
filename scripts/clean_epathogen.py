from __future__ import annotations

from pathlib import Path

import pandas as pd


def _norm(col: str) -> str:
    return (
        str(col)
        .strip()
        .lower()
        .replace("\n", " ")
        .replace("_", " ")
        .replace("  ", " ")
    )


def main() -> None:
    raw_path = Path("data/raw/epathogen_raw.csv")
    if not raw_path.exists():
        raise SystemExit(
            "Missing data/raw/epathogen_raw.csv.\n"
            "Download from https://ePathogen.phac-aspc.gc.ca/ePathogen/do/RSB and save it there, then rerun."
        )

    df = pd.read_csv(raw_path)
    print("Columns:", df.columns.tolist())
    print("Shape:", df.shape)

    # Build a normalized column map for flexible matching
    norm_to_orig = {_norm(c): c for c in df.columns}

    def pick(*candidates: str) -> str | None:
        for cand in candidates:
            key = _norm(cand)
            if key in norm_to_orig:
                return norm_to_orig[key]
        # try contains-match
        for key, orig in norm_to_orig.items():
            for cand in candidates:
                if _norm(cand) in key:
                    return orig
        return None

    # ePATHogen export commonly uses 'Name' and 'Human classification' (RG1-4)
    organism_col = pick("Name", "Organism", "Organism name", "Pathogen", "Pathogen name")
    rg_col = pick("Human classification", "Risk Group", "RG", "Risk group")
    transmission_col = pick("Transmission Route", "Transmission", "Route of transmission")
    host_col = pick("Host Range", "Host", "Hosts")
    agent_type_col = pick("Agent type", "Agent category", "Type")
    alt_names_col = pick("Alternate names", "Aliases", "Synonyms")

    keep = [c for c in [organism_col, rg_col, agent_type_col, alt_names_col, transmission_col, host_col] if c]
    if not keep:
        raise SystemExit("Could not identify relevant columns in ePATHogen export.")

    out = df[keep].copy()
    rename = {}
    if organism_col:
        rename[organism_col] = "Organism"
    if rg_col:
        rename[rg_col] = "Risk Group"
    if agent_type_col:
        rename[agent_type_col] = "Agent Type"
    if alt_names_col:
        rename[alt_names_col] = "Alternate Names"
    if transmission_col:
        rename[transmission_col] = "Transmission Route"
    if host_col:
        rename[host_col] = "Host Range"
    out = out.rename(columns=rename)

    out_path = Path("data/raw/epathogen_clean.csv")
    out.to_csv(out_path, index=False)
    print(f"Saved {out_path.as_posix()} — shape: {out.shape}")


if __name__ == "__main__":
    main()
