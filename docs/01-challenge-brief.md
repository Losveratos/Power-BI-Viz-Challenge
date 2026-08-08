# 01 — Challenge brief (authoritative record)

| Field | Value |
|---|---|
| Competition | Power BI Dataviz World Champs — Barcelona 2026 |
| Round | Round 3 (final round) |
| Title | Lights, Camera, Insight! |
| Opens | July 28 |
| Closes | August 9 |
| Winners announced | August 21 |
| Source | Microsoft Fabric Community blog — <https://community.fabric.microsoft.com/t5/Power-BI-Community-Blog/Power-BI-Dataviz-World-Champs-Round-3/ba-p/5323477> |

This file is the authoritative record of the Round 3 rules for this repository. It
exists so that every later design decision can be traced back to a specific
sentence in the published brief. Where a later document justifies a choice, it
cites an ID from the checklist in section 3. If the brief and a later document
disagree, the brief wins and the later document is wrong.

---

## 1. The brief as published

The text below is quoted verbatim from the source above. It is quoted, not
paraphrased, so that the checklist in section 3 can be audited against it word
for word. Nothing in this blockquote is our own wording.

> Power BI Dataviz World Champs | Round 3
>
> Opens: July 28
> Closes: August 9
> Winners announced: August 21
>
> For Round 3, we're focusing on one of the most important skills a data professional can develop: Using data responsibly. The best analysts don't just create beautiful visuals. They understand the limitations of data, question assumptions, communicate uncertainty, and avoid misleading conclusions.
>
> **Welcome to Lights, Camera, Insight!**
> For our final challenge on the road to Barcelona, you'll be working with a dataset built from publicly available movie data. The dataset includes information about thousands of films, including: Genres, Production companies, Release dates, Revenue, Budgets, Popularity, Audience ratings, And more
>
> In this round, there isn't a single "right" answer. A movie can be a box office hit, a critical darling, or an incredible return on investment. The data can support multiple stories. Your job is to decide which one is worth telling.
>
> **Your Challenge**
>
> Use Power BI to answer the question:
>
> What makes a movie successful? There is no single correct answer. The strongest entries will:
> - Define success clearly
> - Support conclusions with evidence
> - Acknowledge tradeoffs and limitations
> - Communicate findings honestly and responsibly
>
> Remember: this is not a dashboard-building exercise - this is a data storytelling challenge.
>
> **What You Can and Cannot Do**
>
> You CAN
> - Clean and transform the provided data
> - Create calculations and measures
> - Build additional tables derived from the supplied dataset
> - Use custom visuals
> - Add images, logos, posters, and other visual assets
> - Use movie posters, artwork, or images linked directly from the provided dataset
> - Use AI tools to assist with design, accessibility, and report development
>
> You CANNOT
> - Add external datasets
> - Join the dataset to IMDb, Wikipedia, Rotten Tomatoes, Box Office Mojo, TMDB APIs, or any other outside source
> - Bring in additional ratings, revenue data, reviews, awards data, or movie metadata not included in the provided files
> - Use data obtained through web scraping
> - Use any information that would materially change or enrich the underlying dataset
>
> In short: You may enhance the presentation of the data. You may not enhance the data itself. All competitors should be working from the same information.
>
> **Key Takeaway Requirement**
> Every submission must include a visible Key Takeaway statement on the landing page.
> The statement must:
> - Be 50 words or fewer
> - Be written for a general audience
> - Clearly summarize the most important insight from your report
>
> Think of it as the headline of your story.
>
> **Judging Criteria**
> Entries will be evaluated on:
> - Insightfulness
> - Visual Effectiveness
> - Storytelling and Communication
> - Creativity and Innovation
> - Accessibility
> - Responsible Data Use
>
> Responsible Data Use includes:
> - Appropriate interpretation of metrics
> - Clear explanation of assumptions
> - Recognition of limitations
> - Avoidance of misleading comparisons
> - Honest communication of uncertainty
>
> Remember: A beautiful report with a weak conclusion will not outperform a thoughtful report built on strong analysis.
>
> **Submission Requirements**
>
> All submissions must:
> - Be built in Power BI Desktop
> - Be a single .pbix file
> - Contain no more than 5 pages (additional hidden pages used as tooltips are allowed)
> - Use the provided dataset
> - Include at least three core Power BI visuals
> - Meet accessibility expectations: Clear labels and alt text; Strong contrast; Intentional layout and reading order
>
> Accessibility remains a significant portion of your score. Don't skip it.
>
> How to submit:
> - In the Contests gallery, select Submit to contest
> - Add your submission. Be sure to add: Image, Description, .pbix file or Publish to Web URL, Tag your entry with "World Champs BCN"

---

## 2. How the IDs work

Each obligation in the brief is given a stable ID. IDs never change once
assigned, even if the wording of this file is later improved, because other
documents cite them.

| Series | Meaning | Failure mode if ignored |
|---|---|---|
| `R-nn` | Hard rule. Objectively verifiable, pass or fail. | Disqualification or a mechanical rejection. |
| `J-nn` | Judged criterion. Scored subjectively by the judges. | Lost points. |
| `P-nn` | Prohibition. Something the entry must not do. | Disqualification. |
| `A-nn` | Permission. Explicitly allowed by the brief; carries no obligation. | None. Recorded so the boundary of the prohibitions is unambiguous. |

The `A-nn` series is not one of the three requirement types, and its entries are
kept in a separate table in section 4. It exists because the brief's "You CAN"
list is what makes the "You CANNOT" list interpretable: the two lists together
define where enhancing the presentation stops and enriching the data begins.

The brief's description of the dataset's contents — "Genres, Production
companies, Release dates, Revenue, Budgets, Popularity, Audience ratings, And
more" — is descriptive rather than obligatory and is therefore recorded in
section 5 rather than given a requirement ID.

---

## 3. Requirements extracted as a checklist

### 3.1 Hard rules

| ID | Requirement | Type | Source phrase |
|---|---|---|---|
| R-01 | Submit within the entry window: it opens July 28 and closes August 9. | Hard rule | "Opens: July 28 / Closes: August 9" |
| R-02 | Use Power BI to answer the question "What makes a movie successful?" | Hard rule | "Use Power BI to answer the question: What makes a movie successful?" |
| R-03 | Deliver a data story, not a dashboard. | Hard rule | "this is not a dashboard-building exercise - this is a data storytelling challenge" |
| R-04 | Include a visible Key Takeaway statement on the landing page. | Hard rule | "Every submission must include a visible Key Takeaway statement on the landing page." |
| R-05 | The Key Takeaway is 50 words or fewer. | Hard rule | "Be 50 words or fewer" |
| R-06 | The Key Takeaway is written for a general audience. | Hard rule | "Be written for a general audience" |
| R-07 | The Key Takeaway clearly summarizes the most important insight of the report. | Hard rule | "Clearly summarize the most important insight from your report" |
| R-08 | The entry is built in Power BI Desktop. | Hard rule | "Be built in Power BI Desktop" |
| R-09 | The entry is a single .pbix file. | Hard rule | "Be a single .pbix file" |
| R-10 | No more than 5 pages. Additional hidden pages used as tooltips are allowed. | Hard rule | "Contain no more than 5 pages (additional hidden pages used as tooltips are allowed)" |
| R-11 | The entry uses the provided dataset. | Hard rule | "Use the provided dataset" |
| R-12 | The entry includes at least three core Power BI visuals. | Hard rule | "Include at least three core Power BI visuals" |
| R-13 | Accessibility: clear labels and alt text. | Hard rule | "Meet accessibility expectations: Clear labels and alt text" |
| R-14 | Accessibility: strong contrast. | Hard rule | "Meet accessibility expectations: ... Strong contrast" |
| R-15 | Accessibility: intentional layout and reading order. | Hard rule | "Meet accessibility expectations: ... Intentional layout and reading order" |
| R-16 | Submit through the Contests gallery using "Submit to contest". | Hard rule | "In the Contests gallery, select Submit to contest" |
| R-17 | The submission includes an image. | Hard rule | "Be sure to add: Image" |
| R-18 | The submission includes a description. | Hard rule | "Be sure to add: ... Description" |
| R-19 | The submission includes the .pbix file or a Publish to Web URL. | Hard rule | "Be sure to add: ... .pbix file or Publish to Web URL" |
| R-20 | The entry is tagged "World Champs BCN". | Hard rule | "Tag your entry with \"World Champs BCN\"" |

### 3.2 Judged criteria

| ID | Requirement | Type | Source phrase |
|---|---|---|---|
| J-01 | Define success clearly. | Judged criterion | "Define success clearly" |
| J-02 | Support conclusions with evidence. | Judged criterion | "Support conclusions with evidence" |
| J-03 | Acknowledge tradeoffs and limitations. | Judged criterion | "Acknowledge tradeoffs and limitations" |
| J-04 | Communicate findings honestly and responsibly. | Judged criterion | "Communicate findings honestly and responsibly" |
| J-05 | Insightfulness. | Judged criterion | "Insightfulness" |
| J-06 | Visual effectiveness. | Judged criterion | "Visual Effectiveness" |
| J-07 | Storytelling and communication. | Judged criterion | "Storytelling and Communication" |
| J-08 | Creativity and innovation. | Judged criterion | "Creativity and Innovation" |
| J-09 | Accessibility, which is a significant portion of the score. | Judged criterion | "Accessibility" / "Accessibility remains a significant portion of your score. Don't skip it." |
| J-10 | Responsible data use. | Judged criterion | "Responsible Data Use" |
| J-11 | Appropriate interpretation of metrics. | Judged criterion | "Appropriate interpretation of metrics" |
| J-12 | Clear explanation of assumptions. | Judged criterion | "Clear explanation of assumptions" |
| J-13 | Recognition of limitations. | Judged criterion | "Recognition of limitations" |
| J-14 | Avoidance of misleading comparisons. | Judged criterion | "Avoidance of misleading comparisons" |
| J-15 | Honest communication of uncertainty. | Judged criterion | "Honest communication of uncertainty" |
| J-16 | Analytical strength outranks visual polish; a weak conclusion is not rescued by a beautiful report. | Judged criterion | "A beautiful report with a weak conclusion will not outperform a thoughtful report built on strong analysis." |

### 3.3 Prohibitions

| ID | Requirement | Type | Source phrase |
|---|---|---|---|
| P-01 | Do not add external datasets. | Prohibition | "Add external datasets" |
| P-02 | Do not join the dataset to IMDb, Wikipedia, Rotten Tomatoes, Box Office Mojo, TMDB APIs, or any other outside source. | Prohibition | "Join the dataset to IMDb, Wikipedia, Rotten Tomatoes, Box Office Mojo, TMDB APIs, or any other outside source" |
| P-03 | Do not bring in additional ratings, revenue data, reviews, awards data, or movie metadata that is not in the provided files. | Prohibition | "Bring in additional ratings, revenue data, reviews, awards data, or movie metadata not included in the provided files" |
| P-04 | Do not use data obtained through web scraping. | Prohibition | "Use data obtained through web scraping" |
| P-05 | Do not use any information that would materially change or enrich the underlying dataset. | Prohibition | "Use any information that would materially change or enrich the underlying dataset" |
| P-06 | Enhance the presentation only, never the data; all competitors work from the same information. | Prohibition | "You may enhance the presentation of the data. You may not enhance the data itself. All competitors should be working from the same information." |

---

## 4. Permissions recorded for completeness

These are latitudes, not obligations. They are recorded because they mark the
outer edge of P-01 to P-06.

| ID | Permission | Type | Source phrase |
|---|---|---|---|
| A-01 | Clean and transform the provided data. | Permission | "Clean and transform the provided data" |
| A-02 | Create calculations and measures. | Permission | "Create calculations and measures" |
| A-03 | Build additional tables derived from the supplied dataset. | Permission | "Build additional tables derived from the supplied dataset" |
| A-04 | Use custom visuals. | Permission | "Use custom visuals" |
| A-05 | Add images, logos, posters, and other visual assets. | Permission | "Add images, logos, posters, and other visual assets" |
| A-06 | Use movie posters, artwork, or images linked directly from the provided dataset. | Permission | "Use movie posters, artwork, or images linked directly from the provided dataset" |
| A-07 | Use AI tools to assist with design, accessibility, and report development. | Permission | "Use AI tools to assist with design, accessibility, and report development" |

Note the interaction between A-03 and P-01. A derived table computed from the
supplied columns is permitted; a table typed out from an outside reference is
not, even if it is small and even if it is only used for labelling. The test is
whether the information already exists inside the provided files.

---

## 5. Dataset provenance

The competition data is the TMDB movies dataset, roughly 930,000 films,
distributed through Kaggle by asaniczka:

- Kaggle dataset: <https://www.kaggle.com/datasets/asaniczka/tmdb-movies-dataset-2023-930k-movies>
- Licence: Open Data Commons Attribution License (ODC-By 1.0)
- Official starter file: <https://raw.githubusercontent.com/shannonlindsay/FabricCommunityContests/main/StarterFiles/World%20Champs%20BCN%2026%20-%20Round%203.pbix>

The starter .pbix does not contain the full 930,000 rows. Its Power Query
already filters the source to films with a budget greater than zero, which is
why the row count competitors actually receive is far smaller. The 930,000
figure comes from the brief and the Kaggle dataset description; it cannot be
verified from inside the starter file, and any statement about it must be
attributed rather than asserted.

The fields the brief names as present — genres, production companies, release
dates, revenue, budgets, popularity and audience ratings — are descriptive of
the file's contents, not requirements to use each one.

Attribution is required, both by ODC-By 1.0 and by the starter file's own Read
Me page. The report therefore has to credit the TMDB data via Kaggle on the face
of the entry, not only in this repository. ODC-By 1.0 governs attribution for
the data; it does not license the film posters or artwork, which are used only
as images linked from the provided dataset under A-06.
