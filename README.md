# What Makes a Movie Successful?

An entry for the **Power BI Dataviz World Champs, Barcelona 2026 — Round 3
("Lights, Camera, Insight!")**, built end to end by an AI agent from a short human
brief.

> **Key Takeaway** — Bigger budgets buy bigger box office, not better payback. What
> consistently pays is being liked: films rated 7 or above return about twice as
> much per dollar, in every budget class and every era. One caveat — this data can
> measure only 0.8% of its films.

Round 3 is scored on **Responsible Data Use**, so this report's subject is as much
the data's limits as the answer. Of the roughly 930,000 films in the supplied
dataset, **7,733 — 0.8%** can carry a financial claim at all. That number is on the
landing page, not in an appendix.

---

## The findings

| | |
|---|---|
| **Budget predicts revenue, not return** | Spearman ρ = **+0.68** against gross revenue, **−0.11** against return on budget. Stable across fifteen threshold combinations. |
| **Success has four disjoint answers** | Rank the same 7,733 films four defensible ways: **zero** films appear in both the top 100 by box office and the top 100 by return. Box office and gross profit share 91, so gross profit is retired rather than presented twice. |
| **Return is a U-curve, and the middle is worst** | 4.98x under $1M, bottoming at **1.41x in the $15–30M band**, back to 2.70x above $100M. Survives removing the top 5% of earners in every band. |
| **Being liked pays, and costs less** | Films rated 7.0+ return a median **3.28x** against 1.59x for the rest, on a *lower* median budget ($12M vs $17M). Holds in all ten budget deciles and all five eras. |
| **The one finding that did not fully survive** | Cheap films look extraordinary partly because they are missing: films budgeted $10k–100k report revenue **7.8%** of the time, against **91.1%** above $50M. Disclosed beside the chart it undermines, not in a footnote. |

---

## Repository map

```
docs/     the paper trail — rules, audit, narrative, design, DAX, accessibility,
          compliance, decision log, process log, submission text
analysis/ seven scripts: extract the starter model, audit it, explore it, try to
          break the findings, then generate the Power BI project and validate it
src/pbip/ the deliverable — a Power BI Project (TMDL semantic model + PBIR report)
assets/   the validated report theme
```

### Documentation

| Document | What it covers |
|---|---|
| [`01-challenge-brief.md`](docs/01-challenge-brief.md) | The rules verbatim, with every requirement given a traceable ID |
| [`02-data-audit.md`](docs/02-data-audit.md) | The inclusion funnel, four kinds of missing, skew, and five robustness checks |
| [`03-narrative.md`](docs/03-narrative.md) | The story chosen, the metric defined, and why the alternatives lost |
| [`04-design-system.md`](docs/04-design-system.md) | Surfaces, palette, type scale, grid, mark rules — with validator evidence |
| [`05-dax-reference.md`](docs/05-dax-reference.md) | All 24 measures, 14 derived columns and 5 calculated tables |
| [`06-accessibility.md`](docs/06-accessibility.md) | Alt text, reading order, contrast measurements, and what still needs a human |
| [`07-compliance-checklist.md`](docs/07-compliance-checklist.md) | Every rule ID mapped to how this entry satisfies it |
| [`08-build-and-submit.md`](docs/08-build-and-submit.md) | **Start here to produce the .pbix** |
| [`09-decision-log.md`](docs/09-decision-log.md) | Ten ADRs covering every judgement call in the analysis |
| [`10-agentic-process-log.md`](docs/10-agentic-process-log.md) | What the agent did, what it got wrong, and what caught it |
| [`11-submission-description.md`](docs/11-submission-description.md) | Draft gallery post |

---

## Reproducing it

```bash
pip install -r analysis/requirements.txt

python analysis/01_extract_model.py        # read the official starter .pbix
python analysis/02_data_audit.py           # funnel, missingness, skew
python analysis/03_metric_exploration.py   # correlations, bands, genres, overlap
python analysis/04_robustness.py           # five adversarial checks
python analysis/05_build_semantic_model.py # TMDL
python analysis/06_build_report.py         # PBIR
python analysis/07_validate_pbip.py        # gate
```

Every identifier the generators emit is a deterministic UUID5, so a rebuild is
byte-identical: a `git diff` shows a real change or nothing.

`07_validate_pbip.py` is the substitute for a Power BI Desktop that this build
environment does not have. It enforces the 5-page limit, the 3-core-visual minimum,
the 50-word Key Takeaway, alt text on every data-bound visual, unique and positive
tab orders, off-canvas and overlap detection, and — most usefully — that **every
field reference resolves against the TMDL model**. It also cross-checks the figures
quoted in the report's own prose against the generated analysis output, so the
report cannot drift from its evidence.

```
PASSED — 13 checks satisfied, 0 warnings
```

## Turning this into a .pbix

The report is authored as a Power BI Project because the build environment runs
Linux with no Power BI Desktop. One step therefore remains for a human on Windows:
open `src/pbip/MovieSuccess.pbip`, point the `CsvPath` parameter at your copy of
`TMDB_movie_dataset_v11.csv`, refresh, walk the accessibility list, and save as
`.pbix`. Full instructions and the honest list of open risks are in
[`08-build-and-submit.md`](docs/08-build-and-submit.md).

## Rules position

No external datasets, no API joins, no scraping, no source values altered. The
analysis reads the data out of the **official starter `.pbix`** rather than
re-downloading the CSV, which guarantees the same snapshot every competitor
receives. AI assistance was used for design, accessibility and report development,
which Round 3 explicitly permits; the full account is in the process log.

One deliberate refusal: **no inflation adjustment**. A CPI series would have
improved the analysis and would have been an external dataset, so the report
compares dollars only within an era and uses ratios across them.

## Attribution

Movie data sourced from [TMDB and distributed via Kaggle](https://www.kaggle.com/datasets/asaniczka/tmdb-movies-dataset-2023-930k-movies)
under the Open Data Commons Attribution License (ODC-By 1.0). The official starter
file comes from the [contest repository](https://github.com/shannonlindsay/FabricCommunityContests).
No raw data is committed here; `work/` is gitignored and rebuilt by script 01.
