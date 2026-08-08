"""Generate the PBIR report definition for the Power BI Project (PBIP).

Why generated rather than dragged onto a canvas
-----------------------------------------------
The report layer of a modern .pbix is PBIR: one JSON file per visual. Writing
those files from a script buys three things that matter for this entry.

1.  Every visual is positioned on one grid, computed from one set of layout
    constants, so alignment is exact rather than approximately exact.
2.  Alt text and tab order cannot be forgotten. `add_visual` refuses a visual
    that has no alt text, which turns an accessibility requirement into a build
    error instead of a review note.
3.  The report is reproducible. Re-running the script reproduces the report
    byte-for-byte, and a diff shows a real design change rather than a stray
    two-pixel drag.

The grammar used here was learned from the official starter .pbix, which already
ships in PBIR form — schema versions, property shapes and the query-projection
structure are copied from files Power BI Desktop itself wrote.

Usage
-----
    python analysis/06_build_report.py
"""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PBIP = REPO / "src" / "pbip"
REPORT = PBIP / "MovieSuccess.Report"
DEFN = REPORT / "definition"
THEME_SOURCE = REPO / "assets" / "theme" / "movie-success-dark.json"


def _theme_name() -> str:
    """Theme filename with a content-derived suffix.

    Power BI Desktop caches a registered theme by filename, so an edited theme
    under the same name can keep serving the old one. Deriving the suffix from
    the file's own contents means it changes exactly when the theme changes,
    and not on every build.
    """
    import hashlib
    digest = hashlib.sha256(THEME_SOURCE.read_bytes()).hexdigest()[:8]
    return f"movie-success-dark-{digest}"

# Schema versions, taken from the official starter file so that Desktop reads
# exactly the shapes it wrote.
S_REPORT = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.3.0/schema.json"
S_VERSION = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json"
S_PAGES = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json"
S_PAGE = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"
S_VISUAL = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.11.0/schema.json"

NAMESPACE = uuid.UUID("2c9f7b41-8e60-4d3a-95cf-71a8b0e64d22")

# ---- design tokens (mirror docs/04-design-system.md) ----------------------- #
PAGE_BG = "#131110"
CARD_BG = "#1C1917"
HAIRLINE = "#2E2A27"
INK = "#F5F1EC"
INK_2 = "#A8A29B"
INK_3 = "#78716B"
GOLD = "#C98500"
BLUE = "#3987E5"
RED = "#E66767"
GREEN = "#199E70"
VIOLET = "#9085E9"

FONT = "Segoe UI"
FONT_SB = "Segoe UI Semibold"

# ---- layout grid ---------------------------------------------------------- #
W, H = 1920, 1080
MARGIN = 48
CONTENT_W = W - 2 * MARGIN          # 1824
GUTTER = 24
COL = (CONTENT_W - 11 * GUTTER) // 12   # 130px per column


def cols(n: int) -> int:
    """Width of n grid columns including the gutters between them."""
    return n * COL + (n - 1) * GUTTER


def col_x(i: int) -> int:
    """Left edge of column i (0-based)."""
    return MARGIN + i * (COL + GUTTER)


ATTRIBUTION = (
    "Movie data sourced from TMDB and distributed via Kaggle under the Open Data "
    "Commons Attribution License (ODC-By 1.0). Figures cover only the 7,733 films "
    "this dataset can measure. Dollars are nominal and are never compared across eras."
)


def vid(*parts: str) -> str:
    """Deterministic 20-hex-character visual/page id, as Desktop generates."""
    return uuid.uuid5(NAMESPACE, "|".join(parts)).hex[:20]


# --------------------------------------------------------------------------- #
# Expression helpers                                                           #
# --------------------------------------------------------------------------- #

def lit(value: str) -> dict:
    return {"expr": {"Literal": {"Value": value}}}


def slit(text: str) -> dict:
    """A string literal, which PBIR wraps in single quotes."""
    return lit("'" + text.replace("'", "''") + "'")


def num(value: float, suffix: str = "D") -> dict:
    return lit(f"{value}{suffix}")


def color(hex_value: str) -> dict:
    return {"solid": {"color": lit(f"'{hex_value}'")}}


def column_field(entity: str, prop: str) -> dict:
    return {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}


def measure_field(prop: str, entity: str = "_Measures") -> dict:
    return {"Measure": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}


def sum_field(entity: str, prop: str) -> dict:
    return {
        "Aggregation": {
            "Expression": {"Column": {"Expression": {"SourceRef": {"Entity": entity}},
                                      "Property": prop}},
            "Function": 0,
        }
    }


def proj_column(entity: str, prop: str, active: bool | None = None) -> dict:
    out = {"field": column_field(entity, prop), "queryRef": f"{entity}.{prop}",
           "nativeQueryRef": prop}
    if active is not None:
        out["active"] = active
    return out


def proj_measure(prop: str, entity: str = "_Measures") -> dict:
    return {"field": measure_field(prop, entity), "queryRef": f"{entity}.{prop}",
            "nativeQueryRef": prop}


def proj_sum(entity: str, prop: str) -> dict:
    # nativeQueryRef must be "Sum of <Column>" for an aggregation projection.
    # The bare column name yields a blank visual with no error message.
    return {"field": sum_field(entity, prop), "queryRef": f"Sum({entity}.{prop})",
            "nativeQueryRef": f"Sum of {prop}"}


# --------------------------------------------------------------------------- #
# Visual builders                                                              #
# --------------------------------------------------------------------------- #

class Page:
    def __init__(self, key: str, display_name: str, caveat: str):
        self.key = key
        self.name = vid("page", key)
        self.display_name = display_name
        self.caveat = caveat
        self.visuals: list[dict] = []
        self._z = 100
        self._tab = 0

    def next_z(self) -> int:
        self._z += 10
        return self._z

    def next_tab(self) -> int:
        self._tab += 100
        return self._tab

    def add(self, visual: dict) -> None:
        self.visuals.append(visual)


def container(page: Page, key: str, x: int, y: int, w: int, h: int,
              visual: dict, *, alt: str | None, tab: int | None = None,
              z: int | None = None) -> dict:
    """Wrap a visual body in a positioned container.

    Alt text is mandatory for anything that carries information. Decorative
    shapes pass alt=None and are given a negative tab order so the keyboard
    skips them entirely, which is the correct treatment for decoration.
    """
    decorative = alt is None
    if not decorative and not alt.strip():
        raise ValueError(f"visual {key} on page {page.key} has empty alt text")

    body = dict(visual)
    if not decorative:
        vco = body.setdefault("visualContainerObjects", {})
        general = vco.setdefault("general", [{}])
        general[0].setdefault("properties", {})["altText"] = slit(alt)

    return {
        "$schema": S_VISUAL,
        "name": vid("visual", page.key, key),
        "position": {
            "x": x, "y": y, "z": z if z is not None else page.next_z(),
            "width": w, "height": h,
            "tabOrder": -1000 if decorative else (tab if tab is not None else page.next_tab()),
        },
        "visual": body,
    }


def text_runs(runs: list[tuple[str, dict]]) -> list[dict]:
    out = []
    for value, style in runs:
        out.append({"value": value, "textStyle": style})
    return out


def style(size: int, *, bold: bool = False, colour: str = INK,
          italic: bool = False) -> dict:
    out = {
        "fontFamily": FONT_SB if bold else FONT,
        "fontSize": f"{size}pt",
        "color": colour,
    }
    if bold:
        out["fontWeight"] = "bold"
    if italic:
        out["fontStyle"] = "italic"
    return out


def textbox(page: Page, key: str, x: int, y: int, w: int, h: int,
            paragraphs: list[list[tuple[str, dict]]], *, alt: str | None,
            tab: int | None = None) -> dict:
    body = {
        "visualType": "textbox",
        "objects": {
            "general": [
                {"properties": {"paragraphs": [
                    {"textRuns": text_runs(runs)} for runs in paragraphs
                ]}}
            ]
        },
        "drillFilterOtherVisuals": True,
    }
    return container(page, key, x, y, w, h, body, alt=alt, tab=tab)


def panel(page: Page, key: str, x: int, y: int, w: int, h: int, *,
          fill: str = CARD_BG, radius: int = 6, z: int | None = None) -> dict:
    """A decorative rounded rectangle used as a card surface."""
    body = {
        "visualType": "shape",
        "objects": {
            "shape": [{"properties": {
                "tileShape": lit("'rectangleRounded'"),
                "rectangleRoundedCurve": lit(f"{radius}L"),
            }}],
            "fill": [{"properties": {"fillColor": color(fill),
                                      "transparency": num(0)},
                      "selector": {"id": "default"}}],
            "outline": [{"properties": {"show": lit("false")}}],
            "text": [{"properties": {"show": lit("false")}}],
        },
        "drillFilterOtherVisuals": True,
    }
    return container(page, key, x, y, w, h, body, alt=None, z=z)


def card(page: Page, key: str, x: int, y: int, w: int, h: int, *,
         measure: str, label: str, alt: str, value_size: int = 40) -> dict:
    """A KPI tile.

    `cardVisual`, not the legacy `card`. The legacy visual is deprecated and,
    more importantly, neither type accepts a `Values` query role — `cardVisual`
    binds its measures to `Data`. Getting that wrong renders an empty tile with
    no error. Its formatting objects are `value`/`label`/`outline`, each
    requiring the default id selector, and background/border belong to the
    container rather than the visual.
    """
    default = {"id": "default"}
    body = {
        "visualType": "cardVisual",
        "query": {"queryState": {"Data": {"projections": [proj_measure(measure)]}}},
        "objects": {
            "value": [{"properties": {
                "fontColor": color(INK), "fontSize": num(value_size),
                "fontFamily": lit(f"'{FONT_SB}'"),
            }, "selector": default}],
            # The measure name would only repeat the container title, which
            # carries the human-readable label instead.
            "label": [{"properties": {"show": lit("false")}, "selector": default}],
            "outline": [{"properties": {"show": lit("false")}, "selector": default}],
        },
        "visualContainerObjects": {
            "title": [{"properties": {
                "show": lit("true"), "text": slit(label),
                "fontFamily": lit(f"'{FONT}'"), "fontSize": num(11),
                "fontColor": color(INK_2), "alignment": lit("'left'"),
                "titleWrap": lit("true"),
            }}],
            "background": [{"properties": {"show": lit("true"), "color": color(CARD_BG),
                                           "transparency": num(0)}}],
            "border": [{"properties": {"show": lit("true"), "color": color(HAIRLINE),
                                       "radius": num(6)}}],
            "padding": [{"properties": {"left": num(14), "right": num(14),
                                        "top": num(10), "bottom": num(10)}}],
            "visualHeader": [{"properties": {"show": lit("false")}}],
        },
        "drillFilterOtherVisuals": True,
    }
    return container(page, key, x, y, w, h, body, alt=alt)


def _chart_common(title: str, subtitle: str | None) -> dict:
    vco = {
        "title": [{"properties": {
            "show": lit("true"), "text": slit(title),
            "fontFamily": lit(f"'{FONT_SB}'"), "fontSize": num(13),
            "fontColor": color(INK), "alignment": lit("'left'"),
            "titleWrap": lit("true"),
        }}],
        "background": [{"properties": {"show": lit("true"), "color": color(CARD_BG),
                                       "transparency": num(0)}}],
        "border": [{"properties": {"show": lit("true"), "color": color(HAIRLINE),
                                   "radius": num(6)}}],
        "padding": [{"properties": {"left": num(12), "right": num(12),
                                    "top": num(8), "bottom": num(8)}}],
        # background, border, padding and visualHeader must be set together:
        # a partial visualContainerObjects block makes Power BI reset the
        # properties it does not find back to system defaults.
        "visualHeader": [{"properties": {"show": lit("false")}}],
    }
    if subtitle:
        vco["subTitle"] = [{"properties": {
            "show": lit("true"), "text": slit(subtitle),
            "fontFamily": lit(f"'{FONT}'"), "fontSize": num(10),
            "fontColor": color(INK_2), "alignment": lit("'left'"),
            "titleWrap": lit("true"),
        }}]
    return vco


def _axis_objects(*, value_labels: bool, series_colour: str) -> dict:
    objects: dict = {
        "categoryAxis": [{"properties": {
            "show": lit("true"), "showAxisTitle": lit("false"),
            "labelColor": color(INK_2), "fontSize": num(10),
            "fontFamily": lit(f"'{FONT}'"), "gridlineShow": lit("false"),
            "lineColor": color(HAIRLINE),
        }}],
        "valueAxis": [{"properties": {
            "show": lit("true"), "showAxisTitle": lit("false"),
            "labelColor": color(INK_3), "fontSize": num(10),
            "fontFamily": lit(f"'{FONT}'"), "gridlineShow": lit("true"),
            "gridlineColor": color("#262220"), "gridlineThickness": num(1),
        }}],
        # `defaultColor` with NO selector, not `fill` with an id selector.
        # dataPoint accepts only metadata/data selectors, so `fill` with
        # selector {"id": "default"} matches nothing and the marks render
        # invisible while tooltips still show data — a documented failure mode.
        # Safe here only because every chart is single-measure with no Series.
        "dataPoint": [{"properties": {"defaultColor": color(series_colour)}}],
        "legend": [{"properties": {"show": lit("false")}}],
        "plotArea": [{"properties": {"transparency": num(100)}}],
    }
    if value_labels:
        objects["labels"] = [{"properties": {
            "show": lit("true"), "color": color(INK),
            "fontSize": num(10), "fontFamily": lit(f"'{FONT_SB}'"),
        }}]
    else:
        objects["labels"] = [{"properties": {"show": lit("false")}}]
    return objects


def bar_or_column(page: Page, key: str, x: int, y: int, w: int, h: int, *,
                  visual_type: str, category: dict, value: dict,
                  title: str, subtitle: str | None, alt: str,
                  series_colour: str = GOLD, value_labels: bool = True,
                  sort_desc_by_value: bool = False,
                  reference_line: tuple[float, str] | None = None) -> dict:
    # Every documented cartesian example sets active on the Category
    # projection; it records the drill state. Deliberately not applied to
    # tableEx, where `active` triggers drill behaviour and hides columns.
    category = {**category, "active": True}
    query: dict = {"queryState": {
        "Category": {"projections": [category]},
        "Y": {"projections": [value]},
    }}
    if sort_desc_by_value:
        query["sortDefinition"] = {
            "sort": [{"field": value["field"], "direction": "Descending"}],
            # false marks the sort as user-explicit. With true, Power BI is
            # free to replace it with the visual type's default order, which
            # would silently undo a chart sorted by value on purpose.
            "isDefaultSort": False,
        }

    objects = _axis_objects(value_labels=value_labels, series_colour=series_colour)
    if reference_line:
        line_value, line_label = reference_line
        objects["y1AxisReferenceLine"] = [{
            "properties": {
                "show": lit("true"),
                "value": num(line_value),
                "lineColor": color(INK_3),
                "style": lit("'dashed'"),
                "transparency": num(20),
                "dataLabelShow": lit("true"),
                "dataLabelText": lit("'Name'"),
                "dataLabelColor": color(INK_2),
                "dataLabelHorizontalPosition": lit("'right'"),
                "dataLabelVerticalPosition": lit("'above'"),
                "displayName": slit(line_label),
            },
            "selector": {"id": "breakEven"},
        }]

    body = {
        "visualType": visual_type,
        "query": query,
        "objects": objects,
        "visualContainerObjects": _chart_common(title, subtitle),
        "drillFilterOtherVisuals": True,
    }
    return container(page, key, x, y, w, h, body, alt=alt)


def table(page: Page, key: str, x: int, y: int, w: int, h: int, *,
          projections: list[dict], title: str, subtitle: str | None, alt: str,
          sort: tuple[dict, str] | None = None,
          column_widths: list[float] | None = None) -> dict:
    query: dict = {"queryState": {"Values": {"projections": projections}}}
    if sort:
        field, direction = sort
        query["sortDefinition"] = {"sort": [{"field": field, "direction": direction}],
                                   "isDefaultSort": False}
    body = {
        "visualType": "tableEx",
        "query": query,
        "objects": {
            "grid": [{"properties": {
                "gridVertical": lit("false"), "gridHorizontal": lit("true"),
                "gridHorizontalColor": color(HAIRLINE),
                "outlineColor": color(HAIRLINE), "rowPadding": num(6, "L"),
            }}],
            "columnHeaders": [{"properties": {
                "fontColor": color(INK_2), "backColor": color(CARD_BG),
                "fontSize": num(10), "fontFamily": lit(f"'{FONT_SB}'"),
                "outline": lit("'BottomOnly'"), "wordWrap": lit("true"),
                # Without these two, columns shrink-wrap their content.
                "autoSizeColumnWidth": lit("true"),
                "columnAdjustment": lit("'growToFit'"),
            }}],
            # tableEx has no `fontColor` on values, and `backColor` is the
            # conditional-formatting slot. Static row colours must use the
            # Primary/Secondary pair or they are silently ignored.
            "values": [{"properties": {
                "fontColorPrimary": color(INK), "fontColorSecondary": color(INK),
                "backColorPrimary": color(CARD_BG),
                "backColorSecondary": color(CARD_BG),
                "fontSize": num(10), "fontFamily": lit(f"'{FONT}'"),
                "wordWrap": lit("true"),
            }}],
            "total": [{"properties": {"totals": lit("false")}}],
        },
        "visualContainerObjects": {
            **_chart_common(title, subtitle),
            # The default table style preset sets its own row background and
            # would quietly overrule every colour set above. Turning it off is
            # the documented fix for light rows in a dark report.
            "stylePreset": [{"properties": {"name": lit("'None'")}}],
        },
        "drillFilterOtherVisuals": True,
    }
    return container(page, key, x, y, w, h, body, alt=alt)


# --------------------------------------------------------------------------- #
# Shared page furniture                                                        #
# --------------------------------------------------------------------------- #

def add_header(page: Page, title: str, standfirst: str, *, page_number: int) -> None:
    page.add(panel(page, "accent", MARGIN, 48, 72, 4, fill=GOLD, radius=0, z=10))
    page.add(textbox(
        page, "title", MARGIN, 62, cols(9), 56,
        [[(title, style(32, bold=True))]],
        alt=f"Report page {page_number} of 5. Section heading: {title}.",
    ))
    page.add(textbox(
        page, "standfirst", MARGIN, 122, cols(10), 40,
        [[(standfirst, style(15, colour=INK_2))]],
        alt=f"Standfirst for page {page_number}: {standfirst}",
    ))
    page.add(textbox(
        page, "pagenum", col_x(11) - 40, 62, COL + 40, 40,
        [[(f"{page_number} / 5", style(15, bold=True, colour=INK_3))]],
        alt=None,
    ))


def add_footer(page: Page) -> None:
    page.add(panel(page, "footrule", MARGIN, 1006, CONTENT_W, 1,
                   fill=HAIRLINE, radius=0, z=20))
    page.add(textbox(
        page, "footer", MARGIN, 1016, CONTENT_W, 48,
        [[(page.caveat + "  ", style(10, bold=True, colour=INK_2)),
          (ATTRIBUTION, style(10, colour=INK_3))]],
        alt=None,
    ))


# --------------------------------------------------------------------------- #
# The five pages                                                               #
# --------------------------------------------------------------------------- #

# The round caps this at 50 words and 07_validate_pbip.py enforces the count, so
# the wording is kept a few words clear of the limit. An em dash reads as a word
# to a strict counter, which is why the margin is deliberate rather than tight.
KEY_TAKEAWAY = (
    "Bigger budgets buy bigger box office, not better payback. What consistently "
    "pays is being liked: films rated 7 or above return about twice as much per "
    "dollar, in every budget class and every era. One caveat — this data can "
    "measure only 0.8% of its films."
)


def page_one() -> Page:
    page = Page("answer", "1 · The Answer",
                "Scope: 7,733 films of roughly 930,000.")
    add_header(
        page,
        "What Makes a Movie Successful?",
        "Round 3 · Lights, Camera, Insight — one honest answer, and the 99.2% of "
        "this dataset that cannot give one.",
        page_number=1,
    )

    # ---- Key Takeaway: the round's one hard content requirement -------------
    page.add(panel(page, "kt-bg", MARGIN, 180, CONTENT_W, 188, z=30))
    page.add(panel(page, "kt-rule", MARGIN, 180, 5, 188, fill=GOLD, radius=0, z=40))
    page.add(textbox(
        page, "kt", MARGIN + 28, 198, CONTENT_W - 56, 156,
        [
            [("KEY TAKEAWAY", style(11, bold=True, colour=GOLD))],
            [(KEY_TAKEAWAY, style(19, colour=INK))],
        ],
        alt="Key takeaway of the whole report. " + KEY_TAKEAWAY,
        tab=10,
    ))

    # ---- Four scope figures ------------------------------------------------
    kpis = [
        ("kpi-films", "Films Measured Overall", "Films this report can measure",
         "Of the roughly 930,000 films in the published dataset, 7,733 clear every "
         "quality gate and can carry a financial claim."),
        ("kpi-share", "Share Of Source Measurable", "Share of the published dataset",
         "The measurable films are 0.8% of the published dataset. Ninety-nine "
         "percent of the data cannot answer this question."),
        ("kpi-return", "Median Return", "Median return on budget",
         "The median measurable film grossed 1.96 times its production budget."),
        ("kpi-be", "Break-even Rate", "Share clearing 2.5x break-even",
         "Only 41.4% of measurable films grossed at least 2.5 times their budget, "
         "the rule-of-thumb point where a theatrical release breaks even."),
    ]
    for i, (key, measure_name, label, alt) in enumerate(kpis):
        page.add(card(page, key, col_x(i * 3), 396, cols(3), 168,
                      measure=measure_name, label=label, alt=alt))

    # ---- The funnel --------------------------------------------------------
    page.add(bar_or_column(
        page, "funnel", MARGIN, 592, cols(8), 388,
        visual_type="clusteredBarChart",
        category=proj_column("Funnel", "Step"),
        value=proj_sum("Funnel", "Films"),
        title="From roughly 930,000 films to 7,733",
        subtitle="Films surviving each step. The scale is deliberately linear: the "
                 "slice this report can actually measure is almost invisible next to "
                 "the dataset it came from.",
        alt="Horizontal bar chart of the inclusion funnel. The published dataset of "
            "about 930,000 films falls to 85,394 once the starter file keeps only "
            "films with a budget above zero, then to 79,222 released films, 56,072 "
            "with a release date, 28,193 with a credible budget, 10,219 that report "
            "revenue, and finally 7,733 with at least 50 ratings. On a linear scale "
            "the final bar is barely visible.",
        series_colour=GOLD,
        value_labels=True,
    ))

    page.add(panel(page, "guide-bg", col_x(8), 592, cols(4), 388, z=50))
    page.add(textbox(
        page, "guide", col_x(8) + 20, 610, cols(4) - 40, 352,
        [
            [("HOW TO READ THIS REPORT", style(11, bold=True, colour=GOLD))],
            [("1 · The Answer", style(11, bold=True)),
             ("  what the data supports, and how little of it there is.",
              style(11, colour=INK_2))],
            [("2 · Success Has Four Answers", style(11, bold=True)),
             ("  four defensible definitions, and how little they agree.",
              style(11, colour=INK_2))],
            [("3 · What Money Buys", style(11, bold=True)),
             ("  budget buys box office; it does not buy return.",
              style(11, colour=INK_2))],
            [("4 · What Actually Pays", style(11, bold=True)),
             ("  the one signal that holds in every budget class and era.",
              style(11, colour=INK_2))],
            [("5 · What We Cannot Know", style(11, bold=True)),
             ("  the gaps, the assumptions, and what would change our mind.",
              style(11, colour=INK_2))],
            [("", style(10))],
            [("Every page carries its own caveat in the footer. Every dollar figure "
              "is a median of nominal dollars within a single era, never a mean and "
              "never across eras.", style(10, colour=INK_3))],
        ],
        alt="Reading guide. Page 1 states what the data supports and how little of "
            "it there is. Page 2 shows four definitions of success and how little "
            "they agree. Page 3 shows that budget buys box office but not return. "
            "Page 4 identifies the one signal that holds across budget classes and "
            "eras. Page 5 lists the gaps and assumptions. Every page footer carries "
            "its own caveat.",
    ))

    add_footer(page)
    return page


def page_two() -> Page:
    page = Page("definitions", "2 · Success Has Four Answers",
                "Same 7,733 films, four rankings.")
    add_header(
        page,
        "Success Has Four Answers",
        "Before measuring success you have to choose what it means — and the "
        "choice decides the winner.",
        page_number=2,
    )

    page.add(panel(page, "lede-bg", MARGIN, 180, CONTENT_W, 96, z=30))
    page.add(textbox(
        page, "lede", MARGIN + 24, 194, CONTENT_W - 48, 70,
        [
            [("Rank the same 7,733 films four defensible ways and you get four "
              "different films at the top. Box office and return on budget share "
              "nothing at all: not one film in the top hundred by gross revenue "
              "also appears in the top hundred by return. Gross profit, by "
              "contrast, is almost a copy of gross revenue — it adds a number, not "
              "an insight.", style(13, colour=INK))],
        ],
        alt="Ranking the same 7,733 films four defensible ways produces four "
            "different sets of winners. No film appears in both the top 100 by "
            "gross revenue and the top 100 by return on budget. Gross profit is "
            "almost identical to gross revenue.",
        tab=10,
    ))

    overlaps = [
        ("ov-return", "Top 100 Overlap Box Office And Return",
         "Films in the top 100 by BOTH box office and return",
         "Zero films appear in both the top 100 by gross revenue and the top 100 by "
         "return on budget. The two definitions of success have no winners in common."),
        ("ov-acclaim", "Top 100 Overlap Box Office And Acclaim",
         "Films in the top 100 by BOTH box office and rating",
         "Only a handful of films appear in both the top 100 by gross revenue and "
         "the top 100 by audience rating."),
        ("ov-profit", "Top 100 Overlap Box Office And Profit",
         "Films in the top 100 by BOTH box office and gross profit",
         "Almost every film in the top 100 by gross revenue is also in the top 100 "
         "by gross profit, which is why this report does not treat them as two "
         "separate definitions."),
    ]
    for i, (key, measure_name, label, alt) in enumerate(overlaps):
        page.add(card(page, key, col_x(i * 3), 292, cols(3), 128,
                      measure=measure_name, label=label, alt=alt, value_size=34))

    page.add(panel(page, "choice-bg", col_x(9), 292, cols(3), 128, z=40))
    page.add(textbox(
        page, "choice", col_x(9) + 18, 306, cols(3) - 36, 104,
        [
            [("OUR DEFINITION", style(10, bold=True, colour=GOLD))],
            [("Return on production budget, judged against a 2.5x gross "
              "break-even. It rewards performance rather than size — and it "
              "systematically favours cheap films, which page 3 discloses.",
              style(10, colour=INK_2))],
        ],
        alt="This report defines success as return on production budget judged "
            "against a 2.5 times gross break-even multiple, because it rewards "
            "performance rather than size. The tradeoff is that it favours cheap "
            "films, which page 3 discloses.",
    ))

    leaderboards = [
        ("lb-box", "Top By Box Office", "Biggest box office", BLUE,
         "Ranked by gross revenue in nominal dollars.",
         "Top ten films by gross revenue. Nominal dollars, not inflation adjusted."),
        ("lb-profit", "Top By Gross Profit", "Biggest gross profit", BLUE,
         "Revenue minus budget. Almost the same list as box office.",
         "Top ten films by gross revenue minus production budget. The list is "
         "almost identical to the box-office ranking."),
        ("lb-return", "Top By Return", "Biggest return on budget", GOLD,
         "Revenue divided by budget. Cheap films dominate — read page 3 first.",
         "Top ten films by revenue divided by budget. The list is dominated by "
         "very cheap films, which is a known bias of the measure and is discussed "
         "on page 3."),
        ("lb-acclaim", "Top By Acclaim", "Highest audience rating", VIOLET,
         "Average rating out of 10, minimum 50 votes.",
         "Top ten films by average audience rating out of ten, among films with at "
         "least fifty ratings."),
    ]
    for i, (key, entity, title, accent, subtitle, alt) in enumerate(leaderboards):
        page.add(table(
            page, key, col_x(i * 3), 436, cols(3), 476,
            projections=[
                proj_column(entity, "Rank"),
                proj_column(entity, "Film"),
                proj_sum(entity, "Value"),
            ],
            title=title, subtitle=subtitle, alt=alt,
            sort=(column_field(entity, "Rank"), "Ascending"),
        ))

    page.add(textbox(
        page, "closing", MARGIN, 926, CONTENT_W, 72,
        [
            [("So which is right? ", style(13, bold=True, colour=GOLD)),
             ("All four. That is the problem. A ranking is an argument about what "
              "counts, and any report that shows one ranking without naming the "
              "others is making that argument silently. This one names it: the rest "
              "of this report measures return on budget, and page 3 opens by "
              "showing what that choice gets wrong.", style(13, colour=INK))],
        ],
        alt="All four rankings are defensible, which is the problem. A ranking is "
            "an argument about what counts. This report measures return on budget "
            "and page 3 opens by showing what that choice gets wrong.",
    ))

    add_footer(page)
    return page


def page_three() -> Page:
    page = Page("money", "3 · What Money Buys",
                "Caution: cheap films are under-reported. See the panel bottom right.")
    add_header(
        page,
        "What Money Buys",
        "A bigger budget reliably buys a bigger opening. It does not buy a better "
        "return — and the middle of the market is the worst place to stand.",
        page_number=3,
    )

    page.add(bar_or_column(
        page, "revenue-by-band", MARGIN, 188, cols(6), 384,
        visual_type="clusteredColumnChart",
        category=proj_column("Movies", "Budget Band"),
        value=proj_measure("Median Revenue"),
        title="Money does buy box office",
        subtitle="Median gross revenue by production-budget band. Nominal dollars. "
                 "Rank correlation between budget and revenue is +0.68.",
        alt="Column chart of median gross revenue by production-budget band. Median "
            "revenue rises steadily with budget, from about 1.9 million dollars for "
            "films under 1 million to about 379 million dollars for films of 100 "
            "million and above. The rank correlation between budget and revenue is "
            "plus 0.68.",
        series_colour=BLUE,
    ))

    page.add(bar_or_column(
        page, "return-by-band", col_x(6), 188, cols(6), 384,
        visual_type="clusteredColumnChart",
        category=proj_column("Movies", "Budget Band"),
        value=proj_measure("Median Return"),
        title="It does not buy a better return",
        subtitle="Median revenue divided by budget. The curve is a U: the cheapest "
                 "and the most expensive films return most, the middle returns "
                 "least. Rank correlation between budget and return is -0.11.",
        alt="Column chart of median return on budget by production-budget band. The "
            "shape is a U. Films under 1 million dollars return 4.98 times their "
            "budget, the 15 to 30 million band returns only 1.41 times, and films "
            "of 100 million and above return 2.70 times. The rank correlation "
            "between budget and return is minus 0.11, so spending more does not "
            "improve return.",
        series_colour=GOLD,
        reference_line=(2.5, "2.5x break-even"),
    ))

    page.add(bar_or_column(
        page, "breakeven-by-band", MARGIN, 588, cols(6), 392,
        visual_type="clusteredColumnChart",
        category=proj_column("Movies", "Budget Band"),
        value=proj_measure("Break-even Rate"),
        title="The mid-budget film is the one that fails",
        subtitle="Share of films reaching 2.5x their budget. Lowest at $15-30M: "
                 "33.5%. Removing the top 5% of earners in every band leaves the U "
                 "intact, so this is not the work of a few franchises.",
        alt="Column chart of the share of films reaching 2.5 times their budget, by "
            "budget band. The share is 65.8% under 1 million dollars, falls to its "
            "low of 33.5% in the 15 to 30 million band, and recovers to 53.3% for "
            "films of 100 million and above. Removing the highest-earning 5% of "
            "films within each band leaves this U-shape intact.",
        series_colour=GREEN,
    ))

    page.add(panel(page, "warn-bg", col_x(6), 588, cols(6), 392, z=60))
    page.add(panel(page, "warn-rule", col_x(6), 588, 5, 392, fill=RED, radius=0, z=70))
    page.add(textbox(
        page, "warn", col_x(6) + 28, 606, cols(6) - 56, 356,
        [
            [("WHAT IS WRONG WITH THE LEFT-HAND SIDE OF THESE CHARTS",
              style(11, bold=True, colour=RED))],
            [("Cheap films look extraordinary here, and they are partly an "
              "illusion. Revenue reporting is not random: it depends on how big "
              "the film was.", style(12, colour=INK))],
            [("Of films budgeted between $10,000 and $100,000, only 7.8% report any "
              "revenue at all. Of films budgeted above $50M, 91.1% do.",
              style(12, bold=True, colour=INK))],
            [("A cheap film that flopped usually never had its revenue recorded, so "
              "it is absent from every chart on this page. An expensive flop is "
              "recorded and counted. That means the return of the cheapest band is "
              "an upper bound on reality, not an expectation — and it is why this "
              "report does not advise anyone to make cheap films.",
              style(12, colour=INK_2))],
            [("Only 2.4% of films in the $10,000-$100,000 band survive into this "
              "analysis, against 90.8% of films above $50M.",
              style(11, colour=INK_3))],
        ],
        alt="Caution panel. Cheap films look extraordinary on this page partly "
            "because of survivorship bias. Of films budgeted between 10,000 and "
            "100,000 dollars, only 7.8% report any revenue, against 91.1% of films "
            "budgeted above 50 million. Cheap films that flopped were never "
            "recorded, so they are absent from these charts, while expensive flops "
            "are counted. The return figure for the cheapest band is therefore an "
            "upper bound rather than an expectation. Only 2.4% of films in the "
            "10,000 to 100,000 dollar band survive into this analysis, against "
            "90.8% of films above 50 million.",
    ))

    add_footer(page)
    return page


def page_four() -> Page:
    page = Page("merit", "4 · What Actually Pays",
                "Association, not causation. Ratings are collected after release.")
    add_header(
        page,
        "What Actually Pays",
        "One signal survives every control we could apply — and unlike budget, it "
        "does not cost anything.",
        page_number=4,
    )

    page.add(bar_or_column(
        page, "return-by-rating", MARGIN, 188, cols(6), 384,
        visual_type="clusteredColumnChart",
        category=proj_column("Movies", "Rating Band"),
        value=proj_measure("Median Return"),
        title="Being liked pays, and it pays steadily",
        subtitle="Median return on budget by audience-rating band. Every step up "
                 "the rating scale raises the return. The 2.5x line is the "
                 "break-even rule of thumb.",
        alt="Column chart of median return on budget by audience-rating band. "
            "Return rises monotonically with rating: films rated below 5 return "
            "0.73 times their budget, films rated 6.5 to 7 return 2.10 times, and "
            "films rated 7.5 or above return 4.27 times. Only the top two bands sit "
            "above the 2.5 times break-even line.",
        series_colour=GOLD,
        reference_line=(2.5, "2.5x break-even"),
    ))

    page.add(bar_or_column(
        page, "budget-by-rating", col_x(6), 188, cols(6), 384,
        visual_type="clusteredColumnChart",
        category=proj_column("Movies", "Rating Band"),
        value=proj_measure("Median Budget"),
        title="And it does not cost more",
        subtitle="Median production budget by the same rating bands. Budget is flat "
                 "to falling as ratings rise — the best-rated films are the "
                 "cheapest group on the chart.",
        alt="Column chart of median production budget by audience-rating band. "
            "Budget does not rise with rating. The 6.0 to 6.5 band has the highest "
            "median budget at about 19.6 million dollars, while the best-rated band "
            "of 7.5 and above has a median budget of about 12 million. Higher "
            "ratings are not bought with bigger budgets.",
        series_colour=BLUE,
    ))

    page.add(bar_or_column(
        page, "genre", MARGIN, 588, cols(8), 392,
        visual_type="clusteredBarChart",
        category=proj_column("Genres", "Genre"),
        value=proj_measure("Median Return (reliable)"),
        title="Genre matters less than being good",
        subtitle="Median return on budget by genre. Genres with fewer than 100 "
                 "measured films are suppressed rather than ranked on thin "
                 "evidence: TV Movie (4 films) and Documentary (66) are excluded.",
        alt="Horizontal bar chart of median return on budget by genre, sorted "
            "highest first. Animation leads at about 2.44 times, followed by "
            "Family, Horror, Music, Romance, Adventure and Comedy, all between 2.1 "
            "and 2.3 times. History is lowest at about 1.39 times. The spread "
            "between the best and worst genre is narrower than the spread between "
            "the best and worst rating band, which is the point of the chart. "
            "Genres with fewer than 100 measured films are excluded.",
        series_colour=VIOLET,
        sort_desc_by_value=True,
    ))

    page.add(panel(page, "caveat-bg", col_x(8), 588, cols(4), 392, z=60))
    page.add(panel(page, "caveat-rule", col_x(8), 588, 5, 392, fill=GOLD, radius=0, z=70))
    page.add(textbox(
        page, "caveat", col_x(8) + 28, 606, cols(4) - 56, 356,
        [
            [("WHY WE TRUST THIS, AND HOW FAR", style(11, bold=True, colour=GOLD))],
            [("We tried to explain the rating effect away and could not. Films "
              "rated 7.0 or higher out-return the rest in all ten budget deciles "
              "and in all five eras, by a median factor of 2.1x and never by less "
              "than 1.19x. The effect is not cheap films in disguise, and it is not "
              "old films in disguise.", style(11, colour=INK))],
            [("It also holds at every rating threshold we tested, from 0 to 500 "
              "minimum votes.", style(11, colour=INK_2))],
            [("But this is an association, not a cause.",
              style(12, bold=True, colour=INK))],
            [("Ratings are collected after release, from people who chose to watch. "
              "A film that reached a big, willing audience can be rated highly "
              "because it succeeded, not the other way round. Nothing in this "
              "dataset can separate the two, so this report does not claim that "
              "making a better film causes a better return — only that the two "
              "travel together, everywhere we looked.", style(11, colour=INK_2))],
        ],
        alt="Panel explaining how far the rating finding can be trusted. Films "
            "rated 7.0 or higher out-return the rest in all ten budget deciles and "
            "all five eras, by a median factor of 2.1 times and never less than "
            "1.19 times, and the result holds at every vote threshold from 0 to 500. "
            "However this is an association and not a cause: ratings are collected "
            "after release from people who chose to watch, so a film that reached a "
            "large willing audience may be rated highly because it succeeded. This "
            "report does not claim causation.",
    ))

    add_footer(page)
    return page


def page_five() -> Page:
    page = Page("limits", "5 · What We Cannot Know",
                "This page is the report's evidence for its own limits.")
    add_header(
        page,
        "What We Cannot Know",
        "The honest part. What the data hides, what we assumed, and what would "
        "change the answer.",
        page_number=5,
    )

    page.add(table(
        page, "funnel-table", MARGIN, 188, cols(8), 424,
        projections=[
            proj_column("Funnel", "Step"),
            proj_sum("Funnel", "Films"),
            proj_column("Funnel", "Why"),
        ],
        title="Every film this report set aside, and why",
        subtitle="The funnel is computed from the data at refresh time, not typed "
                 "in. Two of these steps were made for us by the supplied starter "
                 "file before we saw the data.",
        alt="Table of the inclusion funnel with one row per step, the number of "
            "films surviving it, and the reason for the step. It runs from about "
            "930,000 films in the published dataset down to 7,733 films with at "
            "least fifty ratings.",
        # Step carries sortByColumn: Step Order in the model, so sorting on
        # Step gives funnel order without projecting the sort column.
        sort=(column_field("Funnel", "Step"), "Ascending"),
    ))

    quality = [
        ("q-revenue", "Share Revenue Unreported",
         "of the starter file reports no revenue at all",
         "79% of the rows in the starter file record a revenue of zero, which means "
         "not reported rather than earned nothing."),
        ("q-placeholder", "Rows With Placeholder Budget",
         "rows carry a budget too small to be real",
         "More than 27,000 rows carry a budget below 10,000 dollars. Thousands "
         "share the exact values 1, 100, 500 and 1,000, which no real production "
         "budget would."),
        ("q-english", "English Language Share",
         "of measurable films are originally in English",
         "85.1% of the measurable films are originally in English, so this report "
         "describes mostly anglophone commercial cinema and cannot speak for world "
         "cinema."),
    ]
    for i, (key, measure_name, label, alt) in enumerate(quality):
        page.add(card(page, key, col_x(8), 188 + i * 144, cols(4), 128,
                      measure=measure_name, label=label, alt=alt, value_size=32))

    page.add(panel(page, "change-bg", MARGIN, 632, cols(8), 348, z=60))
    page.add(textbox(
        page, "change", MARGIN + 28, 650, cols(8) - 56, 312,
        [
            [("WHAT WOULD CHANGE OUR ANSWER", style(11, bold=True, colour=GOLD))],
            [("Revenue for the films that never reported it. ",
              style(11, bold=True, colour=INK)),
             ("This is the big one. If cheap flops were recorded, the low-budget "
              "return advantage would shrink and might vanish. Our finding about "
              "ratings would survive, because it holds inside every budget class "
              "separately.", style(11, colour=INK_2))],
            [("Marketing spend and the exhibitor's share. ",
              style(11, bold=True, colour=INK)),
             ("The dataset has production budget and gross box office. It has no "
              "print-and-advertising spend, no exhibitor split, no home video, no "
              "streaming licence. So 'return' here is a gross multiple, not profit, "
              "and the 2.5x break-even is a borrowed rule of thumb rather than "
              "something this data proves.", style(11, colour=INK_2))],
            [("An inflation series. ", style(11, bold=True, colour=INK)),
             ("A CPI table would be an external dataset, which this round forbids, "
              "so no dollar figure here is inflation adjusted. That is why every "
              "cross-era comparison in this report uses ratios, in which inflation "
              "cancels, and never dollars.", style(11, colour=INK_2))],
            [("A causal design. ", style(11, bold=True, colour=INK)),
             ("Ratings arrive after release. Without something that moves quality "
              "independently of audience size, the direction of the rating effect "
              "cannot be established from this data at all.",
              style(11, colour=INK_2))],
        ],
        alt="Panel listing what would change the report's answer. First, revenue "
            "for films that never reported it: if cheap flops were recorded the "
            "low-budget return advantage would shrink or vanish, though the rating "
            "finding would survive because it holds within each budget class. "
            "Second, marketing spend and the exhibitor's share, which the dataset "
            "lacks, meaning return here is a gross multiple rather than profit and "
            "the 2.5 times break-even is a borrowed rule of thumb. Third, an "
            "inflation series, which the rules forbid as an external dataset, which "
            "is why cross-era comparisons use ratios rather than dollars. Fourth, a "
            "causal design, without which the direction of the rating effect cannot "
            "be established.",
    ))

    page.add(panel(page, "notclaim-bg", col_x(8), 632, cols(4), 348, z=60))
    page.add(textbox(
        page, "notclaim", col_x(8) + 28, 650, cols(4) - 56, 312,
        [
            [("CLAIMS THIS REPORT DOES NOT MAKE", style(11, bold=True, colour=RED))],
            [("That making a better film causes a better return.",
              style(11, colour=INK_2))],
            [("That anything here describes the 99.2% of films outside the "
              "measurable subset.", style(11, colour=INK_2))],
            [("That a 1970s dollar and a 2020s dollar are comparable.",
              style(11, colour=INK_2))],
            [("That 'return' means profit. It is gross revenue over production "
              "budget, and nothing more.", style(11, colour=INK_2))],
            [("That any of this holds for non-English cinema, which is 15% of even "
              "the measurable subset.", style(11, colour=INK_2))],
            [("That a genre or studio ranked on fewer than 100 measured films is "
              "ranked at all. Those are suppressed, not shown small.",
              style(11, colour=INK_2))],
        ],
        alt="Panel listing claims this report does not make: that making a better "
            "film causes a better return; that anything here describes the 99.2% of "
            "films outside the measurable subset; that a 1970s dollar and a 2020s "
            "dollar are comparable; that return means profit rather than gross "
            "revenue over production budget; that any of this holds for non-English "
            "cinema; and that a genre or studio with fewer than 100 measured films "
            "is ranked at all.",
    ))

    add_footer(page)
    return page


# --------------------------------------------------------------------------- #
# Assembly                                                                     #
# --------------------------------------------------------------------------- #

def write_page(page: Page) -> None:
    page_dir = DEFN / "pages" / page.name
    (page_dir / "visuals").mkdir(parents=True, exist_ok=True)
    (page_dir / "page.json").write_text(
        json.dumps({
            "$schema": S_PAGE,
            "name": page.name,
            "displayName": page.display_name,
            "displayOption": "FitToPage",
            "height": H,
            "width": W,
            "objects": {
                "outspace": [{"properties": {"color": color(PAGE_BG)}}],
                "background": [{"properties": {"color": color(PAGE_BG),
                                               "transparency": num(0)}}],
            },
        }, indent=2) + "\n",
        encoding="utf-8",
    )
    for visual in page.visuals:
        target = page_dir / "visuals" / visual["name"]
        target.mkdir(parents=True, exist_ok=True)
        (target / "visual.json").write_text(
            json.dumps(visual, indent=2) + "\n", encoding="utf-8"
        )


def main() -> int:
    if REPORT.exists():
        shutil.rmtree(REPORT)
    (DEFN / "pages").mkdir(parents=True, exist_ok=True)
    (REPORT / "StaticResources" / "RegisteredResources").mkdir(parents=True, exist_ok=True)

    # ---- project-level files ----------------------------------------------
    (PBIP / "MovieSuccess.pbip").write_text(
        json.dumps({
            # The .pbip shortcut uses fabric/pbip/pbipProperties — NOT
            # fabric/item/pbip/definitionProperties. Getting this wrong makes
            # Desktop deserialize `artifacts` to nothing and fail with
            # "ArtifactShortcut: Required artifact is missing".
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/"
                       "pbipProperties/1.0.0/schema.json",
            "version": "1.0",
            "artifacts": [{"report": {"path": "MovieSuccess.Report"}}],
            "settings": {"enableAutoRecovery": True},
        }, indent=2) + "\n",
        encoding="utf-8",
    )
    (REPORT / ".platform").write_text(
        json.dumps({
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/"
                       "platformProperties/2.0.0/schema.json",
            "metadata": {"type": "Report", "displayName": "MovieSuccess"},
            "config": {"version": "2.0",
                       "logicalId": str(uuid.uuid5(NAMESPACE, "platform|report"))},
        }, indent=2) + "\n",
        encoding="utf-8",
    )
    (REPORT / "definition.pbir").write_text(
        json.dumps({
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/"
                       "definitionProperties/2.0.0/schema.json",
            "version": "4.0",
            "datasetReference": {"byPath": {"path": "../MovieSuccess.SemanticModel"}},
        }, indent=2) + "\n",
        encoding="utf-8",
    )

    # ---- theme -------------------------------------------------------------
    theme_name = _theme_name()
    theme_target = REPORT / "StaticResources" / "RegisteredResources" / f"{theme_name}.json"
    shutil.copyfile(THEME_SOURCE, theme_target)

    (DEFN / "version.json").write_text(
        json.dumps({"$schema": S_VERSION, "version": "2.0.0"}, indent=2) + "\n",
        encoding="utf-8",
    )
    (DEFN / "report.json").write_text(
        json.dumps({
            "$schema": S_REPORT,
            "themeCollection": {
                "customTheme": {"name": f"{theme_name}.json", "type": "RegisteredResources"}
            },
            # Only outspacePane belongs at report level; `outspace` is a page
            # object and every page already sets its own.
            "objects": {
                "outspacePane": [{"properties": {"expanded": lit("false")}}],
            },
            "resourcePackages": [{
                "name": "RegisteredResources",
                "type": "RegisteredResources",
                "items": [{"name": f"{theme_name}.json", "path": f"{theme_name}.json",
                           "type": "CustomTheme"}],
            }],
            "settings": {
                "useStylableVisualContainerHeader": True,
                "exportDataMode": "AllowSummarized",
                "defaultDrillFilterOtherVisuals": True,
                "useEnhancedTooltips": True,
                "useDefaultAggregateDisplayName": True,
            },
        }, indent=2) + "\n",
        encoding="utf-8",
    )

    # ---- pages -------------------------------------------------------------
    pages = [page_one(), page_two(), page_three(), page_four(), page_five()]
    for page in pages:
        write_page(page)

    (DEFN / "pages" / "pages.json").write_text(
        json.dumps({
            "$schema": S_PAGES,
            "pageOrder": [p.name for p in pages],
            "activePageName": pages[0].name,
            "landingPageName": pages[0].name,
        }, indent=2) + "\n",
        encoding="utf-8",
    )

    total = sum(len(p.visuals) for p in pages)
    informative = sum(
        1 for p in pages for v in p.visuals
        if "altText" in v["visual"].get("visualContainerObjects", {})
                          .get("general", [{}])[0].get("properties", {})
    )
    print(f"report written to {REPORT.relative_to(REPO)}")
    print(f"  pages:              {len(pages)}")
    print(f"  visuals:            {total}")
    print(f"  with alt text:      {informative}")
    print(f"  decorative (skipped in tab order): {total - informative}")
    for p in pages:
        print(f"    {p.display_name:34} {len(p.visuals):>2} visuals")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
