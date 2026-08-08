"""Generate the TMDL semantic model for the Power BI Project (PBIP).

Why generated rather than hand-written
--------------------------------------
The model is a faithful transcription of the official starter file's model plus
our own additions. Transcribing by hand invites silent drift; generating it from
one script means the eight starter tables are provably unmodified in structure
and every addition is visible in one place, which matters because the round's
rules turn on exactly what we did and did not change.

What is transcribed unchanged from the starter file
    - the `Source` and `Schema` shared queries (the CSV path is turned into a
      parameter, which is the one edit the official instructions ask for)
    - the M for Movies, Genres, Genre Bridge, Keyword, Keyword Bridge,
      Production Company, Production Company Bridge, Date
    - all seven relationships

What this script adds (all permitted by the brief: "Create calculations and
measures", "Build additional tables derived from the supplied dataset")
    - derived columns on Movies: ROI, Is Measurable, Breaks Even, Budget Band,
      Rating Band, Release Year, Era, and their sort-order companions
    - a `_Measures` table of DAX measures
    - four DAX leaderboard tables, one per competing definition of success
    - a DAX `Funnel` table that computes the inclusion funnel from the data

Usage
-----
    python analysis/05_build_semantic_model.py
"""

from __future__ import annotations

import shutil
import sys
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PBIP = REPO / "src" / "pbip"
MODEL = PBIP / "MovieSuccess.SemanticModel"
DEFN = MODEL / "definition"

# Thresholds. These are the same constants the analysis scripts use; they are
# restated here because the model must be readable on its own.
MIN_BUDGET = 10_000
MIN_REVENUE = 10_000
MIN_VOTES = 50
BREAKEVEN = 2.5
SOURCE_FILMS_STATED = 930_000
RELIABLE_MIN_FILMS = 100

# Deterministic lineage tags: a fixed namespace means re-running the generator
# produces byte-identical output, so a diff shows real changes only.
NAMESPACE = uuid.UUID("6f1d4a2e-3c7b-4f58-9a10-2b5e8c4d7f31")


def tag(*parts: str) -> str:
    return str(uuid.uuid5(NAMESPACE, "|".join(parts)))


def block(text: str, indent: int) -> str:
    """Indent a multi-line M expression for TMDL's indentation-delimited block.

    Every line is padded, including blank ones: a column-zero line inside an
    indentation-delimited block would end the block early.
    """
    pad = "\t" * indent
    lines = [line.rstrip() for line in text.strip("\n").split("\n")]
    return "\n".join(f"{pad}{line}" for line in lines)


def dax(text: str, indent: int) -> str:
    """A DAX expression, fenced in triple backticks when it spans lines.

    TMDL requires the fence for multi-line DAX; bare indentation is valid only
    for Power Query. A single-line expression stays on the declaration line.
    """
    body = text.strip()
    if "\n" not in body:
        return body
    pad = "\t" * indent
    lines = "\n".join(f"{pad}{line.rstrip()}" for line in body.split("\n"))
    return f"```\n{lines}\n{pad}```"


# --------------------------------------------------------------------------- #
# Shared queries, transcribed from the starter file                            #
# --------------------------------------------------------------------------- #

# The starter file hardcoded the author's own download folder. Turning it into a
# parameter is exactly the edit the contest instructions ask competitors to make
# ("replace the file path in the Source step of the Source query").
CSV_PATH_DEFAULT = r"C:\Users\Public\Documents\TMDB\TMDB_movie_dataset_v11.csv"

M_CSV_PATH = f'"{CSV_PATH_DEFAULT}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'

M_SOURCE = """
let
    // Transcribed from the official Round 3 starter file. The only change is
    // that the hardcoded path is now the CsvPath parameter.
    // Data published at:
    // https://www.kaggle.com/datasets/asaniczka/tmdb-movies-dataset-2023-930k-movies
    Source = Csv.Document(File.Contents(CsvPath),[Delimiter=",", Columns=24, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{{"id", Int64.Type}, {"title", type text}, {"vote_average", type number}, {"vote_count", Int64.Type}, {"status", type text}, {"release_date", type date}, {"revenue", Int64.Type}, {"runtime", Int64.Type}, {"adult", type logical}, {"backdrop_path", type text}, {"budget", Int64.Type}, {"homepage", type text}, {"imdb_id", type text}, {"original_language", type text}, {"original_title", type text}, {"overview", type text}, {"popularity", type number}, {"poster_path", type text}, {"tagline", type text}, {"genres", type text}, {"production_companies", type text}, {"production_countries", type text}, {"spoken_languages", type text}, {"keywords", type text}})
in
    #"Changed Type"
"""

M_SCHEMA = """
let
    Source = Csv.Document(File.Contents(CsvPath),[Delimiter=",", Columns=24, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Kept First Rows" = Table.FirstN(Source,2),
    #"Transposed Table" = Table.Transpose(#"Kept First Rows"),
    #"Renamed Columns" = Table.RenameColumns(#"Transposed Table",{{"Column1", "Column"}, {"Column2", "Sample Entry"}})
in
    #"Renamed Columns"
"""

# --------------------------------------------------------------------------- #
# Movies: starter M, then our derived columns                                  #
# --------------------------------------------------------------------------- #

M_MOVIES_HEAD = f"""
let
    Src = Source,
    // ---- transcribed unchanged from the starter file ----------------------
    #"Filtered Rows" = Table.SelectRows(Src, each [budget] > 0),
    #"Renamed Columns" = Table.RenameColumns(#"Filtered Rows",{{{{"id", "Movie ID"}}, {{"title", "Title"}}, {{"vote_average", "Vote Average"}}, {{"vote_count", "Vote Count"}}, {{"release_date", "Release Date"}}, {{"revenue", "Revenue"}}, {{"backdrop_path", "Backdrop Path"}}, {{"budget", "Budget"}}, {{"homepage", "Homepage"}}, {{"popularity", "Popularity"}}, {{"runtime", "Runtime"}}}}),
    #"Removed Other Columns" = Table.SelectColumns(#"Renamed Columns",{{"Movie ID", "Title", "Vote Average", "Vote Count", "status", "Release Date", "Revenue", "Runtime", "adult", "Backdrop Path", "Budget", "Homepage", "original_language", "original_title", "Popularity", "poster_path", "tagline", "genres"}}),
    #"Renamed Columns1" = Table.RenameColumns(#"Removed Other Columns",{{{{"genres", "genres"}}, {{"adult", "Adult"}}, {{"original_language", "Original Language"}}, {{"original_title", "Original Title"}}, {{"tagline", "Tagline"}}, {{"poster_path", "Poster Path"}}, {{"status", "Status"}}}}),
    #"Removed Columns" = Table.RemoveColumns(#"Renamed Columns1",{{"genres"}}),
"""

# The derived-column pipeline, shared verbatim by the canonical build and the
# bundled-data build. Every head that precedes it must end with a step named
# #"Removed Columns".
M_MOVIES_DERIVED = f"""
    // ---- our additions: derived columns, no source values altered ---------
    // "Measurable" is the single gate every financial figure in the report
    // passes through. It is a column rather than a report filter so that it is
    // visible in the model and cannot be forgotten on a page.
    AddMeasurable = Table.AddColumn(#"Removed Columns", "Is Measurable", each
        [Status] = "Released"
        and [Release Date] <> null
        and [Budget] >= {MIN_BUDGET}
        and [Revenue] >= {MIN_REVENUE}
        and [Vote Count] >= {MIN_VOTES}, type logical),

    // Return on production budget. Null, never zero, when it cannot be formed:
    // a film with unreported revenue has an unknown return, not a zero one.
    AddROI = Table.AddColumn(AddMeasurable, "ROI", each
        if [Is Measurable] then [Revenue] / [Budget] else null, type number),

    AddProfit = Table.AddColumn(AddROI, "Gross Profit", each
        if [Is Measurable] then [Revenue] - [Budget] else null, Int64.Type),

    AddBreakEven = Table.AddColumn(AddProfit, "Breaks Even", each
        if [Is Measurable] then [ROI] >= {BREAKEVEN} else null, type logical),

    AddYear = Table.AddColumn(AddBreakEven, "Release Year", each
        if [Release Date] = null then null else Date.Year([Release Date]), Int64.Type),

    AddMonth = Table.AddColumn(AddYear, "Release Month", each
        if [Release Date] = null then null else Date.Month([Release Date]), Int64.Type),

    AddMonthName = Table.AddColumn(AddMonth, "Release Month Name", each
        if [Release Date] = null then null else Date.MonthName([Release Date]), type text),

    // Fixed dollar bands rather than deciles: a reader understands "$15-30M",
    // and a decile boundary shifts every time the filter context changes.
    AddBudgetBand = Table.AddColumn(AddMonthName, "Budget Band", each
        if not [Is Measurable] then null
        else if [Budget] < 1000000 then "Under $1M"
        else if [Budget] < 5000000 then "$1M to $5M"
        else if [Budget] < 15000000 then "$5M to $15M"
        else if [Budget] < 30000000 then "$15M to $30M"
        else if [Budget] < 60000000 then "$30M to $60M"
        else if [Budget] < 100000000 then "$60M to $100M"
        else "$100M and above", type text),

    AddBudgetBandSort = Table.AddColumn(AddBudgetBand, "Budget Band Sort", each
        if [Budget Band] = null then null
        else if [Budget Band] = "Under $1M" then 1
        else if [Budget Band] = "$1M to $5M" then 2
        else if [Budget Band] = "$5M to $15M" then 3
        else if [Budget Band] = "$15M to $30M" then 4
        else if [Budget Band] = "$30M to $60M" then 5
        else if [Budget Band] = "$60M to $100M" then 6
        else 7, Int64.Type),

    AddRatingBand = Table.AddColumn(AddBudgetBandSort, "Rating Band", each
        if not [Is Measurable] then null
        else if [Vote Average] < 5 then "Below 5.0"
        else if [Vote Average] < 6 then "5.0 to 6.0"
        else if [Vote Average] < 6.5 then "6.0 to 6.5"
        else if [Vote Average] < 7 then "6.5 to 7.0"
        else if [Vote Average] < 7.5 then "7.0 to 7.5"
        else "7.5 and above", type text),

    AddRatingBandSort = Table.AddColumn(AddRatingBand, "Rating Band Sort", each
        if [Rating Band] = null then null
        else if [Rating Band] = "Below 5.0" then 1
        else if [Rating Band] = "5.0 to 6.0" then 2
        else if [Rating Band] = "6.0 to 6.5" then 3
        else if [Rating Band] = "6.5 to 7.0" then 4
        else if [Rating Band] = "7.0 to 7.5" then 5
        else 6, Int64.Type),

    // Eras exist so that dollars are never compared across them. See
    // docs/09-decision-log.md ADR-006.
    AddEra = Table.AddColumn(AddRatingBandSort, "Era", each
        if [Release Year] = null then null
        else if [Release Year] < 1980 then "Before 1980"
        else if [Release Year] < 1995 then "1980 to 1994"
        else if [Release Year] < 2005 then "1995 to 2004"
        else if [Release Year] < 2015 then "2005 to 2014"
        else "2015 onward", type text),

    AddEraSort = Table.AddColumn(AddEra, "Era Sort", each
        if [Era] = null then null
        else if [Era] = "Before 1980" then 1
        else if [Era] = "1980 to 1994" then 2
        else if [Era] = "1995 to 2004" then 3
        else if [Era] = "2005 to 2014" then 4
        else 5, Int64.Type),

    // The report needs to name the placeholder budgets, so it needs to be able
    // to count them.
    AddPlaceholder = Table.AddColumn(AddEraSort, "Budget Looks Like A Placeholder", each
        [Budget] < {MIN_BUDGET}, type logical),

    // Break-even outcome as a category, for the scatter plot's two-colour
    // series. Text plus a sort key, so red is always the first legend entry.
    AddOutcome = Table.AddColumn(AddPlaceholder, "Outcome", each
        if not [Is Measurable] then null
        else if [ROI] >= {BREAKEVEN} then "Clears 2.5x break-even"
        else "Below 2.5x break-even", type text),

    AddOutcomeSort = Table.AddColumn(AddOutcome, "Outcome Sort", each
        if [Outcome] = null then null
        else if [Outcome] = "Below 2.5x break-even" then 1
        else 2, Int64.Type),

    // The rules explicitly allow "movie posters ... linked directly from the
    // provided dataset". Poster Path is a dataset column; this only prefixes
    // the TMDB image host it belongs to.
    AddPosterUrl = Table.AddColumn(AddOutcomeSort, "Poster URL", each
        if [Poster Path] = null or [Poster Path] = "" then null
        else "https://image.tmdb.org/t/p/w185" & [Poster Path], type text)
in
    AddPosterUrl
"""

M_MOVIES = M_MOVIES_HEAD.rstrip() + "\n\n" + M_MOVIES_DERIVED.strip("\n")

# --------------------------------------------------------------------------- #
# Bundled-data mode (--bundled)                                                #
#                                                                              #
# The canonical build loads the raw Kaggle CSV, exactly as the official        #
# instructions describe. The bundled build instead loads per-table CSVs that   #
# analysis/08_export_bundled_data.py exports from the official starter         #
# file's own model - the same snapshot every competitor receives - so the      #
# project can refresh on a machine with no Kaggle account. Only the loading    #
# steps differ; every derived column, measure, calculated table and            #
# relationship is identical between the two builds.                            #
# --------------------------------------------------------------------------- #

BUNDLED_LOAD_TEMPLATE = """
let
    Raw = Csv.Document(File.Contents(DataFolder & "{bs}{filename}"),[Delimiter=",", Columns={ncols}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    #"Promoted Headers" = Table.PromoteHeaders(Raw, [PromoteAllScalars=true]),
    // Types are pinned to the en-US culture: the shipped CSVs carry ISO dates
    // and dot decimals regardless of the machine locale.
    #"{last}" = Table.TransformColumnTypes(#"Promoted Headers",{{{types}}}, "en-US")
in
    #"{last}"
"""

BUNDLED_TYPES = {
    "Movies": [
        ("Movie ID", "Int64.Type"), ("Title", "type text"),
        ("Vote Average", "type number"), ("Vote Count", "Int64.Type"),
        ("Release Date", "type date"), ("Revenue", "Int64.Type"),
        ("Runtime", "Int64.Type"), ("Budget", "Int64.Type"),
        ("Popularity", "type number"), ("Status", "type text"),
        ("Adult", "type logical"), ("Backdrop Path", "type text"),
        ("Homepage", "type text"), ("Original Language", "type text"),
        ("Original Title", "type text"), ("Poster Path", "type text"),
        ("Tagline", "type text"),
    ],
    "Genres": [("Genre", "type text"), ("Genre ID", "Int64.Type")],
    "Genre Bridge": [("Movie ID", "Int64.Type"), ("Genre ID", "Int64.Type")],
    "Production Company": [("Production Company", "type text"),
                           ("Production Company ID", "Int64.Type")],
    "Production Company Bridge": [("Movie ID", "Int64.Type"),
                                  ("Production Company ID", "Int64.Type")],
    "Keyword": [("Keywords", "type text"), ("Keyword ID", "Int64.Type")],
    "Keyword Bridge": [("Movie ID", "Int64.Type"), ("Keyword ID", "Int64.Type")],
}


def bundled_load(table: str, last: str = "Typed") -> str:
    types = BUNDLED_TYPES[table]
    type_list = ", ".join('{"%s", %s}' % (column, kind) for column, kind in types)
    return BUNDLED_LOAD_TEMPLATE.format(
        bs=chr(92), filename=f"{table}.csv", ncols=len(types),
        last=last, types=type_list,
    )


def bundled_movies_m() -> str:
    """The bundled Movies pipeline: CSV load, then the shared derived steps."""
    load = bundled_load("Movies", last="Removed Columns")
    head, _, _ = load.rpartition("\nin\n")
    return head.rstrip() + ",\n\n" + M_MOVIES_DERIVED.strip("\n")


# --------------------------------------------------------------------------- #
# The remaining starter tables, transcribed unchanged                          #
# --------------------------------------------------------------------------- #

M_PRODUCTION_COMPANY = """
let
    Src = Source,
    Companies = Table.SelectColumns(Src, {"production_companies"}),
    SplitCompanies = Table.ExpandListColumn(
        Table.TransformColumns(Companies, {{"production_companies", each List.Transform(Splitter.SplitTextByDelimiter(",", QuoteStyle.Csv)(_), Text.Trim), type {text}}}),
        "production_companies"),
    ProductionCompanyDimension = Table.RenameColumns(
        Table.AddIndexColumn(
            Table.Sort(
                Table.Distinct(
                    Table.SelectRows(SplitCompanies, each [production_companies] <> null and [production_companies] <> "")),
                {{"production_companies", Order.Ascending}}),
            "Production Company ID", 1, 1, Int64.Type),
        {{"production_companies", "Production Company"}})
in
    ProductionCompanyDimension
"""

M_GENRES = """
let
    Src = Source,
    Genres = Table.SelectColumns(Src, {"genres"}),
    SplitGenres = Table.ExpandListColumn(
        Table.TransformColumns(Genres, {{"genres", each List.Transform(Splitter.SplitTextByDelimiter(",", QuoteStyle.Csv)(_), each Text.Clean(Text.Trim(_))), type {text}}}),
        "genres"),
    GenreDimension = Table.AddIndexColumn(
        Table.Sort(
            Table.Distinct(
                Table.SelectRows(SplitGenres, each [genres] <> null and [genres] <> "")),
            {{"genres", Order.Ascending}}),
        "GenreID", 1, 1, Int64.Type),
    #"Renamed Columns" = Table.RenameColumns(GenreDimension,{{"GenreID", "Genre ID"}, {"genres", "Genre"}})
in
    #"Renamed Columns"
"""

M_GENRE_BRIDGE = """
let
    Src = Source,
    MovieGenres = Table.SelectColumns(Src, {"id", "genres"}),
    SplitGenres = Table.SelectRows(
        Table.ExpandListColumn(
            Table.TransformColumns(MovieGenres, {{"genres", each List.Transform(Splitter.SplitTextByDelimiter(",", QuoteStyle.Csv)(_), each Text.Clean(Text.Trim(_))), type {text}}}),
            "genres"),
        each [genres] <> null and [genres] <> ""),
    MergeGenres = Table.NestedJoin(SplitGenres, {"genres"}, Genres, {"Genre"}, "GenreLookup", JoinKind.LeftOuter),
    BridgeMovieGenre = Table.RenameColumns(
        Table.RemoveColumns(
            Table.ExpandTableColumn(MergeGenres, "GenreLookup", {"Genre ID"}, {"Genre ID"}),
            {"genres"}),
        {{"id", "Movie ID"}})
in
    BridgeMovieGenre
"""

M_PRODUCTION_COMPANY_BRIDGE = """
let
    Src = Source,
    MovieCompanies = Table.SelectColumns(Src, {"id", "production_companies"}),
    SplitCompanies = Table.SelectRows(
        Table.ExpandListColumn(
            Table.TransformColumns(MovieCompanies, {{"production_companies", each List.Transform(Splitter.SplitTextByDelimiter(",", QuoteStyle.Csv)(_), Text.Trim), type {text}}}),
            "production_companies"),
        each [production_companies] <> null and [production_companies] <> ""),
    MergeCompanies = Table.NestedJoin(SplitCompanies, {"production_companies"}, #"Production Company", {"Production Company"}, "CompanyLookup", JoinKind.LeftOuter),
    BridgeMovieProductionCompany = Table.RenameColumns(
        Table.RemoveColumns(
            Table.ExpandTableColumn(MergeCompanies, "CompanyLookup", {"Production Company ID"}, {"Production Company ID"}),
            {"production_companies"}),
        {{"id", "Movie ID"}})
in
    BridgeMovieProductionCompany
"""

M_DATE = """
let
    StartDate = #date(1937, 1, 1),
    EndDate = Date.From(DateTime.LocalNow()),
    DateList = List.Dates(StartDate, Duration.Days(EndDate - StartDate) + 1, #duration(1, 0, 0, 0)),
    DateTable = Table.FromList(DateList, Splitter.SplitByNothing(), {"Date"}),
    AddedYear = Table.AddColumn(DateTable, "Year", each Date.Year([Date]), Int64.Type),
    AddedMonthNumber = Table.AddColumn(AddedYear, "Month Number", each Date.Month([Date]), Int64.Type),
    AddedMonthName = Table.AddColumn(AddedMonthNumber, "Month Name", each Date.MonthName([Date]), type text),
    AddedWeekNumber = Table.AddColumn(AddedMonthName, "Week Number", each Date.WeekOfYear([Date]), Int64.Type),
    #"Changed Type" = Table.TransformColumnTypes(AddedWeekNumber,{{"Date", type date}})
in
    #"Changed Type"
"""

# --------------------------------------------------------------------------- #
# Column definitions                                                           #
# --------------------------------------------------------------------------- #

# (name, dataType, formatString, summarizeBy, extra lines)
MOVIES_COLUMNS = [
    ("Movie ID", "int64", "0", "none", []),
    ("Title", "string", None, "none", []),
    ("Vote Average", "double", "0.0", "none", []),
    ("Vote Count", "int64", "#,0", "none", []),
    ("Status", "string", None, "none", []),
    ("Release Date", "dateTime", "Long Date", "none", []),
    ("Revenue", "int64", '\\$#,0;(\\$#,0);\\$#,0', "sum", []),
    ("Runtime", "int64", "#,0", "none", []),
    # Booleans deliberately carry no formatString: the TMDL escaping for the
    # default boolean format is fragile, and Desktop supplies it anyway.
    ("Adult", "boolean", None, "none", []),
    ("Backdrop Path", "string", None, "none", []),
    ("Budget", "int64", '\\$#,0;(\\$#,0);\\$#,0', "sum", []),
    ("Homepage", "string", None, "none", ["dataCategory: WebUrl"]),
    ("Original Language", "string", None, "none", []),
    ("Original Title", "string", None, "none", []),
    ("Popularity", "double", "0.00", "none", []),
    ("Poster Path", "string", None, "none", []),
    ("Tagline", "string", None, "none", []),
    ("Is Measurable", "boolean", None, "none", []),
    ("ROI", "double", "0.00", "none", []),
    ("Gross Profit", "int64", '\\$#,0;(\\$#,0);\\$#,0', "sum", []),
    ("Breaks Even", "boolean", None, "none", []),
    ("Release Year", "int64", "0", "none", []),
    ("Release Month", "int64", "0", "none", []),
    ("Release Month Name", "string", None, "none", []),
    ("Budget Band", "string", None, "none", ["sortByColumn: 'Budget Band Sort'"]),
    ("Budget Band Sort", "int64", "0", "none", ["isHidden"]),
    ("Rating Band", "string", None, "none", ["sortByColumn: 'Rating Band Sort'"]),
    ("Rating Band Sort", "int64", "0", "none", ["isHidden"]),
    ("Era", "string", None, "none", ["sortByColumn: 'Era Sort'"]),
    ("Era Sort", "int64", "0", "none", ["isHidden"]),
    ("Budget Looks Like A Placeholder", "boolean", None, "none", []),
    ("Outcome", "string", None, "none", ["sortByColumn: 'Outcome Sort'"]),
    ("Outcome Sort", "int64", "0", "none", ["isHidden"]),
    ("Poster URL", "string", None, "none", ["dataCategory: ImageUrl"]),
]

SIMPLE_TABLES = [
    ("Genres", M_GENRES, [("Genre", "string", None, "none", []),
                          ("Genre ID", "int64", "0", "none", [])]),
    ("Genre Bridge", M_GENRE_BRIDGE, [("Movie ID", "int64", "0", "none", []),
                                      ("Genre ID", "int64", "0", "none", [])]),
    ("Production Company", M_PRODUCTION_COMPANY,
     [("Production Company", "string", None, "none", []),
      ("Production Company ID", "int64", "0", "none", [])]),
    ("Production Company Bridge", M_PRODUCTION_COMPANY_BRIDGE,
     [("Movie ID", "int64", "0", "none", []),
      ("Production Company ID", "int64", "0", "none", [])]),
    ("Date", M_DATE, [("Date", "dateTime", "Long Date", "none", []),
                      ("Year", "int64", "0", "none", []),
                      ("Month Number", "int64", "0", "none", []),
                      ("Month Name", "string", None, "none", ["sortByColumn: 'Month Number'"]),
                      ("Week Number", "int64", "0", "none", [])]),
]

# --------------------------------------------------------------------------- #
# Measures                                                                     #
# --------------------------------------------------------------------------- #

MEASURABLE = "'Movies'[Is Measurable] = TRUE()"

MEASURES: list[tuple[str, str, str | None, str]] = [
    # (name, DAX, formatString, description)
    (
        "Films Measured",
        f"CALCULATE ( COUNTROWS ( 'Movies' ), {MEASURABLE} )",
        "#,0",
        "Films that clear every quality gate: released, dated, budget and revenue "
        "both at least $10,000, and at least 50 ratings.",
    ),
    (
        "Films In Starter File",
        "COUNTROWS ( ALL ( 'Movies' ) )",
        "#,0",
        "Every row the supplied starter file loads, after its own Budget > 0 filter.",
    ),
    (
        "Films Measured Overall",
        f"CALCULATE ( COUNTROWS ( 'Movies' ), ALL ( 'Movies' ), {MEASURABLE} )",
        "#,0",
        "Films Measured ignoring all report filters, for scope statements that must "
        "not move when a slicer moves.",
    ),
    (
        "Source Films As Published",
        f"{SOURCE_FILMS_STATED}",
        "#,0",
        "The film count the challenge brief attributes to the source dataset. A "
        "stated figure, not one this model can verify.",
    ),
    (
        "Share Of Source Measurable",
        "DIVIDE ( [Films Measured Overall], [Source Films As Published] )",
        "0.0%",
        "How much of the published dataset survives to the point where a financial "
        "question can be asked of it.",
    ),
    (
        "Median Return",
        f"CALCULATE ( MEDIAN ( 'Movies'[ROI] ), {MEASURABLE} )",
        "0.00\\x",
        "Median revenue divided by production budget. Median, because the "
        "distribution is extreme enough that a mean describes nothing.",
    ),
    (
        "Median Budget",
        f"CALCULATE ( MEDIAN ( 'Movies'[Budget] ), {MEASURABLE} )",
        '\\$#,0',
        "Median production budget in nominal dollars. Never compare across eras.",
    ),
    (
        "Median Revenue",
        f"CALCULATE ( MEDIAN ( 'Movies'[Revenue] ), {MEASURABLE} )",
        '\\$#,0',
        "Median reported gross revenue in nominal dollars.",
    ),
    (
        "Median Rating",
        f"CALCULATE ( MEDIAN ( 'Movies'[Vote Average] ), {MEASURABLE} )",
        "0.00",
        "Median audience rating out of 10.",
    ),
    (
        "Break-even Rate",
        f"""VAR Pool = CALCULATETABLE ( 'Movies', {MEASURABLE} )
VAR Cleared = FILTER ( Pool, 'Movies'[ROI] >= {BREAKEVEN} )
RETURN
    DIVIDE ( COUNTROWS ( Cleared ), COUNTROWS ( Pool ) )""",
        "0.0%",
        f"Share of films whose gross revenue reached {BREAKEVEN} times their "
        "production budget. The multiple is an industry rule of thumb, not a "
        "figure derived from this data.",
    ),
    (
        "Recovered Budget Rate",
        f"""VAR Pool = CALCULATETABLE ( 'Movies', {MEASURABLE} )
VAR Cleared = FILTER ( Pool, 'Movies'[ROI] >= 1 )
RETURN
    DIVIDE ( COUNTROWS ( Cleared ), COUNTROWS ( Pool ) )""",
        "0.0%",
        "Share of films whose gross revenue merely exceeded their budget. The gap "
        "between this and Break-even Rate is the cost of distribution and marketing.",
    ),
    # Reliability-gated variants. A blank result drops the category from the
    # chart, which is how the report avoids ranking a genre on 4 films.
    (
        "Median Return (reliable)",
        f"IF ( [Films Measured] >= {RELIABLE_MIN_FILMS}, [Median Return] )",
        "0.00\\x",
        f"Median Return, suppressed for categories with fewer than "
        f"{RELIABLE_MIN_FILMS} measured films.",
    ),
    (
        "Break-even Rate (reliable)",
        f"IF ( [Films Measured] >= {RELIABLE_MIN_FILMS}, [Break-even Rate] )",
        "0.0%",
        f"Break-even Rate, suppressed below {RELIABLE_MIN_FILMS} measured films.",
    ),
    (
        "Median Budget (reliable)",
        f"IF ( [Films Measured] >= {RELIABLE_MIN_FILMS}, [Median Budget] )",
        '\\$#,0',
        f"Median Budget, suppressed below {RELIABLE_MIN_FILMS} measured films.",
    ),
    # Data-quality measures. The report shows these as first-class content.
    (
        "Rows With Unreported Revenue",
        "CALCULATE ( COUNTROWS ( 'Movies' ), ALL ( 'Movies' ), 'Movies'[Revenue] = 0 )",
        "#,0",
        "Rows whose revenue is recorded as 0. Zero here means not reported, which "
        "is not the same as earned nothing.",
    ),
    (
        "Share Revenue Unreported",
        "DIVIDE ( [Rows With Unreported Revenue], [Films In Starter File] )",
        "0.0%",
        "How much of the starter file cannot answer a revenue question at all.",
    ),
    (
        "Rows With Placeholder Budget",
        "CALCULATE ( COUNTROWS ( 'Movies' ), ALL ( 'Movies' ), "
        "'Movies'[Budget Looks Like A Placeholder] = TRUE() )",
        "#,0",
        f"Rows whose budget is under ${MIN_BUDGET:,}. Real budgets are "
        "near-continuous; values shared by thousands of unrelated films are "
        "data-entry defaults.",
    ),
    (
        "Rows Missing Release Date",
        "CALCULATE ( COUNTROWS ( 'Movies' ), ALL ( 'Movies' ), "
        "ISBLANK ( 'Movies'[Release Date] ) )",
        "#,0",
        "Rows that cannot be placed in time.",
    ),
    (
        "English Language Share",
        f"""VAR Pool = CALCULATETABLE ( 'Movies', ALL ( 'Movies' ), {MEASURABLE} )
VAR English = FILTER ( Pool, 'Movies'[Original Language] = "en" )
RETURN
    DIVIDE ( COUNTROWS ( English ), COUNTROWS ( Pool ) )""",
        "0.0%",
        "Share of the measurable subset originally in English. This is the single "
        "clearest reason the report cannot speak about world cinema.",
    ),
    # The overlap measures prove the brief's own premise with a number.
    (
        "Top 100 Overlap Box Office And Return",
        f"""VAR Pool = CALCULATETABLE ( 'Movies', ALL ( 'Movies' ), {MEASURABLE} )
VAR ByRevenue = TOPN ( 100, Pool, 'Movies'[Revenue], DESC )
VAR ByReturn = TOPN ( 100, Pool, 'Movies'[ROI], DESC )
RETURN
    COUNTROWS (
        INTERSECT (
            SELECTCOLUMNS ( ByRevenue, "@id", 'Movies'[Movie ID] ),
            SELECTCOLUMNS ( ByReturn, "@id", 'Movies'[Movie ID] )
        )
    ) + 0""",
        "#,0",
        "How many films appear in both the top 100 by gross revenue and the top 100 "
        "by return on budget.",
    ),
    (
        "Top 100 Overlap Box Office And Acclaim",
        f"""VAR Pool = CALCULATETABLE ( 'Movies', ALL ( 'Movies' ), {MEASURABLE} )
VAR ByRevenue = TOPN ( 100, Pool, 'Movies'[Revenue], DESC )
VAR ByRating = TOPN ( 100, Pool, 'Movies'[Vote Average], DESC, 'Movies'[Vote Count], DESC )
RETURN
    COUNTROWS (
        INTERSECT (
            SELECTCOLUMNS ( ByRevenue, "@id", 'Movies'[Movie ID] ),
            SELECTCOLUMNS ( ByRating, "@id", 'Movies'[Movie ID] )
        )
    ) + 0""",
        "#,0",
        "How many films appear in both the top 100 by gross revenue and the top 100 "
        "by audience rating.",
    ),
    (
        "Top 100 Overlap Box Office And Profit",
        f"""VAR Pool = CALCULATETABLE ( 'Movies', ALL ( 'Movies' ), {MEASURABLE} )
VAR ByRevenue = TOPN ( 100, Pool, 'Movies'[Revenue], DESC )
VAR ByProfit = TOPN ( 100, Pool, 'Movies'[Gross Profit], DESC )
RETURN
    COUNTROWS (
        INTERSECT (
            SELECTCOLUMNS ( ByRevenue, "@id", 'Movies'[Movie ID] ),
            SELECTCOLUMNS ( ByProfit, "@id", 'Movies'[Movie ID] )
        )
    ) + 0""",
        "#,0",
        "How many films appear in both the top 100 by gross revenue and the top 100 "
        "by gross profit. A high number means profit adds nothing to the story that "
        "revenue did not already tell.",
    ),
    # The rating uplift, stated as a measure so the report can show it live.
    (
        "Return Uplift Of Well Rated Films",
        f"""VAR WellRated =
    CALCULATE ( MEDIAN ( 'Movies'[ROI] ), {MEASURABLE}, 'Movies'[Vote Average] >= 7 )
VAR Rest =
    CALCULATE ( MEDIAN ( 'Movies'[ROI] ), {MEASURABLE}, 'Movies'[Vote Average] < 7 )
RETURN
    DIVIDE ( WellRated, Rest )""",
        "0.00\\x",
        "How many times more a film rated 7.0 or better returns, compared with the "
        "rest of the same selection. An association, not a cause.",
    ),
    # Studio measures share a 25-film reliability gate: a studio's slate is
    # narrower than a genre, so the 100-film gate would empty the table, but a
    # median over fewer than 25 films is still noise. The gate re-evaluates
    # inside the current filter, so "top studios per genre" only ever ranks
    # studios with at least 25 measured films IN that genre.
    (
        "Films Measured (studios)",
        "IF ( [Films Measured] >= 25, [Films Measured] )",
        "#,0",
        "Films Measured, suppressed for production companies with fewer than 25 "
        "measured films in the current filter context.",
    ),
    (
        "Median Return (studios)",
        "IF ( [Films Measured] >= 25, [Median Return] )",
        "0.00\\x",
        "Median Return, suppressed below 25 measured films. The gate re-applies "
        "inside any genre or era filter.",
    ),
    (
        "Break-even Rate (studios)",
        "IF ( [Films Measured] >= 25, [Break-even Rate] )",
        "0.0%",
        "Break-even Rate, suppressed below 25 measured films.",
    ),
    (
        "Median Budget (studios)",
        "IF ( [Films Measured] >= 25, [Median Budget] )",
        '\$#,0',
        "Median Budget, suppressed below 25 measured films.",
    ),
    (
        "Revenue Reporting Rate",
        """VAR Pool = CALCULATETABLE ( 'Movies', 'Movies'[Budget] >= 10000 )
VAR Reported = FILTER ( Pool, 'Movies'[Revenue] >= 10000 )
RETURN
    DIVIDE ( COUNTROWS ( Reported ), COUNTROWS ( Pool ) )""",
        "0.0%",
        "Share of films with a credible budget that also report revenue. This rate "
        "climbs steeply with budget size, which is the survivorship problem the "
        "report has to disclose.",
    ),
]

# --------------------------------------------------------------------------- #
# DAX calculated tables                                                        #
# --------------------------------------------------------------------------- #

FUNNEL_DAX = f"""
VAR Pool = ALL ( 'Movies' )
VAR Released = FILTER ( Pool, 'Movies'[Status] = "Released" )
VAR Dated = FILTER ( Released, NOT ISBLANK ( 'Movies'[Release Date] ) )
VAR Budgeted = FILTER ( Dated, 'Movies'[Budget] >= {MIN_BUDGET} )
VAR Earning = FILTER ( Budgeted, 'Movies'[Revenue] >= {MIN_REVENUE} )
VAR Rated = FILTER ( Earning, 'Movies'[Vote Count] >= {MIN_VOTES} )
RETURN
    UNION (
        ROW (
            "Step Order", 1,
            "Step", "Films in the published dataset",
            "Films", {SOURCE_FILMS_STATED} * 1.0,
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
            "Step", "Budget is at least ${MIN_BUDGET:,}",
            "Films", COUNTROWS ( Budgeted ) * 1.0,
            "Why", "Removes placeholder budgets. Thousands of films share values such as 1, 100 and 1,000, which no real production budget would."
        ),
        ROW (
            "Step Order", 6,
            "Step", "Revenue is at least ${MIN_REVENUE:,}",
            "Films", COUNTROWS ( Earning ) * 1.0,
            "Why", "A revenue of 0 means not reported, not earned nothing. An unknown cannot go into a ratio. Judged against the whole starter file this is the biggest data-quality problem: 79% of rows carry a revenue of 0."
        ),
        ROW (
            "Step Order", 7,
            "Step", "At least {MIN_VOTES} audience ratings",
            "Films", COUNTROWS ( Rated ) * 1.0,
            "Why", "An average built from a handful of votes is noise dressed as a score."
        )
    )
"""

LEADERBOARDS = [
    (
        "Top By Box Office",
        "Revenue",
        "'Movies'[Revenue]",
        '\\$#,0',
        "Gross revenue",
    ),
    (
        "Top By Return",
        "ROI",
        "'Movies'[ROI]",
        "0.0\\x",
        "Return on budget",
    ),
    (
        "Top By Acclaim",
        "Vote Average",
        "'Movies'[Vote Average]",
        "0.0",
        "Audience rating",
    ),
    (
        "Top By Gross Profit",
        "Gross Profit",
        "'Movies'[Gross Profit]",
        '\\$#,0',
        "Gross revenue minus budget",
    ),
]


def leaderboard_dax(order_by: str) -> str:
    return f"""
VAR Pool = CALCULATETABLE ( 'Movies', ALL ( 'Movies' ), {MEASURABLE} )
VAR Picked = TOPN ( 10, Pool, {order_by}, DESC )
VAR Ranked =
    ADDCOLUMNS (
        Picked,
        "@Rank", RANKX ( Picked, {order_by}, , DESC, DENSE )
    )
RETURN
    SELECTCOLUMNS (
        Ranked,
        "Rank", [@Rank],
        "Poster", 'Movies'[Poster URL],
        "Film", 'Movies'[Title] & " (" & FORMAT ( 'Movies'[Release Year], "0" ) & ")",
        "Value", {order_by} * 1.0
    )
"""


# --------------------------------------------------------------------------- #
# TMDL emitters                                                                #
# --------------------------------------------------------------------------- #


def emit_column(table: str, name: str, data_type: str, fmt: str | None,
                summarize: str, extra: list[str]) -> str:
    lines = [f"\tcolumn '{name}'" if " " in name or "-" in name else f"\tcolumn {name}"]
    lines.append(f"\t\tdataType: {data_type}")
    if fmt:
        lines.append(f"\t\tformatString: {fmt}")
    lines.append(f"\t\tlineageTag: {tag(table, 'column', name)}")
    lines.append(f"\t\tsummarizeBy: {summarize}")
    lines.append(f"\t\tsourceColumn: {name}")
    for line in extra:
        lines.append(f"\t\t{line}")
    lines.append("")
    lines.append("\t\tannotation SummarizationSetBy = Automatic")
    lines.append("")
    return "\n".join(lines)


def emit_calc_column(table: str, name: str, data_type: str, fmt: str | None,
                     summarize: str, extra: list[str]) -> str:
    """Column of a DAX calculated table: sourceColumn is the field name."""
    quoted = f"'{name}'" if " " in name else name
    lines = [f"\tcolumn {quoted}"]
    lines.append(f"\t\tdataType: {data_type}")
    if fmt:
        lines.append(f"\t\tformatString: {fmt}")
    lines.append(f"\t\tlineageTag: {tag(table, 'column', name)}")
    lines.append(f"\t\tsummarizeBy: {summarize}")
    lines.append(f"\t\tsourceColumn: [{name}]")
    for line in extra:
        lines.append(f"\t\t{line}")
    lines.append("")
    lines.append("\t\tannotation SummarizationSetBy = Automatic")
    lines.append("")
    return "\n".join(lines)


def emit_m_table(name: str, m_expression: str,
                 columns: list[tuple[str, str, str | None, str, list[str]]]) -> str:
    quoted = f"'{name}'" if " " in name else name
    parts = [f"table {quoted}", f"\tlineageTag: {tag(name, 'table')}", ""]
    for col in columns:
        parts.append(emit_column(name, *col))
    parts.append(f"\tpartition {quoted} = m")
    parts.append("\t\tmode: import")
    parts.append("\t\tsource =")
    parts.append(block(m_expression, 4))
    parts.append("")
    parts.append("\tannotation PBI_ResultType = Table")
    parts.append("")
    return "\n".join(parts)


def emit_calculated_table(name: str, expression: str,
                          columns: list[tuple[str, str, str | None, str, list[str]]]) -> str:
    quoted = f"'{name}'" if " " in name else name
    parts = [f"table {quoted}", f"\tlineageTag: {tag(name, 'table')}", ""]
    for col in columns:
        parts.append(emit_calc_column(name, *col))
    parts.append(f"\tpartition {quoted} = calculated")
    parts.append("\t\tmode: import")
    # PBI_Id is Power BI internal metadata and must never be hand-authored.
    parts.append(f"\t\tsource = {dax(expression, 4)}")
    parts.append("")
    return "\n".join(parts)


def emit_measures_table() -> str:
    parts = ["table _Measures", f"\tlineageTag: {tag('_Measures', 'table')}", ""]
    for name, expression, fmt, description in MEASURES:
        # TMDL has no `description` property. A description is a `///` comment
        # above the object; Desktop surfaces it as the field tooltip, so an
        # assumption stays documented at the point it is used.
        parts.append(f"\t/// {' '.join(description.split())}")
        parts.append(f"\tmeasure '{name}' = {dax(expression, 3)}")
        if fmt:
            parts.append(f"\t\tformatString: {fmt}")
        parts.append(f"\t\tlineageTag: {tag('_Measures', 'measure', name)}")
        parts.append("")
    # Mirrors the starter file's own holder table: partition `{ BLANK() }`
    # yields a single inferred column named Value, which stays hidden.
    parts.append("\tcolumn Value")
    parts.append("\t\tisHidden")
    parts.append("\t\tformatString: 0")
    parts.append(f"\t\tlineageTag: {tag('_Measures', 'column', 'Value')}")
    parts.append("\t\tsummarizeBy: sum")
    parts.append("\t\tisNameInferred")
    parts.append("\t\tsourceColumn: [Value]")
    parts.append("")
    parts.append("\t\tannotation SummarizationSetBy = Automatic")
    parts.append("")
    parts.append("\tpartition _Measures = calculated")
    parts.append("\t\tmode: import")
    parts.append("\t\tsource = { BLANK() }")
    parts.append("")
    return "\n".join(parts)


RELATIONSHIPS = [
    ("Movies", "Movie ID", "Genre Bridge", "Movie ID", "manyToMany"),
    ("Movies", "Movie ID", "Keyword Bridge", "Movie ID", "manyToMany"),
    ("Movies", "Movie ID", "Production Company Bridge", "Movie ID", "manyToMany"),
    ("Genre Bridge", "Genre ID", "Genres", "Genre ID", None),
    ("Keyword Bridge", "Keyword ID", "Keyword", "Keyword ID", None),
    ("Production Company Bridge", "Production Company ID",
     "Production Company", "Production Company ID", None),
    ("Movies", "Release Date", "Date", "Date", None),
]

M_KEYWORD = """
let
    Src = Source,
    Keywords = Table.SelectColumns(Src, {"keywords"}),
    SplitKeywords = Table.ExpandListColumn(
        Table.TransformColumns(Keywords, {{"keywords", each List.Transform(Splitter.SplitTextByDelimiter(",", QuoteStyle.Csv)(_), each Text.Clean(Text.Trim(_))), type {text}}}),
        "keywords"),
    KeywordDimension = Table.AddIndexColumn(
        Table.Sort(
            Table.Distinct(
                Table.SelectRows(SplitKeywords, each [keywords] <> null and [keywords] <> "")),
            {{"keywords", Order.Ascending}}),
        "KeywordID", 1, 1, Int64.Type),
    #"Renamed Columns" = Table.RenameColumns(KeywordDimension,{{"keywords", "Keywords"}, {"KeywordID", "Keyword ID"}})
in
    #"Renamed Columns"
"""

M_KEYWORD_BRIDGE = """
let
    Src = Source,
    MovieKeywords = Table.SelectColumns(Src, {"id", "keywords"}),
    SplitKeywords = Table.SelectRows(
        Table.ExpandListColumn(
            Table.TransformColumns(MovieKeywords, {{"keywords", each List.Transform(Splitter.SplitTextByDelimiter(",", QuoteStyle.Csv)(_), Text.Trim), type {text}}}),
            "keywords"),
        each [keywords] <> null and [keywords] <> ""),
    MergeKeywords = Table.NestedJoin(SplitKeywords, {"keywords"}, Keyword, {"Keywords"}, "KeywordLookup", JoinKind.LeftOuter),
    BridgeMovieKeyword = Table.RenameColumns(
        Table.RemoveColumns(
            Table.ExpandTableColumn(MergeKeywords, "KeywordLookup", {"Keyword ID"}, {"Keyword ID"}),
            {"keywords"}),
        {{"id", "Movie ID"}})
in
    BridgeMovieKeyword
"""


def emit_relationships() -> str:
    parts = []
    for from_table, from_col, to_table, to_col, cardinality in RELATIONSHIPS:
        name = tag("rel", from_table, from_col, to_table, to_col)
        fq = f"'{from_table}'.'{from_col}'" if " " in from_table else f"{from_table}.'{from_col}'"
        tq = f"'{to_table}'.'{to_col}'" if " " in to_table else f"{to_table}.'{to_col}'"
        parts.append(f"relationship {name}")
        if cardinality == "manyToMany":
            parts.append("\tfromCardinality: many")
            parts.append("\ttoCardinality: many")
        parts.append(f"\tfromColumn: {fq}")
        parts.append(f"\ttoColumn: {tq}")
        parts.append("")
    return "\n".join(parts)


def main() -> int:
    global MODEL, DEFN
    bundled = "--bundled" in sys.argv
    data_folder_default = "C:" + chr(92) + "MovieSuccess" + chr(92) + "Data"
    if "--data-folder" in sys.argv:
        data_folder_default = sys.argv[sys.argv.index("--data-folder") + 1]
    if bundled:
        MODEL = REPO / "work" / "bundle" / "MovieSuccess" / "MovieSuccess.SemanticModel"
        DEFN = MODEL / "definition"

    movies_m = bundled_movies_m() if bundled else M_MOVIES
    override_m = (
        {name: bundled_load(name) for name in BUNDLED_TYPES if name != "Movies"}
        if bundled else {}
    )

    if MODEL.exists():
        shutil.rmtree(MODEL)
    (DEFN / "tables").mkdir(parents=True, exist_ok=True)

    # ---- .platform and definition.pbism -----------------------------------
    (MODEL / ".platform").write_text(
        '{\n'
        '  "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/'
        'platformProperties/2.0.0/schema.json",\n'
        '  "metadata": {\n'
        '    "type": "SemanticModel",\n'
        '    "displayName": "MovieSuccess"\n'
        '  },\n'
        '  "config": {\n'
        '    "version": "2.0",\n'
        f'    "logicalId": "{tag("platform", "semanticmodel")}"\n'
        '  }\n'
        '}\n',
        encoding="utf-8",
    )
    # Exactly as Microsoft's PBIP reference specifies. The $schema line is not
    # decoration: Desktop validates against it.
    (MODEL / "definition.pbism").write_text(
        '{\n'
        '  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/'
        'semanticModel/definitionProperties/1.0.0/schema.json",\n'
        '  "version": "4.2",\n'
        '  "settings": {\n'
        '    "qnaEnabled": true\n'
        '  }\n'
        '}\n',
        encoding="utf-8",
    )

    # ---- database.tmdl -----------------------------------------------------
    (DEFN / "database.tmdl").write_text(
        "database\n\tcompatibilityLevel: 1567\n", encoding="utf-8"
    )

    # ---- expressions.tmdl --------------------------------------------------
    expressions = [
        "/// The full path to TMDB_movie_dataset_v11.csv on this machine.",
        "/// This is the one value you must set before refreshing. The official",
        "/// contest instructions ask for exactly this edit.",
        f"expression CsvPath = {M_CSV_PATH}",
        f"\tlineageTag: {tag('expression', 'CsvPath')}",
        "",
        "\tannotation PBI_ResultType = Text",
        "",
        "/// The raw CSV, transcribed from the starter file.",
        "expression Source =",
        block(M_SOURCE, 2),
        f"\tlineageTag: {tag('expression', 'Source')}",
        "",
        "\tannotation PBI_ResultType = Table",
        "",
        "/// Column names and one sample row, as shipped in the starter file.",
        "expression Schema =",
        block(M_SCHEMA, 2),
        f"\tlineageTag: {tag('expression', 'Schema')}",
        "",
        "\tannotation PBI_ResultType = Table",
        "",
    ]
    if bundled:
        expressions = [
            "/// Full path of the Data folder that ships next to the .pbip,",
            "/// WITHOUT a trailing backslash. This is the one value to set",
            "/// before refreshing.",
            'expression DataFolder = "' + data_folder_default
            + '" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]',
            f"\tlineageTag: {tag('expression', 'DataFolder')}",
            "",
            "\tannotation PBI_ResultType = Text",
            "",
        ]
    (DEFN / "expressions.tmdl").write_text("\n".join(expressions), encoding="utf-8")

    # ---- relationships.tmdl ------------------------------------------------
    (DEFN / "relationships.tmdl").write_text(emit_relationships(), encoding="utf-8")

    # ---- tables ------------------------------------------------------------
    tables_written: list[str] = []

    (DEFN / "tables" / "Movies.tmdl").write_text(
        emit_m_table("Movies", movies_m, MOVIES_COLUMNS), encoding="utf-8"
    )
    tables_written.append("Movies")

    for name, m_expr, columns in SIMPLE_TABLES:
        (DEFN / "tables" / f"{name}.tmdl").write_text(
            emit_m_table(name, override_m.get(name, m_expr), columns),
            encoding="utf-8",
        )
        tables_written.append(name)

    for name, m_expr, columns in [
        ("Keyword", M_KEYWORD, [("Keywords", "string", None, "none", []),
                                ("Keyword ID", "int64", "0", "none", [])]),
        ("Keyword Bridge", M_KEYWORD_BRIDGE, [("Movie ID", "int64", "0", "none", []),
                                              ("Keyword ID", "int64", "0", "none", [])]),
    ]:
        (DEFN / "tables" / f"{name}.tmdl").write_text(
            emit_m_table(name, override_m.get(name, m_expr), columns),
            encoding="utf-8",
        )
        tables_written.append(name)

    (DEFN / "tables" / "_Measures.tmdl").write_text(
        emit_measures_table(), encoding="utf-8"
    )
    tables_written.append("_Measures")

    (DEFN / "tables" / "Funnel.tmdl").write_text(
        emit_calculated_table(
            "Funnel",
            FUNNEL_DAX,
            [
                ("Step Order", "int64", "0", "none", ["isHidden"]),
                ("Step", "string", None, "none", ["sortByColumn: 'Step Order'"]),
                ("Films", "double", "#,0", "sum", []),
                ("Why", "string", None, "none", []),
            ],
        ),
        encoding="utf-8",
    )
    tables_written.append("Funnel")

    for name, _column, order_by, value_format, value_label in LEADERBOARDS:
        (DEFN / "tables" / f"{name}.tmdl").write_text(
            emit_calculated_table(
                name,
                leaderboard_dax(order_by),
                [
                    ("Rank", "int64", "0", "none", []),
                    ("Poster", "string", None, "none", ["dataCategory: ImageUrl"]),
                    ("Film", "string", None, "none", []),
                    ("Value", "double", value_format, "sum", []),
                ],
            ),
            encoding="utf-8",
        )
        tables_written.append(name)

    # ---- model.tmdl --------------------------------------------------------
    query_order = (
        '["Source","Schema","Movies","Production Company","Genres","Genre Bridge",'
        '"Production Company Bridge","Keyword","Keyword Bridge","Date"]'
    )
    if bundled:
        query_order = (
            '["DataFolder","Movies","Production Company","Genres","Genre Bridge",'
            '"Production Company Bridge","Keyword","Keyword Bridge","Date"]'
        )
    model_lines = [
        "model Model",
        "\tculture: en-US",
        "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
        "\tdiscourageImplicitMeasures",
        "\tsourceQueryCulture: en-US",
        "\tdataAccessOptions",
        "\t\tlegacyRedirects",
        "\t\treturnErrorValuesAsNull",
        "",
        "annotation PBI_QueryOrder = " + query_order,
        "",
        "annotation __PBI_TimeIntelligenceEnabled = 0",
        "",
    ]
    for name in tables_written:
        quoted = f"'{name}'" if " " in name else name
        model_lines.append(f"ref table {quoted}")
    model_lines.append("")
    (DEFN / "model.tmdl").write_text("\n".join(model_lines), encoding="utf-8")

    print(f"semantic model written to {MODEL.relative_to(REPO)}")
    print(f"  tables:       {len(tables_written)}  ({', '.join(tables_written)})")
    print(f"  measures:     {len(MEASURES)}")
    print(f"  relationships:{len(RELATIONSHIPS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
