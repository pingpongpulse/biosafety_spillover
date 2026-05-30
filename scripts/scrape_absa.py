from __future__ import annotations

import re
import time
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse
import json

import pandas as pd
import requests
from bs4 import BeautifulSoup


# The ABSA site redirects to a JS-driven app at my.absa.org.
# The table rows are fetched via an XHR POST endpoint (HTML snippet response).
BASE_PAGE = "https://my.absa.org/RiskGroups"
SEARCH_ENDPOINT = "https://my.absa.org/tiki-search_customsearch-customsearch"

# Fallback token observed from the browser XHR request. The site may rotate this;
# the scraper first tries to extract from HTML and only uses this if needed.
FALLBACK_DEFINITION = "deeb6df526292fb698072a3a6531a9ae"

SLEEP_SECONDS = 1
PAGE_SIZE = 500


def _extract_organism_from_entry_html(entry_html: str) -> str | None:
    soup = BeautifulSoup(entry_html, "html.parser")
    table = soup.find("table")
    if not table:
        return None

    rows: list[list[str]] = []
    for tr in table.find_all("tr"):
        cells = [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
        cells = [c for c in cells if c]
        if cells:
            rows.append(cells)
    if not rows:
        return None

    # The last row tends to be the actual value row.
    value_row = rows[-1]
    # Common shape: [Category, Genus, Species] or [Category, Viral Group] etc.
    # If we have genus+species, join them.
    if len(value_row) >= 3:
        genus = value_row[1].strip()
        species = value_row[2].strip()
        if genus and species and species.lower() != "species" and genus.lower() != "genus":
            return f"{genus} {species}".strip()
        if genus and genus.lower() != "genus":
            return genus
        return value_row[-1].strip() or None

    if len(value_row) == 2:
        # [Category, Viral Group] or similar
        val = value_row[1].strip()
        return val if val and val.lower() not in {"viral group", "group"} else None

    if len(value_row) == 1:
        return value_row[0].strip() or None
    return None


def _extract_risk_group_from_entry_html(entry_html: str) -> int | None:
    # Jurisdiction fields look like:
    #   <strong>Belgium (2008):</strong>  2<br>
    # Extract all 1-4 values that appear immediately after a </strong> tag.
    vals = [int(v) for v in re.findall(r"</strong>\s*([1-4])\s*(?:<br\s*/?>|<)", entry_html, flags=re.IGNORECASE)]
    if not vals:
        return None
    return max(vals)


def _extract_notes_from_entry_html(entry_html: str) -> str:
    # Keep the short 'notes:' fields (often Canada ePATHogen / Germany)
    notes = [
        n.strip()
        for n in re.findall(r"notes:</strong>\s*([^<]+)", entry_html, flags=re.IGNORECASE)
        if n and n.strip()
    ]
    # De-duplicate while preserving order
    seen: set[str] = set()
    out: list[str] = []
    for n in notes:
        if n not in seen:
            out.append(n)
            seen.add(n)
    return " | ".join(out)


def _parse_search_results(html: str) -> pd.DataFrame:
    # The response is a concatenation of entry blocks separated by <hr />.
    # Each entry usually contains a 2-row table (Category/Genus/Species) plus jurisdiction RG fields.
    parts = re.split(r"<hr\s*/?>", html, flags=re.IGNORECASE)
    records: list[dict[str, object]] = []
    for part in parts:
        if "<table" not in part.lower():
            continue
        organism = _extract_organism_from_entry_html(part)
        risk_group = _extract_risk_group_from_entry_html(part)
        if not organism or risk_group is None:
            continue
        records.append(
            {
                "organism": organism,
                "risk_group": risk_group,
                "notes": _extract_notes_from_entry_html(part),
            }
        )
    return pd.DataFrame.from_records(records)


def _extract_definition_token(page_html: str) -> str | None:
    # Token appears as a form field or inside JS as 'definition=<md5-like>'
    m = re.search(r"definition=([0-9a-f]{32})", page_html, flags=re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.search(r"name=['\"]definition['\"]\s+value=['\"]([0-9a-f]{32})['\"]", page_html, flags=re.IGNORECASE)
    if m:
        return m.group(1)
    return None


def _extract_content_input_id(page_html: str) -> str | None:
    # The search box id changes; we look for the customsearch_rg_* text input.
    soup = BeautifulSoup(page_html, "html.parser")
    for inp in soup.find_all("input"):
        if inp.get("type", "").lower() not in {"text", "search", ""}:
            continue
        inp_id = inp.get("id") or ""
        if inp_id.startswith("customsearch_rg_"):
            return inp_id
    # Fallback regex
    m = re.search(r"id=['\"](customsearch_rg_\d+)['\"]", page_html, flags=re.IGNORECASE)
    return m.group(1) if m else None


def _extract_quicklink_terms(page_html: str) -> list[str]:
    # Quicklinks are plain <a> tags pointing to tiki-index.php?page=Riskgroups&default%5bcontent%5d=<term>
    soup = BeautifulSoup(page_html, "html.parser")
    terms: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not isinstance(href, str):
            continue
        if "default%5bcontent%5d=" not in href and "default[content]=" not in href:
            continue

        try:
            href_decoded = unquote(href)
            parsed = urlparse(href_decoded)
            qs = parse_qs(parsed.query)
            vals = qs.get("default[content]")
            if not vals:
                continue
            term = str(vals[0]).strip()
            if term:
                terms.add(term)
        except Exception:
            continue

    return sorted(terms)


def main() -> None:
    out_dir = Path("data/raw")
    out_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (compatible; BioRiskNet/1.0)",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )

    # Prime cookies and fetch the dynamic definition token
    page_resp = session.get(BASE_PAGE, timeout=30)
    if page_resp.status_code != 200:
        raise SystemExit(f"Failed to load {BASE_PAGE} (status {page_resp.status_code})")

    page_html = page_resp.text

    definition = _extract_definition_token(page_html)
    if not definition:
        definition = FALLBACK_DEFINITION
        print(
            "WARNING: Could not extract 'definition' token from HTML; using fallback token. "
            "If scraping fails, recapture the token from browser network calls."
        )

    content_input_id = _extract_content_input_id(page_html)
    if not content_input_id:
        raise SystemExit("Could not identify the ABSA search input id (customsearch_rg_*).")

    terms = _extract_quicklink_terms(page_html)
    if not terms:
        raise SystemExit(
            "Could not extract Quicklinks terms from the page HTML. The site may have changed.\n"
            "As a fallback, use the browser to expand Quicklinks and capture their links."
        )

    print(f"Found {len(terms)} Quicklinks terms. Querying in batches of {PAGE_SIZE}...")

    all_tables: list[pd.DataFrame] = []
    headers = {
        "Referer": BASE_PAGE,
        "X-Requested-With": "XMLHttpRequest",
    }

    for idx, term in enumerate(terms, start=1):
        # The UI sends a JSON object under adddata keyed by the input id.
        adddata_obj = {
            content_input_id: {
                "config": {"_filter": "content", "type": "text"},
                "name": "input",
                "value": term,
            }
        }
        adddata = json.dumps(adddata_obj, separators=(",", ":"))

        offset = 0
        while True:
            form = {
                "definition": definition,
                "adddata": adddata,
                "searchid": "rg",
                "offset": str(offset),
                "maxRecords": str(PAGE_SIZE),
                "store_query": "",
                "page": "Riskgroups",
                "recalllastsearch": "1",
            }
            resp = session.post(SEARCH_ENDPOINT, data=form, headers=headers, timeout=30)
            if resp.status_code != 200:
                print(f"WARN: term={term!r} offset={offset} status={resp.status_code}")
                break

            if "Cache Expired" in resp.text:
                form["recalllastsearch"] = "0"
                resp = session.post(SEARCH_ENDPOINT, data=form, headers=headers, timeout=30)

            page_df = _parse_search_results(resp.text)
            if page_df.empty:
                break

            page_df["_query_term"] = term
            all_tables.append(page_df)

            if page_df.shape[0] < PAGE_SIZE:
                break
            offset += PAGE_SIZE
            time.sleep(SLEEP_SECONDS)

        if idx % 25 == 0:
            print(f"  Queried {idx}/{len(terms)} terms...")

    if not all_tables:
        df = pd.DataFrame(columns=["organism", "risk_group", "notes", "source_url", "query_term"])
    else:
        raw = pd.concat(all_tables, ignore_index=True)
        cols_norm = {c: str(c).strip().lower() for c in raw.columns}

        query_term = raw["_query_term"].astype(str).str.strip() if "_query_term" in raw.columns else ""
        df = pd.DataFrame(
            {
                "organism": raw["organism"].astype(str).str.strip(),
                "risk_group": raw["risk_group"],
                "notes": raw.get("notes", "").astype(str).str.strip() if "notes" in raw.columns else "",
                "source_url": BASE_PAGE,
                "query_term": query_term,
            }
        )

        df = df[(df["organism"] != "") & (df["risk_group"] != "")]
        df = df.drop_duplicates(subset=["organism", "risk_group", "notes"]) 

    out_path = out_dir / "absa_raw.csv"
    df.to_csv(out_path, index=False)
    print(f"Done. Saved {len(df)} records to {out_path.as_posix()}")

    if df.empty:
        print(
            "WARNING: No rows were extracted from the my.absa.org endpoint.\n"
            "The site may require additional parameters (filters/search term) or may have changed."
        )


if __name__ == "__main__":
    main()
