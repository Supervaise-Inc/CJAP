# The Panganiban Knowledge Base

This folder is the knowledge base behind the conversation app that speaks as retired Philippine Chief Justice
Artemio V. Panganiban (“CJP”). It was prepared by the Supervaise project team for the Foundation. It holds
1,290 documents – his newspaper columns, the chapters of his books, his speeches and two biographies – each in
three forms, plus the map the app uses to decide which documents to read when someone asks a question.

Everything here is a copy. It is produced by a script from the project’s pinned source files and is never edited by hand; if
something in this folder is wrong, the fix is made at the source and the folder is rebuilt. `MANIFEST.md` lists every file with its
SHA-256 fingerprint, so any copy can be checked against the original.

## 1. What the corpus is and where it came from

| Kind of document | Documents | What they are |
|---|---:|---|
| Columns | 803 | *With Due Respect*, Justice Panganiban’s column in the Philippine Daily Inquirer, 17 April 2011 to 21 September 2026 |
| Book chapters | 299 | One document per chapter, from 18 works (table below) |
| Speeches | 153 | Speeches and addresses, 23 November 1994 to 27 April 2026 |
| Biography chapters | 35 | Chapters of two biographies written about him by other authors |
| **Total** | **1,290** | |

**Book chapters by work.** “Chapters” are the chapters (or sections) that were turned into documents.

| Work | Published | Chapters in the corpus |
|---|---:|---:|
| Love God, Serve Man | 1994 | 22 |
| Justice and Faith | 1997 | 14 |
| Battles in the Supreme Court | 1998 | 11 |
| Leadership by Example: The Davide Standard | 1999 | 14 |
| Transparency, Unanimity & Diversity | 2000 | 24 |
| A Centenary of Justice | 2001 | 23 |
| Reforming the Judiciary | 2002 | 20 |
| The Bio-Age Dawns on the Judiciary | 2003 | 20 |
| Leveling the Playing Field | 2004 | 20 |
| Judicial Renaissance | 2005 | 21 |
| Liberty and Prosperity | 2006 | 35 |
| With Due Respect (Vol. 1) | 2011 | 10 |
| With Due Respect (Vol. 2) | 2011 | 10 |
| With Due Respect (Vol. 3) | 2011 | 10 |
| With Due Respect (Vol. 4) | 2011 | 10 |
| With Due Respect (Vol. 5) | 2011 | 10 |
| With Due Respect (Vol. 6) | 2011 | 10 |
| With Due Respect (Vol. 7) | 2011 | 15 |

The seven *With Due Respect* volumes reprint columns from 2007 to 2011, so they are the only column material from those years in the
corpus; the columns of that period that were never sourced are described in section 6. *Liberty and Prosperity* (2006) is his own book; it is not the biography with a
similar title described next.

**Biography chapters.** `GC001` to `GC020` are the twenty chapters, Prologue to Epilogue, of Reginald T. Yu’s *Liberty and
Prosperity: The Making of Chief Justice Artemio Villaseñor Panganiban Jr.*; `GC021` to `GC035` are the fifteen chapters of a second
biography (Chapter 1, Early Years, to Chapter 15, Papal Award). In these documents the author is the biographer, not Justice Panganiban,
and his own words appear only as quotations.

**How each document was prepared.** The source text of every document was collected and cleaned first. A description of each was then
written in a fixed set of fields – a one-paragraph summary, keywords, the people and institutions named, his stances, anecdotes, the
audience it suits, the register (tone) it is written in, and the decision-making signals it shows – with AI assistance and spot-checks by the project team, and
recorded in four spreadsheets. Those descriptions are the project’s notes *about* a document; they are not Justice Panganiban’s words.
The words themselves are in `data/text`.

## 2. What is in this folder

```
knowledge-base/
  README.md, MANIFEST.md
  data/
    text/         1,290 source texts, one file per document, named <doc_id>.md
    enriched/     columns.csv, books.csv, speeches.csv, biography.csv - the descriptive fields, one row per document
  corpus/
    columns/ books/ speeches/ biography/   one folder per theme; each document is a pair: <doc_id>.md and <doc_id>.json
    topic_map.json     the 30-dimension topic map (section 5)
    voice_card.md      how the app is told to speak as Justice Panganiban
    router_prompt.md   how the app is told to choose a dimension for a question
```

* **`data/text/<doc_id>.md`** – the source text. Columns, book chapters and speeches start with a short header (title, date, publisher, source); biography chapters are the chapter text alone.
* **`data/enriched/*.csv`** – the four spreadsheets exported as plain CSV files (UTF-8, with a byte-order mark so Excel opens them correctly). The column called *Article Code* is the document’s ID. The biography file has no *Link* column because chapters of a book have no web address.
* **`corpus/<kind>/<theme>/<doc_id>.md`** – the document’s *card*: its descriptive fields at the top, then the full text.
* **`corpus/<kind>/<theme>/<doc_id>.json`** – the same descriptive fields in a form a program can read, plus `topic_paths` (section 5) and `source_xlsx`, which names the spreadsheet the row came from (the spreadsheets themselves are not in this folder; `data/enriched` replaces them).

The search indexes (the files that let the app look documents up by meaning and by keyword) are large binary files and are **not** in this
folder. They stay in the project repository under `data/index/`; `MANIFEST.md` names each one, its size and its build date.

## 3. What a document ID means

An ID such as `SB085` has three parts:

1. **First letter – the kind:** `C` column, `B` book chapter, `S` speech, `G` biography chapter.
2. **Second letter – the theme:** `A` to `E` (section 4).
3. **Three digits – a number** within that kind and theme. The number is only a label; it does not follow date order.

**IDs are never reused.** If a document is withdrawn, its ID is retired for good and no later document takes it. That is why the
numbers within a kind and theme have gaps, and why five IDs are missing (section 6).

## 4. The five themes

Each document sits in exactly one theme, which is its folder and its second letter. Themes are broad shelves; they are not the topic map.

| Letter | Theme | Documents |
|---|---|---:|
| A | Liberty and Rule of Law | 678 |
| B | Prosperity and Economic Philosophy | 85 |
| C | Biographical and Personal | 249 |
| D | FLP Mission and Foundation | 119 |
| E | Signature Current Events Commentary | 159 |

## 5. The topic map

The **topic map** (`corpus/topic_map.json`) is the list of subjects the app can route a question to. Each subject is a **dimension** – for
example *Libel and Cybercrime* or *Liberty and Prosperity: the Twin Beacons*. When someone asks a question, the app picks the one or two dimensions that fit it and reads
the documents filed under them.

The current map has **30 dimensions**. It was derived from the whole 1,290-document corpus in September 2026. It replaces a 35-topic
list that had been written when the corpus held only 79 documents and had never seen a book; that list is retired and is not in this folder.

Every dimension has a definition, a list of member documents and a set of keywords that identify it. Beside the 30 dimensions the map holds one **intent**,
`robot_identity_meta`, for questions about the robot itself rather than about the law; it is handled separately and is not a subject.

| Dimension ID | Name | What it covers | Documents listed in the map |
|---|---|---|---:|
| `foundation_for_liberty_and_prosperity` | The Foundation for Liberty and Prosperity and Its Benefactors | The Foundation's work and people: scholarships and dissertation fellows, its museum and Prosperity Fund, and the business leaders and donors who fund it. | 107 |
| `twin_beacons_doctrine` | Liberty and Prosperity: the Twin Beacons | The Chief Justice's core philosophy that liberty and prosperity depend on each other, and that both rest on the rule of law and social justice. | 41 |
| `life_story_family_school_and_church` | Life Story: Family, School and Church | The Chief Justice's own life: his family, his schooling and mentors, his church and community life, and the eulogies and tributes he gives to people who shaped him. | 193 |
| `criminal_trials_and_prosecutions` | Criminal Trials, Prosecutions and the ICC | How major criminal cases actually proceed in the Philippines: bail, probable cause, the Sandiganbayan and the plunder and pork-barrel trials, and the International Criminal Court's case against Duterte. | 164 |
| `international_law_disputes` | International Law: the West Philippine Sea and Arbitration | The Philippines' sea dispute with China: the 2016 arbitral award, UNCLOS, the exclusive economic zone and the nine-dash line, and what international arbitration can and cannot enforce. | 85 |
| `property_contracts_and_economic_rights` | Property, Contracts and Labor Rights | Supreme Court decisions on ownership, contracts, natural resources, investment and labor, read for what they mean for livelihoods and business. | 66 |
| `presidential_power_martial_law_people_power` | Presidential Power, Martial Law and People Power | The limits of presidential power in a crisis: martial law and rebellion, EDSA and the presidencies of Estrada and Arroyo. | 45 |
| `elections_and_automated_voting` | Elections and Automated Voting | How Philippine elections are run and litigated: the Commission on Elections, precinct-count optical scanners and the disputes over automation. | 91 |
| `judicial_reform` | Judicial Reform and Court Delay | Reforming the courts: the Action Program for Judicial Reform, case backlogs, judges' pay and how to speed up justice. | 54 |
| `party_list_charter_change_and_dynasties` | Party-List, Charter Change and Political Dynasties | How Congress is chosen and the Constitution is amended: the party-list system, Charter change and political dynasties. | 68 |
| `science_technology_and_the_law` | Science, Technology and the Law | How courts and lawyers should deal with new science: DNA and genetics, cloning, the internet and artificial intelligence. | 63 |
| `impeachment_accountability` | Impeachment | The impeachment process from the House to the Senate: its rules and limits, and the Corona and Sara Duterte cases. | 47 |
| `public_funds_budget_and_bank_evidence` | Public Funds, the Budget and Bank Evidence | How public money is spent and traced: the budget, the DAP and PDAF rulings, and bank deposits used as evidence of corruption. | 47 |
| `us_supreme_court_and_american_politics` | The US Supreme Court and American Politics | Commentary on the American presidency and the US Supreme Court, from Trump to Biden and the electoral college, and what they teach the Philippines. | 50 |
| `faith_journey` | Faith: Scripture, Prayer and the Gospel | Reflections on scripture and prayer, on Jesus and the Gospel and on the Bukas Loob sa Diyos community, drawn mainly from the faith-themed books. | 49 |
| `how_the_supreme_court_decides` | How the Supreme Court Decides | How the Court reasons and writes its decisions, and why the judiciary's independence from the other branches matters. | 21 |
| `libel_and_cybercrime` | Libel and Cybercrime | Criminal libel and cybercrime cases: the Maria Ressa cyberlibel prosecution, libel of public figures online, and the Cybercrime Prevention Act. | 28 |
| `judiciary_milestones_and_tributes` | The Judiciary's Milestones and Tributes | Celebrations of the judiciary and of the people in it: the Supreme Court centenary, retirements, book launches, honors and tributes to fellow justices. | 37 |
| `economy_taxes_and_prosperity` | The Economy, Taxes and Wages | Economic policy seen through a lawyer's eyes: growth, jobs, taxes and wages, and what makes nations prosper. | 17 |
| `death_penalty_and_echegaray` | The Death Penalty and the Echegaray Reflection | The Chief Justice's writing on capital punishment: the Echegaray case, the 2006 abolition of the death penalty and the conscience-versus-institution distinction. | 30 |
| `independent_commissions_and_appointments` | Independent Commissions and Appointments | The constitutional commissions and the Ombudsman: how their officials are appointed, how long they serve and how independent they really are. | 15 |
| `bangsamoro_peace_process` | The Bangsamoro Peace Process | The peace agreements with the MILF, the Bangsamoro Basic Law and the question of whether they fit the Constitution. | 28 |
| `marcos_robredo_election_contest` | The Marcos-Robredo Election Contest | The vice-presidential protest of 2016 and the 2022 campaign that followed: canvassing, protests and what the results meant. | 38 |
| `supreme_court_vacancies_and_chief_justiceship` | Supreme Court Vacancies and the Chief Justiceship | Who sits on the Court and who leads it: retirements, appointments by President Duterte and the succession to the chief justiceship. | 28 |
| `asean_law_association` | The ASEAN Law Association | The regional association of lawyers and judges the Chief Justice helped lead, and the rule of law in Southeast Asia. | 11 |
| `ill_gotten_wealth_and_the_pcgg` | Ill-Gotten Wealth and the PCGG | The recovery of wealth amassed under Marcos: sequestration, forfeiture and the Sandiganbayan's rulings. | 27 |
| `bar_exam_and_legal_education` | The Bar Exam and Legal Education | How lawyers are trained and admitted: the bar examinations, legal education and the profession's duties. | 20 |
| `citizenship_and_residency_grace_poe` | Citizenship and Residency: the Grace Poe Case | Who counts as a natural-born citizen (foundlings, dual citizens and residency), argued through the Grace Poe case. | 24 |
| `marriage_annulment_and_the_family_code` | Marriage, Annulment and the Family Code | How the law treats marriage: psychological incapacity, nullity, divorce and the Family Code. | 29 |
| `jbc_discernment_and_appointment` | The Judicial and Bar Council | How judges are nominated: the Council's role, its rules and the shortlist for each vacancy. | 34 |

**How each document is filed.** Every card carries a `topic_paths` field with a `primary` dimension, up to a few `secondary` ones, and a `route_source` that says how the filing was decided:

| `route_source` | Meaning | Documents |
|---|---|---:|
| `matcher` | Keyword matchers (the dimension’s own keywords, names and cases) recognised the document. | 1,045 |
| `affinity` | No matcher recognised it, but its passages sit close to one dimension. *Affinity* is the similarity between a document’s closest passage and the centre of a dimension; a document is filed there only above a fixed floor (0.31 on the app’s centred scale). | 227 |
| `orphan` | Neither. The `primary` is an explicit `null` – no topic – never a blank. | 18 |
| **Total** | | **1,290** |

`topic_map.json` lists the 1,045 documents the matchers filed. The 227 affinity-filed documents carry their dimension in their own `.json` card only, so
adding up the member lists in the map gives fewer documents than the corpus holds.

## 6. What is deliberately not here

* **About 222 Inquirer columns from February 2007 to April 2011.** They were never sourced, so there is nothing to put in the corpus. The columns that are here start on 17 April 2011. Some columns from that period do appear, as chapters of the seven *With Due Respect* volumes (75 chapters); the ~222 unsourced columns are not otherwise represented.
* **Five retired documents.** Each was withdrawn from the corpus in September 2026. Their IDs are retired and are deliberately not listed in this folder.

| Retired document | Why it was withdrawn |
|---|---|
| A Centenary of Justice -- Ch. 20: Social Weather Stations v. Comelec -- May Election Surveys Be Banned? | No source text (summary-only); chapter text not in data/ and not online |
| A Centenary of Justice -- Appendix D: MPGR (a tribute to Justice Minerva P. Gonzaga-Reyes) | No source text (summary-only); not in data/ and not online |
| A Centenary of Justice -- Back Matter: Davide Foreword, Accolades & Aquino Book Review | No source text (summary-only); paratext written by others about the book |
| A Centenary of Justice -- Front Matter (Cover, Centennial Prayer, Contents, Foreword, Preface) | No source text (summary-only); not in data/ and not online |
| How the Judiciary Can Help the Economy | Duplicate of SB085 (same title, date 2012-11-29 and link); SB085 carries the full text |

## 7. Known limitations

**Three biography chapters do not fit the dimensions.**

- `GC012` – The Call from Malacañang -- and the First Refusal
- `GC015` – The Bench
- `GC018` – Retirement Without Retreat

No dimension came close enough to these chapters to clear the affinity floor. `GC015` and `GC018` carry no topic (`primary` is `null`); `GC012` carries a keyword-matched
filing (Life Story: Family, School and Church) although it sits below that floor. Across the whole corpus 18 documents have no topic (11 columns, 2 books, 3 speeches, 2 biography chapters; the full list is in `MANIFEST.md`),
and 22 more are filed by a keyword matcher although their affinity is below the floor.

**Dates: 1 January means “the year”.** 45 documents – 25 biography chapters and 20 book chapters (all from *The Bio-Age Dawns on the Judiciary*) – are dated 1 January of a year. For these the project has no date finer than the year, and 1 January is a placeholder, not a day.
The date is left as it appears in the source, everywhere in this folder. The app’s date index labels these documents “year” precision instead of “day”, so a search by date does not treat them as exact days. Please read any 1 January date on a book or biography chapter as “sometime that year”.

**The descriptive fields are drafted, not authored.** Summaries, keywords, stances and the rest were drafted with AI assistance and spot-checked, not read line by line by Justice Panganiban or the Foundation. Treat them as a guide to the text, and the text in `data/text` as the authority.

**Known limitation – topic routing.** Topic routing is newly rebuilt and has not been validated end to end. The routing measured here is the closest-dimension router in the app’s retrieval code, which compares a question with the centre of each of the 30 dimensions. On 30 short questions, one per dimension, it named the intended dimension first for 26 of 30 (86.7%) and within its top three for 26 of 30 (86.7%). Four dimensions never won their own question: `judiciary_milestones_and_tributes` (“Tell me about the centenary.” went to `foundation_for_liberty_and_prosperity`); `public_funds_budget_and_bank_evidence` (“What is the pork barrel?” went to `economy_taxes_and_prosperity`, with a closeness of 0.0938, under the router’s 0.12 out-of-scope line); `twin_beacons_doctrine` (“What is the twin-beacons doctrine?” went to `international_law_disputes`); `ill_gotten_wealth_and_the_pcgg` (“What is ill-gotten wealth?” went to `economy_taxes_and_prosperity`). One of the four is the project’s flagship concept, the twin-beacons doctrine. A second set of 60 longer, descriptive questions (two per dimension) did better – 86.7% first and 100% within three, with every dimension winning at least one of its own questions – but 8 questions still went to a wrong first choice. Chance for 30 dimensions is 3.3% first and 10% within three, so the router is doing real work; it is not yet reliable enough to trust unattended. Two things were not measured: the live robot’s own router (a language-model call driven by router_prompt.md, which needs an API key that was not available) and end-to-end answer quality. On the frozen 40-query retrieval set, 14 of 40 selected result sets changed after the move to the 30-dimension map and gold hit@10 fell by 2.9 points, while hit@1, hit@3 and hit@5 did not move. Routing was deliberately not adjusted in this delivery. CE-11 to CE-14 are the gate before the robot is demonstrated.
