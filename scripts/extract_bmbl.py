from __future__ import annotations

from pathlib import Path

import pandas as pd
import pdfplumber
import re


def main() -> None:
    pdf_path = Path("data/raw/bmbl.pdf")
    if not pdf_path.exists():
        raise SystemExit(
            "Missing data/raw/bmbl.pdf.\n"
            "Download the BMBL 6th Edition PDF from CDC and save it there, then rerun.\n"
            "URL: https://www.cdc.gov/labs/pdf/SF__19_308133-A_BMBL6_00-BOOK-WEB-final-3.pdf"
        )

    label_re = re.compile(
        r"\b(?:BSL\s*-?\s*[1-4]|RG\s*-?\s*[1-4]|CONTAINMENT\s+LEVEL\s*[1-4]|RISK\s+GROUP\s*[1-4]|[1-4])\b",
        flags=re.IGNORECASE,
    )

    records: list[dict[str, object]] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_index, page in enumerate(pdf.pages):
            try:
                tables = page.extract_tables()
            except Exception:  # noqa: BLE001
                tables = []

            for table in tables or []:
                for row in table or []:
                    if not row or len(row) < 2:
                        continue
                    agent = str(row[0]).strip() if row[0] else ""
                    bsl = str(row[1]).strip() if row[1] else ""
                    if not agent or not bsl:
                        continue

                    # Skip section markers / table footnote keys
                    if agent in {"S", "A"} or re.fullmatch(r"[A-Z]\d{0,2}", agent):
                        continue

                    if label_re.search(bsl):
                        records.append({"organism": agent, "bsl_level": bsl, "page": page_index + 1})

    df = pd.DataFrame(records)
    if not df.empty:
        df = df.drop_duplicates(subset=["organism"])

    out_path = Path("data/raw/bmbl_extracted.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Extracted {len(df)} records from BMBL PDF -> {out_path.as_posix()}")


if __name__ == "__main__":
    main()
