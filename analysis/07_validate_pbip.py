"""Validate the generated PBIP before it ever reaches Power BI Desktop.

This build environment has no Power BI Desktop, so the report cannot be opened
and looked at here. That is a real limitation, and this script exists to shrink
it: it checks everything about the project that is checkable from the files
themselves, so that what remains for the Desktop pass is genuinely visual.

Checks
------
STRUCTURE   every JSON file parses; every required PBIP file is present
MODEL       every field a visual references exists in the TMDL model — this is
            the check that catches the failure mode most likely to go unnoticed,
            a mistyped column or measure name that silently yields a broken visual
RULES       page count, core-visual count, Key Takeaway word count
ACCESS      alt text on every informative visual, unique tab order, no
            information-carrying visual excluded from the tab order
LAYOUT      nothing off-canvas, no unintended overlap between sibling visuals
CLAIMS      figures quoted in report text are checked against the analysis output

Exit code is non-zero if any check fails, so this can gate a commit.

Usage
-----
    python analysis/07_validate_pbip.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PBIP = REPO / "src" / "pbip"
REPORT = PBIP / "MovieSuccess.Report"
MODEL = PBIP / "MovieSuccess.SemanticModel"
OUT = REPO / "analysis" / "out"

MAX_PAGES = 5
MIN_CORE_VISUALS = 3
MAX_TAKEAWAY_WORDS = 50

# Visual types the contest would count as "core Power BI visuals".
CORE_VISUAL_TYPES = {
    "clusteredColumnChart", "clusteredBarChart", "columnChart", "barChart",
    "lineChart", "areaChart", "stackedAreaChart", "scatterChart", "pieChart",
    "donutChart", "map", "filledMap", "treemap", "tableEx", "pivotTable",
    "matrix", "card", "cardVisual", "multiRowCard", "kpi", "gauge",
    "waterfallChart", "funnel", "ribbonChart", "lineClusteredColumnComboChart",
}
# Types that only ever decorate or narrate.
NON_DATA_TYPES = {"textbox", "shape", "image", "actionButton", "pageNavigator"}

failures: list[str] = []
warnings: list[str] = []
notes: list[str] = []


def fail(message: str) -> None:
    failures.append(message)


def warn(message: str) -> None:
    warnings.append(message)


# --------------------------------------------------------------------------- #
# Load the model surface out of TMDL                                           #
# --------------------------------------------------------------------------- #

def parse_model() -> tuple[dict[str, set[str]], set[str]]:
    """Return {table: {column names}} and the set of measure names."""
    tables: dict[str, set[str]] = {}
    measures: set[str] = set()

    table_dir = MODEL / "definition" / "tables"
    if not table_dir.is_dir():
        fail(f"no TMDL tables directory at {table_dir}")
        return tables, measures

    for path in sorted(table_dir.glob("*.tmdl")):
        text = path.read_text(encoding="utf-8")
        match = re.search(r"^table\s+('([^']+)'|(\S+))", text, re.MULTILINE)
        if not match:
            fail(f"{path.name}: no table declaration found")
            continue
        table_name = match.group(2) or match.group(3)
        columns = set()
        for col_match in re.finditer(r"^\tcolumn\s+('([^']+)'|(\S+))\s*$",
                                     text, re.MULTILINE):
            columns.add(col_match.group(2) or col_match.group(3))
        tables[table_name] = columns
        for measure_match in re.finditer(r"^\tmeasure\s+'([^']+)'\s*=", text, re.MULTILINE):
            measures.add(measure_match.group(1))
    return tables, measures


# --------------------------------------------------------------------------- #
# Walk the report                                                              #
# --------------------------------------------------------------------------- #

def load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        fail(f"{path.relative_to(REPO)}: invalid JSON — {error}")
        return None


def collect_field_refs(node: object, found: list[tuple[str, str, str]]) -> None:
    """Gather (kind, entity, property) for every field reference in a visual."""
    if isinstance(node, dict):
        for kind in ("Column", "Measure"):
            if kind in node and isinstance(node[kind], dict):
                inner = node[kind]
                entity = (
                    inner.get("Expression", {}).get("SourceRef", {}).get("Entity")
                )
                prop = inner.get("Property")
                if entity and prop:
                    found.append((kind, entity, prop))
        for value in node.values():
            collect_field_refs(value, found)
    elif isinstance(node, list):
        for item in node:
            collect_field_refs(item, found)


def rects_overlap(a: dict, b: dict) -> bool:
    return not (
        a["x"] + a["width"] <= b["x"]
        or b["x"] + b["width"] <= a["x"]
        or a["y"] + a["height"] <= b["y"]
        or b["y"] + b["height"] <= a["y"]
    )


def main() -> int:
    print("=" * 74)
    print("PBIP validation")
    print("=" * 74)

    # ---- STRUCTURE ---------------------------------------------------------
    required = [
        PBIP / "MovieSuccess.pbip",
        REPORT / ".platform",
        REPORT / "definition.pbir",
        REPORT / "definition" / "report.json",
        REPORT / "definition" / "version.json",
        REPORT / "definition" / "pages" / "pages.json",
        MODEL / ".platform",
        MODEL / "definition.pbism",
        MODEL / "definition" / "model.tmdl",
        MODEL / "definition" / "database.tmdl",
        MODEL / "definition" / "expressions.tmdl",
        MODEL / "definition" / "relationships.tmdl",
    ]
    for path in required:
        if not path.is_file():
            fail(f"missing required file: {path.relative_to(REPO)}")

    for path in REPORT.rglob("*.json"):
        load_json(path)

    # The report must point at the sibling semantic model by relative path,
    # otherwise Desktop opens it against nothing.
    pbir = load_json(REPORT / "definition.pbir") or {}
    dataset_path = pbir.get("datasetReference", {}).get("byPath", {}).get("path")
    if dataset_path != "../MovieSuccess.SemanticModel":
        fail(f"definition.pbir points at {dataset_path!r}, expected "
             "'../MovieSuccess.SemanticModel'")
    elif not (REPORT.parent / "MovieSuccess.SemanticModel").is_dir():
        fail("definition.pbir target directory does not exist")
    else:
        notes.append("report -> semantic model reference resolves")

    # The theme must actually be present where report.json says it is.
    report_json = load_json(REPORT / "definition" / "report.json") or {}
    for package in report_json.get("resourcePackages", []):
        for item in package.get("items", []):
            resource = REPORT / "StaticResources" / package["type"] / item["path"]
            if not resource.is_file():
                fail(f"resource declared but missing: {resource.relative_to(REPO)}")
            else:
                notes.append(f"resource present: {item['path']}")

    tables, measures = parse_model()
    print(f"\nmodel surface: {len(tables)} tables, "
          f"{sum(len(c) for c in tables.values())} columns, {len(measures)} measures")

    # ---- pages -------------------------------------------------------------
    pages_meta = load_json(REPORT / "definition" / "pages" / "pages.json") or {}
    page_order = pages_meta.get("pageOrder", [])

    if len(page_order) > MAX_PAGES:
        fail(f"{len(page_order)} pages, the rules allow at most {MAX_PAGES}")
    else:
        notes.append(f"page count {len(page_order)} within the limit of {MAX_PAGES}")

    if pages_meta.get("landingPageName") != page_order[0] if page_order else False:
        warn("landing page is not the first page in page order")

    core_visual_total = 0
    takeaway_checked = False

    for page_name in page_order:
        page_dir = REPORT / "definition" / "pages" / page_name
        page_json = load_json(page_dir / "page.json") or {}
        display = page_json.get("displayName", page_name)
        width = page_json.get("width", 1920)
        height = page_json.get("height", 1080)

        visual_files = sorted(page_dir.glob("visuals/*/visual.json"))
        if not visual_files:
            fail(f"page {display}: no visuals")
            continue

        positions: list[tuple[str, dict, bool]] = []
        tab_orders: dict[int, list[str]] = {}
        page_core = 0

        for path in visual_files:
            visual = load_json(path) or {}
            body = visual.get("visual", {})
            vtype = body.get("visualType", "?")
            position = visual.get("position", {})
            name = visual.get("name", path.parent.name)

            general = (body.get("visualContainerObjects", {})
                           .get("general", [{}])[0]
                           .get("properties", {}))
            has_alt = "altText" in general
            informative = vtype not in NON_DATA_TYPES or has_alt

            # ACCESS: anything data-bound must have alt text.
            if vtype in CORE_VISUAL_TYPES and not has_alt:
                fail(f"{display} / {vtype} {name}: data visual without alt text")

            # ACCESS: alt text must say something, not restate the chart type.
            if has_alt:
                alt_value = general["altText"]["expr"]["Literal"]["Value"].strip("'")
                if len(alt_value) < 40:
                    warn(f"{display} / {name}: alt text is only "
                         f"{len(alt_value)} characters — likely too thin")

            # ACCESS: tab order must be unique among informative visuals.
            tab = position.get("tabOrder")
            if has_alt:
                tab_orders.setdefault(tab, []).append(f"{vtype} {name}")
                if tab is None or tab < 0:
                    fail(f"{display} / {name}: informative visual excluded from "
                         f"tab order (tabOrder={tab})")

            if vtype in CORE_VISUAL_TYPES:
                page_core += 1

            # LAYOUT: on-canvas.
            if position:
                right = position.get("x", 0) + position.get("width", 0)
                bottom = position.get("y", 0) + position.get("height", 0)
                if position.get("x", 0) < 0 or position.get("y", 0) < 0:
                    fail(f"{display} / {name}: negative position")
                if right > width or bottom > height:
                    fail(f"{display} / {name}: extends past the canvas "
                         f"({right}x{bottom} vs {width}x{height})")
                positions.append((f"{vtype} {name}", position, has_alt))

            # MODEL: every field reference must resolve.
            refs: list[tuple[str, str, str]] = []
            collect_field_refs(body.get("query", {}), refs)
            collect_field_refs(body.get("filterConfig", {}), refs)
            for kind, entity, prop in refs:
                if kind == "Measure":
                    if prop not in measures:
                        fail(f"{display} / {name}: measure '{prop}' not found in "
                             "the semantic model")
                else:
                    if entity not in tables:
                        fail(f"{display} / {name}: table '{entity}' not found in "
                             "the semantic model")
                    elif prop not in tables[entity]:
                        fail(f"{display} / {name}: column '{entity}'[{prop}] not "
                             "found in the semantic model")

            # RULES: the Key Takeaway.
            if vtype == "textbox":
                paragraphs = (body.get("objects", {}).get("general", [{}])[0]
                                  .get("properties", {}).get("paragraphs", []))
                text = " ".join(
                    run.get("value", "")
                    for para in paragraphs for run in para.get("textRuns", [])
                )
                if "KEY TAKEAWAY" in text.upper():
                    statement = re.sub(r"(?i)key takeaway", "", text).strip()
                    words = [w for w in re.split(r"\s+", statement) if w]
                    takeaway_checked = True
                    if len(words) > MAX_TAKEAWAY_WORDS:
                        fail(f"Key Takeaway is {len(words)} words, the limit is "
                             f"{MAX_TAKEAWAY_WORDS}")
                    else:
                        notes.append(f"Key Takeaway is {len(words)} words "
                                     f"(limit {MAX_TAKEAWAY_WORDS})")

        for tab, owners in sorted(tab_orders.items(), key=lambda kv: (kv[0] is None, kv[0])):
            if len(owners) > 1:
                fail(f"{display}: tabOrder {tab} shared by {len(owners)} visuals: "
                     + ", ".join(owners))

        # LAYOUT: two informative visuals must not sit on top of each other.
        # A decorative panel behind a textbox is intentional, so only pairs where
        # both carry alt text are reported.
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                (name_a, rect_a, alt_a), (name_b, rect_b, alt_b) = positions[i], positions[j]
                if alt_a and alt_b and rects_overlap(rect_a, rect_b):
                    fail(f"{display}: informative visuals overlap — {name_a} and {name_b}")

        core_visual_total += page_core
        print(f"  {display:34} {len(visual_files):>2} visuals, {page_core:>2} core")

    if not takeaway_checked:
        fail("no Key Takeaway textbox found on any page")

    if core_visual_total < MIN_CORE_VISUALS:
        fail(f"{core_visual_total} core visuals, the rules require at least "
             f"{MIN_CORE_VISUALS}")
    else:
        notes.append(f"{core_visual_total} core Power BI visuals "
                     f"(minimum {MIN_CORE_VISUALS})")

    # ---- CLAIMS ------------------------------------------------------------
    # Numbers written into report prose are checked against the generated
    # analysis, so the report cannot drift away from its own evidence.
    summary_path = OUT / "audit_summary.json"
    robust_path = OUT / "robustness.json"
    if summary_path.is_file() and robust_path.is_file():
        summary = json.loads(summary_path.read_text())
        robust = json.loads(robust_path.read_text())
        all_text = " ".join(
            path.read_text(encoding="utf-8")
            for path in REPORT.rglob("visual.json")
        )
        expected = {
            "7,733": summary["analysable_rows"] == 7733,
            "85,394": summary["starter_rows"] == 85394,
            "0.8%": round(summary["analysable_share_of_source"] * 100, 1) == 0.8,
            "1.96": round(summary["roi_skew"]["median"], 2) == 1.96,
            "41.4%": round(robust["thresholds"][7]["Share breaking even"] * 100, 1) == 41.4,
            "7.8%": round(
                robust["survivorship"]["summary"]["low_reporting_rate"] * 100, 1) == 7.8,
            "91.1%": round(
                robust["survivorship"]["summary"]["high_reporting_rate"] * 100, 1) == 91.1,
            "85.1%": round(summary["language_mix"]["en"] * 100, 1) == 85.1,
        }
        for literal, matches_analysis in expected.items():
            in_report = literal in all_text
            if in_report and not matches_analysis:
                fail(f"report quotes {literal} but the analysis output disagrees")
            elif in_report:
                notes.append(f"figure {literal} in report text matches the analysis")
            else:
                warn(f"figure {literal} not found in report text")
    else:
        warn("analysis outputs not present; skipped the claim cross-check "
             "(run scripts 02 and 04 first)")

    # ---- report ------------------------------------------------------------
    print()
    for note in notes:
        print(f"  PASS  {note}")
    for warning in warnings:
        print(f"  WARN  {warning}")
    for failure in failures:
        print(f"  FAIL  {failure}")

    print()
    print("=" * 74)
    if failures:
        print(f"FAILED — {len(failures)} problem(s), {len(warnings)} warning(s)")
        return 1
    print(f"PASSED — {len(notes)} check(s) satisfied, {len(warnings)} warning(s)")
    print("Remaining verification requires Power BI Desktop: see "
          "docs/08-build-and-submit.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
