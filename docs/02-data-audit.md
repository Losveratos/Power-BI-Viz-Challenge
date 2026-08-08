# 02 — Data audit

The prose companion to `analysis/out/audit_report.md` and
`analysis/out/robustness.md`. Those two files are generated; this one explains
what the generated numbers mean and what follows from them.

---

## 1. Why this document exists

Round 3 is scored in part on Responsible Data Use, which the brief expands into
appropriate interpretation of metrics, clear explanation of assumptions,
recognition of limitations, avoidance of misleading comparisons, and honest
communication of uncertainty (J-10 through J-15 in
`docs/01-challenge-brief.md`). In a normal analytics project a data audit is a
preliminary step: you do it, you fix what you can, you throw the notes away and
you present the findings. Here the audit is the subject matter. The shape of
the data — what it covers, what it silently omits, and which of its zeros are
really nulls — is a substantial part of what the report has to say. A finding
that survives an honest account of its own data is worth more in this round than
a larger finding presented without one.

Every number in this document is produced by the scripts in `analysis/` and can
be regenerated from the starter file:

| Script | What it produces |
|---|---|
| `analysis/01_extract_model.py` | Extracts the semantic model from the official starter `.pbix` into `work/extract/*.parquet`, and prints the file's SHA-256 so the audit is pinned to one snapshot. |
| `analysis/02_data_audit.py` | `analysis/out/audit_report.md`, `audit_summary.json`, `funnel.csv`, `budget_placeholders.csv`. Sections 2 to 6 below quote this output. |
| `analysis/03_metric_exploration.py` | `analysis/out/findings.json` and seven CSVs — the metric evidence the report's pages draw on. |
| `analysis/04_robustness.py` | `analysis/out/robustness.md` and `robustness.json`. Section 7 below quotes this output. |

No figure in this document was typed in by hand. Where a number appears here it
appears in one of those generated files as well, and the thresholds that produce
it are named constants at the top of the scripts. If a threshold changes, the
numbers change with it, and this document is wrong until it is updated — which
is the intended failure mode.

---

## 2. What the starter file already decided for us

The competition supplies a starter `.pbix`. Its `Movies` query begins:

```m
let
    Source = Source,
    #"Filtered Rows" = Table.SelectRows(Source, each [budget] > 0),
    ...
```

That single line is the most consequential decision in the whole project, and it
was made before any competitor opened the file. The upstream TMDB dataset holds
roughly 930,000 films, as stated by the brief. After `[budget] > 0` the model
contains 85,394 — 9.2% of the source. Roughly 844,606 films are gone before the
analysis starts.

This matters for a specific reason, and it is not simply that the sample is
smaller. The filter selects on a **financial disclosure variable**. A film is in
the starter file if and only if somebody entered a non-zero production budget for
it in TMDB. Budgets get entered for films that have distributors, press coverage,
trade reporting, and volunteers who care enough to look the figure up. They do
not get entered for the very large population of films that were made and then
quietly went nowhere. So the retained 9.2% is not a random ninth of world
cinema: it is systematically tilted towards films whose finances were public
enough for someone to record them, which correlates with commercial scale,
distribution, and being in a market that trade press covers.

Two consequences run through the rest of the report:

1. Every statement the report makes is a statement about films with disclosed
   budgets, not about films. The report never uses the phrase "all movies".
2. The bias is not correctable from inside the data. There is no variable in the
   starter file that measures disclosure propensity, and the round's rules forbid
   bringing in an external one (P-01 through P-05). It can only be described,
   which is what this document does.

The filter is not a defect of the starter file — an ROI analysis needs a budget.
It is simply a decision the report inherited rather than made, and the report
says so rather than presenting 85,394 films as if they were the population.

---

## 3. The inclusion funnel

On top of the inherited filter, this analysis applies five further cuts. Each
one is a judgement call, each one is stated, and each one is reversible in the
code by changing a constant.

| Step | Films | Dropped here | Share of source | Why |
|---|---:|---:|---:|---|
| Source dataset (TMDB, as described by the brief) | 930,000 | 0 | 100.0% | Approximate; stated by the challenge brief, not verifiable inside the starter file. |
| Starter file: Budget > 0 | 85,394 | 844,606 | 9.2% | Applied by the supplied Power Query, before competitors see the data. |
| Status = Released | 79,222 | 6,172 | 8.5% | Excludes planned/in-production titles. |
| Release Date present | 56,072 | 23,150 | 6.0% | A film with no date cannot be placed in time. |
| Budget >= $10,000 | 28,193 | 27,879 | 3.0% | Removes placeholder budgets such as the repeated value 100. |
| Revenue >= $10,000 | 10,219 | 17,974 | 1.1% | Revenue 0 means 'not reported', not 'earned nothing' — it cannot enter a ratio. |
| Vote Count >= 50 | 7,733 | 2,486 | 0.8% | A rating from a handful of voters is noise. |

Step by step:

**Status = Released** (6,172 dropped). The table contains titles that are
planned, in production, or post-production. A film that has not been released
cannot have box-office revenue, so including it would add rows whose revenue is
structurally zero and would drag every aggregate down for a reason that has
nothing to do with performance.

**Release Date present** (23,150 dropped). 30.6% of the starter file has no
release date. Without a date a film cannot be placed in an era, cannot be
assigned to a release month, and cannot be excluded from a cross-era comparison
that would otherwise be misleading. Since the report's structure is partly
chronological, an undated film has nowhere to go.

**Budget >= $10,000** (27,879 dropped). See section 4(c) and ADR-002: budgets
below this are dominated by data-entry defaults, not by genuinely
micro-budgeted films. 51,634 of the 85,394 starter rows (60.5%) carry a budget
under $10,000.

**Revenue >= $10,000** (17,974 dropped). Revenue is 0 for 67,436 starter rows.
A zero here means "nobody recorded a gross", not "the film earned nothing"; a
row like that cannot enter a revenue/budget ratio without inventing a fact. See
ADR-004.

**Vote Count >= 50** (2,486 dropped). A rating of 8.0 from three voters is not
evidence about audience reception. 50 is deliberately conservative, and check C
in section 7 shows the conclusions are unchanged anywhere between 0 and 500
votes.

**The headline: 7,733 films. 0.8% of the source dataset**, and 9.1% of the
starter file. That number is not buried in an appendix — it is stated on the
report's landing page, because a viewer who does not know it will over-read
everything else. Two smaller sanity notes belong with it: the analysable subset
is derived from the model's `Movie ID`, not from titles, because 5,436 titles in
the starter file are shared by more than one film and one title is shared by 40.

---

## 4. Four kinds of missing

"Missing data" is treated here as four distinct problems, because they need four
different responses and only the first of them is visible to a normal
completeness check.

### (a) Genuinely null

The value is absent and the absence is recorded as absence. Release Date is
missing for 26,166 films, 30.6% of the starter file. Poster Path is missing for
23,467 (27.5%) and Tagline for 45,130 (52.8%), which matters for presentation
rather than analysis. Title is missing for exactly one row.

This is the honest kind of missing. It is detectable, countable, and safe: any
tool will exclude it or complain about it.

### (b) Zero used as "unknown"

The column is populated, the value is a number, and the number is a lie of
convenience. This is the dangerous kind, because every aggregation will happily
consume it.

| Column | Rows equal to 0 | Share of 85,394 |
|---|---:|---:|
| Revenue | 67,436 | 79.0% |
| Vote Average | 56,028 | 65.6% |
| Vote Count | 55,958 | 65.5% |
| Runtime | 18,470 | 21.6% |

A Revenue of 0 does not mean a film sold no tickets. In a database assembled by
volunteers it overwhelmingly means nobody filled the field in. Treating those
67,436 zeros as earnings would put the median revenue of the starter file at
zero and would make every ROI figure meaningless. A Vote Average of 0 is the
same story: 56,028 films have no rating rather than the worst possible rating.
A Runtime of 0 is not a film of zero length.

The report's rule is that a zero in a measure that cannot legitimately be zero
is treated as unknown, and unknown rows are excluded from the metric they are
unknown for rather than counted as zero.

### (c) Placeholder values

The third kind is a value that is neither null nor zero and is still not a
measurement. Real production budgets are near-continuous: two unrelated films
almost never cost exactly the same amount to the dollar. So when thousands of
unrelated films share one budget figure, that figure is a data-entry default.

| Budget | Films | Share of 85,394 |
|---:|---:|---:|
| 100 | 3,531 | 4.13% |
| 1,000 | 3,107 | 3.64% |
| 500 | 2,619 | 3.07% |
| 5,000 | 2,286 | 2.68% |
| 10,000 | 2,165 | 2.54% |
| 2,000 | 1,932 | 2.26% |
| 10 | 1,887 | 2.21% |
| 200 | 1,868 | 2.19% |
| 50 | 1,863 | 2.18% |
| 1 | 1,731 | 2.03% |

3,531 films with a budget of exactly 100. 1,731 with a budget of exactly 1.
These are not micro-budget productions; they are what somebody typed to satisfy
a form that would not accept a blank. Note also that the starter file's own
`[budget] > 0` filter is what makes these visible: films whose budget was left
at 0 were already removed, so the remaining defaults are the non-zero ones.

The response is the $10,000 floor (ADR-002). It is a blunt instrument — it will
remove a handful of genuine micro-budget films along with the placeholders — and
the report prefers losing real rows to computing a 4,000x return on a budget of
1 dollar.

### (d) Structurally absent

The fourth kind is invisible: films that were never entered into TMDB at all.
Nothing in the data indicates them, no completeness check can count them, and no
threshold can recover them. The population is certainly large, and it is
certainly not random — it will be weighted towards films with no distributor, no
trade coverage, and no English-language audience.

This is the only one of the four kinds that cannot be quantified from the data,
and it is the reason the report describes its scope in terms of what the sample
contains rather than claiming to characterise cinema. The honest statement is
that the size and direction of this gap are unknown, and unknowable from inside
the round's rules.

---

## 5. Coverage, and who is missing

The 7,733 analysable films cover:

- **Language.** 85.1% are English-language by original language, then French
  3.2%, Hindi 2.3%, Spanish 1.5%, Japanese 1.2%, Italian 1.0%, Russian 1.0%,
  Korean 0.9%. This is not a dataset about world cinema. It is a dataset about
  mostly Anglophone commercial cinema with a thin sampling of everything else.
  Nigerian, Chinese, Egyptian and Turkish output — all large industries by volume
  — are effectively absent. Any statement the report made about "films" would in
  practice be a statement about English-language films, so it does not make one.
- **Era.** Release years run from 1915 to 2023, a 109-year span. 21.3% were
  released in 2015 or later and 9.4% before 1980, so the bulk of the sample sits
  in the 1980 to 2014 window. The long tail back to 1915 is thin enough that
  pre-1980 figures are reported with their film count attached (780 films) and
  never used to anchor a trend line.
- **Financial disclosure.** By construction, 100% have both a budget and a gross
  above $10,000. The population of films that disclosed neither is larger than
  the sample by two orders of magnitude.

The single sentence version, which the report uses: this is a study of 7,733
mostly English-language films that reported both a budget and a box-office
gross, released between 1915 and 2023.

---

## 6. Skew, and why medians

Film revenue is one of the most skewed quantities in commercial life, and the
subset shows it:

- Revenue: **mean $84,932,088 versus median $25,155,355**. The mean is 3.4 times
  the median.
- The **top 1% of films take 14.2%** of all revenue in the subset.
- The 90th percentile of revenue is $216,738,739 and the 99th is $874,875,406.
- ROI: **median 1.96x, mean 6.26x, maximum 4,144x**.
- 31.4% of the subset earned less than its production budget back in gross, and
  58.6% fall below the 2.5x gross break-even multiple described in ADR-005.

A mean of 6.26x return would be a wonderful headline and it is an artefact. It
is produced by a handful of extreme ratios — a film with a recorded budget just
above the floor and a substantial gross generates a four-figure multiple that
moves the average of thousands of rows. The mean revenue figure is only slightly
less misleading: it describes a film that does not exist, sitting above roughly
three quarters of the sample.

Means are therefore unusable here, and **every money figure in the report is a
median.** Where a mean appears at all it appears next to its median, as evidence
for why the median was chosen — the pattern used in `audit_report.md` and
reproduced on the report's methodology page. Rank-based statistics are used for
the same reason (ADR-008), and distributions are shown rather than summarised
wherever the page has room for them.

---

## 7. The robustness checks

`analysis/04_robustness.py` exists to try to break the findings before the
report publishes them. Each of the report's headline claims has an obvious
alternative explanation, and each alternative gets tested rather than
acknowledged in passing. There are five checks, A through E. Where a finding
survives, the report states it plainly. Where it only partly survives, the
report says so on the page that shows it, not in a footnote elsewhere.

### A. Survivorship bias in the low-budget tail

**The alternative explanation.** The data says cheap films return more: the
lowest budget decile has a median ROI of 4.02x against 2.48x for the highest.
But a cheap film that vanished without a trace has no revenue figure recorded,
so it never enters the analysis. If low-budget flops are missing and low-budget
successes are present, the measured return of cheap films is inflated by
selection, not earned.

**The result.** Revenue reporting completeness rises steeply with budget:

| Budget band | Films | Revenue reported | Reporting rate | Enters analysis |
|---|---:|---:|---:|---:|
| 10k–100k | 8,114 | 636 | 7.8% | 2.4% |
| 100k–1M | 6,054 | 1,092 | 18.0% | 13.9% |
| 1M–5M | 5,492 | 1,992 | 36.3% | 38.5% |
| 5M–20M | 4,547 | 2,991 | 65.8% | 75.5% |
| 20M–50M | 2,361 | 2,028 | 85.9% | 92.0% |
| 50M+ | 1,625 | 1,480 | 91.1% | 90.8% |

Films budgeted above $50M report revenue 91.1% of the time. Films budgeted
between $10,000 and $100,000 report it 7.8% of the time — 11.6 times less often.
For the cheapest band, only 2.4% of films clear every filter and reach the
analysis.

**Verdict: the finding is real but substantially overstated, and the low-budget
advantage is largely survivorship.** Of the 8,114 films in the cheapest band,
we see the outcomes of 636. Those 636 are not a sample of cheap films; they are
approximately the cheap films that worked, because working is what caused
someone to record the gross. The 4.02x median for the lowest decile is
therefore an **upper bound, not an expectation**, and a producer cannot plan
against it. The report shows this table on the same page as the low-budget
claim, and states the reporting rates in the annotation rather than only in the
methodology notes. What does survive is the weaker and still useful statement
that a large budget does not buy a large return: budget correlates with revenue
at rho 0.676 and with ROI at rho -0.105.

### B. Is the rating effect just budget or era in disguise?

**The alternative explanation.** Well-rated films show a higher return. Perhaps
that is not about being well rated at all. Older films are cheaper in nominal
dollars and rate higher on TMDB; cheap films show higher ratios. Either
confound could produce the whole effect.

**The result.** The comparison was re-run inside each budget decile and inside
each era, so neither can be doing the work. Median ROI, films rated 7.0 or
above versus the rest:

| Budget decile | Rated < 7.0 | Rated >= 7.0 | Uplift |
|---:|---:|---:|---:|
| 1 | 3.47x | 4.74x | 1.37x |
| 2 | 1.87x | 3.99x | 2.14x |
| 3 | 1.58x | 2.94x | 1.87x |
| 4 | 1.28x | 2.69x | 2.10x |
| 5 | 1.34x | 3.14x | 2.35x |
| 6 | 1.23x | 2.58x | 2.10x |
| 7 | 1.14x | 2.76x | 2.42x |
| 8 | 1.50x | 2.79x | 1.86x |
| 9 | 1.68x | 2.53x | 1.51x |
| 10 | 2.14x | 3.51x | 1.64x |

| Era | Rated < 7.0 | Rated >= 7.0 | Uplift |
|---|---:|---:|---:|
| pre-1980 | 3.76x | 4.47x | 1.19x |
| 1980–94 | 1.78x | 3.11x | 1.75x |
| 1995–2004 | 1.37x | 3.09x | 2.26x |
| 2005–14 | 1.58x | 3.21x | 2.03x |
| 2015+ | 1.24x | 2.78x | 2.24x |

**Verdict: survives.** The uplift is present in all ten budget deciles and all
five eras, with a median of 1.98x and a minimum of 1.37x. Being well rated is
not a proxy for being cheap or for being old.

One thing this check does **not** establish is direction. Ratings are collected
after release from people who chose to watch. A film that reached a large,
willing audience can be rated highly because it succeeded, rather than
succeeding because it was good. Nothing in a single cross-section of
post-release ratings can separate those. The report states the association,
quantifies it, and explicitly declines to claim causation.

### C. Threshold sensitivity

**The alternative explanation.** Every cut-off in section 3 is a judgement
call. A conclusion that exists only at one arbitrary threshold is not a
conclusion, it is an artefact of the analyst's choices.

**The result.** The vote-count floor was moved across 0, 10, 50, 100 and 500,
and the revenue floor across $1, $10,000 and $1,000,000 — fifteen combinations,
spanning subsets from 4,614 to 10,439 films. Across all fifteen:

- Budget–Revenue rank correlation stays strongly positive: 0.656 to 0.758.
- Budget–ROI stays at or below zero: -0.247 to -0.052.
- Rating–ROI stays positive: 0.265 to 0.340.
- Median ROI moves from 1.79x to 2.61x, and the break-even share from 38.7% to
  51.8%.

**Verdict: the two headline relationships are threshold-independent; the levels
are not.** The direction and rough strength of both relationships hold
everywhere tested, which is what the report claims. The median ROI and the
break-even share move materially with the thresholds, which is why the report
presents those two as figures for a stated subset — "41.4% of these 7,733 films"
— rather than as facts about cinema. The full sensitivity table is in
`analysis/out/robustness.md`.

### D. Is the budget U-curve a franchise artefact?

**The alternative explanation.** Return by budget decile is U-shaped: high at
the cheap end, a trough in the middle, rising again at the top. The rise at the
top could easily be a handful of billion-dollar franchises rather than a
property of large budgets.

**The result.** The top 5% of earners were removed from inside every decile and
the medians recomputed:

| Budget decile | Films | Median ROI | Median ROI, top 5% earners removed | Break-even share |
|---:|---:|---:|---:|---:|
| 1 | 774 | 4.02x | 3.69x | 61.5% |
| 2 | 807 | 2.72x | 2.43x | 51.9% |
| 3 | 840 | 1.84x | 1.68x | 41.2% |
| 4 | 684 | 1.69x | 1.55x | 36.1% |
| 5 | 840 | 1.76x | 1.59x | 38.8% |
| 6 | 725 | 1.40x | 1.34x | 33.8% |
| 7 | 879 | 1.41x | 1.26x | 31.2% |
| 8 | 711 | 1.66x | 1.57x | 35.3% |
| 9 | 726 | 1.81x | 1.74x | 34.6% |
| 10 | 747 | 2.48x | 2.33x | 49.1% |

**Verdict: survives.** Trimming the biggest hits lowers every decile slightly
and leaves the shape intact: 3.69x at the bottom, 1.26x in the trough at decile
7, 2.33x at the top. The U is not the work of a few franchises.

Read with check A, the two ends of the curve are not equally trustworthy. The
right-hand rise is measured on films that report revenue 91.1% of the time; the
left-hand peak is measured on films that report it 7.8% of the time. The most
defensible part of the curve is the **trough** — deciles 6 and 7, budgets around
$19M to $25M, median return 1.40x and 1.41x and only about a third breaking
even. That is a well-populated, well-reported region of the data, and it is
where a producer has least room for error.

### E. Nominal dollars, because inflation adjustment is not permitted

**The alternative explanation.** Any cross-era money comparison in this report
is partly just inflation. A 1970 budget and a 2020 budget are not the same
quantity, and a chart that puts them on one axis invites a false reading.

**The result.**

| Era | Films | Median budget | Median revenue | Median ROI | Break-even share |
|---|---:|---:|---:|---:|---:|
| pre-1980 | 780 | $2,489,500 | $10,000,000 | 4.03x | 66.5% |
| 1980–94 | 1,309 | $13,800,000 | $21,435,321 | 2.02x | 42.9% |
| 1995–2004 | 1,710 | $25,000,000 | $33,779,668 | 1.66x | 35.1% |
| 2005–14 | 2,537 | $18,000,000 | $29,523,237 | 1.84x | 39.0% |
| 2015+ | 1,397 | $19,000,000 | $28,000,000 | 1.68x | 38.0% |

**Verdict: never compare money across eras in this report.** A CPI series would
be an external dataset, which Round 3 forbids (P-01), so no inflation
adjustment is available. The median pre-1980 budget of $2,489,500 is not
comparable to the median 2015+ budget of $19,000,000 in any useful sense, and
the report never puts them side by side as a trend.

Ratios are a different matter. Inflation largely cancels in a revenue/budget
ratio, because numerator and denominator are denominated in the same year's
dollars. ROI and break-even share are therefore the only quantities the report
compares across eras, and the pre-1980 figures still carry their film count
(780) because that era is thinly sampled and, per check A, its surviving films
are the ones somebody thought worth recording fifty years later. See ADR-006.

---

## 8. What this report will not claim

The following claims are not supportable from this data, and the report does not
make them in any form — not in a headline, not in a chart title, not in an
annotation:

- **That a good rating causes higher revenue or return.** The association is
  strong and survives controls for budget and era (check B), but ratings are
  collected after release from self-selected viewers. Direction is not
  identifiable from this data. The report says "is associated with", not
  "drives".
- **Anything about films outside the analysable 0.8%.** 7,733 of roughly 930,000
  films clear every filter. Statements are scoped to films that disclosed a
  budget and a gross, and the report says so on the landing page rather than
  only in a methodology note.
- **That cheap films are a reliable way to make money.** Section 7A: films
  budgeted $10,000 to $100,000 report revenue 7.8% of the time. The low-budget
  return figure is an upper bound on an unrepresentative 636 films, not an
  expectation for the 8,114.
- **Any comparison of dollar amounts across eras.** No inflation adjustment is
  possible under the round's rules, so nominal dollars from 1970 and 2020 are
  never placed on a shared scale as a trend. Cross-era comparison is done with
  ratios only.
- **Profitability in the accounting sense.** The data contains a production
  budget and a gross revenue figure. It does not contain marketing and
  distribution spend, exhibitor splits, home video, streaming licences,
  television, merchandising, participations, or tax credits. "Break-even" in
  this report means a gross-to-budget multiple against a stated assumption
  (ADR-005), and the report calls it that. No film is described as profitable
  or unprofitable.
- **Anything about non-English cinema.** 85.1% of the subset is
  English-language. The remaining slices — French at 3.2%, Hindi at 2.3% and
  down — are too small and too obviously selected to support a claim about a
  national industry, and the report does not rank languages or countries by
  performance.
- **That the reported budget and revenue figures are accurate.** They are
  volunteer-entered values in a public database, with no audit trail and no
  currency normalisation guarantee. The placeholder clusters in section 4(c) are
  direct evidence of how the values were produced. The report treats them as
  the best available figures, not as accounts.
- **That any ranking of production companies reflects skill.** Company medians
  are reported with film counts and a 25-film minimum, and small-sample studio
  results are presented as description, not as a league table of competence.

The general rule the report follows: a claim is stated only if it survives the
robustness checks in section 7, and it is stated with the scope it actually
has — this subset, these years, these languages, this definition of success.
