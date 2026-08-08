# 07 — Compliance checklist

Every ID defined in [01 — Challenge brief](01-challenge-brief.md) is listed here
exactly once, with the mechanism by which this entry satisfies it and the
evidence a reviewer can inspect.

Status vocabulary:

| Status | Meaning |
|---|---|
| MET | Satisfaction is already structural. It follows from how the analysis and the report are built, and no further action changes it. |
| PENDING | Can only be confirmed once the report is opened in Power BI Desktop and saved as .pbix, or once the entry is actually submitted. Design intent exists; verification does not. |

The entry is currently authored as a Power BI Project (PBIP) under `src/pbip/`.
Anything that depends on the compiled artefact — page count, alt text, contrast,
visual inventory, file format — is therefore PENDING by construction, not
because it has been neglected. See "Open risks" at the end.

Report page numbering used throughout:

| Page | Title |
|---|---|
| 1 | The Answer |
| 2 | Success Has Four Answers |
| 3 | What Money Buys |
| 4 | What Actually Pays |
| 5 | What We Cannot Know |

---

## 1. Hard rules

| ID | Requirement (short) | How this entry satisfies it | Status | Evidence |
|---|---|---|---|---|
| R-01 | Submit inside the July 28 – August 9 window | The build is complete ahead of the close date; the remaining step is the gallery submission itself, which has not been made yet. | PENDING | Submission receipt in the Contests gallery, once filed. |
| R-02 | Use Power BI to answer "What makes a movie successful?" | The report is organised as an answer, not a browse. Page 1 states the answer in one sentence; pages 2 to 4 build the case; page 5 bounds it. | MET | Page 1 (The Answer); `analysis/out/findings.json` |
| R-03 | A data story, not a dashboard | The five pages form a single argument with a fixed reading order — definition, then what money buys, then what actually pays, then what cannot be known. There is no page whose purpose is free-form exploration. | MET | Page sequence 1–5; `docs/01-challenge-brief.md` §3.1 |
| R-04 | Visible Key Takeaway on the landing page | Page 1 carries the Key Takeaway as a headline text element, above the fold, not in a tooltip or a collapsed panel. | MET | Page 1 |
| R-05 | Key Takeaway 50 words or fewer | The statement is 48 words. | MET | Page 1 text element; word count recorded at 48 |
| R-06 | Key Takeaway written for a general audience | Written in plain language: no metric names, no thresholds, no jargon such as ROI or median. A reader who has never opened Power BI can read it as a sentence about films. | MET | Page 1 |
| R-07 | Key Takeaway summarizes the most important insight | It states the single headline conclusion of the analysis rather than describing the report's contents or listing its pages. | MET | Page 1; `analysis/out/findings.json` |
| R-08 | Built in Power BI Desktop | The project is authored as PBIP and must be opened in Power BI Desktop and saved to .pbix before submission. Until that pass is done, this is unverified. | PENDING | `src/pbip/` |
| R-09 | A single .pbix file | The PBIP compiles to exactly one .pbix. No supplementary workbook, dataflow or external model is part of the entry. | PENDING | `src/pbip/`; saved .pbix after the Desktop pass |
| R-10 | No more than 5 pages | Five visible pages by design, listed above. Any tooltip pages must be confirmed hidden in Desktop so they do not count toward the limit. | PENDING | Page list in `src/pbip/`; visual confirmation in Desktop |
| R-11 | Use the provided dataset | Data comes from the official Round 3 starter .pbix only. `analysis/01_extract_model.py` reads the semantic model straight out of the starter file, so the analysis works from the same rows every competitor receives. The Kaggle TMDB dataset is the documented upstream provenance of that file; no third source is read anywhere in the pipeline. | MET | `analysis/01_extract_model.py`; `work/extract/*.parquet`; `docs/01-challenge-brief.md` §5 |
| R-12 | At least three core Power BI visuals | The charts carrying the argument are core Power BI visual types rather than custom ones. The exact inventory must be enumerated in Desktop to prove the minimum of three distinct core visuals is met. | PENDING | Visual inventory pass in Desktop |
| R-13 | Clear labels and alt text | Every visual needs alt text written against what the visual claims, not what it plots. Titles are written as claims so the label and the alt text say the same thing. Not yet verifiable per visual. | PENDING | Per-visual alt text audit in Desktop |
| R-14 | Strong contrast | The report uses a single shared theme in `assets/theme/` so colour decisions are made once rather than per visual. Measured contrast ratios still need checking against the rendered pages, including text over any poster imagery. | PENDING | `assets/theme/`; contrast measurement pass in Desktop |
| R-15 | Intentional layout and reading order | Each page has a deliberate single reading path, and tab order must be set explicitly per page so keyboard and screen-reader traversal follows that path rather than the object creation order. | PENDING | Tab order settings per page in Desktop |
| R-16 | Submit via the Contests gallery | Submission to be filed through "Submit to contest" in the Contests gallery. | PENDING | Submission receipt |
| R-17 | Submission includes an image | A cover image of page 1 to be attached at submission time. | PENDING | Submission record |
| R-18 | Submission includes a description | A description to be attached at submission time, drawn from the Key Takeaway plus a short statement of the success definitions used. | PENDING | Submission record |
| R-19 | Submission includes the .pbix or a Publish to Web URL | The saved .pbix from the Desktop pass will be attached. | PENDING | Submission record |
| R-20 | Tagged "World Champs BCN" | Tag to be applied at submission time, spelled exactly as in the brief. | PENDING | Submission record |

---

## 2. Judged criteria

| ID | Requirement (short) | How this entry satisfies it | Status | Evidence |
|---|---|---|---|---|
| J-01 | Define success clearly | Page 2 sets out four separate definitions of success and shows how little their top lists overlap, so the report names which definition it argues from instead of leaving "successful" ambient. | MET | Page 2; `analysis/out/definition_overlap.csv` |
| J-02 | Support conclusions with evidence | Every number on the report traces to a script in `analysis/`, and the outputs are committed. The analysis is reproducible end to end from the starter file. | MET | `analysis/01_extract_model.py` … `analysis/04_robustness.py`; `analysis/out/` |
| J-03 | Acknowledge tradeoffs and limitations | Page 5 exists solely for what the data cannot answer, and each headline claim on pages 3 and 4 carries the specific limitation that bounds it rather than deferring all caveats to the end. | MET | Page 5; `analysis/out/robustness.md` |
| J-04 | Communicate findings honestly and responsibly | Claims are stated at the strength the evidence supports. Where a relationship survives testing it is called an association, not a cause; where a finding is an upper bound it is labelled as one. | MET | `analysis/out/robustness.md` §A, §B |
| J-05 | Insightfulness | The report's central finding is a distinction rather than a ranking: budget predicts revenue strongly but return barely or negatively, so the question "what makes a film successful" has different answers depending on which success is meant. | MET | Pages 3 and 4; `analysis/out/correlations.csv` |
| J-06 | Visual effectiveness | Chart forms are chosen per claim and share one theme. Whether the rendered pages read cleanly at presentation size still needs eyes on the compiled report. | PENDING | `assets/theme/`; visual review in Desktop |
| J-07 | Storytelling and communication | The five pages are a linear argument, each titled as the claim it makes. Page titles read as sentences, so the page list alone conveys the story. | MET | Page titles 1–5 |
| J-08 | Creativity and innovation | The structural choice is to make the data's weakness the story: an inclusion funnel and a survivorship check are load-bearing narrative pages, not appendices. | MET | Pages 2 and 5; `analysis/out/funnel.csv` |
| J-09 | Accessibility (significant portion of score) | Approached as a build requirement rather than a finishing task: one shared theme, claim-style titles, explicit reading order. All of it needs measurement on the compiled report. | PENDING | See R-13, R-14, R-15 |
| J-10 | Responsible data use | Responsible data use is the spine of the report rather than a disclaimer. Page 2 shows that only 7,733 of roughly 930,000 films (0.8%) can be measured at all; page 5 quantifies the biases that remain in those 7,733. | MET | `analysis/out/audit_report.md`; `analysis/out/robustness.md` |
| J-11 | Appropriate interpretation of metrics | Zero revenue is treated as "not reported" rather than "earned nothing", so such rows are excluded from ratios instead of dragging them to zero. 79% of starter-file rows report zero revenue (67,436 of 85,394), which is why this distinction determines the whole analysis. | MET | `analysis/out/audit_report.md` (column completeness); `analysis/02_data_audit.py` |
| J-12 | Clear explanation of assumptions | Every filter in the inclusion funnel is shown with the reason it exists, and the thresholds are stated on the report rather than buried in the model. | MET | `analysis/out/funnel.csv`; `analysis/out/audit_report.md` |
| J-13 | Recognition of limitations | Named and quantified: a 0.8% measurable subset, placeholder budgets (the value 100 appears 3,531 times, 4.1% of rows), 79% zero revenue, an 85% English-language skew, and survivorship bias in the low-budget tail. | MET | `analysis/out/budget_placeholders.csv`; `analysis/out/audit_report.md`; `analysis/out/robustness.md` §A |
| J-14 | Avoidance of misleading comparisons | Money is never compared across eras, because inflation adjustment is impossible without an external CPI series. Ratios are used for cross-era comparison since inflation cancels in a revenue/budget ratio; absolute dollars are only compared inside one era. | MET | `analysis/out/robustness.md` §E |
| J-15 | Honest communication of uncertainty | Findings are stress-tested and the verdicts are reported as found, including the one that does not fully hold: the low-budget return advantage is real but overstated, because films in the 50M+ budget band report revenue 11.6 times more often than films budgeted at 10k–100k. | MET | `analysis/out/robustness.md` §A–§D |
| J-16 | Analysis outranks polish | The build order put the data audit and robustness work before any page design, and the conclusion on page 1 is the output of that work rather than a headline chosen first and supported afterwards. | MET | `analysis/02_data_audit.py`; `analysis/04_robustness.py` |

---

## 3. Prohibitions

| ID | Requirement (short) | How this entry satisfies it | Status | Evidence |
|---|---|---|---|---|
| P-01 | No external datasets | The only data input is the official starter .pbix. Notably, the era analysis deliberately does not inflation-adjust money, because a CPI series would be an external dataset — the report loses comparability rather than break this rule. | MET | `analysis/01_extract_model.py`; `analysis/out/robustness.md` §E |
| P-02 | No joins to IMDb, Wikipedia, Rotten Tomatoes, Box Office Mojo, TMDB APIs or any outside source | No API call, no join, no lookup against any outside source anywhere in the pipeline. The scripts read local Parquet extracted from the starter file. | MET | `analysis/*.py`; `work/extract/*.parquet` |
| P-03 | No additional ratings, revenue, reviews, awards or metadata | Every field used — budget, revenue, vote average, vote count, release date, runtime, original language, genre, production company — comes from the starter model. No awards, reviews or critic scores appear anywhere, because none exist in the file. | MET | `work/extract/Movies.parquet` and the four dimension/bridge extracts |
| P-04 | No web-scraped data | Nothing is scraped. The only network access in the pipeline is the documented download of the official starter file itself. | MET | `analysis/01_extract_model.py` |
| P-05 | No information that materially changes or enriches the dataset | All derived objects are functions of supplied columns: filters, ratios, deciles, bands and eras. No fact enters the model that was not already in the starter file. | MET | `analysis/02_data_audit.py`; `analysis/03_metric_exploration.py` |
| P-06 | Enhance presentation, not data | The enhancements are presentational: a theme, layout, narrative titles and derived groupings. The measurable universe of the report is exactly the starter file's, reduced by stated filters and never extended. | MET | `assets/theme/`; `analysis/out/funnel.csv` |

---

## 4. Permissions exercised

Permissions carry no obligation, so Status here records whether the entry uses
the latitude, not whether it complies.

| ID | Permission (short) | How this entry uses it | Status | Evidence |
|---|---|---|---|---|
| A-01 | Clean and transform the provided data | Used. Rows are filtered to a measurable subset (released, dated, budget and revenue above placeholder level, at least 50 votes) with each step recorded. | Exercised | `analysis/out/funnel.csv` |
| A-02 | Create calculations and measures | Used. Return, break-even share and rating bands are computed measures over supplied columns. | Exercised | `analysis/03_metric_exploration.py` |
| A-03 | Build additional tables derived from the supplied dataset | Used. Budget deciles, release eras, rating bands and genre/company aggregates are all derived from supplied columns. | Exercised | `analysis/out/budget_deciles.csv`; `analysis/out/rating_bands.csv`; `analysis/out/genre_performance.csv` |
| A-04 | Use custom visuals | Not relied upon. The design favours core visuals so alt-text and reading-order behaviour is predictable. If a custom visual is added during the Desktop pass, R-12 and R-13 must be re-checked. | Not exercised | Visual inventory pass in Desktop |
| A-05 | Add images, logos, posters and other visual assets | Used for presentation only, styled through the shared theme. | PENDING | `assets/theme/` |
| A-06 | Use posters or artwork linked from the provided dataset | Poster imagery, where used, comes from the `Poster Path` values already in the starter model and no other source. Note that 27.5% of rows have no poster path, so any poster-dependent element needs a defined empty state. | PENDING | `analysis/out/audit_report.md` (column completeness) |
| A-07 | Use AI tools for design, accessibility and report development | Used, for analysis scripting, documentation and report development, within the allowance the brief grants explicitly. | Exercised | This repository |

---

## 5. Open risks

Listed as things that could still fail verification, not as things believed to be
fine.

1. **PBIP to .pbix conversion is unverified.** The report is authored as a Power
   BI Project and must be opened in Power BI Desktop and saved as .pbix. Until
   that pass is done, page count (R-10), alt text (R-13), contrast (R-14) and
   reading order (R-15) have no visual confirmation, and R-08 and R-09 cannot be
   claimed at all. This single pass gates the largest block of PENDING rows in
   this document.
2. **Page count could break silently.** R-10 allows hidden tooltip pages but
   counts visible ones. A tooltip page left visible after the Desktop pass moves
   the entry from five pages to six and fails a hard rule mechanically.
3. **Alt text quality, not just presence.** R-13 is satisfiable in letter by
   auto-generated alt text and still lose points under J-09. Each visual needs
   alt text stating the claim, which is a manual pass with no shortcut.
4. **Contrast over imagery is the weak point.** Theme colours can pass in
   isolation and fail where text sits over poster artwork or a dark panel.
   Contrast has to be measured on the rendered page, not on the palette.
5. **Poster images render from an outside host.** A-06 permits images linked
   directly from the provided dataset, and poster paths are in the dataset, but
   the images themselves resolve from a TMDB image host at view time. This is
   allowed on a plain reading of A-06 and adds no data to the model, yet a strict
   reviewer could read it against P-02. If that reading is a concern, the entry
   should either drop posters or state on the page that only the paths supplied
   in the dataset are used.
6. **The 930,000 figure is attributed, not verified.** It comes from the brief
   and the Kaggle description and cannot be checked inside the starter file,
   whose Power Query already filters to budget greater than zero. Wherever the
   0.8% coverage claim appears, the denominator must be presented as stated by
   the brief rather than as a measured fact.
7. **Key Takeaway word count is fragile.** It stands at 48 words, two under the
   R-05 limit. Any late copy edit must be re-counted, since the margin does not
   absorb an added clause.
8. **Threshold choices remain a judgement call.** The 50-vote and $10,000 cuts
   are defensible and their sensitivity is documented, but a judge may disagree
   with them. The mitigation is that the sensitivity table is on the report, so
   the choice is visible and arguable rather than hidden.
9. **Submission mechanics are all unfiled.** R-01 and R-16 to R-20 depend on
   actions in the Contests gallery — image, description, file or Publish to Web
   URL, and the exact tag "World Champs BCN". None can be evidenced before the
   entry is filed, and the window closes August 9.
