# Draft submission description

Text for the Contests gallery post. Two versions: a short one that fits a gallery
card, and a longer one if the field allows it. Tag the entry **World Champs BCN**.

---

## Short version

**What Makes a Movie Successful?**

Bigger budgets buy bigger box office, not better payback. What consistently pays is
being liked: films rated 7 or above return about twice as much per dollar, in every
budget class and every era.

The catch, and the reason this report is built the way it is: of the roughly 930,000
films in the dataset, only **7,733 — 0.8%** can carry a financial claim at all. The
starter file keeps only films with a budget above zero; 79% of the rows that remain
report no revenue; thousands share placeholder budgets like 1, 100 and 1,000. The
report shows that funnel on its landing page rather than hiding it.

Rank the same 7,733 films four defensible ways and you get four different winners —
**not one film** appears in both the top 100 by box office and the top 100 by return
on budget. So the report picks a definition in the open, says what the choice costs,
and then shows the evidence: return follows a U-curve across budget bands with its
worst point at $15–30M, and rises monotonically with audience rating while median
budget *falls*.

Every finding was tested against the obvious objection. The one that did not fully
survive is disclosed next to the chart it undermines: cheap films look
extraordinary partly because films budgeted $10k–100k report revenue only 7.8% of
the time, against 91.1% above $50M — the flops were never recorded.

Data: TMDB via Kaggle (ODC-By 1.0). No external data, no joins, no scraping.

---

## Longer version

**What Makes a Movie Successful?** — five pages, one answer, and an honest account
of how little of the data can support it.

**The answer.** Money buys attendance, not a return. Production budget is the
strongest predictor of gross revenue in this dataset (Spearman ρ = +0.68) and a
slightly *negative* predictor of return on that budget (ρ = −0.11). The signal that
does track return is audience rating: films rated 7.0 or above return a median
**3.28x** against **1.59x** for the rest — and their median budget is *lower*
($12M against $17M), not higher.

**Why you should not simply believe it.** Of roughly 930,000 films, 7,733 survive to
the point where revenue and budget can honestly be divided. That is 0.8%. The
supplied starter file had already kept only films with a budget above zero — a
filter on a financial variable, applied before any competitor saw the data, which
biases the sample toward films that disclose money. Of the rows that remain, 79%
record a revenue of zero, which means *not reported*, not *earned nothing*. The
budget value 100 appears 3,531 times. 85% of the measurable films are
English-language, so this is a report about anglophone commercial cinema and says
so.

**Success has four answers.** Box office, gross profit, return on budget and
audience acclaim each produce a defensible top 100, and they barely agree: box
office and return share **zero** films; box office and gross profit share 91, which
is why the report retires gross profit rather than presenting it as a second
insight. Page 2 makes that disagreement the argument, then commits to return on
budget against a 2.5x gross break-even multiple — labelled throughout as an
industry rule of thumb rather than something the data proves.

**The shape of the finding.** Median return by budget band is a U: 4.98x under $1M,
bottoming at **1.41x in the $15–30M band**, recovering to 2.70x above $100M. Only
33.5% of mid-budget films clear break-even. Removing the top 5% of earners inside
every band leaves the U intact, so it is not a few franchises.

**How hard it was pushed.** Four adversarial checks. The rating effect survives all
ten budget deciles and all five eras (median uplift 2.1x, minimum 1.19x) and every
vote threshold from 0 to 500. The low-budget advantage does *not* fully survive:
films budgeted $10k–100k report revenue only 7.8% of the time versus 91.1% above
$50M, so cheap flops are largely missing and that band's return is an upper bound.
The report states this in a panel beside the chart, not in a footnote. And no dollar
figure is inflation-adjusted, because a CPI series would be an external dataset —
so cross-era comparisons use ratios only.

**What it refuses to claim.** That better films *cause* better returns. Ratings are
collected after release from people who chose to watch, so the causal direction
cannot be established from this data. Page 5 lists every claim not being made,
alongside what would change the answer.

**Accessibility.** Alt text on all 41 information-carrying visuals, written as
statements of meaning rather than chart descriptions. Explicit tab order in
narrative sequence, with the Key Takeaway first. Palette validated with a CVD
simulator rather than by eye; break-even status is never encoded by colour alone.

**Build note.** The report was authored as a Power BI Project — TMDL model, PBIR
report — generated by scripts, with a validator enforcing the 5-page limit, the
50-word Key Takeaway, alt-text coverage and tab-order uniqueness on every build.
AI assistance was used for design, accessibility and report development, as the
round permits. The full process log is published with the entry.

Data: TMDB, distributed via Kaggle under ODC-By 1.0. No external datasets, no API
joins, no scraping, no source values altered.
