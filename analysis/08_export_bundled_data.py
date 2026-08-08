"""Export the starter file's model tables as CSVs for the bundled-data build.

Why this exists
---------------
The canonical semantic model loads the raw Kaggle CSV, exactly as the official
contest instructions describe. That requires a Kaggle account. For a machine
without one, this script exports every table of the official starter .pbix's
own model to CSV, so that the bundled variant of the project (see
``05_build_semantic_model.py --bundled``) can refresh from files shipped next
to the .pbip.

The data is byte-for-byte the starter file's model content — the same snapshot
every competitor receives — just serialised to CSV. Nothing is added, dropped
or altered. `Movies.csv` carries the 17 columns the starter's own Power Query
produces; the derived columns (ROI, Is Measurable, …) are NOT exported, because
the bundled M pipeline computes them the same way the canonical one does.

Usage
-----
    python analysis/01_extract_model.py       # once, to fill work/extract
    python analysis/08_export_bundled_data.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
EXTRACT = REPO / "work" / "extract"
OUT = REPO / "work" / "bundle" / "MovieSuccess" / "Data"

# Table -> exported file name. Date is not exported: its M query generates the
# calendar locally and needs no data.
TABLES = {
    "Movies": "Movies.csv",
    "Genres": "Genres.csv",
    "Genre Bridge": "Genre Bridge.csv",
    "Production Company": "Production Company.csv",
    "Production Company Bridge": "Production Company Bridge.csv",
    "Keyword": "Keyword.csv",
    "Keyword Bridge": "Keyword Bridge.csv",
}

# The 17 columns the starter's Movies query yields, in a fixed order the
# bundled M pipeline relies on.
MOVIES_COLUMNS = [
    "Movie ID", "Title", "Vote Average", "Vote Count", "Release Date",
    "Revenue", "Runtime", "Budget", "Popularity", "Status", "Adult",
    "Backdrop Path", "Homepage", "Original Language", "Original Title",
    "Poster Path", "Tagline",
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for table, filename in TABLES.items():
        source = EXTRACT / f"{table}.parquet"
        if not source.is_file():
            raise SystemExit(f"missing {source}; run analysis/01_extract_model.py first")
        frame = pd.read_parquet(source)

        if table == "Movies":
            frame = frame[MOVIES_COLUMNS].copy()
            # ISO dates parse unambiguously under the en-US culture the M
            # pipeline pins; lowercase booleans parse as M logicals.
            frame["Release Date"] = frame["Release Date"].dt.strftime("%Y-%m-%d")
            frame["Adult"] = frame["Adult"].map({True: "true", False: "false"})

        target = OUT / filename
        frame.to_csv(target, index=False, encoding="utf-8")
        print(f"{filename:32} rows={len(frame):>9,}  {target.stat().st_size/1e6:6.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
