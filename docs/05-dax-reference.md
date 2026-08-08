# 05 — DAX and model reference

A complete reference for everything this entry adds to the semantic model: the
derived columns on `Movies`, the 24 measures in `_Measures`, the `Funnel`
calculated table and the four leaderboard calculated tables.

The authoritative source for every expression quoted here is the TMDL under
`src/pbip/MovieSuccess.SemanticModel/definition/`. Where this document and the
TMDL disagree, the TMDL is what refreshes.

---

## 1. What was inherited and what was added

The official Round 3 starter model is transcribed into TMDL unchanged. That
covers:

- **Eight tables** — `Movies`, `Genres`, `Genre Bridge`, `Keyword`,
  `Keyword Bridge`, `Production Company`, `Production Company Bridge`, `Date`.
- **Seven relationships** — three many-to-many links from `Movies`[Movie ID] to
  the three bridge tables, three one-to-many links from each bridge to its
  dimension, and `Movies`[Release Date] to `Date`[Date].
- **The shared queries** — `Source` (the CSV load, promoted headers and the
  24-column type transform) and `Schema` (the column-name and sample-row table),
  both in query group `00 Source`.

There is one exception. The starter file hardcodes the path to
`TMDB_movie_dataset_v11.csv`; here that literal is replaced by a parameter
expression, `CsvPath`, declared with `IsParameterQuery=true` and
`IsParameterQueryRequired=true`. The official contest instructions ask
competitors to make exactly this edit before refreshing, and making it a
parameter means the edit happens in one visible place rather than inside a query
step.

Everything below is added by this entry:

| Addition | Where |
|---|---|
| 14 derived columns on `Movies` | in the `Movies` M partition, after the `#"Removed Columns"` step |
| `_Measures` — 24 measures on an empty calculated table | `tables/_Measures.tmdl` |
| `Funnel` — calculated table, 7 rows | `tables/Funnel.tmdl` |
| `Top By Box Office`, `Top By Gross Profit`, `Top By Return`, `Top By Acclaim` | four leaderboard calculated tables |

No source value is altered anywhere. Every addition is a new column, a new
measure or a new table.

---

## 2. Derived columns on Movies

All fourteen are added by `Table.AddColumn` steps in the `Movies` partition,
after the transcribed starter steps end at `#"Removed Columns"`. The three
`… Sort` columns are marked `isHidden` and exist only to give their paired text
column a defined order via `sortByColumn`.

| Column | Type | Definition | Why it exists |
|---|---|---|---|
| `Is Measurable` | boolean | `[Status] = "Released"` and `[Release Date] <> null` and `[Budget] >= 10000` and `[Revenue] >= 10000` and `[Vote Count] >= 50` | The single gate every financial figure in the report passes through. See the note below. |
| `ROI` | double | `[Revenue] / [Budget]` when `Is Measurable`, otherwise `null` | Return on production budget. Null rather than zero when it cannot be formed: a film with unreported revenue has an unknown return, not a zero one. A zero would be averaged in and would drag every median down. |
| `Gross Profit` | int64 | `[Revenue] - [Budget]` when `Is Measurable`, otherwise `null` | Needed to test whether gross profit is a distinct definition of success or a restatement of revenue. Page 2 shows it is the latter. |
| `Breaks Even` | boolean | `[ROI] >= 2.5` when `Is Measurable`, otherwise `null` | A per-film flag for the 2.5x rule of thumb, so break-even status can be read off a row and not only computed in aggregate. |
| `Release Year` | int64 | `Date.Year([Release Date])`, null when the date is null | Era assignment and cross-era ratio comparisons. |
| `Release Month` | int64 | `Date.Month([Release Date])`, null when the date is null | Release-timing analysis; also the sort key for the month name. |
| `Release Month Name` | string | `Date.MonthName([Release Date])`, null when the date is null | A readable category label for release timing. |
| `Budget Band` | string | Fixed dollar bands: `Under $1M`, `$1M to $5M`, `$5M to $15M`, `$15M to $30M`, `$30M to $60M`, `$60M to $100M`, `$100M and above`. Null when not measurable. | Fixed bands rather than deciles: a reader understands "$15M to $30M", and a decile boundary shifts every time the filter context changes, so the same band would mean different things on two pages. |
| `Budget Band Sort` | int64 (hidden) | 1–7 in band order, null when the band is null | Gives `Budget Band` a monotonic axis order instead of an alphabetical one. |
| `Rating Band` | string | `Below 5.0`, `5.0 to 6.0`, `6.0 to 6.5`, `6.5 to 7.0`, `7.0 to 7.5`, `7.5 and above`. Null when not measurable. | The rating scale is compressed in its middle, so the bands narrow where the films are, rather than being equal-width. |
| `Rating Band Sort` | int64 (hidden) | 1–6 in band order, null when the band is null | Sort order for `Rating Band`. |
| `Era` | string | `Before 1980`, `1980 to 1994`, `1995 to 2004`, `2005 to 2014`, `2015 onward`, from `Release Year`. Null when the year is null. | Eras exist so that nominal dollars are never compared across them. No inflation series is permitted in this round, so the era boundary is the substitute control. See `docs/09-decision-log.md` ADR-006. |
| `Era Sort` | int64 (hidden) | 1–5 in era order, null when the era is null | Sort order for `Era`. |
| `Budget Looks Like A Placeholder` | boolean | `[Budget] < 10000` | Computed for **all** rows, including non-measurable ones, because the report has to count the placeholder budgets in order to name them on page 5. |

### Why `Is Measurable` is a column

`Is Measurable` could have been a report-level filter. It is a column instead,
for two reasons.

It is visible in the model. Anyone opening the semantic model sees the gate, its
five conditions and its thresholds, without having to inspect a filter pane on
five pages.

It cannot be forgotten. A report-level filter is a per-file setting that a later
edit can drop; a column referenced inside every measure cannot be lost by
adding a page. Every financial measure in `_Measures` filters on it explicitly,
so a new visual built on those measures inherits the gate whether or not its
author knows the gate exists.

The five conditions and their thresholds:

1. `Status = "Released"` — an unreleased film has no audience and no box office.
2. `Release Date` is not null — without a date a film cannot be placed in an era.
3. `Budget >= 10000` — removes placeholder budgets, where thousands of unrelated
   films share values such as 1, 100 and 1,000.
4. `Revenue >= 10000` — a revenue of 0 means "not reported", not "earned
   nothing", and an unknown cannot go into a ratio.
5. `Vote Count >= 50` — an average built from a handful of votes is noise
   dressed as a score.

Both $10,000 thresholds and the 50-vote floor are chosen judgements, not values
derived from the data. They are stated here, on the funnel on page 1 and in the
`Funnel` table's own `Why` column so that a reader can disagree with them
specifically.

---

## 3. Measures

All 24 measures live on `_Measures`, a calculated table whose partition is
`{ BLANK() }` with a single hidden `Value` column — the standard measures-only
table pattern.

### Scope and coverage

#### Films Measured

```dax
CALCULATE ( COUNTROWS ( 'Movies' ), 'Movies'[Is Measurable] = TRUE() )
```

Format string: `#,0`

The count of films inside the current filter context that clear every gate:
released, dated, budget and revenue both at least $10,000, and at least 50
ratings. This is the denominator behind every rate in the report and the input
to the reliability gate. It must not be read as "films of this kind that
exist" — it is films of this kind that this dataset can measure, which on page 1
is shown to be a very different quantity.

#### Films In Starter File

```dax
COUNTROWS ( ALL ( 'Movies' ) )
```

Format string: `#,0`

Every row the supplied starter file loads, after the starter query's own
`[budget] > 0` filter. Because of the `ALL`, it does not respond to any slicer
or page filter. It is the honest denominator for the data-quality shares, and it
must not be used as a population count for cinema: the `budget > 0` filter was
applied to the data before any competitor saw it, and it is a filter on a
financial field, so what remains is already biased toward films that disclose
money.

#### Films Measured Overall

```dax
CALCULATE ( COUNTROWS ( 'Movies' ), ALL ( 'Movies' ), 'Movies'[Is Measurable] = TRUE() )
```

Format string: `#,0`

`Films Measured` with all report filters removed. It exists for scope
statements — the KPI card on page 1 and the footer attribution — which must
state the same figure no matter what is selected. Using it inside a
per-category visual would be a bug: every category would show the same number.

#### Source Films As Published

```dax
930000
```

Format string: `#,0`

A hardcoded constant. It is the film count the challenge brief attributes to the
published source dataset, and this model cannot verify it: the starter query
filters on `budget > 0` before the data reaches the model, so the pre-filter row
count is not observable here. It is labelled as a stated figure wherever it
appears, and it must not be treated as a measurement.

#### Share Of Source Measurable

```dax
DIVIDE ( [Films Measured Overall], [Source Films As Published] )
```

Format string: `0.0%`

How much of the published dataset survives to the point where a financial
question can be asked of it. The numerator is measured and the denominator is
the stated 930,000, so this is a ratio of one measured quantity to one asserted
one, and it inherits that assumption exactly.

### Central tendency

Every measure in this group is a median under the `Is Measurable` gate. The
median is not a stylistic preference: the return distribution has a long enough
right tail that a mean describes nothing that happens to a typical film.

#### Median Return

```dax
CALCULATE ( MEDIAN ( 'Movies'[ROI] ), 'Movies'[Is Measurable] = TRUE() )
```

Format string: `0.00\x`

Median revenue divided by production budget, within the current filter context.
This is the report's chosen definition of success. It is a **gross** multiple:
it must not be read as profit, because the dataset carries no marketing spend,
no exhibitor split and no home-video or streaming revenue. It is also
ungated — on a category axis with thin categories, use
`Median Return (reliable)` instead.

#### Median Budget

```dax
CALCULATE ( MEDIAN ( 'Movies'[Budget] ), 'Movies'[Is Measurable] = TRUE() )
```

Format string: `\$#,0`

Median production budget in nominal dollars. Never compare it across eras: no
inflation adjustment is applied anywhere in this model, so a 1975 dollar and a
2023 dollar are treated as the same unit. Within one era, or within a rating
band as on page 4, the comparison is sound.

#### Median Revenue

```dax
CALCULATE ( MEDIAN ( 'Movies'[Revenue] ), 'Movies'[Is Measurable] = TRUE() )
```

Format string: `\$#,0`

Median reported gross revenue in nominal dollars. The same era caveat applies.
It is reported revenue, not receipts: films whose revenue was never recorded
are excluded by the gate rather than counted as zero.

#### Median Rating

```dax
CALCULATE ( MEDIAN ( 'Movies'[Vote Average] ), 'Movies'[Is Measurable] = TRUE() )
```

Format string: `0.00`

Median audience rating out of 10, among films with at least 50 votes. It is a
post-release audience score collected from people who chose to watch the film,
so it must not be treated as an independent measure of quality.

### Break-even

#### Break-even Rate

```dax
VAR Pool = CALCULATETABLE ( 'Movies', 'Movies'[Is Measurable] = TRUE() )
VAR Cleared = FILTER ( Pool, 'Movies'[ROI] >= 2.5 )
RETURN
    DIVIDE ( COUNTROWS ( Cleared ), COUNTROWS ( Pool ) )
```

Format string: `0.0%`

Share of measurable films whose gross revenue reached at least 2.5 times their
production budget. **The 2.5 multiple is hardcoded** and is an industry rule of
thumb, not a figure this data derives or validates: it stands in for the
distributor and exhibitor share plus print-and-advertising spend, none of which
the dataset contains. Every visual that uses this measure states the threshold
in its subtitle for that reason. It must not be described as a profitability
rate.

#### Recovered Budget Rate

```dax
VAR Pool = CALCULATETABLE ( 'Movies', 'Movies'[Is Measurable] = TRUE() )
VAR Cleared = FILTER ( Pool, 'Movies'[ROI] >= 1 )
RETURN
    DIVIDE ( COUNTROWS ( Cleared ), COUNTROWS ( Pool ) )
```

Format string: `0.0%`

Share of measurable films whose gross revenue merely exceeded their production
budget. The gap between this and `Break-even Rate` is the size of the assumption
the 2.5 multiple represents — that is its purpose. On its own it must not be
read as "films that made money", because clearing 1.0x gross is well short of
covering the cost of distribution and marketing.

### Reliability gates

Three measures wrap a base measure in the same suppression test. They exist so
that a category with too few measured films returns blank rather than a
confident-looking number. See section 4 for what the blank does.

#### Median Return (reliable)

```dax
IF ( [Films Measured] >= 100, [Median Return] )
```

Format string: `0.00\x`

`Median Return`, suppressed for any category with fewer than 100 measured films.
**The 100-film floor is hardcoded** and chosen, not derived. It must not be used
for a total or a single-value card: at report scope `Films Measured` is far above
100, so the gate never fires and the measure is simply a slower `Median Return`.

#### Break-even Rate (reliable)

```dax
IF ( [Films Measured] >= 100, [Break-even Rate] )
```

Format string: `0.0%`

`Break-even Rate` under the same 100-film floor, for use on any category axis
where break-even share is compared between groups of unequal size.

#### Median Budget (reliable)

```dax
IF ( [Films Measured] >= 100, [Median Budget] )
```

Format string: `\$#,0`

`Median Budget` under the same 100-film floor. The era caveat on `Median Budget`
applies unchanged; the gate addresses sample size, not comparability.

### Data quality

These measures describe the dataset rather than the films. Each uses
`ALL ( 'Movies' )` where it needs to speak about the whole starter file
regardless of what the reader has selected.

#### Rows With Unreported Revenue

```dax
CALCULATE ( COUNTROWS ( 'Movies' ), ALL ( 'Movies' ), 'Movies'[Revenue] = 0 )
```

Format string: `#,0`

Rows whose revenue is recorded as 0. Zero here means "not reported", which is
not the same as "earned nothing", and the distinction is the reason those rows
are excluded rather than counted at zero. It must not be read as a count of
films that took no money.

#### Share Revenue Unreported

```dax
DIVIDE ( [Rows With Unreported Revenue], [Films In Starter File] )
```

Format string: `0.0%`

How much of the starter file cannot answer a revenue question at all. Both parts
ignore report filters, so the figure is stable across the report — which is what
a scope statement needs.

#### Rows With Placeholder Budget

```dax
CALCULATE ( COUNTROWS ( 'Movies' ), ALL ( 'Movies' ), 'Movies'[Budget Looks Like A Placeholder] = TRUE() )
```

Format string: `#,0`

Rows whose budget is under $10,000. Real production budgets are near-continuous;
values shared by thousands of unrelated films are data-entry defaults. This is
an inference about the shape of the distribution, not a statement about any
individual film, and it must not be used to assert that a specific title's
budget is wrong.

#### Rows Missing Release Date

```dax
CALCULATE ( COUNTROWS ( 'Movies' ), ALL ( 'Movies' ), ISBLANK ( 'Movies'[Release Date] ) )
```

Format string: `#,0`

Rows that cannot be placed in time, and therefore cannot be assigned an era or
compared in dollars with anything.

#### English Language Share

```dax
VAR Pool = CALCULATETABLE ( 'Movies', ALL ( 'Movies' ), 'Movies'[Is Measurable] = TRUE() )
VAR English = FILTER ( Pool, 'Movies'[Original Language] = "en" )
RETURN
    DIVIDE ( COUNTROWS ( English ), COUNTROWS ( Pool ) )
```

Format string: `0.0%`

Share of the measurable subset originally in English. This is the single
clearest reason the report cannot speak about world cinema, which is why it is
given a KPI card on page 5 rather than a footnote. It describes the measurable
subset only, not the starter file and not cinema.

#### Revenue Reporting Rate

```dax
VAR Pool = CALCULATETABLE ( 'Movies', 'Movies'[Budget] >= 10000 )
VAR Reported = FILTER ( Pool, 'Movies'[Revenue] >= 10000 )
RETURN
    DIVIDE ( COUNTROWS ( Reported ), COUNTROWS ( Pool ) )
```

Format string: `0.0%`

Share of films with a credible budget that also report revenue. Unlike the other
data-quality measures this one respects the filter context, because its whole
purpose is to be sliced: the rate climbs steeply with budget size, which is the
survivorship problem page 3 has to disclose. Note that its pool is gated on
budget alone, not on `Is Measurable` — gating it on revenue would make the
measure tautological.

### Definition overlap

Three measures count how many films two rankings have in common. All three
build their pool with `ALL ( 'Movies' )` so that "the top 100" always means the
top 100 of the measurable subset and never the top 100 of a selection, and all
three add `+ 0` so an empty intersection reads as 0 rather than as a blank cell.

#### Top 100 Overlap Box Office And Return

```dax
VAR Pool = CALCULATETABLE ( 'Movies', ALL ( 'Movies' ), 'Movies'[Is Measurable] = TRUE() )
VAR ByRevenue = TOPN ( 100, Pool, 'Movies'[Revenue], DESC )
VAR ByReturn = TOPN ( 100, Pool, 'Movies'[ROI], DESC )
RETURN
    COUNTROWS (
        INTERSECT (
            SELECTCOLUMNS ( ByRevenue, "@id", 'Movies'[Movie ID] ),
            SELECTCOLUMNS ( ByReturn, "@id", 'Movies'[Movie ID] )
        )
    ) + 0
```

Format string: `#,0`

How many films appear in both the top 100 by gross revenue and the top 100 by
return on budget. It is the evidence for page 2's central claim that the choice
of definition decides the winner. It measures agreement between two rankings at
the top only; it must not be read as a correlation between revenue and return
across the whole distribution.

#### Top 100 Overlap Box Office And Acclaim

```dax
VAR Pool = CALCULATETABLE ( 'Movies', ALL ( 'Movies' ), 'Movies'[Is Measurable] = TRUE() )
VAR ByRevenue = TOPN ( 100, Pool, 'Movies'[Revenue], DESC )
VAR ByRating = TOPN ( 100, Pool, 'Movies'[Vote Average], DESC, 'Movies'[Vote Count], DESC )
RETURN
    COUNTROWS (
        INTERSECT (
            SELECTCOLUMNS ( ByRevenue, "@id", 'Movies'[Movie ID] ),
            SELECTCOLUMNS ( ByRating, "@id", 'Movies'[Movie ID] )
        )
    ) + 0
```

Format string: `#,0`

The same count for gross revenue against audience rating. The rating `TOPN`
carries a second sort key, `Vote Count` descending, because ratings tie
frequently at one decimal place; without it the membership of the top 100 would
depend on `TOPN`'s tie handling and could return more than 100 rows.

#### Top 100 Overlap Box Office And Profit

```dax
VAR Pool = CALCULATETABLE ( 'Movies', ALL ( 'Movies' ), 'Movies'[Is Measurable] = TRUE() )
VAR ByRevenue = TOPN ( 100, Pool, 'Movies'[Revenue], DESC )
VAR ByProfit = TOPN ( 100, Pool, 'Movies'[Gross Profit], DESC )
RETURN
    COUNTROWS (
        INTERSECT (
            SELECTCOLUMNS ( ByRevenue, "@id", 'Movies'[Movie ID] ),
            SELECTCOLUMNS ( ByProfit, "@id", 'Movies'[Movie ID] )
        )
    ) + 0
```

Format string: `#,0`

The same count for gross revenue against gross profit. A high number is the
finding: it means gross profit adds nothing to the story that revenue did not
already tell, and it is the reason this report treats four candidate definitions
of success rather than five.

### Effect size

#### Return Uplift Of Well Rated Films

```dax
VAR WellRated =
    CALCULATE ( MEDIAN ( 'Movies'[ROI] ), 'Movies'[Is Measurable] = TRUE(), 'Movies'[Vote Average] >= 7 )
VAR Rest =
    CALCULATE ( MEDIAN ( 'Movies'[ROI] ), 'Movies'[Is Measurable] = TRUE(), 'Movies'[Vote Average] < 7 )
RETURN
    DIVIDE ( WellRated, Rest )
```

Format string: `0.00\x`

How many times more a film rated 7.0 or better returns, compared with the rest
of the same selection. Because both halves are computed inside the current
filter context, the measure can be dropped onto a budget-decile or era axis to
ask whether the effect survives that control — which is how page 4's robustness
claim was tested. The 7.0 cut is hardcoded and chosen. This is an
**association, not a cause**: ratings are collected after release from people
who chose to watch, so the measure must never be presented as the effect of
making a better film.

---

## 4. The reliability gate pattern

Three measures share one idiom:

```dax
IF ( [Films Measured] >= 100, [Median Return] )
```

The `IF` has no else branch, so a category below the floor returns `BLANK()`.
That matters because of how Power BI treats a blank measure on a category axis:
the category is dropped from the visual entirely. It is not drawn as a zero
bar, not drawn as a gap, and not drawn small. A genre with four measured films
does not appear at all rather than being ranked on four films' worth of
evidence.

This is the deliberate choice. The alternatives are worse. Showing the thin
category ranks it, and a reader comparing bars has no way to see that one bar
rests on 4 films and another on 1,900. Showing it with a warning icon still puts
it on the same axis and still invites the comparison. Suppression removes the
invitation.

Suppression alone would be dishonest, so it is paired with disclosure. The
excluded categories are named in the affected visual's subtitle, not left to be
noticed by absence:

- **Page 4, "Genre matters less than being good"** — the horizontal bar chart of
  median return by genre binds `Median Return (reliable)`. Its subtitle reads:
  "Genres with fewer than 100 measured films are suppressed rather than ranked on
  thin evidence: TV Movie (4 films) and Documentary (66) are excluded." The alt
  text repeats the exclusion, so a screen-reader user receives it too.
- **Page 5, "Claims this report does not make"** — states the rule in general
  form: "That a genre or studio ranked on fewer than 100 measured films is
  ranked at all. Those are suppressed, not shown small."

`Break-even Rate (reliable)` and `Median Budget (reliable)` are defined for the
same pattern and are not currently bound to a visual. They exist so that any
later category breakdown of break-even share or median budget uses the gated
form by default rather than reintroducing the thin-evidence problem.

The 100-film floor is a judgement. It is not a power calculation, and a
different analyst could defend 50 or 250. What is not defensible is having no
floor.

---

## 5. Calculated tables

### Funnel

```dax
VAR Pool = ALL ( 'Movies' )
VAR Released = FILTER ( Pool, 'Movies'[Status] = "Released" )
VAR Dated = FILTER ( Released, NOT ISBLANK ( 'Movies'[Release Date] ) )
VAR Budgeted = FILTER ( Dated, 'Movies'[Budget] >= 10000 )
VAR Earning = FILTER ( Budgeted, 'Movies'[Revenue] >= 10000 )
VAR Rated = FILTER ( Earning, 'Movies'[Vote Count] >= 50 )
RETURN
    UNION (
        ROW (
            "Step Order", 1,
            "Step", "Films in the published dataset",
            "Films", 930000 * 1.0,
            "Why", "Attributed to the source dataset by the challenge brief. This model cannot verify it."
        ),
        ROW (
            "Step Order", 2,
            "Step", "Starter file keeps only Budget > 0",
            "Films", COUNTROWS ( Pool ) * 1.0,
            "Why", "Applied by the supplied query before any competitor sees the data. It is a filter on a financial field, so what remains is biased toward films that disclose money."
        ),
        ROW (
            "Step Order", 3,
            "Step", "Released, not planned or in production",
            "Films", COUNTROWS ( Released ) * 1.0,
            "Why", "An unreleased film has no audience and no box office."
        ),
        ROW (
            "Step Order", 4,
            "Step", "Has a release date",
            "Films", COUNTROWS ( Dated ) * 1.0,
            "Why", "Without a date a film cannot be placed in an era, and dollars are only comparable within an era."
        ),
        ROW (
            "Step Order", 5,
            "Step", "Budget is at least $10,000",
            "Films", COUNTROWS ( Budgeted ) * 1.0,
            "Why", "Removes placeholder budgets. Thousands of films share values such as 1, 100 and 1,000, which no real production budget would."
        ),
        ROW (
            "Step Order", 6,
            "Step", "Revenue is at least $10,000",
            "Films", COUNTROWS ( Earning ) * 1.0,
            "Why", "A revenue of 0 means not reported, not earned nothing. An unknown cannot go into a ratio. Judged against the whole starter file this is the biggest data-quality problem: 79% of rows carry a revenue of 0."
        ),
        ROW (
            "Step Order", 7,
            "Step", "At least 50 audience ratings",
            "Films", COUNTROWS ( Rated ) * 1.0,
            "Why", "An average built from a handful of votes is noise dressed as a score."
        )
    )
```

Four columns: `Step Order` (int64, hidden, the sort key), `Step` (string, sorted
by `Step Order`), `Films` (double, format `#,0`) and `Why` (string).

The structure is a chain of nested `FILTER` calls, each narrowing the previous
one, so the steps compose in exactly the order the report presents them and each
row's count is genuinely the survivors of everything above it. The order matches
the five conditions of `Is Measurable`, and step 7's count is therefore
identical to `Films Measured Overall` by construction rather than by
coincidence.

**The point of this table is that the funnel numbers are computed, not typed.**
The obvious way to build an inclusion funnel is a text box or a static table of
numbers copied out of an analysis notebook. That version drifts: the model gets
a threshold change, the funnel keeps the old figures, and the report's headline
scope statement quietly stops describing the report. Here every figure except
one is recomputed from `Movies` at each refresh, so the funnel cannot disagree
with the model that produced it. Change `Budget >= 10000` and step 5 moves on
its own.

The one exception is step 1, the 930,000 films of the published dataset. That
figure is hardcoded, for the same reason `Source Films As Published` is: the
starter query applies `budget > 0` before the model sees the data, so the
pre-filter count is not observable here. Its own `Why` cell says so on the face
of the report — "This model cannot verify it."

`Films` is multiplied by `1.0` throughout so that `UNION` receives a consistent
double type in that position across all seven rows; the literal 930000 would
otherwise be an integer and the union would be typed by the first row.

The table is used twice: as the horizontal bar chart "From roughly 930,000 films
to 7,733" on page 1, and as the full table with its `Why` column, "Every film
this report set aside, and why", on page 5.

### The four leaderboards

`Top By Box Office`, `Top By Gross Profit`, `Top By Return` and `Top By Acclaim`
are the same shape with one substituted ranking column. `Top By Return`:

```dax
VAR Pool = CALCULATETABLE ( 'Movies', ALL ( 'Movies' ), 'Movies'[Is Measurable] = TRUE() )
VAR Picked = TOPN ( 10, Pool, 'Movies'[ROI], DESC )
VAR Ranked =
    ADDCOLUMNS (
        Picked,
        "@Rank", RANKX ( Picked, 'Movies'[ROI], , DESC, DENSE )
    )
RETURN
    SELECTCOLUMNS (
        Ranked,
        "Rank", [@Rank],
        "Film", 'Movies'[Title] & " (" & FORMAT ( 'Movies'[Release Year], "0" ) & ")",
        "Value", 'Movies'[ROI] * 1.0
    )
```

| Table | Ranked and valued by | `Value` format string |
|---|---|---|
| `Top By Box Office` | `Movies`[Revenue] | `\$#,0` |
| `Top By Gross Profit` | `Movies`[Gross Profit] | `\$#,0` |
| `Top By Return` | `Movies`[ROI] | `0.0\x` |
| `Top By Acclaim` | `Movies`[Vote Average] | `0.0` |

Each produces three columns — `Rank` (int64), `Film` (string) and `Value`
(double) — which is what lets one `table()` call in the report generator render
all four with identical structure and column order.

Notes on the shape:

- The pool is `ALL ( 'Movies' )` under the `Is Measurable` gate. A leaderboard
  is a fixed claim about the measurable subset, so it must not move when a
  reader clicks a bar elsewhere on the page. Computing it as a calculated table
  makes that structural rather than a per-visual interaction setting.
- `RANKX` is evaluated over `Picked`, the ten selected rows, not over the whole
  pool, so ranks are always 1 to 10.
- `DENSE` means a tie shares a rank and the next rank does not skip. With
  `Top By Acclaim` this matters: ratings tie readily, and the ten rows may
  therefore carry fewer than ten distinct rank numbers.
- `Film` is materialised as `Title (Year)` at refresh time. The year
  disambiguates remakes, and doing the concatenation in the table rather than in
  the visual keeps the report layer free of expressions.
- `Value` is multiplied by `1.0` so that all four tables expose the same double
  type in the same position, whatever the source column's type was.

---

## 6. Format strings and units

| Format string | Renders as | Used for | What it signals |
|---|---|---|---|
| `#,0` | `7,733` | all counts of films and rows; `Funnel`[Films] | A whole count. No decimal, because a fraction of a film is meaningless. |
| `0` | `1994` | `Movie ID`, `Release Year`, `Release Month`, `Rank`, the three hidden sort columns, `Funnel`[Step Order] | An identifier or ordinal, not a quantity. No thousands separator, so a year never reads as `1,994`. |
| `0.0%` | `41.4%` | `Share Of Source Measurable`, `Break-even Rate`, `Recovered Budget Rate`, `Break-even Rate (reliable)`, `Share Revenue Unreported`, `English Language Share`, `Revenue Reporting Rate` | A share of a stated population. One decimal: enough to separate 33.5% from 34.0%, not enough to imply precision the sample does not support. |
| `0.00\x` | `1.96x` | `Median Return`, `Median Return (reliable)`, `Return Uplift Of Well Rated Films` | A multiple of production budget. See the note below. |
| `0.0\x` | `12.4x` | `Top By Return`[Value] | The same multiple at one decimal, because leaderboard returns are large enough that the second decimal is noise. |
| `\$#,0` | `$14,000,000` | `Median Budget`, `Median Revenue`, `Median Budget (reliable)`, `Top By Box Office`[Value], `Top By Gross Profit`[Value] | Nominal dollars, no cents. Never inflation adjusted, and never compared across eras. |
| `\$#,0;(\$#,0);\$#,0` | `$14,000,000` / `($2,000,000)` | `Movies`[Budget], `Movies`[Revenue], `Movies`[Gross Profit] | Nominal dollars with negatives in parentheses, which `Gross Profit` needs. |
| `0.00` | `6.40` | `Median Rating`, `Movies`[ROI], `Movies`[Popularity] | A dimensionless score or ratio at two decimals. |
| `0.0` | `7.4` | `Movies`[Vote Average], `Top By Acclaim`[Value] | A rating out of 10, at the precision the source records. |
| `Long Date` | `12 July 1994` | `Movies`[Release Date] | A date, spelled out so no reader has to guess a day/month order. |

### Why returns are a multiple and not a percentage

`ROI` is `Revenue / Budget`, so a film that grossed twice its budget has a value
of 2.0. The report shows that as **2.00x**, not as 200% and not as 100%.

The choice is about ambiguity. "Return of 200%" and "return of 100%" are both
used in ordinary writing for the same film — one means the ratio of revenue to
budget, the other the profit as a fraction of budget — and a reader cannot tell
from the number alone which convention a chart used. "2.00x" has one reading:
the film grossed twice what it cost. It also makes the break-even reference line
legible without arithmetic. The threshold is 2.5x, the bar is 1.41x, and the
comparison is immediate; as percentages the reader has to hold 250% against
141% and remember which convention is in play.

The `x` suffix is carried in the format string itself rather than in a title or
a label, so the unit travels with the number into tooltips, data labels and
exported data.
