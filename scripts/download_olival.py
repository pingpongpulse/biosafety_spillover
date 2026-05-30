from __future__ import annotations

from pathlib import Path

import requests


BASE = "https://raw.githubusercontent.com/ecohealthalliance/HP3/master/data/"
FILES = ["associations.csv", "viruses.csv", "hosts.csv"]


def main() -> None:
    out_dir = Path("data/raw")
    out_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    for filename in FILES:
        url = f"{BASE}{filename}"
        resp = session.get(url, timeout=30)
        if resp.status_code != 200:
            raise SystemExit(f"FAILED: {url} — status {resp.status_code}")

        out_path = out_dir / f"olival_{filename}"
        out_path.write_bytes(resp.content)
        print(f"Downloaded: {filename} -> {out_path.as_posix()}")


if __name__ == "__main__":
    main()
