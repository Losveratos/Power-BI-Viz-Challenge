"""Data audit for Round 3 — "Lights, Camera, Insight".

Round 3 is scored on Responsible Data Use, so the audit is not a preliminary
step we throw away: its findings are the report's content. Every claim the
report makes about data quality is produced here, and every number in
docs/02-data-audit.md comes from this script's output.

Outputs
-------
analysis/out/audit_summary.json      machine-readable findings
analysis/out/audit_report.md         human-readable findings
analysis/out/budget_placeholders.csv the suspicious-budget evidence table
analysis/out/funnel.csv              the inclusion funnel, step by step

Usage
-----
    python analysis/02_data_audit.py
"""

from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
EXTRACT = REPO / "work" / "extract"
OUT = REPO / "analysis" / "out"

# Size of the upstream Kaggle dataset as stated by the challenge brief
# ("930k movies"). Used only to quantify how much the starter file's
# `[budget] > 0` filter removes before we ever see the data.
SOURCE_ROWS_APPROX = 930_000

# A rating average is meaningless when almost nobody voted. 50 is deliberately
# conservative: see docs/09-decision-log.md ADR-003 for the sensitivity check.
MIN_VOTES_FOR_RATING = 50

# Below this, a "budget" cannot plausibly be a real theatrical production
# budget stated in dollars. See ADR-002.
MIN_CREDIBLE_BUDGET = 10_000
MIN_CREDIBLE_REVENUE = 10_000


def load() -> dict[str, pd.DataFrame]:
    frames = {}
    for path in sorted(EXTRACT.glob("*.parquet")):
        frames[path.stem] = pd.read_parquet(path)
    if "Movies" not in frames:
        raise SystemExit("run analysis/01_extract_model.py first")
    return frames


def describe_placeholder_budgets(movies: pd.DataFrame) -> pd.DataFrame:
    """Find budget values that repeat far too often to be real budgets.

    Real production budgets are near-continuous. A value shared by hundreds of
    unrelated films is a data-entry default, not a budget.
    """
    counts = movies["Budget"].value_counts().reset_index()
    counts.columns = ["Budget", "Films"]
    counts["Share of films"] = counts["Films"] / len(movies)
    return counts.head(30)


def build_funnel(movies: pd.DataFrame) -> pd.DataFrame:
    """Every row we drop, and why — the report shows this to the viewer."""
    steps: list[tuple[str, int, str]] = []

    steps.append(
        (
            "Source dataset (TMDB, as described by the brief)",
            SOURCE_ROWS_APPROX,
            "Approximate; stated by the challenge brief, not verifiable inside the starter file.",
        )
    )
    steps.append(
        (
            "Starter file: Budget > 0",
            len(movies),
            "Applied by the supplied Power Query, before competitors see the data.",
        )
    )

    frame = movies
    frame = frame[frame["Status"] == "Released"]
    steps.append(("Status = Released", len(frame), "Excludes planned/in-production titles."))

    frame = frame[frame["Release Date"].notna()]
    steps.append(("Release Date present", len(frame), "A film with no date cannot be placed in time."))

    frame = frame[frame["Budget"] >= MIN_CREDIBLE_BUDGET]
    steps.append(
        (
            f"Budget >= ${MIN_CREDIBLE_BUDGET:,}",
            len(frame),
            "Removes placeholder budgets such as the repeated value 100.",
        )
    )

    frame = frame[frame["Revenue"] >= MIN_CREDIBLE_REVENUE]
    steps.append(
        (
            f"Revenue >= ${MIN_CREDIBLE_REVENUE:,}",
            len(frame),
            "Revenue 0 means 'not reported', not 'earned nothing' — it cannot enter a ratio.",
        )
    )

    frame = frame[frame["Vote Count"] >= MIN_VOTES_FOR_RATING]
    steps.append(
        (
            f"Vote Count >= {MIN_VOTES_FOR_RATING}",
            len(frame),
            "A rating from a handful of voters is noise.",
        )
    )

    out = pd.DataFrame(steps, columns=["Step", "Films", "Why"])
    out["Retained vs source"] = out["Films"] / SOURCE_ROWS_APPROX
    out["Dropped at this step"] = out["Films"].shift(1).fillna(out["Films"]) - out["Films"]
    return out


def analysable(movies: pd.DataFrame) -> pd.DataFrame:
    """The subset every financial claim in the report is restricted to."""
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
    return frame


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    frames = load()
    movies = frames["Movies"]

    findings: OrderedDict[str, object] = OrderedDict()
    findings["starter_rows"] = int(len(movies))
    findings["source_rows_approx"] = SOURCE_ROWS_APPROX
    findings["starter_share_of_source"] = round(len(movies) / SOURCE_ROWS_APPROX, 4)

    # --- Completeness of the columns the question depends on -----------------
    completeness = {}
    for column in [
        "Title",
        "Release Date",
        "Revenue",
        "Budget",
        "Runtime",
        "Vote Average",
        "Vote Count",
        "Original Language",
        "Poster Path",
        "Tagline",
    ]:
        series = movies[column]
        if series.dtype == "string" or series.dtype == object:
            missing = int((series.isna() | (series.astype("string").fillna("") == "")).sum())
        else:
            missing = int(series.isna().sum())
        completeness[column] = {
            "missing": missing,
            "missing_share": round(missing / len(movies), 4),
        }
    # Zeros are a second, sneakier kind of missing: the column is populated but
    # the value is a stand-in for "unknown".
    completeness["Revenue"]["zero"] = int((movies["Revenue"] == 0).sum())
    completeness["Revenue"]["zero_share"] = round(
        (movies["Revenue"] == 0).sum() / len(movies), 4
    )
    completeness["Runtime"]["zero"] = int((movies["Runtime"] == 0).sum())
    completeness["Vote Count"]["zero"] = int((movies["Vote Count"] == 0).sum())
    completeness["Vote Average"]["zero"] = int((movies["Vote Average"] == 0).sum())
    findings["completeness"] = completeness

    # --- Placeholder budgets -------------------------------------------------
    placeholders = describe_placeholder_budgets(movies)
    placeholders.to_csv(OUT / "budget_placeholders.csv", index=False)
    findings["top_budget_value"] = int(placeholders.iloc[0]["Budget"])
    findings["top_budget_films"] = int(placeholders.iloc[0]["Films"])
    findings["budget_under_10k"] = int((movies["Budget"] < MIN_CREDIBLE_BUDGET).sum())
    findings["budget_under_10k_share"] = round(
        (movies["Budget"] < MIN_CREDIBLE_BUDGET).sum() / len(movies), 4
    )

    # --- The inclusion funnel ------------------------------------------------
    funnel = build_funnel(movies)
    funnel.to_csv(OUT / "funnel.csv", index=False)
    findings["funnel"] = funnel.to_dict(orient="records")

    # --- The analysable subset ----------------------------------------------
    core = analysable(movies)
    findings["analysable_rows"] = int(len(core))
    findings["analysable_share_of_starter"] = round(len(core) / len(movies), 4)
    findings["analysable_share_of_source"] = round(len(core) / SOURCE_ROWS_APPROX, 4)
    findings["analysable_year_min"] = int(core["Release Year"].min())
    findings["analysable_year_max"] = int(core["Release Year"].max())

    # Revenue is extremely skewed; the mean is the wrong summary and the report
    # must say so rather than quietly using medians.
    findings["revenue_skew"] = {
        "mean": float(core["Revenue"].mean()),
        "median": float(core["Revenue"].median()),
        "p90": float(core["Revenue"].quantile(0.90)),
        "p99": float(core["Revenue"].quantile(0.99)),
        "top1pct_share_of_total": float(
            core.nlargest(max(1, len(core) // 100), "Revenue")["Revenue"].sum()
            / core["Revenue"].sum()
        ),
    }
    findings["roi_skew"] = {
        "mean": float(core["ROI"].mean()),
        "median": float(core["ROI"].median()),
        "p99": float(core["ROI"].quantile(0.99)),
        "max": float(core["ROI"].max()),
        "share_below_1x": float((core["ROI"] < 1).mean()),
        "share_below_2_5x": float((core["ROI"] < 2.5).mean()),
    }

    # --- Language and era coverage: who is *not* in this data ----------------
    findings["language_mix"] = (
        core["Original Language"].value_counts(normalize=True).head(8).round(4).to_dict()
    )
    findings["pre_1980_share"] = float((core["Release Year"] < 1980).mean())
    findings["last_decade_share"] = float((core["Release Year"] >= 2015).mean())

    # --- Duplicate titles ---------------------------------------------------
    dupes = movies["Title"].value_counts()
    findings["duplicate_titles"] = int((dupes > 1).sum())
    findings["max_same_title"] = int(dupes.max())

    (OUT / "audit_summary.json").write_text(
        json.dumps(findings, indent=2, default=str), encoding="utf-8"
    )

    # --- Human-readable report ----------------------------------------------
    lines: list[str] = []
    add = lines.append
    add("# Data audit output")
    add("")
    add("Generated by `analysis/02_data_audit.py`. Do not edit by hand.")
    add("")
    add("## Inclusion funnel")
    add("")
    add("| Step | Films | Dropped here | Share of source | Why |")
    add("|---|---:|---:|---:|---|")
    for row in funnel.itertuples():
        add(
            f"| {row.Step} | {row.Films:,} | "
            f"{int(getattr(row, '_5')):,} | "
            f"{getattr(row, '_4'):.1%} | {row.Why} |"
        )
    add("")
    add("## Column completeness (starter file, 85k rows)")
    add("")
    add("| Column | Missing | Missing % | Zero-as-unknown |")
    add("|---|---:|---:|---:|")
    for column, stats in completeness.items():
        zero = stats.get("zero")
        zero_text = f"{zero:,}" if zero is not None else "—"
        add(
            f"| {column} | {stats['missing']:,} | "
            f"{stats['missing_share']:.1%} | {zero_text} |"
        )
    add("")
    add("## Most repeated budget values (placeholder evidence)")
    add("")
    add("| Budget | Films | Share |")
    add("|---:|---:|---:|")
    for row in placeholders.head(10).itertuples():
        add(f"| {row.Budget:,} | {row.Films:,} | {getattr(row, '_3'):.2%} |")
    add("")
    add("## Skew")
    add("")
    add(
        f"- Revenue: mean ${findings['revenue_skew']['mean']:,.0f} vs median "
        f"${findings['revenue_skew']['median']:,.0f}"
    )
    add(
        f"- Top 1% of films earn "
        f"{findings['revenue_skew']['top1pct_share_of_total']:.1%} of all revenue in the subset"
    )
    add(
        f"- ROI: median {findings['roi_skew']['median']:.2f}x, "
        f"mean {findings['roi_skew']['mean']:.2f}x, max {findings['roi_skew']['max']:,.0f}x"
    )
    add(
        f"- {findings['roi_skew']['share_below_2_5x']:.1%} of films fall below the "
        "2.5x break-even rule of thumb"
    )
    add("")
    add("## Coverage")
    add("")
    add(f"- Analysable subset: {len(core):,} films "
        f"({findings['analysable_share_of_source']:.1%} of the source dataset)")
    add(f"- Years covered: {findings['analysable_year_min']}–{findings['analysable_year_max']}")
    add(f"- Released 2015 or later: {findings['last_decade_share']:.1%}")
    add(f"- Released before 1980: {findings['pre_1980_share']:.1%}")
    add("- Original-language mix (top 8): " + ", ".join(
        f"{k} {v:.1%}" for k, v in findings["language_mix"].items()
    ))

    (OUT / "audit_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n".join(lines))
    print(f"\nwrote {OUT.relative_to(REPO)}/audit_report.md, audit_summary.json, "
          "funnel.csv, budget_placeholders.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
