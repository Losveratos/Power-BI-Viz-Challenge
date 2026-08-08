"""Extract the semantic model out of the official Round 3 starter .pbix.

Why this exists
---------------
The competition supplies a starter .pbix whose `Movies` query is already
filtered and whose data is embedded in the file. Rather than re-downloading the
raw Kaggle CSV (which would risk working from a *different* snapshot than the
one every other competitor gets), we read the model straight out of the starter
file. That guarantees "Use the provided dataset" in the strictest sense.

`pbixray` parses the VertiPaq `DataModel` stream, so this runs on any platform
without Power BI Desktop installed.

Outputs
-------
work/extract/<Table>.parquet   one file per model table
work/model/*.txt               M queries, DAX, relationships, schema

Usage
-----
    python analysis/01_extract_model.py
"""

from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

STARTER_URL = (
    "https://raw.githubusercontent.com/shannonlindsay/FabricCommunityContests/"
    "main/StarterFiles/World%20Champs%20BCN%2026%20-%20Round%203.pbix"
)

REPO = Path(__file__).resolve().parent.parent
WORK = REPO / "work"
STARTER = WORK / "starter.pbix"
EXTRACT = WORK / "extract"
MODEL = WORK / "model"

# Tables we need for the analysis. `Keyword`/`Keyword Bridge` are skipped:
# 1.2M+ rows that the final report does not use.
TABLES = [
    "Movies",
    "Genres",
    "Genre Bridge",
    "Production Company",
    "Production Company Bridge",
]


def download_starter() -> None:
    if STARTER.exists():
        print(f"starter.pbix already present ({STARTER.stat().st_size:,} bytes)")
        return
    WORK.mkdir(parents=True, exist_ok=True)
    print(f"downloading {STARTER_URL}")
    urllib.request.urlopen  # noqa: B018 - documents the transport used below
    with urllib.request.urlopen(STARTER_URL) as response, STARTER.open("wb") as fh:
        fh.write(response.read())
    print(f"saved {STARTER.stat().st_size:,} bytes")


def fingerprint() -> str:
    """SHA-256 of the starter file, so the audit is pinned to one snapshot."""
    digest = hashlib.sha256()
    with STARTER.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    try:
        from pbixray import PBIXRay
    except ImportError:
        print("pip install -r analysis/requirements.txt", file=sys.stderr)
        return 1

    download_starter()
    EXTRACT.mkdir(parents=True, exist_ok=True)
    MODEL.mkdir(parents=True, exist_ok=True)

    print(f"starter.pbix sha256 = {fingerprint()}")

    model = PBIXRay(str(STARTER))

    # Model metadata first: the M queries are the evidence for what the starter
    # file already filtered out before we ever saw the data.
    (MODEL / "schema.txt").write_text(model.schema.to_string(), encoding="utf-8")
    (MODEL / "relationships.txt").write_text(
        model.relationships.to_string(), encoding="utf-8"
    )
    (MODEL / "dax_measures.txt").write_text(
        model.dax_measures.to_string(), encoding="utf-8"
    )
    power_query = "\n\n".join(
        f"// ===== {row.TableName} =====\n{row.Expression}"
        for row in model.power_query.itertuples()
    )
    (MODEL / "power_query.m").write_text(power_query, encoding="utf-8")
    print(f"wrote model metadata to {MODEL.relative_to(REPO)}/")

    for table in TABLES:
        frame = model.get_table(table)
        target = EXTRACT / f"{table}.parquet"
        frame.to_parquet(target)
        print(f"{table:30} rows={len(frame):>9,}  cols={len(frame.columns):>2}  -> {target.name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
