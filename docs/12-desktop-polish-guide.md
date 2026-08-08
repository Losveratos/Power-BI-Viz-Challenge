# Desktop polish guide

The generated report is structurally complete, rule-compliant and validated —
but it was authored blind, and the last 10% is judgement by eye: decluttering,
explicit measures, colour ramps, image sizing. That work belongs in Power BI
Desktop, and this guide is the worklist for it.

**Work on your extracted Desktop folder** (`Desktop\MovieSuccess`). From this
point that folder is the source of truth for the submission; manual edits there
are not known to the repo's generators, and that is fine — the deliverable is
the `.pbix`, not the generator. Keep a copy of the folder before big changes.

Every instruction gives the Desktop click path. German UI names in brackets
where they differ.

---

## 0 · Guardrails — keep these intact while polishing

These are the rule- and score-critical properties. Everything else is fair game.

| Keep | Why |
|---|---|
| The Key Takeaway box on page 1, at 50 words or fewer | Hard submission requirement. Current text is 46 words — if you reword it, count again. |
| 5 pages maximum | Hard rule. Hidden tooltip pages would be allowed, ordinary hidden pages count. |
| The caveat panels and page footers | Responsible Data Use is a scored criterion; the caveats sitting next to the charts they qualify is the entry's core argument. |
| Alt text on every data visual | If you change what a chart shows, update its alt text: **Format visual → General → Alt text** (Alternativtext). It should state the finding, not the chart type. |
| Tab order after moving/adding visuals | **View → Selection pane → Tab order** (Ansicht → Auswahl → Tabulatorreihenfolge). Narrative order, Key Takeaway first on page 1. |
| No external anything | No images from other sites (the TMDB posters via the dataset's own Poster Path are explicitly allowed), no extra data, no scraped anything. |

---

## 1 · Declutter the axes

You are right that there is too much ink. The band and rating charts carry
direct data labels, so their value axes are redundant.

**On the four band/rating column charts** (pages 3 and 4):

1. **Format visual → Y-axis → Values: Off** (Y-Achse → Werte: Aus). The data
   labels already state the numbers.
2. While there: **Y-axis → Title: Off** if it came on, and
   **Gridlines: Off** — with labels on the bars, gridlines earn nothing.
3. **X-axis → Title: Off** — the visual title already says what the bands are.
4. If category labels crowd: **X-axis → Values → Max area** up, or rotate off
   by widening the visual instead of shrinking the font. Never below 9pt.

**On the genre bar chart** (page 4): same treatment — data labels on, value
axis off.

**On the scatter** (page 3) the axes must STAY, because log scales are
unreadable without them. Instead make them minimal:

- **X-axis / Y-axis → Values**: keep, 9–10pt, the muted grey `#78716B`.
- **Axis titles: On**, but they will show raw field names — fix that with the
  explicit measures in section 2, then the titles read cleanly.
- Reduce tick density if Desktop overcrowds: X-axis → Range, set explicit
  min/max (e.g. 10,000 to 1,000,000,000).

**Tables**: no axes, but check **Format → Grid → Row padding** ~6px and turn
off anything Desktop re-enabled (totals should be off).

---

## 2 · Explicit measures instead of implicit aggregations

Correct instinct. The scatter and the leaderboard value columns currently use
implicit `Sum of Budget` / `Sum of Revenue` / `Sum of Vote Average` — they
work, but they surface ugly auto-names in tooltips and field lists, and an
average hidden behind a Sum on a deduplicated title is sloppy modelling.

Create these in the `_Measures` table (**Model view → right-click `_Measures`
→ New measure**, then set the format string in Measure tools):

```dax
Total Budget = SUM ( Movies[Budget] )
```
Format: `$#,0` · Description: *Sum of production budgets in the current
context. Nominal dollars.*

```dax
Total Revenue = SUM ( Movies[Revenue] )
```
Format: `$#,0`

```dax
Rating (mean) = AVERAGE ( Movies[Vote Average] )
```
Format: `0.0` · Note: mean, not median, deliberately — as a scatter SIZE
input a mean is fine; every headline claim in the prose stays median-based.

Then **rebind the scatter** (page 3): select it, and in the field wells drag
`Total Budget` onto X (replacing Sum of Budget), `Total Revenue` onto Y,
`Rating (mean)` onto Size. The axis titles now read the measure names.

**Leaderboard tables** (page 2): the `Value` column shows as "Sum of Value".
Double-click the field in the well ("Werte") and rename per table — that
renames only within that visual:

| Table | Rename to |
|---|---|
| Biggest box office | `Box office` |
| Biggest gross profit | `Gross profit` |
| Biggest return on budget | `Return on budget` |
| Highest audience rating | `Audience rating` |

**Funnel visuals** (pages 1 and 5): rename `Sum of Films` to `Films` the same
way.

**Model hygiene while you are in Model view** (judges do open the model):

- Hide: `Movies[Movie ID]`, both columns of all three bridge tables,
  `Movies[Poster Path]`, `Movies[Backdrop Path]`, `Movies[Homepage]`.
  (The sort columns are already hidden.)
- Set **Summarization: Don't summarize** (Nicht zusammenfassen) on
  `Movies[Budget]`, `Movies[Revenue]`, `Movies[Gross Profit]` once the
  explicit measures exist — implicit sums then stop being offered.
- Spot-check the measure descriptions survived: hover any measure — the
  tooltip should show the documentation sentence.

---

## 3 · Scatter fine-tuning

- **Log scale**: Format → X-axis → **Scale type: Log** (Skalierungstyp:
  Logarithmisch), same for Y-axis. The generator requested it, but the
  property was unverifiable — check it stuck. Without log, the blockbusters
  crush the cloud into the corner.
- **Markers**: Format → Markers → Size range min **3**, max **16**; Shape
  circle. If the cloud is too dense: marker **Transparency 15–25%**.
- **Tooltips**: drag `Movies[ROI]`, `Movies[Vote Count]` and `Movies[Era]`
  into the Tooltips well, so a hover answers everything at once.
- **Legend**: keep. It is the CVD-safe channel for the red/green pair.
- Optional wow, test before keeping: drag `Movies[Era]` into **Play axis** —
  the market animates through five eras. If it stutters or distracts, drop it.

---

## 4 · Gold ramp on the rating bands (known gap)

The two rating-band charts (page 4) draw in a single gold. The design system
specifies a six-step ordinal ramp — per-category colours were too brittle to
author blind, so this was left for Desktop (documented as risk #3 in
`08-build-and-submit.md`).

Select the chart → **Format → Columns → Colors** → turn **Show all** on, then
assign per band, dark to light = low to high rating:

| Band | Hex |
|---|---|
| Below 5.0 | `#6B4A00` |
| 5.0 to 6.0 | `#8A6100` |
| 6.0 to 6.5 | `#A87700` |
| 6.5 to 7.0 | `#C98500` |
| 7.0 to 7.5 | `#DFA234` |
| 7.5 and above | `#F0C260` |

Apply to **both** rating charts so the encoding is consistent. The ramp is
validated (monotone lightness, visible step gaps) — see
`04-design-system.md`.

---

## 5 · Tables

- **Posters** (page 2): Format → **Image size → Height** ~**48–56px**
  (Bildgröße). If a poster cell is empty, that film has no Poster Path in the
  dataset — leave it, do not fetch a substitute image.
- **Studios table** (page 4): confirm it sorts by `Median Return (studios)`
  descending (click the column header if not). Optional: **Format → Cell
  elements → Data bars** on the Break-even Rate column, bar colour `#199E70` —
  one extra encoding, cheap and legible.
- Column widths: with `autoSizeColumnWidth` on they self-fit; drag the Film
  column wider if titles truncate.

---

## 6 · Reference lines

The 2.5x break-even line is the report's most important threshold. Verify it
renders **with its label** on page 3's return chart and page 4's rating chart.
If missing: select chart → **Analytics pane** (magnifier icon) → **Y-axis
constant line** → value `2.5`, colour `#78716B`, style Dashed, **Data label:
On**, Name `2.5x break-even`, label colour `#A8A29B`.

---

## 7 · Slicers

- Check the dropdowns render dark. If Desktop restyled them: Format →
  **Values** → font `#F5F1EC` on `#1C1917`; **Slicer header** → `#A8A29B`.
- Genre slicer: multi-select stays on (Ctrl-click); that is fine.
- **Edit interactions** (Format → Interaktionen bearbeiten): slicers should
  filter every chart on their page — default is correct. Decide whether a
  click on a scatter point should cross-filter the band charts; keeping it is
  a feature (click a dot, see its band highlighted).

---

## 8 · After every editing session

1. **Accessibility checker** — Optimize/View ribbon → Accessibility checker,
   clear anything new.
2. **Tab order** — if you moved or added a visual, re-check it.
3. **Alt text** — if a chart's content changed, its alt text is now wrong;
   update it in the same edit.
4. Look at every page at 100% on a 16:9 screen for clipped text.
5. Save. The folder is your working copy — commit it nowhere, it is fine.

---

## 9 · Submit (deadline: August 9)

1. Numbers still right? Movies 85,394 · measured 7,733 · median 1.96x ·
   break-even 41.4% · overlap 0.
2. **File → Save as → Power BI file (.pbix)** — outside the project folder.
3. Screenshot page 1 (Key Takeaway legible) as the gallery image; the scatter
   on page 3 makes a strong second image.
4. [Contests gallery](https://community.fabric.microsoft.com/t5/Contests-Gallery/bd-p/pbi_contestsgallery)
   → Submit to contest → image + description (ready in
   [`11-submission-description.md`](11-submission-description.md)) + the
   `.pbix` → tag **`World Champs BCN`**.

---

## If something breaks while editing

The generated JSON/TMDL is plain text. If Desktop refuses to reopen the
project after a crash mid-save, the pristine generated state is always
recoverable from the repo (`src/pbip/` + the bundled-data build steps in
`08-build-and-submit.md`) — you lose only your manual polish, which is why
step 8.5 says save often and copy the folder before big changes.
