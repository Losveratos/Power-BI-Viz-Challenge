# Narrative and metric definition

The brief asks a single question — *What makes a movie successful?* — and says
plainly that there is no single correct answer, that the strongest entries will
define success clearly, support conclusions with evidence, acknowledge tradeoffs
and communicate honestly. It also says this is a storytelling challenge, not a
dashboard-building exercise.

This document records the story that was chosen, why it beat the alternatives,
and exactly what the report is claiming.

---

## The answer, in one sentence

Money buys attendance; it does not buy a return. The one thing that tracks return
in every budget class and every era is whether people liked the film — and unlike
budget, it costs nothing.

## The Key Takeaway (the round's hard requirement)

> Bigger budgets buy bigger box office, not better payback. What consistently
> pays is being liked: films rated 7 or above return about twice as much per
> dollar, in every budget class and every era. One caveat — this data can measure
> only 0.8% of its films.

46 words. Written for a general audience: no jargon, no metric names, one number.
The word count is enforced on every build by `analysis/07_validate_pbip.py`, which
counts an em dash as a word so the margin is real rather than nominal.

---

## Defining success

The brief lists three candidate definitions in its own text: a box office hit, a
critical darling, an incredible return on investment. Rather than assert one, the
report measures how much they disagree, using the same 7,733 films:

| Comparison | Films shared between the two top 100s |
|---|---:|
| Box office and return on budget | **0** |
| Box office and audience rating | 11 |
| Box office and gross profit | 91 |

Two findings fall out of that table and both are load-bearing.

**Box office and return share nothing.** Not one film in the hundred
highest-grossing is also in the hundred highest-returning. These are not two
angles on one idea; they are different questions with disjoint answers. Any report
that shows a "top films" chart without saying which of the two it means is making
an argument without admitting to it.

**Gross profit adds nothing to gross revenue.** A 91% overlap means "revenue minus
budget" is essentially a re-ranking of "revenue" at this scale, because budgets are
small relative to the spread in revenue. The report shows it once, on page 2, to
retire it — and to make the point that a metric can be perfectly defensible and
still be redundant.

### What this report chose, and what the choice costs

**Success = return on production budget, judged against a 2.5x gross break-even
multiple.**

Chosen because it rewards performance rather than size. A $200M film that grosses
$400M and a $2M film that grosses $4M performed identically, and revenue alone
cannot say that.

The 2.5x figure is an **assumption imported from industry practice**, not a number
this data produces: exhibitors retain roughly half of ticket revenue, and
marketing spend is not included in a reported production budget. The report labels
it as a rule of thumb everywhere it appears, and the measure's own description in
the model says so, so the assumption travels with the number.

The cost of the choice is that **a ratio flatters cheap films**, and cheap films
are exactly the ones this dataset under-reports. Page 3 leads with that admission
rather than burying it.

---

## The evidence, and how hard it was pushed

### Money buys revenue, not return

| Driver | vs Revenue | vs Return on budget |
|---|---:|---:|
| Budget | **+0.68** | **-0.11** |
| Vote count | +0.70 | +0.39 |
| Popularity | +0.63 | +0.33 |
| Audience rating | +0.18 | **+0.33** |
| Runtime | +0.24 | +0.06 |

Spearman rank correlations, because revenue and budget are skewed enough that
Pearson would describe a handful of blockbusters rather than the population.

Budget is the strongest predictor of gross revenue and a slightly *negative*
predictor of return. That holds at every threshold tested, from zero to 500
minimum votes and from $1 to $1M minimum revenue.

### The shape is a U, and the middle is the dangerous place

| Budget band | Films | Median return | Share clearing 2.5x |
|---|---:|---:|---:|
| Under $1M | 456 | 4.98x | 65.8% |
| $1M–$5M | 1,263 | 2.63x | 51.4% |
| $5M–$15M | 1,983 | 1.75x | 38.7% |
| **$15M–$30M** | **1,616** | **1.41x** | **33.5%** |
| $30M–$60M | 1,277 | 1.68x | 34.5% |
| $60M–$100M | 633 | 1.96x | 37.0% |
| $100M and above | 505 | 2.70x | 53.3% |

Removing the top 5% of earners inside every band leaves the U intact, so this is
not a handful of franchises carrying the right-hand side. The mid-budget trough is
the most useful part of the chart, because it is where a producer has least room
for error — and it is a well-known industry phenomenon arriving here from the data
rather than from received wisdom.

### Being liked pays, and it survives every control

| Rating band | Films | Median budget | Median return | Share clearing 2.5x |
|---|---:|---:|---:|---:|
| Below 5.0 | 303 | $14.0M | 0.73x | 21.5% |
| 5.0–6.0 | 1,720 | $17.0M | 1.14x | 26.0% |
| 6.0–6.5 | 1,770 | $19.6M | 1.71x | 35.5% |
| 6.5–7.0 | 1,825 | $15.0M | 2.10x | 43.8% |
| 7.0–7.5 | 1,342 | $12.0M | 2.77x | 53.7% |
| 7.5 and above | 773 | $12.0M | **4.27x** | **70.0%** |

Two things at once: return rises monotonically with rating, and **median budget
falls** while it does. The best-rated group is the cheapest group on the chart.

The obvious objection is that this is budget or era in disguise. It is not:

- Films rated 7.0+ out-return the rest in **all ten budget deciles**, by a median
  factor of 2.1x and never less than 1.37x.
- They out-return the rest in **all five eras**, never by less than 1.19x.
- The relationship holds at every vote-count threshold from 0 to 500.

### Genre matters, but less than being good

The best genre (Animation, 2.44x) and the worst (History, 1.39x) are a factor of
1.75 apart. The best rating band and the worst are a factor of 5.9 apart. Genre is
a much smaller lever than quality, and the report says so rather than implying
that picking horror is a strategy.

Genres with fewer than 100 measured films — TV Movie (4) and Documentary (66) —
are suppressed by a reliability gate in the measure rather than ranked, and the
visual's subtitle names them.

---

## Why not the other stories

| Alternative | Why it was rejected |
|---|---|
| **Box office and studio market share** | Well-trodden, and it answers "who is biggest", not "what makes a film successful". It also compares nominal dollars across eras, which this dataset cannot support. |
| **Critics versus audience** | The dataset has one rating source (TMDB audience votes) and no critic score. Building a critics-versus-audience story would require joining Rotten Tomatoes or Metacritic, which the rules explicitly prohibit. |
| **Release-window seasonality** | It is in the data — June returns 2.59x, September 1.35x — but the confound is severe: September is festival and dump-month, so release timing and film quality are entangled in a way this data cannot separate. It appears in the analysis output but was kept out of the report rather than presented as a finding we cannot defend. |
| **Franchise and sequel effects** | Reachable through the `keywords` table, and interesting. Dropped for space: five pages is the cap, and the four pages of evidence already carry the argument. |

---

## The story arc across five pages

| Page | Job in the story |
|---|---|
| **1 · The Answer** | Lead with the conclusion and immediately with its scope. Key Takeaway, four scope figures, and the funnel from 930,000 films to 7,733. A reader who stops here leaves with the answer *and* the caveat. |
| **2 · Success Has Four Answers** | Establish that the question is ambiguous, prove it with the zero-overlap number, then commit to one definition in the open and say what it costs. |
| **3 · What Money Buys** | The first half of the evidence: budget buys revenue, not return, and the middle of the market is the worst place to be. The survivorship problem is disclosed on the same page, next to the chart it undermines. |
| **4 · What Actually Pays** | The second half: the rating effect, and the four controls it survives. Ends by refusing to claim causation. |
| **5 · What We Cannot Know** | The funnel in full, the missingness evidence, what would change the answer, and an explicit list of claims not being made. |

Limitations are not confined to page 5. Every page footer carries its own caveat
line, page 3's caution panel sits beside the chart it qualifies, and page 4's
causation warning is the same size as the finding it qualifies. That placement is
the point: a limitation on the last page is a disclaimer, while a limitation next
to the chart is part of the argument.
