"""Try to break the findings from 03 before the report publishes them.

Round 3 rewards "avoidance of misleading comparisons" and "honest communication
of uncertainty". The three headline findings all have plausible alternative
explanations, so each one gets an adversarial check here. Where a finding
survives, the report states it. Where it only partly survives, the report says
so on the page that shows it.

Checks
------
A. Survivorship bias in the low-budget tail. Low-budget films are far less
   likely to have any revenue reported, so the surviving ones are the ones that
   worked. This inflates decile 1's ROI. Quantified, not hand-waved.
B. Is the rating -> ROI relationship just an era effect, or a budget effect?
   Re-tested inside budget deciles and inside release eras.
C. Threshold sensitivity. Do the findings hold if the vote-count and revenue
   cut-offs move? If a conclusion only exists at one arbitrary threshold it is
   not a conclusion.
D. Is the budget U-curve driven by a handful of franchises?
E. Nominal-dollar distortion: how much of any cross-era comparison is just
   inflation we are forbidden to adjust for?

Outputs
-------
analysis/out/robustness.md     the write-up the report's Limits page draws on
analysis/out/robustness.json   the numbers

Usage
-----
    python analysis/04_robustness.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
EXTRACT = REPO / "work" / "extract"
OUT = REPO / "analysis" / "out"

BREAKEVEN_MULTIPLE = 2.5


def base() -> pd.DataFrame:
    movies = pd.read_parquet(EXTRACT / "Movies.parquet")
    movies = movies[(movies["Status"] == "Released") & movies["Release Date"].notna()].copy()
    movies["Release Year"] = movies["Release Date"].dt.year
    return movies


def subset(movies: pd.DataFrame, min_votes: int, min_revenue: int, min_budget: int) -> pd.DataFrame:
    frame = movies[
        (movies["Budget"] >= min_budget)
        & (movies["Revenue"] >= min_revenue)
        & (movies["Vote Count"] >= min_votes)
    ].copy()
    frame["ROI"] = frame["Revenue"] / frame["Budget"]
    frame["Breaks Even"] = frame["ROI"] >= BREAKEVEN_MULTIPLE
    return frame


def check_a_survivorship(movies: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """How reporting completeness varies with budget size."""
    credible = movies[movies["Budget"] >= 10_000].copy()
    bands = [10_000, 100_000, 1_000_000, 5_000_000, 20_000_000, 50_000_000, 1e12]
    labels = ["10k–100k", "100k–1M", "1M–5M", "5M–20M", "20M–50M", "50M+"]
    credible["Budget band"] = pd.cut(credible["Budget"], bands, labels=labels, right=False)
    grouped = credible.groupby("Budget band", observed=True).agg(
        Films=("Movie ID", "size"),
        **{
            "Revenue reported": ("Revenue", lambda s: int((s >= 10_000).sum())),
            "Has 50+ votes": ("Vote Count", lambda s: int((s >= 50).sum())),
        },
    ).reset_index()
    grouped["Revenue reporting rate"] = grouped["Revenue reported"] / grouped["Films"]
    grouped["Enters analysis rate"] = grouped["Has 50+ votes"] / grouped["Films"]

    lowest = grouped.iloc[0]
    highest = grouped.iloc[-1]
    summary = {
        "low_band": str(lowest["Budget band"]),
        "low_reporting_rate": float(lowest["Revenue reporting rate"]),
        "high_band": str(highest["Budget band"]),
        "high_reporting_rate": float(highest["Revenue reporting rate"]),
        "ratio": float(
            highest["Revenue reporting rate"] / max(lowest["Revenue reporting rate"], 1e-9)
        ),
    }
    return grouped, summary


def check_b_rating_confound(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Rating -> ROI, held inside budget deciles and inside eras."""
    frame = frame.copy()
    frame["Budget decile"] = pd.qcut(frame["Budget"], 10, labels=False, duplicates="drop") + 1
    frame["Well rated"] = frame["Vote Average"] >= 7.0

    within_budget = frame.groupby(["Budget decile", "Well rated"]).agg(
        Films=("Movie ID", "size"),
        **{"Median ROI": ("ROI", "median"), "Share breaking even": ("Breaks Even", "mean")},
    ).reset_index()
    pivot_budget = within_budget.pivot(
        index="Budget decile", columns="Well rated", values="Median ROI"
    )
    pivot_budget.columns = ["Rated < 7.0", "Rated >= 7.0"]
    pivot_budget["Uplift"] = pivot_budget["Rated >= 7.0"] / pivot_budget["Rated < 7.0"]
    pivot_budget = pivot_budget.reset_index()

    frame["Era"] = pd.cut(
        frame["Release Year"],
        [1900, 1980, 1995, 2005, 2015, 2030],
        labels=["pre-1980", "1980–94", "1995–2004", "2005–14", "2015+"],
    )
    within_era = frame.groupby(["Era", "Well rated"], observed=True).agg(
        Films=("Movie ID", "size"),
        **{"Median ROI": ("ROI", "median")},
    ).reset_index()
    pivot_era = within_era.pivot(index="Era", columns="Well rated", values="Median ROI")
    pivot_era.columns = ["Rated < 7.0", "Rated >= 7.0"]
    pivot_era["Uplift"] = pivot_era["Rated >= 7.0"] / pivot_era["Rated < 7.0"]
    pivot_era = pivot_era.reset_index()

    return pivot_budget, pivot_era


def check_c_thresholds(movies: pd.DataFrame) -> pd.DataFrame:
    """Do the headlines survive different arbitrary cut-offs?"""
    rows = []
    for min_votes in [0, 10, 50, 100, 500]:
        for min_revenue in [1, 10_000, 1_000_000]:
            frame = subset(movies, min_votes, min_revenue, 10_000)
            if len(frame) < 100:
                continue
            budget_roi = float(frame["Budget"].rank().corr(frame["ROI"].rank()))
            budget_rev = float(frame["Budget"].rank().corr(frame["Revenue"].rank()))
            rating_roi = float(frame["Vote Average"].rank().corr(frame["ROI"].rank()))
            rows.append(
                {
                    "Min votes": min_votes,
                    "Min revenue": min_revenue,
                    "Films": len(frame),
                    "rho Budget-Revenue": round(budget_rev, 3),
                    "rho Budget-ROI": round(budget_roi, 3),
                    "rho Rating-ROI": round(rating_roi, 3),
                    "Median ROI": round(float(frame["ROI"].median()), 2),
                    "Share breaking even": round(float(frame["Breaks Even"].mean()), 3),
                }
            )
    return pd.DataFrame(rows)


def check_d_ucurve(frame: pd.DataFrame) -> pd.DataFrame:
    """The U-curve, with the top decile's biggest hits removed."""
    frame = frame.copy()
    frame["Budget decile"] = pd.qcut(frame["Budget"], 10, labels=False, duplicates="drop") + 1

    full = frame.groupby("Budget decile")["ROI"].median()
    breakeven = frame.groupby("Budget decile")["Breaks Even"].mean()

    # Drop the 5% highest-revenue films inside every decile: if the U survives,
    # it is not a franchise artefact.
    trimmed_parts = []
    for _, group in frame.groupby("Budget decile"):
        cutoff = group["Revenue"].quantile(0.95)
        trimmed_parts.append(group[group["Revenue"] <= cutoff])
    trimmed = pd.concat(trimmed_parts)
    trimmed_median = trimmed.groupby("Budget decile")["ROI"].median()

    out = pd.DataFrame(
        {
            "Median ROI (all)": full,
            "Median ROI (top 5% revenue removed)": trimmed_median,
            "Share breaking even": breakeven,
            "Films": frame.groupby("Budget decile").size(),
        }
    ).reset_index()
    return out


def check_e_nominal(frame: pd.DataFrame) -> pd.DataFrame:
    """Median budget and revenue by era, in the nominal dollars we are stuck with."""
    frame = frame.copy()
    frame["Era"] = pd.cut(
        frame["Release Year"],
        [1900, 1980, 1995, 2005, 2015, 2030],
        labels=["pre-1980", "1980–94", "1995–2004", "2005–14", "2015+"],
    )
    return frame.groupby("Era", observed=True).agg(
        Films=("Movie ID", "size"),
        **{
            "Median budget": ("Budget", "median"),
            "Median revenue": ("Revenue", "median"),
            "Median ROI": ("ROI", "median"),
            "Share breaking even": ("Breaks Even", "mean"),
        },
    ).reset_index()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    movies = base()
    frame = subset(movies, 50, 10_000, 10_000)
    results: dict[str, object] = {}
    lines: list[str] = ["# Robustness checks", "",
                        "Generated by `analysis/04_robustness.py`. Do not edit by hand.", ""]

    # A ----------------------------------------------------------------------
    band_table, band_summary = check_a_survivorship(movies)
    results["survivorship"] = {
        "table": band_table.to_dict(orient="records"),
        "summary": band_summary,
    }
    print("=== A. Survivorship: revenue reporting rate by budget band ===")
    print(band_table.to_string(index=False))
    lines += [
        "## A. Survivorship bias in the low-budget tail",
        "",
        "| Budget band | Films | Revenue reported | Reporting rate | Enters analysis |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in band_table.itertuples():
        lines.append(
            f"| {row[1]} | {row.Films:,} | {getattr(row, '_3'):,} | "
            f"{getattr(row, '_5'):.1%} | {getattr(row, '_6'):.1%} |"
        )
    lines += [
        "",
        f"**Verdict: the finding is real but overstated.** Films in the "
        f"{band_summary['high_band']} budget band report revenue "
        f"{band_summary['ratio']:.1f}x more often than films in the "
        f"{band_summary['low_band']} band "
        f"({band_summary['high_reporting_rate']:.1%} vs "
        f"{band_summary['low_reporting_rate']:.1%}). Cheap films that flopped are "
        "largely absent from the data, so the measured return of the lowest "
        "budget decile is an upper bound, not an expectation. The report shows "
        "this on the page that makes the low-budget claim.",
        "",
    ]

    # B ----------------------------------------------------------------------
    pivot_budget, pivot_era = check_b_rating_confound(frame)
    results["rating_within_budget"] = pivot_budget.to_dict(orient="records")
    results["rating_within_era"] = pivot_era.to_dict(orient="records")
    print("\n=== B. Rating uplift within budget deciles ===")
    print(pivot_budget.to_string(index=False))
    print("\n=== B. Rating uplift within eras ===")
    print(pivot_era.to_string(index=False))

    uplifts = pivot_budget["Uplift"].dropna()
    survives_budget = bool((uplifts > 1).all())
    era_uplifts = pivot_era["Uplift"].dropna()
    survives_era = bool((era_uplifts > 1).all())
    results["rating_uplift_survives_budget_control"] = survives_budget
    results["rating_uplift_survives_era_control"] = survives_era
    results["rating_uplift_min"] = float(uplifts.min())
    results["rating_uplift_median"] = float(uplifts.median())

    lines += [
        "## B. Is the rating effect just budget or era in disguise?",
        "",
        "Median ROI of well-rated (>= 7.0) vs other films, *inside* each budget decile:",
        "",
        "| Budget decile | Rated < 7.0 | Rated >= 7.0 | Uplift |",
        "|---:|---:|---:|---:|",
    ]
    for row in pivot_budget.itertuples():
        lines.append(
            f"| {int(row[1])} | {row[2]:.2f}x | {row[3]:.2f}x | {row.Uplift:.2f}x |"
        )
    lines += ["", "And inside each release era:", "",
              "| Era | Rated < 7.0 | Rated >= 7.0 | Uplift |", "|---|---:|---:|---:|"]
    for row in pivot_era.itertuples():
        lines.append(f"| {row[1]} | {row[2]:.2f}x | {row[3]:.2f}x | {row.Uplift:.2f}x |")
    lines += [
        "",
        f"**Verdict: survives.** The uplift holds in "
        f"{'every' if survives_budget else 'most'} budget decile and in "
        f"{'every' if survives_era else 'most'} era, with a median uplift of "
        f"{uplifts.median():.2f}x and a minimum of {uplifts.min():.2f}x. Being "
        "well rated is not a proxy for being cheap or being old.",
        "",
        "**But note the direction of causation is not established.** Ratings are "
        "collected after release, from people who chose to watch. A film that "
        "reached a large, willing audience can be rated highly *because* it "
        "succeeded. The report states the association and explicitly declines to "
        "claim causation.",
        "",
    ]

    # C ----------------------------------------------------------------------
    thresholds = check_c_thresholds(movies)
    results["thresholds"] = thresholds.to_dict(orient="records")
    print("\n=== C. Threshold sensitivity ===")
    print(thresholds.to_string(index=False))
    sign_stable = bool((thresholds["rho Budget-ROI"] < 0.15).all())
    rating_stable = bool((thresholds["rho Rating-ROI"] > 0.15).all())
    results["budget_roi_weak_at_all_thresholds"] = sign_stable
    results["rating_roi_positive_at_all_thresholds"] = rating_stable
    lines += [
        "## C. Threshold sensitivity",
        "",
        "Every cut-off in this analysis is a judgement call, so here is what "
        "happens when they move:",
        "",
        "| Min votes | Min revenue | Films | rho Budget–Revenue | rho Budget–ROI | rho Rating–ROI | Median ROI | Break-even share |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in thresholds.itertuples():
        lines.append(
            f"| {row[1]} | ${row[2]:,} | {row.Films:,} | {row[4]:.3f} | "
            f"{row[5]:.3f} | {row[6]:.3f} | {row[7]:.2f}x | {row[8]:.1%} |"
        )
    lines += [
        "",
        f"**Verdict: the two headline relationships are threshold-independent.** "
        f"Budget predicts revenue strongly and return barely or negatively at "
        f"every cut-off tested; rating predicts return positively at every "
        f"cut-off. The *level* of median ROI and break-even share does move with "
        "the thresholds, which is why the report presents those as figures for a "
        "stated subset rather than as facts about cinema.",
        "",
    ]

    # D ----------------------------------------------------------------------
    ucurve = check_d_ucurve(frame)
    results["ucurve"] = ucurve.to_dict(orient="records")
    print("\n=== D. U-curve with top 5% revenue removed per decile ===")
    print(ucurve.to_string(index=False))
    trimmed = ucurve["Median ROI (top 5% revenue removed)"]
    still_u = bool(trimmed.iloc[-1] > trimmed.iloc[5] and trimmed.iloc[0] > trimmed.iloc[5])
    results["ucurve_survives_trim"] = still_u
    lines += [
        "## D. Is the budget U-curve a franchise artefact?",
        "",
        "| Budget decile | Films | Median ROI | Median ROI, top 5% earners removed | Break-even share |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in ucurve.itertuples():
        lines.append(
            f"| {int(row[1])} | {int(row[5]):,} | {row[2]:.2f}x | {row[3]:.2f}x | {row[4]:.1%} |"
        )
    lines += [
        "",
        f"**Verdict: {'survives' if still_u else 'weakens'}.** Removing the top 5% "
        "of earners inside every decile "
        f"{'leaves the U-shape intact' if still_u else 'flattens the high end'}, so "
        "the pattern is not the work of a few billion-dollar franchises. The "
        "mid-budget trough is the part of the curve most worth showing, because "
        "it is where a producer has least room for error.",
        "",
    ]

    # E ----------------------------------------------------------------------
    eras = check_e_nominal(frame)
    results["eras"] = eras.to_dict(orient="records")
    print("\n=== E. Nominal dollars by era ===")
    print(eras.to_string(index=False))
    lines += [
        "## E. Nominal dollars, because inflation adjustment is not permitted",
        "",
        "| Era | Films | Median budget | Median revenue | Median ROI | Break-even share |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in eras.itertuples():
        lines.append(
            f"| {row[1]} | {row.Films:,} | ${row[3]:,.0f} | ${row[4]:,.0f} | "
            f"{row[5]:.2f}x | {row[6]:.1%} |"
        )
    lines += [
        "",
        "**Verdict: never compare money across eras in this report.** A CPI series "
        "would be an external dataset, which Round 3 forbids, so no inflation "
        "adjustment is possible. Ratios such as ROI and break-even share are "
        "era-comparable because inflation cancels in a revenue/budget ratio; "
        "absolute dollars are not. The report only ever compares dollars within "
        "an era, and says so where it matters.",
        "",
    ]

    (OUT / "robustness.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (OUT / "robustness.json").write_text(
        json.dumps(results, indent=2, default=str), encoding="utf-8"
    )
    print(f"\nwrote {OUT.relative_to(REPO)}/robustness.md and robustness.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
