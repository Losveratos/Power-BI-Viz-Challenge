# Agentic process log

This entry was produced by an AI agent (Claude Code) working from a short human
brief, in a single session, on a Linux machine with no Power BI Desktop. The
round's rules explicitly permit "AI tools to assist with design, accessibility,
and report development"; this document records exactly what the agent did and what
the human did, so the claim can be checked rather than taken on faith.

It is written to be usable as the source material for a write-up about the
process.

---

## Division of labour

**The human contributed, in total:**

1. The task: enter Round 3 with an agent-built submission, document the process,
   keep documentation in English, follow the rules, do not make me work by hand.
2. Four answers to a clarifying question block: supply the rules and dataset
   yourself / produce a PBIP + TMDL project / decide the story after auditing the
   data / dark editorial cinematic design.
3. The full text of the Round 3 blog post, pasted in after the agent reported that
   `community.fabric.microsoft.com` was blocked by the environment's egress proxy.
4. A pointer to `kagglehub` when the agent reported it could not reach Kaggle.

No data modelling, no DAX, no layout, no colour picking, no copywriting.

**The agent produced** every file in this repository: the analysis scripts, the
semantic model, the report definition, the theme, and all documentation.

---

## What happened, in order

### 1. Two dead ends, reported rather than worked around

The first two actions both failed. `community.fabric.microsoft.com` and
`powerbi.microsoft.com` are blocked by the environment's egress policy, so the
official rules page could not be read. Later, `api.kaggle.com` returned 403
through the same proxy, so the source CSV could not be downloaded.

Neither was routed around. Both were reported, and the human supplied the rules
text directly. The Kaggle block turned out not to matter, for a reason that made
the entry stronger — see step 3.

### 2. Reading the official starter file without Power BI

`raw.githubusercontent.com` *was* reachable, so the official 53 MB starter `.pbix`
was downloaded and opened as what it is: a ZIP file. Two things came out of it that
shaped everything after.

**The report layer is already PBIR.** The starter ships
`Report/definition/pages/<page>/visuals/<id>/visual.json` — one JSON file per
visual, written by Power BI Desktop itself. That is a complete, authoritative
grammar reference for authoring a report as text. Every schema version, property
shape and query-projection structure used in this entry was copied from files
Desktop wrote, rather than guessed from documentation.

**The data is inside the file.** The `DataModel` stream is a 50 MB compressed
VertiPaq model. The `pbixray` Python library parses that stream on any platform,
which meant the entire dataset — schema, M queries, DAX, relationships and all
85,394 rows — could be read on Linux with no Power BI Desktop involved.

### 3. The first real finding was in the starter file, not the data

`pbixray` recovered the starter file's own Power Query:

```m
#"Filtered Rows" = Table.SelectRows(Source, each [budget] > 0)
```

The supplied model keeps only films with a budget above zero: 85,394 rows out of
roughly 930,000. That filter is applied *before any competitor sees the data*, and
it is a filter on a financial variable, which means the sample every entrant works
from is systematically biased toward films that disclose money.

For a round scored on Responsible Data Use, that is not a footnote. It became the
spine of the report.

It also settled the Kaggle problem. Reading the data out of the starter file is
strictly *more* rule-compliant than re-downloading the CSV, because it guarantees
the analysis uses the exact snapshot every other competitor receives rather than a
possibly newer one.

### 4. Audit before story

The human's answer to the narrative question had been "decide after the data
check", so the audit came first, as a reproducible script rather than exploratory
poking. `analysis/02_data_audit.py` produced the inclusion funnel:

| | Films |
|---|---:|
| Published dataset (per the brief) | ~930,000 |
| Starter file, budget > 0 | 85,394 |
| Released | 79,222 |
| Has a release date | 56,072 |
| Budget at least $10,000 | 28,193 |
| Revenue at least $10,000 | 10,219 |
| At least 50 ratings | **7,733** |

**0.8% of the dataset can carry a financial claim.** Alongside it: 79% of rows
report a revenue of zero; the budget value `100` appears 3,531 times and `1`
appears 1,731 times, which no real production budget does; 85.1% of what survives
is English-language.

### 5. Then the analysis, then an attempt to break it

`03_metric_exploration.py` found the substance: budget correlates +0.68 with
revenue and **-0.11** with return; the top 100 by revenue and the top 100 by return
share **zero** films; return follows a U-curve across budget bands with its trough
at $15–30M; and return rises monotonically with audience rating while median budget
*falls*.

`04_robustness.py` then tried to destroy each of those findings — this is the step
that changes the character of the entry:

| Check | Result |
|---|---|
| **A. Is the low-budget advantage survivorship?** | **Largely yes.** Films budgeted $10k–100k report revenue only **7.8%** of the time; films above $50M report it **91.1%** of the time. Cheap flops were never recorded. The finding is kept but reframed as an upper bound, and the disclosure sits on the same page as the chart. |
| **B. Is the rating effect really budget or era?** | **No.** The uplift holds in all ten budget deciles and all five eras, median 2.1x, minimum 1.19x. |
| **C. Do the thresholds matter?** | **No.** Both headline correlations keep their sign and rough size across fifteen threshold combinations. |
| **D. Is the U-curve a few franchises?** | **No.** Removing the top 5% of earners within every band leaves it intact. |
| **E. Can dollars be compared across eras?** | **No, and it cannot be fixed.** A CPI series would be an external dataset, which the rules forbid. The report therefore compares dollars only within an era and uses ratios across eras. |

Check A is the one worth noting: an agent optimising for a flattering result would
have shipped "low-budget films return 5x" as the headline. The check found the
result was partly an artefact, and the report now says so in a red-ruled panel next
to the chart.

### 6. Colour was computed, not chosen

The palette was validated with a runnable checker (OKLab ΔE, Machado–Oliveira–
Fernandes CVD simulation) rather than eyeballed. The first candidate palette
**failed** three checks — lightness band, chroma floor, and a green/magenta pair at
ΔE 1.6 under deuteranopia. It took four iterations to reach a passing five-slot
palette on both the page and card surfaces.

One check ends in a permanent WARN: the aqua-green and red used for break-even
status sit at ΔE 6.5 under protanopia, inside the 6–8 floor band that is legal
*only* with secondary encoding. Rather than swap the semantics, the constraint was
accepted and written into the design system as an obligation — that pair never
carries meaning alone, and every use adds a direct label and a stated threshold.

### 7. The report was generated, not dragged

Both halves of the Power BI project are emitted by scripts:

- `05_build_semantic_model.py` → TMDL. The eight starter tables and seven
  relationships are transcribed unchanged; the additions are 14 derived columns, 24
  DAX measures, and five calculated tables. Every identifier is a deterministic
  UUID5, so a rebuild is byte-identical and a `git diff` shows real changes only.
- `06_build_report.py` → PBIR. 5 pages, 72 visuals, one layout grid.

The reason to generate rather than click is not speed. It is that
`container()` — the function every visual passes through — **takes alt text as a
required argument and raises on an empty one**. Accessibility stops being a review
step and becomes a build error.

### 8. A validator to stand in for the missing Desktop

The one thing the environment could not do was open the result. So
`07_validate_pbip.py` checks everything checkable from the files: JSON validity,
required project files, page count against the 5-page rule, core-visual count
against the 3-visual rule, Key Takeaway word count, alt text on every data-bound
visual, unique and positive tab orders, off-canvas and overlap detection, and —
most usefully — **every field reference resolved against the TMDL**, which is the
failure mode most likely to go unnoticed.

It also cross-checks the figures written into report prose against the analysis
output, so the report cannot drift away from its own evidence.

It found a real rule violation on first run: the Key Takeaway was **51 words**
against a 50-word limit, because a strict counter reads the em dash as a word. It
was rewritten to 46.

### 9. Four subagents wrote the documentation

Four subagents ran in parallel on separable writing tasks — the rules record and
compliance checklist, the data-audit and decision-log prose, the design system, and
the DAX and accessibility references — each given the analysis outputs and told to
read the numbers from the files rather than from the prompt.

Three of them corrected the orchestrating agent, which is the useful part:

- One found that a funnel step had been labelled "the largest single cut" when the
  budget floor removes more films (27,879 versus 17,974). The label was wrong and
  was fixed.
- One found that a stated 12-column grid did not divide the canvas as claimed
  (130px per column, not 118px) and recorded the discrepancy rather than silently
  changing a locked value.
- One measured the WCAG contrast ratios instead of asserting them and surfaced that
  the muted ink token clears 3:1 but not 4.5:1, which is now documented as the
  reason it is confined to non-load-bearing text.

---

## What an agent was good at here

**Reading a binary format as a specification.** Recovering the `budget > 0` filter
from a compressed VertiPaq stream, and lifting the PBIR grammar from the starter
file's own JSON, both mattered more than any downstream cleverness. The most
valuable finding in the entry came from reading the *provided file* rather than the
provided data.

**Adversarial self-checking, when it is a separate step.** The robustness script
is the difference between "low-budget films return 5x" and "low-budget films
appear to return 5x, and here is the 7.8%-versus-91.1% reason to distrust that".
That only happened because falsification was its own script with its own output,
rather than a paragraph of caution.

**Turning requirements into build errors.** Word count, alt text, page count,
tab order and field references are all mechanically checkable. Once checked by a
script, they cannot be forgotten under deadline.

**Consistency at volume.** 72 visuals on one grid, 24 measures with the same
filter pattern, and every number in the prose traceable to a generated file.

## What it was not good at

**It could not look at its own work.** No Power BI Desktop means the report has
never been rendered. The validator checks structure, not whether a label collides
with a bar or whether the dark theme reads well on a projector. That gap is real
and is listed as an open risk in `docs/08-build-and-submit.md`.

**It could not test the data pipeline end to end.** Kaggle was unreachable, so the
M queries have never run against the real CSV. They are transcribed from the
starter file's working queries, but the first refresh will be the first real test.

**It got things wrong, and needed checking.** The mislabelled funnel step, the
51-word takeaway, the wrong grid arithmetic, an incorrect genre-spread figure in a
draft — each was caught by a script or a reviewing subagent, not by the agent that
wrote it. The lesson is not that the agent was reliable; it is that the checks
were cheap enough to run on everything.

---

## Rules position

The round permits AI assistance for "design, accessibility, and report
development". Everything an AI did here falls inside that: analysis of the
provided data, model and measure authoring, layout, colour, copy, and
documentation. No external data was introduced, nothing was scraped, no rating or
revenue figure came from anywhere but the supplied dataset, and no source value
was altered. The one deliberate *refusal* to enhance is the absence of inflation
adjustment: a CPI series would have improved the analysis and would have broken
the rules, so the report explains what it cannot do instead.
