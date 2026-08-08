# 04 — Design system

The locked visual specification for the Round 3 report. Every value here is
final. This document exists so that the build, the theme file and any later
review all work from one record, and so that each decision can be audited
against measured evidence rather than taste.

Scope and ownership:

- This file is the record of the design system. It defines the tokens, the
  rules and the reasoning.
- The Power BI theme JSON under `assets/theme/` is the machine-readable
  implementation of this record and is owned separately. Where the two
  disagree, this document states the intent and the theme file is wrong.
- Report structure, page purpose and narrative order belong to the report
  design documents, not here. This file governs surfaces, colour, type,
  spacing, mark form and accessibility.

The report is five pages, each on a 1920x1080 canvas with `displayOption` set to
`FitToPage`, answering "What makes a movie successful?".

| Page | Title |
|---|---|
| 1 | The Answer |
| 2 | Success Has Four Answers |
| 3 | What Money Buys |
| 4 | What Actually Pays |
| 5 | What We Cannot Know |

The report commits to a single dark appearance. There is no light variant. A
Power BI report ships one theme, and a half-considered second mode would be
worse than one mode designed properly, so the palette was chosen for a dark
surface from the start rather than inverted from a light one. The consequences of
that choice are set out in "Why dark" at the end.

---

## 1. Surfaces

| Token | Hex | Use |
|---|---|---|
| Page background (outspace) | `#131110` | The canvas and the report outspace. Near-black, very slightly warm — a darkened auditorium rather than a pure black screen. |
| Card / visual background | `#1C1917` | The fill behind every visual and every KPI card. One step above the page, so a card reads as a raised surface without a border. |
| Hairline / divider | `#2E2A27` | Card edges where an edge is needed, and rules between sections. |
| Gridlines | `#262220` | Chart gridlines only. Deliberately recessive: present enough to let a reader trace a value across a wide chart, quiet enough that it never competes with a mark. |

Two decisions are load-bearing here.

The page is warm rather than neutral. A pure `#000000` canvas makes gold read as
yellow and makes thin light type vibrate against the background. Pulling a small
amount of warmth into the near-black keeps the gold accent reading as gold and
softens the edge between type and surface.

Cards are separated by luminance, not by outline. `#1C1917` on `#131110` is a
1.08:1 step. That is intentionally almost nothing: it defines a region under
raking attention and disappears otherwise. Where a card genuinely needs an edge,
the hairline at `#2E2A27` provides it at 1.23:1 against the card. Neither of
these is text and neither carries meaning, so neither is held to a text contrast
threshold.

---

## 2. Ink

Text tokens. Text never wears a series colour: a series colour on a label makes
the label look like a mark, and it makes the reader wonder which category the
sentence belongs to.

| Token | Hex | Use |
|---|---|---|
| Ink primary | `#F5F1EC` | Page titles, visual titles, hero numbers, any load-bearing figure. Warm off-white, matched to the warmth of the surface. |
| Ink secondary | `#A8A29B` | Standfirsts, visual subtitles, KPI labels, all running text and annotation. |
| Ink muted | `#78716B` | Footnotes, axis furniture and reference-line labels. |

Measured WCAG contrast, as computed rather than judged:

| Ink | On page `#131110` | On card `#1C1917` |
|---|---|---|
| `#F5F1EC` | 16.74:1 | 15.55:1 |
| `#A8A29B` | 7.45:1 | 6.92:1 |
| `#78716B` | 3.92:1 | 3.64:1 |

Ink primary and ink secondary both clear 4.5:1 on both surfaces by a wide
margin. Ink muted does not: it clears 3:1 but not 4.5:1. That is the reason for
the rule stated in the typography section — ink secondary, not ink muted,
carries all running text, and nothing that carries a claim, a caveat or a number
a reader must be able to act on is ever set in ink muted. Ink muted is reserved
for text whose loss does not change what the reader understands: attribution,
axis furniture, and labels that repeat information already present elsewhere on
the visual.

---

## 3. Categorical palette

Five slots in a fixed order. The order is semantic, not decorative. Slots are
assigned by meaning and never cycled: a category keeps its colour on every page
it appears on, and an unused slot stays unused rather than being reallocated.

| Slot | Hex | Name | Meaning |
|---|---|---|---|
| 1 | `#C98500` | Gold | The accent. Marks the report's own chosen definition of success, and any highlighted mark. |
| 2 | `#3987E5` | Blue | Box office / gross revenue. |
| 3 | `#E66767` | Red | Below break-even (loss). |
| 4 | `#199E70` | Aqua-green | At or above break-even (return). |
| 5 | `#9085E9` | Violet | Audience acclaim. |

Gold is first because the report argues for one definition of success out of
four, and the argument needs one colour that means "this is the one we chose".
Reserving the accent to that single job is what lets a page carry focus with very
little ink: on a dark surface, one warm mark among quiet ones does the work that
a light-surface layout would need weight, size or a box to do.

Blue for box office and violet for audience acclaim are the two "kinds of
success" that are not the report's chosen one, and they are hue-separated from
gold and from each other so a reader can hold three definitions on one page.

Red and aqua-green are a status pair, not two categories. They encode one binary
— below break-even against at or above break-even — and they are the reason the
palette carries a warning. See section 5.

Measured contrast of each slot against both surfaces, all above the 3:1 floor for
a non-text mark:

| Slot | On page `#131110` | On card `#1C1917` |
|---|---|---|
| `#C98500` | 6.13:1 | 5.69:1 |
| `#3987E5` | 5.17:1 | 4.81:1 |
| `#E66767` | 5.83:1 | 5.41:1 |
| `#199E70` | 5.53:1 | 5.13:1 |
| `#9085E9` | 6.02:1 | 5.59:1 |

---

## 4. Ordinal ramp

A single-hue gold ramp, six steps, used for the rating bands. Ordered data takes
a ramp, not categorical hues; using the categorical palette for bands would
imply the bands are unrelated kinds rather than positions on one scale.

| Step | Hex |
|---|---|
| 1 (darkest) | `#6B4A00` |
| 2 | `#8A6100` |
| 3 | `#A87700` |
| 4 | `#C98500` |
| 5 | `#DFA234` |
| 6 (lightest) | `#F0C260` |

Step 4 is the accent gold itself, so the ramp and the accent are visibly the same
family. The ramp is used only where the encoded variable is ordered. It is never
used to distinguish categories, and a value shown on the ramp always resolves to
one of these six steps rather than to an interpolated colour, so that a reader
comparing two marks is comparing two bands and not two shades.

---

## 5. Validation

The palette was not approved by eye. It was checked with a runnable validator
that computes the parts of a palette that are computable: OKLCH lightness and
chroma, OKLab ΔE (x100) between slots under simulated colour vision deficiency
using the Machado-Oliveira-Fernandes (2009) severity-1.0 model, and WCAG contrast
against the surface. The results below are the validator's output, recorded as
evidence. They are reproducible, and they are what the build must be held to —
not a claim that the palette "looks accessible".

The palette was run against both surfaces it is drawn on, `#131110` (page) and
`#1C1917` (card), in dark mode. Both runs return identical results, because the
two surfaces differ by too little to move any check.

| Check | Result | Detail |
|---|---|---|
| Lightness band | PASS | All five slots inside OKLCH L 0.48–0.67, the dark-mode band. |
| Chroma floor | PASS | All five at or above C 0.10, so no slot reads as grey. |
| CVD separation | WARN | Worst adjacent pair `#199E70` against `#E66767` at ΔE 6.5 under protanopia; 9.4 under tritanopia. |
| Normal-vision floor | PASS | Worst adjacent pair `#9085E9` against `#199E70` at ΔE 24.6. |
| Contrast versus surface | PASS | All five at or above 3:1 against both surfaces. |

The gold ordinal ramp is checked as a ramp, against different criteria — one hue,
monotone lightness, visible steps, and a light end that still reads as a mark:

| Check | Result | Detail |
|---|---|---|
| Lightness monotonicity | PASS | Steps read as a single ordered progression. |
| Adjacent lightness gaps | PASS | All gaps at or above 0.06, so neighbouring bands are distinguishable. |
| Light-end contrast | PASS | 2.34:1 against the page surface. |
| Single hue | PASS | 11 degrees of hue spread across six steps. |

The CVD result is a WARN, not a PASS. ΔE 6.5 sits in the 6–8 floor band, which is
permissible only where secondary encoding is present. It is recorded here as a
warning rather than smoothed over, because the obligation it creates is a build
requirement and not a preference.

### The green/red obligation

The aqua-green and red slots encode break-even status. They are the one place in
this palette where two hues that are similar under protanopia sit next to each
other in meaning as well as in the palette. The rule that follows is not
optional:

**The green/red pair never carries meaning alone.** A viewer who cannot separate
the two hues must still be able to read the chart correctly from its labels.

Every use of that pair must add secondary encoding. All three of the following
are required, not a choice between them:

1. A direct value label on the mark, so the quantity is legible without
   reference to the legend.
2. An explicit text label naming the status in words — "returns 2.3x", "below
   break-even" — so the category is legible without reference to hue.
3. The threshold stated in the visual's subtitle, so a reader knows what divides
   the two groups and can verify any individual mark against the number rather
   than against its colour.

Consequences for the build: a break-even chart with a bare legend and no labels
is not acceptable, and neither is one where the status appears only as a colour
in a tooltip. If a chart cannot carry the labels — too many marks, marks too thin
— then the chart is wrong for the claim and the form changes, rather than the
rule bending. Removing the hue entirely and reading the chart in greyscale is the
test: if the meaning survives, the visual passes.

This satisfies the colour-is-never-the-only-channel requirement (R-13, J-09) at
the point where the palette is weakest, which is the only place it matters.

---

## 6. Typography

One family throughout: **Segoe UI**. It is the Power BI default, so it renders
identically on every judge's machine with no font substitution, no metric shift
and no risk of a layout reflowing on a system that lacks an embedded face. A
report is judged as rendered, and choosing a distinctive face would trade a small
gain in character for a real risk of broken pages.

| Role | Size | Weight | Ink |
|---|---|---|---|
| Page title | 32pt | Semibold | Primary |
| Page subtitle / standfirst | 15pt | Regular | Secondary |
| Section / visual title | 13pt | Semibold | Primary |
| Visual subtitle | 10pt | Regular | Secondary |
| Hero number | 54pt | Semibold | Primary |
| KPI label | 11pt | Regular | Secondary |
| Body / annotation | 11pt | Regular | Secondary |
| Footnote | 10pt | Regular | Muted |
| Data label | 10pt | Semibold | Primary |

The scale has six steps and no more. Each step is far enough from its neighbour
to be read as a different level rather than as an inconsistency: 10, 11, 13, 15,
32, 54.

The visual subtitle is the most important line in this table. It is where the
caveat lives, and where the threshold is stated — including the 2.5x break-even
threshold on every visual that shows return. A subtitle is not a decorative
restatement of the title; if a visual has no caveat and no threshold to declare,
it does not need a subtitle.

Nothing is set below 10pt. Thin light type on a dark surface loses more at small
sizes than dark type on a light surface does, and a 9pt annotation that a
designer can read on a large monitor is not readable in a judging context.

---

## 7. Layout grid

| Property | Value |
|---|---|
| Canvas | 1920 x 1080, `displayOption: FitToPage` |
| Outer margin | 48px on all four sides |
| Columns | 12 |
| Gutter | 24px |
| Column width | 118px |
| Title block | Top 132px of every page |
| Content start | y = 180 |
| Footer strip | y = 1016 |

The vertical rhythm is fixed across all five pages, so a reader moving between
pages finds the title in the same place every time and does not have to
re-locate the page. The title block occupies the top 132px; content begins at
y = 180, leaving a 48px band of clear space between the title and the first
visual.

Every page carries a footer strip at y = 1016 holding two things: the data
attribution — the TMDB dataset distributed via Kaggle under ODC-By 1.0, which is
required on the face of the entry and not only in this repository — and that
page's own caveat line. The caveat is per page rather than collected at the end,
so the limitation that bounds a page's claim is visible while the reader is
looking at the claim.

Note on the column figure: with a 48px margin on each side the content width is
1824px, and dividing that by 12 columns with 11 24px gutters gives 130px per
column, not 118px. The two figures cannot both be exact. The margin, the gutter
and the column count are the operative constraints and the ones the build snaps
to; the 118px column figure is recorded here as specified and flagged so that a
later pass can reconcile it deliberately rather than discovering the residual
mid-layout.

---

## 8. Mark specification

These are rules, not preferences.

**Bars and columns.** Thin marks. 2px rounded data ends. A 2px gap in the surface
colour between adjacent fills, so that a stacked or grouped bar separates without
an outline. Bars start at zero, always.

**Lines.** 2px stroke. Where markers are shown they are at least 8px, so a marker
is a mark rather than a thickening of the line. Lines are not smoothed; a
smoothed line invents values between the points.

**Reference lines.** 1px dashed in ink muted, and always labelled with their
value. The 2.5x break-even line is the report's most important reference line and
is labelled on every chart that shows return. An unlabelled reference line asks
the reader to guess what the line means, which is worse than no line.

**Direct labels.** Selective. Never a number on every point — a fully labelled
chart is a table drawn badly. The highlighted mark always carries its value, and
so does any mark the surrounding text refers to by name.

**Recessive furniture.** Gridlines at `#262220`, axes recessive, no chart junk,
no shadows, no 3D, no gradient fills on categorical marks, no background image
behind a plot area.

**Never a dual-axis chart.** Two measures on two scales in one frame let the
designer choose where the lines cross, which means the reader is being shown a
relationship that was decided rather than measured. Two measures of different
scale become two charts stacked on a shared x-axis, or one indexed comparison on
a single scale. This rule has no exception in this report.

---

## 9. Accessibility rules

Requirements the build must satisfy, not aspirations. These carry the
accessibility weight of the judged criteria (R-13, R-14, R-15, J-09).

**Alt text on every visual, written as a sentence.** The sentence states what the
visual shows and what it means. "Bar chart of median return by budget band" is
not acceptable alt text; "Films budgeted under 10 million return a median 2.5x,
while films over 100 million return 1.9x — but the small-budget group reports
revenue far less often" is. Alt text is written from the visual's claim, so it
says the same thing the title says.

**Explicit tab order on every visual.** Tab order is set per page so that
keyboard and screen-reader traversal follows the narrative order, not the order
in which objects happened to be drawn. Decorative shapes and background elements
are removed from the tab order entirely.

**Colour is never the only channel.** A legend is present wherever two or more
series appear. Highlighted marks carry direct labels. Status is encoded in text
as well as in hue — see section 5, which is the strict form of this rule for the
one pair where it is load-bearing.

**Text contrast.** Ink primary on both surfaces exceeds 4.5:1: `#F5F1EC` on
`#131110` measures 16.74:1, and `#F5F1EC` on `#1C1917` measures 15.55:1. Ink
secondary also clears 4.5:1 on both (7.45:1 and 6.92:1), which is why it and not
ink muted carries all running text. Any text placed over poster imagery must be
measured against the image region behind it rather than against the page token,
and gets a scrim if it does not clear 4.5:1.

**The caveat arrives with the claim.** Limitations live in titles and subtitles,
not only in a notes panel or a tooltip. A screen-reader user, who meets the
subtitle immediately after the title, therefore encounters the limitation at the
same moment a sighted reader does. A caveat reachable only by hover is a caveat
that some readers never receive.

---

## 10. Why dark

The honest reasoning, in order of weight.

The subject is cinema. A darkened room is the medium's own condition, and a dark
surface puts the reader in it without needing an illustration to say so.

A dark surface lets the gold accent carry focus with very little ink. On a light
page, drawing the eye to one mark usually means adding something — weight, size,
a box, an arrow. On `#131110`, a single `#C98500` mark among quiet ones is
already the brightest thing on the page. That is the mechanism the whole report
relies on: five pages that each have one thing to look at first, achieved by
restraint rather than by decoration.

The palette was selected for the dark surface, not inverted from a light one.
Every value in sections 3 and 4 was validated in dark mode against `#131110` and
`#1C1917`. This matters because inversion does not preserve the properties that
make a palette work: a hue that sits correctly in the light-mode lightness band
lands outside the dark-mode band, and a colour that separates cleanly on white
can collapse toward its neighbour on near-black.

The cost is real, and it is paid in the typography. Dark surfaces demand more
care with thin type: light strokes on a dark ground bloom slightly, and small
light text loses legibility faster than small dark text does. That is why nothing
in this report is set below 10pt, and why ink secondary at roughly 7:1 rather
than ink muted at roughly 3.7:1 carries all running text. The dark surface is
worth those two constraints. It would not be worth ignoring them.
