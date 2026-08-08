"""Find the evidence-backed answer to "What makes a movie successful?".

The audit (02) established *which* films can be analysed at all. This script
asks what the analysable subset actually supports, and it deliberately tests
the claims we would like to make against the ones the data will carry.

Method notes
------------
* Spearman (rank) correlation throughout. Revenue, budget and ROI are all
  heavily right-skewed; Pearson on raw values would be dominated by a handful
  of blockbusters.
* Medians, never means, for any money figure — with the mean printed alongside
  so the report can show *why* the median was chosen.
* Every breakdown carries its film count. A genre with 30 films does not get
  the same visual weight as one with 3,000.
* No inflation adjustment. A CPI series would be an external dataset, which
  Round 3 forbids. Cross-era money comparisons are therefore reported as
  nominal and flagged as such.

Outputs
-------
analysis/out/correlations.csv      rank correlations vs each success definition
analysis/out/budget_deciles.csv    the "does money buy returns" evidence
analysis/out/genre_performance.csv genre medians with counts
analysis/out/definition_overlap.csv how little the three top-100 lists overlap
analysis/out/seasonality.csv       release month vs outcome
analysis/out/companies.csv         studios with enough films to rank
analysis/out/findings.json         everything the report quotes

Usage
-----
    python analysis/03_metric_exploration.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
EXTRACT = REPO / "work" / "extract"
OUT = REPO / "analysis" / "out"

MIN_VOTES_FOR_RATING = 50
MIN_CREDIBLE_BUDGET = 10_000
MIN_CREDIBLE_REVENUE = 10_000

# Industry rule of thumb: a theatrical film needs roughly 2.5x its production
# budget in gross box office to break even, because the exhibitor keeps around
# half the ticket price and marketing ("P&A") is not in the budget figure.
# This is an assumption imported from domain knowledge, NOT from the data, and
# the report states it as such.
BREAKEVEN_MULTIPLE = 2.5


def analysable() -> pd.DataFrame:
    movies = pd.read_parquet(EXTRACT / "Movies.parquet")
    frame = movies[
        (movies["Status"] == "Released")
        & (movies["Release Date"].notna())
        & (movies["Budget"] >= MIN_CREDIBLE_BUDGET)
        & (movies["Revenue"] >= MIN_CREDIBLE_REVENUE)
        & (movies["Vote Count"] >= MIN_VOTES_FOR_RATING)
    ].copy()
    frame["ROI"] = frame["Revenue"] / frame["Budget"]
    frame["Profit"] = frame["Revenue"] - frame["Budget"]
    frame["Release Year"] = frame["Release Date"].dt.year
    frame["Release Month"] = frame["Release Date"].dt.month
    frame["Breaks Even"] = frame["ROI"] >= BREAKEVEN_MULTIPLE
    return frame


def spearman(frame: pd.DataFrame, drivers: list[str], targets: list[str]) -> pd.DataFrame:
    rows = []
    for driver in drivers:
        row = {"Driver": driver}
        for target in targets:
            subset = frame[[driver, target]].dropna()
            row[target] = round(
                float(subset[driver].rank().corr(subset[target].rank())), 3
            )
        row["n"] = int(len(frame[drivers + targets].dropna()))
        rows.append(row)
    return pd.DataFrame(rows)


def deciles(frame: pd.DataFrame) -> pd.DataFrame:
    """Does a bigger budget buy a bigger *return*, or just a bigger gross?"""
    frame = frame.copy()
    frame["Budget decile"] = pd.qcut(frame["Budget"], 10, labels=False, duplicates="drop") + 1
    grouped = frame.groupby("Budget decile").agg(
        Films=("Movie ID", "size"),
        **{
            "Median budget": ("Budget", "median"),
            "Median revenue": ("Revenue", "median"),
            "Median ROI": ("ROI", "median"),
            "Median profit": ("Profit", "median"),
            "Share breaking even": ("Breaks Even", "mean"),
            "Median rating": ("Vote Average", "median"),
        },
    ).reset_index()
    return grouped


def genre_performance(frame: pd.DataFrame) -> pd.DataFrame:
    bridge = pd.read_parquet(EXTRACT / "Genre Bridge.parquet")
    genres = pd.read_parquet(EXTRACT / "Genres.parquet")
    joined = (
        frame.merge(bridge, on="Movie ID", how="inner")
        .merge(genres, on="Genre ID", how="inner")
    )
    grouped = joined.groupby("Genre").agg(
        Films=("Movie ID", "nunique"),
        **{
            "Median budget": ("Budget", "median"),
            "Median revenue": ("Revenue", "median"),
            "Median ROI": ("ROI", "median"),
            "Share breaking even": ("Breaks Even", "mean"),
            "Median rating": ("Vote Average", "median"),
        },
    ).reset_index()
    # A genre needs enough films for a median to mean anything.
    grouped["Reliable"] = grouped["Films"] >= 100
    return grouped.sort_values("Median ROI", ascending=False)


def definition_overlap(frame: pd.DataFrame, top_n: int = 100) -> pd.DataFrame:
    """Three defensible definitions of success, three different top-100 lists."""
    definitions = {
        "Box office (Revenue)": frame.nlargest(top_n, "Revenue")["Movie ID"],
        "Return (ROI)": frame.nlargest(top_n, "ROI")["Movie ID"],
        "Acclaim (Vote Average)": frame.nlargest(top_n, "Vote Average")["Movie ID"],
        "Profit (Revenue - Budget)": frame.nlargest(top_n, "Profit")["Movie ID"],
    }
    names = list(definitions)
    matrix = pd.DataFrame(index=names, columns=names, dtype=float)
    for a in names:
        for b in names:
            set_a, set_b = set(definitions[a]), set(definitions[b])
            matrix.loc[a, b] = len(set_a & set_b) / top_n
    matrix = matrix.reset_index().rename(columns={"index": "Definition"})

    all_four = set.intersection(*(set(v) for v in definitions.values()))
    return matrix, all_four, definitions


def seasonality(frame: pd.DataFrame) -> pd.DataFrame:
    grouped = frame.groupby("Release Month").agg(
        Films=("Movie ID", "size"),
        **{
            "Median budget": ("Budget", "median"),
            "Median revenue": ("Revenue", "median"),
            "Median ROI": ("ROI", "median"),
            "Share breaking even": ("Breaks Even", "mean"),
        },
    ).reset_index()
    return grouped


def companies(frame: pd.DataFrame, min_films: int = 25) -> pd.DataFrame:
    bridge = pd.read_parquet(EXTRACT / "Production Company Bridge.parquet")
    dim = pd.read_parquet(EXTRACT / "Production Company.parquet")
    joined = (
        frame.merge(bridge, on="Movie ID", how="inner")
        .merge(dim, on="Production Company ID", how="inner")
    )
    grouped = joined.groupby("Production Company").agg(
        Films=("Movie ID", "nunique"),
        **{
            "Median budget": ("Budget", "median"),
            "Median revenue": ("Revenue", "median"),
            "Median ROI": ("ROI", "median"),
            "Share breaking even": ("Breaks Even", "mean"),
            "Median rating": ("Vote Average", "median"),
        },
    ).reset_index()
    return grouped[grouped["Films"] >= min_films].sort_values("Median ROI", ascending=False)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    frame = analysable()
    findings: dict[str, object] = {}

    print(f"analysable films: {len(frame):,}\n")

    # ---- 1. What correlates with what ---------------------------------------
    drivers = ["Budget", "Runtime", "Vote Average", "Vote Count", "Popularity"]
    targets = ["Revenue", "ROI", "Profit"]
    corr = spearman(frame, drivers, targets)
    corr.to_csv(OUT / "correlations.csv", index=False)
    print("=== Spearman rank correlations ===")
    print(corr.to_string(index=False))
    findings["correlations"] = corr.to_dict(orient="records")

    # ---- 2. Does money buy returns? ----------------------------------------
    dec = deciles(frame)
    dec.to_csv(OUT / "budget_deciles.csv", index=False)
    print("\n=== Budget deciles ===")
    print(dec.to_string(index=False))
    findings["budget_deciles"] = dec.to_dict(orient="records")

    lowest, highest = dec.iloc[0], dec.iloc[-1]
    findings["decile_contrast"] = {
        "lowest_budget_median": float(lowest["Median budget"]),
        "lowest_median_roi": float(lowest["Median ROI"]),
        "lowest_share_breakeven": float(lowest["Share breaking even"]),
        "highest_budget_median": float(highest["Median budget"]),
        "highest_median_revenue": float(highest["Median revenue"]),
        "highest_median_roi": float(highest["Median ROI"]),
        "highest_share_breakeven": float(highest["Share breaking even"]),
        "revenue_multiple": float(highest["Median revenue"] / lowest["Median revenue"]),
    }

    # ---- 3. The definitions disagree ---------------------------------------
    overlap, all_four, definitions = definition_overlap(frame)
    overlap.to_csv(OUT / "definition_overlap.csv", index=False)
    print("\n=== Top-100 overlap between success definitions ===")
    print(overlap.to_string(index=False))
    findings["definition_overlap"] = overlap.to_dict(orient="records")
    findings["films_in_all_four_top100"] = int(len(all_four))
    if all_four:
        names = frame[frame["Movie ID"].isin(all_four)][
            ["Title", "Release Year", "Budget", "Revenue", "ROI", "Vote Average"]
        ].sort_values("Revenue", ascending=False)
        print("\nFilms in ALL four top-100 lists:")
        print(names.to_string(index=False))
        findings["films_in_all_four"] = names.to_dict(orient="records")

    # ---- 4. Break-even reality ---------------------------------------------
    findings["breakeven"] = {
        "multiple": BREAKEVEN_MULTIPLE,
        "share_breaking_even": float(frame["Breaks Even"].mean()),
        "share_revenue_above_budget": float((frame["ROI"] >= 1).mean()),
        "median_roi": float(frame["ROI"].median()),
    }
    print(
        f"\n=== Break-even ===\n"
        f"revenue > budget:        {(frame['ROI'] >= 1).mean():.1%}\n"
        f"revenue > {BREAKEVEN_MULTIPLE}x budget:  {frame['Breaks Even'].mean():.1%}\n"
        f"median ROI:              {frame['ROI'].median():.2f}x"
    )

    # ---- 5. Genre ----------------------------------------------------------
    genre = genre_performance(frame)
    genre.to_csv(OUT / "genre_performance.csv", index=False)
    print("\n=== Genre performance ===")
    print(genre.to_string(index=False))
    findings["genre_performance"] = genre.to_dict(orient="records")

    # ---- 6. Seasonality ----------------------------------------------------
    season = seasonality(frame)
    season.to_csv(OUT / "seasonality.csv", index=False)
    print("\n=== Release month ===")
    print(season.to_string(index=False))
    findings["seasonality"] = season.to_dict(orient="records")

    # ---- 7. Studios --------------------------------------------------------
    comp = companies(frame)
    comp.to_csv(OUT / "companies.csv", index=False)
    print("\n=== Production companies (>=25 films) — top 15 by median ROI ===")
    print(comp.head(15).to_string(index=False))
    print("\n=== bottom 10 ===")
    print(comp.tail(10).to_string(index=False))
    findings["companies_top"] = comp.head(20).to_dict(orient="records")

    # ---- 8. Rating vs money: the acclaim/return gap ------------------------
    frame["Rating band"] = pd.cut(
        frame["Vote Average"],
        [0, 5, 6, 6.5, 7, 7.5, 10],
        labels=["<5", "5–6", "6–6.5", "6.5–7", "7–7.5", "7.5+"],
    )
    rating_band = frame.groupby("Rating band", observed=True).agg(
        Films=("Movie ID", "size"),
        **{
            "Median budget": ("Budget", "median"),
            "Median revenue": ("Revenue", "median"),
            "Median ROI": ("ROI", "median"),
            "Share breaking even": ("Breaks Even", "mean"),
        },
    ).reset_index()
    rating_band.to_csv(OUT / "rating_bands.csv", index=False)
    print("\n=== Rating bands ===")
    print(rating_band.to_string(index=False))
    findings["rating_bands"] = rating_band.to_dict(orient="records")

    (OUT / "findings.json").write_text(
        json.dumps(findings, indent=2, default=str), encoding="utf-8"
    )
    print(f"\nwrote {OUT.relative_to(REPO)}/findings.json and 7 CSVs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
