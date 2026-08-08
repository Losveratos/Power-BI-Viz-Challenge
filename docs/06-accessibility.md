# 06 — Accessibility conformance record

Accessibility carries a significant portion of the judged score (R-13, R-14,
R-15, J-09). This document records what was done, what was mechanically
verified, and what could not be verified in this environment.

The rules themselves live in `docs/04-design-system.md` section 9. This file is
the evidence that they were met, not a restatement of them.

---

## 1. Approach

Accessibility here is a build constraint, not a review step. The difference is
whether an omission produces a note or an error.

**Alt text is a required argument.** Every visual in the report is created
through one function, `container()` in `analysis/06_build_report.py`. Its
signature makes `alt` a keyword-only parameter with no default, so a visual
cannot be constructed without the author deciding something about its alt text.
An empty or whitespace-only string is rejected outright:

```python
decorative = alt is None
if not decorative and not alt.strip():
    raise ValueError(f"visual {key} on page {page.key} has empty alt text")
```

**Decoration is declared, not defaulted.** Passing `alt=None` marks a visual as
decorative. `container()` then writes no `altText` property and sets
`tabOrder` to `-1000`, so a keyboard user never lands on a background panel, a
footer rule or a page-number label. Decoration is a positive statement by the
author, not the outcome of forgetting.

**The build is then re-checked from the files.**
`analysis/07_validate_pbip.py` reads the generated PBIR back off disk and fails
the build — non-zero exit, so it can gate a commit — on any of the following:

| Condition | Check |
|---|---|
| A data-bound visual has no alt text | any `visualType` in the core-visual set without an `altText` property |
| Two informative visuals share a tab order | `tabOrder` collision among visuals that carry alt text |
| An informative visual is excluded from the tab order | a visual with alt text whose `tabOrder` is `None` or negative |
| Two informative visuals overlap | rectangle intersection between two visuals that both carry alt text |

The overlap check ignores pairs where one side is decorative, because a
decorative panel sitting behind a text box is the intended card construction. It
fires only when two things a reader is meant to read are drawn on top of each
other.

The validator also warns — rather than fails — when alt text is shorter than 40
characters, on the grounds that a short sentence is usually a chart-type
restatement. The current build produces no such warning.

The last validator run reports `PASSED — 13 check(s) satisfied, 0 warning(s)`
across 5 pages, 72 visuals and 22 core Power BI visuals.

---

## 2. Alt text

The writing rule: **one or more sentences stating what the visual shows and what
it means, including the actual figures.** Never a restatement of the chart type.
Alt text is written from the visual's claim, so a screen-reader user receives the
same argument, with the same numbers and the same caveat, that a sighted reader
takes from the title, the subtitle and the marks together.

Two examples, quoted from the generated `visual.json` files.

The funnel chart on page 1 (`clusteredBarChart`, visual
`8643335545465e9aa0e6`):

> Horizontal bar chart of the inclusion funnel. The published dataset of about
> 930,000 films falls to 85,394 once the starter file keeps only films with a
> budget above zero, then to 79,222 released films, 56,072 with a release date,
> 28,193 with a credible budget, 10,219 that report revenue, and finally 7,733
> with at least 50 ratings. On a linear scale the final bar is barely visible.

Every step figure is in the sentence, so the chart's content does not have to be
inferred from bar lengths. The closing clause carries the visual rhetoric of the
chart — that the final bar is almost invisible — because that is the point being
made, and a reader who cannot see the bars would otherwise lose it.

The survivorship caution panel on page 3 (visual `c2c5da2764045ee59801`):

> Caution panel. Cheap films look extraordinary on this page partly because of
> survivorship bias. Of films budgeted between 10,000 and 100,000 dollars, only
> 7.8% report any revenue, against 91.1% of films budgeted above 50 million.
> Cheap films that flopped were never recorded, so they are absent from these
> charts, while expensive flops are counted. The return figure for the cheapest
> band is therefore an upper bound rather than an expectation. Only 2.4% of films
> in the 10,000 to 100,000 dollar band survive into this analysis, against 90.8%
> of films above 50 million.

This one matters most. It is the caveat that bounds every claim on page 3, and it
is a text panel rather than a chart, so nothing else would announce it. Dollar
amounts are spelled out as words ("100,000 dollars", "50 million") because a
screen reader's handling of `$50M` is not dependable.

### Counts

Counted by presence of an `altText` property in the `visual.json` files under
`src/pbip/MovieSuccess.Report/definition/pages/`:

| Page | Visuals | With alt text | Decorative (no alt text, `tabOrder -1000`) |
|---|---|---|---|
| 1 · The Answer | 16 | 9 | 7 |
| 2 · Success Has Four Answers | 18 | 12 | 6 |
| 3 · What Money Buys | 12 | 6 | 6 |
| 4 · What Actually Pays | 12 | 6 | 6 |
| 5 · What We Cannot Know | 14 | 8 | 6 |
| **Total** | **72** | **41** | **31** |

All 22 core Power BI visuals — the cards, charts and tables that bind to the
model — carry alt text; the validator's data-bound check would fail the build
otherwise. The remaining 19 alt-texted visuals are text boxes that carry
narrative content: page titles, standfirsts, the Key Takeaway, the reading
guide, the caution and caveat panels, and the closing statements. The 31
decorative visuals are the card background panels, the gold accent rules, the
page-number labels, the footer hairlines and the footer attribution lines.

---

## 3. Reading order

Tab order is assigned explicitly, never left to the order in which objects
happened to be written. `Page.next_tab()` hands out `100, 200, 300, …` in the
order visuals are added to the page, and pages are assembled in narrative order,
so traversal follows the argument rather than the canvas geometry.

The step of 100 is deliberate: it leaves room to insert a visual between two
existing ones without renumbering the page, so a later edit cannot silently
shuffle the reading order of everything after it.

Two positions are pinned rather than allocated:

- **Tab order 10 — the report's conclusion.** On page 1 the Key Takeaway text box
  is pinned at `10`, ahead of the page title at `100` and the standfirst at
  `200`. A keyboard or screen-reader user therefore meets the report's answer
  first, before any furniture. Page 2 pins its lede statement the same way, for
  the same reason.
- **Tab order -1000 — decoration.** Every visual constructed with `alt=None`
  gets `-1000`, which removes it from keyboard traversal.

The resulting order on page 1 is: Key Takeaway (10), page title (100),
standfirst (200), the four scope KPI cards (300–600), the funnel chart (700), the
reading guide (800). Pages 3, 4 and 5 run 100–600, 100–600 and 100–800
respectively; page 2 runs 10 then 100–1100. No informative visual on any page
shares a tab order with another, and none is excluded — both conditions are
enforced by the validator rather than asserted here.

---

## 4. Colour is never the only channel

The design system states the rule (section 9) and its strict form for the one
pair where it is load-bearing (section 5). This is how the build meets it.

**Legends are off, and nothing is lost.** Every chart in the report binds exactly
one measure to `Y` and one column to `Category`, so each chart is single-series;
`_axis_objects()` sets `legend.show` to `false` accordingly. A one-entry legend
tells a reader nothing they cannot get from the title, and each chart's title
names the measure it draws — "Money does buy box office", "It does not buy a
better return", "The mid-budget film is the one that fails". The design system's
requirement that a legend be present wherever two or more series appear is
therefore satisfied vacuously: no chart has two series. Series colour in this
report identifies the subject of the chart, not a category within it.

**Marks carry their own values.** `bar_or_column()` enables direct value labels
by default and no chart in the build overrides that, so every mark states its
quantity in ink primary at 10pt semibold. Any mark the surrounding text refers to
by name therefore carries its figure, and no quantity anywhere depends on hue or
on estimating a bar against an axis.

**Break-even status is a stated threshold, not a colour.** Break-even appears
three ways, all textual:

1. In the subtitle as a number — "Share of films reaching 2.5x their budget.
   Lowest at $15-30M: 33.5%" on the break-even-rate chart on page 3, and "The
   2.5x line is the break-even rule of thumb" on the return-by-rating chart on
   page 4.
2. As a labelled reference line. The two charts that show return set a
   `y1AxisReferenceLine` at `2.5` with `dataLabelShow` true and `displayName`
   "2.5x break-even", rendered dashed in ink muted per the mark specification. An
   unlabelled reference line would ask the reader to guess the threshold.
3. In prose on page 2's "OUR DEFINITION" panel, which states the 2.5x gross
   break-even as the report's chosen standard.

**The red/green pair never encodes two categories.** In this build the pair is
never used as a two-value series in one chart. Aqua-green `#199E70` appears as
the single series colour of the break-even-rate chart, whose bars all carry
percentage labels; red `#E66767` appears only as the accent rule on the page 3
caution panel and as the heading colour of two warning panels, in both cases
next to text that says the same thing in words.

### The green/red obligation, reproduced

From `docs/04-design-system.md` section 5, the palette validator's own output:

> CVD separation — **WARN**. Worst adjacent pair `#199E70` against `#E66767` at
> ΔE 6.5 under protanopia; 9.4 under tritanopia.

ΔE 6.5 sits inside the 6–8 floor band, which is permissible **only** where
secondary encoding is present. The obligation that follows is not optional: the
green/red pair never carries meaning alone, and every use of it must add all
three of a direct value label on the mark, an explicit text label naming the
status in words, and the threshold stated in the visual's subtitle. Removing the
hue and reading the chart in greyscale is the test — if the meaning survives, the
visual passes.

---

## 5. Contrast

Measured ratios as recorded in `docs/04-design-system.md` section 2. These are
computed values, reproduced here rather than recomputed.

| Ink token | Hex | On page `#131110` | On card `#1C1917` | Verdict |
|---|---|---|---|---|
| Ink primary | `#F5F1EC` | 16.74:1 | 15.55:1 | clears 4.5:1 by a wide margin on both surfaces |
| Ink secondary | `#A8A29B` | 7.45:1 | 6.92:1 | clears 4.5:1 on both surfaces |
| Ink muted | `#78716B` | 3.92:1 | 3.64:1 | clears 3:1 but **not** 4.5:1 on either surface |

Because ink muted does not clear 4.5:1, it is confined to text whose loss does
not change what the reader understands: attribution, axis furniture, and labels
that repeat information already present on the visual. Ink secondary, not ink
muted, carries all running text, every standfirst, every visual subtitle and
every caveat. Nothing that carries a claim, a number a reader must act on, or a
limitation is set in ink muted.

One consequence for a Desktop pass: any text placed over poster imagery must be
measured against the image region behind it rather than against the page token,
and takes a scrim if it does not clear 4.5:1.

---

## 6. What still needs a human in Power BI Desktop

This build environment has no Power BI Desktop. Everything checkable from the
project files has been checked by `analysis/07_validate_pbip.py`; the following
cannot be, and were **not** verified here. They are listed as outstanding work,
not as passes.

1. **Run the built-in accessibility checker.** Power BI Desktop's own checker
   inspects properties this build does not write and may flag defaults that the
   generator does not control. Its findings should be recorded before submission.
2. **Tab through every page.** Confirm that traversal actually follows the
   narrative — Key Takeaway, then title, then the argument in order — and that no
   decorative panel receives focus. The tab-order numbers are correct in the
   files; how Desktop realises them for a screen reader has not been observed.
3. **Confirm no text is clipped at `FitToPage` on a 16:9 display.** Every page is
   1920x1080 with `displayOption: FitToPage`. Text-box heights were computed, not
   measured against rendered Segoe UI metrics, so a long standfirst or a wrapped
   subtitle could overflow its box at scale.
4. **Confirm the reference-line labels render.** The 2.5x break-even lines are
   written with `dataLabelShow`, `dataLabelText: 'Name'` and a `displayName`. That
   property shape came from files Desktop itself wrote, but whether the label
   appears in the intended position, in the intended colour, and without
   colliding with a bar can only be seen.
5. **Check the report in Windows high-contrast mode.** High contrast overrides
   theme colours, and a dark report built on luminance separation rather than
   outlines is exactly the case where card boundaries can disappear. Confirm that
   cards, gridlines and reference lines remain distinguishable.

The mechanical guarantees in sections 1 to 5 are real and reproducible. They are
not a substitute for these five checks, and this record does not claim they are.
