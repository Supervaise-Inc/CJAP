# B4 / CE-1b QA — batch-04 book chapters

**Run date** 24 September 2026 · **Under review** `batch-04/books_enriched_normalized.xlsx` (the P5 output, 168 rows)
**Method** a mechanical sweep over every row and every cell, then an independent read of all 168 rows
against their own `batch-04/data_text/<ID>.md` by reviewers who did not write them.
**Prompt** B4 in `BATCH-04_BOOKS_PROMPTS.md`. Read-only apart from this file and `spot_check_books.xlsx`.

---

## 1. Pass / fail

| Check | Result |
|---|---|
| Header — 15 fields in pinned order | **PASS** |
| Row count == manifest `book chapter` rows | **PASS** (168 == 168) |
| Article Codes unique, each with a `data_text/<ID>.md` | **PASS** (168 / 168) |
| Every `Date` text `YYYY-MM-DD` and equal to the manifest | **PASS** (168 / 168) |
| Every `Title` equal to the manifest | **PASS** (168 / 168) |
| Every JSON cell parses, shapes per Data Flow §3 | **PASS** (1,680 / 1,680) |
| `entities` keys within the allowed set | **PASS** |
| `stances.confidence` one of the four allowed values | **PASS** (767 / 767) |
| Every signature phrase **verbatim** in its `.md` | **PASS** (1,421 / 1,421) |
| Every `entities.people` name appears in its `.md` | **FAIL** (1,224 / 1,226 — 2 machine-detected) |
| Independent review: anecdotes, summary and stance attribution | **FAIL** (37 of 168 rows) |

**Verdicts:** pass **38** · pass with notes **93** · fail **37**.
**54 failures** and **168 notes** in all. Of 180 machine hints resolved by the reviewers, 12 were real and the rest were script artefacts (accents, acronyms spelled out, OCR damage).

### The one pattern that matters

**22 of the 54 failures are signature phrases that are verbatim but not his.** The chapters quote other
justices, popes, presidents, church councils and reprinted articles at length, and B3's verbatim check
cannot tell the difference — a line by Justice Regalado, Justice Puno, Chief Justice Narvasa, J. B. L.
Reyes, Abraham Lincoln, Ramon Magsaysay, Confucius or PCP II sits in the text word for word and passes.
For a corpus built to answer **in CJP's voice**, that is the worst kind of error: fluent, sourced, and wrong.

`signature_phrases` needs an attribution test, not just a presence test — B3 should be amended to require
that a phrase be checked against the nearest preceding attribution cue ("As X said", "in the words of X",
"wrote the esteemed magistrate", a block quotation, a named ponencia or dissent) before it is accepted.

### Failures by field

| Field | Failures |
|---|---:|
| `signature_phrases` | 22 |
| `entities.people` | 8 |
| `one_paragraph_summary` | 7 |
| `stances` | 5 |
| `notable_anecdotes` | 5 |
| `entities.laws_treaties` | 2 |
| `primary_topics` | 1 |
| `entities.institutions` | 1 |
| `sub_topics` | 1 |
| `decision_framework_signals` | 1 |
| `entities.events` | 1 |

### Failing rows by book

| Book | Failing | Rows |
|---|---:|---:|
| A Centenary of Justice | 0 | 1 |
| Battles in the Supreme Court | 5 | 11 |
| Judicial Renaissance | 5 | 21 |
| Leadership by Example: The Davide Standard | 3 | 14 |
| Leveling the Playing Field | 4 | 20 |
| Liberty and Prosperity | 6 | 35 |
| Love God, Serve Man | 6 | 22 |
| Reforming the Judiciary | 6 | 20 |
| Transparency, Unanimity & Diversity | 2 | 24 |
| **Total** | **37** | **168** |

---

## 2. Every failure

Each one names the row, the cell and the exact offending text. **Flag, do not fix** — these go back to B3.


### BD028 — Battles in the Supreme Court, Ch. 1

- **`signature_phrases`** — The chapter expressly gives this aphorism to Justice Florenz D. Regalado ('Justice Florenz D. Regalado ... aptly said'), and the row itself credits him with it in sub_topics and in an anecdote, so listing it among CJP's own phrases misattributes it.
  - offending text: `In trial courts, the rule is transparency; but in the Supreme Court, it is confidentiality.`
  - suggested: Drop it from signature_phrases and keep it where the row already has it, as Regalado's formulation that CJP quotes approvingly.

### BA054 — Battles in the Supreme Court, Ch. 4

- **`signature_phrases`** — The chapter gives this line to an unnamed dissenter in the Lethal Injection case ('One member simply wrote...'), not to CJP, and the chapter expressly refuses to identify the authors of death-penalty opinions; the same applies to 'That would be a massacre more gruesome than the AIDS epidemic and the Cambodian killing fields', 'my belief in the transcendent value of life and in the absolute nullity of this law', 'I will continue to vote against every death penalty imposed against any man or woman' and 'This Constitutional explosion of concern for man more than property, for people more than the state, and for life more than mere existence', all of which come from the anonymous quoted dissents.
  - offending text: `The spring cannot rise higher than its source.`
  - suggested: Keep only the phrases the chapter has in CJP's own narrating voice ('death is too final and too irreversible a penalty to stay long in our statute books', 'True, the death penalty is not per se objectionable.', 'The judicial execution of one innocent man cannot be offset by the execution of a hundred others...', 'there is always the haunting possibility that an innocent man would be held legally g
- **`stances`** — This is the argument of the anonymous 32-page Dissent that the chapter reproduces; CJP states at the outset that death-penalty opinions are per curiam and 'I shall not name the ponentes or the dissenters', and repeats at the close that 'I have not identified the justices voting for or against RA 7659', so the text does not make this his own asserted position (confidence 'asserted with evidence').
  - offending text: `Congress did not discharge its constitutional duty under Section 19, Article III: by merely reimposing death on the very same crimes already punishable by death, without defining heinousness or stating compelling reasons crime by crime, RA 7659 failed the two concurrent requirements the Charter imposes.`
  - suggested: Mark it confidence: 'reported (not his view)' and attribute it to the unnamed 32-page dissent, noting separately that CJP interjects in his own voice only that there are now too many capital crimes.
- **`stances`** — This position is stated only inside the Escala Dissenting Opinion, which the chapter reproduces verbatim without naming its author; marking it 'asserted' presents an unidentified dissenter's stand as CJP's own.
  - offending text: `A justice may keep casting a negative vote in every death case even after the majority has ruled: review is de novo, the constitutionality of the law is an indispensable issue in each case, and duty to the Court, the country, conscience and God requires speaking out.`
  - suggested: Mark it confidence: 'reported (not his view)' and describe it as the position of the dissenter whose opinion is reproduced in Escala.
- **`notable_anecdotes`** — That arithmetic appears inside the anonymous Escala dissent, not in CJP's own narration -- his own figures earlier in the chapter are 748 sentences growing by about thirteen a month -- so 'His' misattributes it.
  - offending text: `His arithmetic of alarm: with about 600 death cases decided and thirty more arriving monthly, affirming even half would put one convict to death every working day, giving the Philippines and the Court 'the dubious distinction of being the worst judicial killers in this world.'`
  - suggested: 'The Escala dissenter's arithmetic of alarm: about 600 death cases and thirty more monthly, so that affirming even half would mean one execution every working day...'

### BA056 — Battles in the Supreme Court, Ch. 7

- **`signature_phrases`** — The chapter gives this phrase to Justice Puno -- 'Justice Puno, in his well-articulated Dissent, explained that Article XII, Section 10 of the Constitution, was "pro-Filipino and not anti-alien"' -- so it is a quoted colleague's wording, not CJP's own.
  - offending text: `pro-Filipino and not anti-alien`
  - suggested: Drop it from signature_phrases (it is already correctly reported as Puno's position in sub_topics).
- **`signature_phrases`** — These are Justice Puno's words in his Ople v. Torres ponencia as the chapter quotes them, and the row itself elsewhere marks that rationale 'reported (not his view)'; CJP's own ground in Ople was the narrower legislative-power point.
  - offending text: `a covert invitation to misuse, a temptation that may be just too great for some of our authorities to resist`
  - suggested: Drop it, or keep only CJP's own 'beyond the powers of the President to regulate without a legislative enactment'.

### BA057 — Battles in the Supreme Court, Ch. 9

- **`signature_phrases`** — This sentence belongs to the Court's earlier decision in People v. Aminnudin, which CJP block-quotes inside his Montilla dissent ('In invalidating his arrest, this Court reasoned: ...'), so it is quoted precedent rather than his own wording.
  - offending text: `It was the furtive finger that triggered his arrest`
  - suggested: Drop it from signature_phrases and keep it where the row already has it, as the Aminnudin language he relies on.
- **`signature_phrases`** — The chapter attributes this to the International Military Tribunal at Nuremberg in its Judgment of October 1, 1946, which CJP quotes; the row's own sub_topics say so, yet the phrase is listed as one of his.
  - offending text: `is not the existence of the order but whether moral choice was in fact possible`
  - suggested: Drop it; his own wording on the same point is 'The defense of "obedience to a superior's order" is already obsolete' and 'Resurrecting this internationally discredited Nazi defense'.

### BA058 — Battles in the Supreme Court, Ch. 10

- **`signature_phrases`** — This is the holding of the 8-7 majority speaking through Justice Romero -- the very proposition CJP dissented from -- so it is not one of his phrases.
  - offending text: `a natural child by legal fiction cannot rise beyond that to which an acknowledged natural child is entitled`
  - suggested: Remove it from signature_phrases; it belongs in sub_topics as the majority's holding, where the row already has it.
- **`signature_phrases`** — The chapter gives this line to the Court speaking through Justice Hermosisima in the Mayfair ponencia, not to CJP, whose own contribution was a Separate Concurring Opinion quoted separately.
  - offending text: `the requirement of a separate consideration for the option has no applicability in the instant case`
  - suggested: Remove it and keep only CJP's own wording from his concurrence ('the right created is one springing from a contract', 'the principle of consensuality of a contract of sale should be deemed satisfied').

### BD050 — Judicial Renaissance, Ch. 2

- **`signature_phrases`** — these are not CJP's words but a verbatim quotation from World Bank chief counsel Anthony Gerald Toft ('In the words of Anthony Gerald Toft ... "the APJR is fundamentally well-rooted x x x"'), so listing it as a signature phrase of the speaker misattributes it
  - offending text: `the APJR is fundamentally well-rooted`
  - suggested: drop it from signature_phrases (it is already correctly credited to Toft in primary_topics and the stances), or replace it with a phrase of CJP's own, e.g. 'I do not know of any other country in the world that has received the same degree of cooperation and assistance from the international community'

### BD056 — Judicial Renaissance, Ch. 11

- **`stances`** — the chapter says only that more lawyers complain of judicial corruption than ten years ago 'and yet they do nothing about it' and that 'it is worse when corruption is perpetrated by members of the bar'; it never claims corruption persists ONLY where lawyers tolerate or abet it, nor does it rank bar corruption against the judges lawyers complain about
  - offending text: `because corruption in the judiciary persists only where lawyers tolerate or abet it -- and lawyers who fold bribe money into their fees are worse offenders than the judges they complain about`
  - suggested: state the claim as the chapter does: 'The bar must shun corruption by reporting it where and when it happens: lawyers complain of judicial corruption more than they did ten years ago yet do nothing about it, and it is worse still when corruption is perpetrated by members of the bar, who per SWS include bribe money in computing attorney's fees.'

### BD057 — Judicial Renaissance, Ch. 12

- **`signature_phrases`** — verbatim but not the speaker's: the chapter attributes the exhortation to another jurist -- 'As the great Mr. Justice J. B. L. Reyes once exhorted, lawyers must always “keep their souls attuned to the demands of morality and honor...”' -- so listing it as a signature phrase puts Reyes's words in CJP's voice
  - offending text: `keep their souls attuned to the demands of morality and honor, since a just cause cannot be protected or defended by dishonorable means`
  - suggested: drop it from signature_phrases (the row already credits Reyes in entities and sub_topics), or mark it explicitly as quoted from J. B. L. Reyes

### BC043 — Judicial Renaissance, Ch. 13

- **`signature_phrases`** — these words are not the speaker's: the chapter has him reporting Salonga citing Confucius -- 'He cites Confucius, the Asian philosopher, who said a long time ago that “[g]overnment, to be effective, must be government by example”' -- so listing the fragment as a signature phrase puts a quoted maxim in CJP's voice
  - offending text: `to be effective, must be government by example`
  - suggested: drop it from signature_phrases (the row already credits Confucius in entities and in the third stance), or mark it as quoted from Confucius via Salonga

### BB032 — Judicial Renaissance, Ch. 14

- **`one_paragraph_summary`** — the chapter never dates the Decision itself or states any interval between it and the address; it says only that the Decision was 'recent' and that it became final 'just the other day, February 1, 2005'
  - offending text: `delivered weeks after the Supreme Court upheld the constitutionality of the Mining Law`
  - suggested: drop the interval: 'delivered after the Supreme Court upheld the constitutionality of the Mining Law, days after the ruling became final'

### BD031 — Leadership by Example: The Davide Standard, Ch. 1

- **`signature_phrases`** — the chapter expressly borrows this image from someone else -- 'To borrow the words of Chief Justice Andres R. Narvasa' -- so it is a quoted phrase, not CJP's own signature language, even though the row credits Narvasa correctly in sub_topics and entities
  - offending text: `return to the land of the living after being judicially entombed`
  - suggested: drop it from signature_phrases, or carry it only as a phrase he quotes from Chief Justice Narvasa

### BA059 — Leadership by Example: The Davide Standard, Ch. 6

- **`entities.people`** — The chapter says the phrase "was an amendment introduced by Comm. Christian Monsod" alone; Suarez appears only as the commissioner who, with Monsod, "agreed on 'organized murder' or 'brutal murder of a rape victim'" as examples of heinousness, not as an author of the amendment.
  - offending text: `Comm. Christian Monsod and Comm. Jose Suarez (authors of the "compelling reasons involving heinous crimes" amendment)`
  - suggested: "Comm. Christian Monsod (introduced the 'compelling reasons involving heinous crimes' amendment) and Comm. Jose Suarez (agreed with him that organized murder or the brutal murder of a rape victim could qualify as heinous)."

### BA064 — Leadership by Example: The Davide Standard, Ch. 13

- **`notable_anecdotes`** — The chapter says only that the case "had initially been raffled" to her for study and that she "wrote a more lengthy 17-page Dissent"; it never says she wrote a draft ponencia or that any draft of hers was rejected.
  - offending text: `He recalls that the case had initially been raffled to Justice Flerida Ruth P. Romero for study, and that her rejected draft became a seventeen-page dissent.`
  - suggested: "He notes that the case had initially been raffled to Justice Flerida Ruth P. Romero for study and that she wrote a longer, seventeen-page dissent, which he quotes at length."

### BB028 — Leveling the Playing Field, Ch. 3

- **`entities.people`** — The chapter gives only the case name 'Chavez v. Public Estates Authority'; no first name, and no statement that any person named Chavez was a petitioner, appears anywhere in the text.
  - offending text: `Francisco Chavez (petitioner in Chavez v. PEA, as referenced)`
  - suggested: Drop the entry, or list it only as the case 'Chavez v. Public Estates Authority' under entities.cases, which the row already does.
- **`entities.people`** — The chapter names only the case 'Jaworski v. PAGCOR'; the first name and the petitioner role come from outside the text.
  - offending text: `Robert Jaworski (petitioner in Jaworski v. PAGCOR, as referenced)`
  - suggested: Drop the entry and leave 'Jaworski v. PAGCOR' under entities.cases.

### BE033 — Leveling the Playing Field, Ch. 13

- **`entities.people`** — No such person is named anywhere in the chapter -- EINSHAC appears only as the sponsor of the Kona conversation and co-sponsor of the 'World Congress on the Gene', with no individual attached to it.
  - offending text: `Dr. Franklin M. Zweig (referred to in connection with EINSHAC)`
  - suggested: Delete the entry; the chapter's named people are Huanming Yang, Xiao Yang, Hwang Woo Suk, Moon Shin Yong, Thaksin Shinawatra and Yong Pung How.

### BA088 — Leveling the Playing Field, Ch. 17

- **`one_paragraph_summary`** — The chapter says the opposite -- 'the defense had fallen short of proving all three phases of the "cycle of violence"' -- and records only that acute battering incidents existed and that Marivic described the tension-building phase of the fatal incident; no complete cycle is ever said to have been proved.
  - offending text: `only one full sequence was proved`
  - suggested: only the tension-building phase of the fatal incident was described in adequate detail, and the defense fell short of proving all three phases
- **`primary_topics`** — Same unsupported claim: the chapter states the defense failed to prove all three phases at all, and that it failed to establish a similar pattern in at least one earlier battering episode.
  - offending text: `that the defense proved only one full cycle rather than the required two`
  - suggested: that the defense failed to prove all three phases of the cycle, and failed to show a like pattern in at least one earlier battering episode as the syndrome requires

### BA092 — Leveling the Playing Field, Ch. 21

- **`signature_phrases`** — The sentence is verbatim but not his: it sits inside the block quotation from People v. Mateo introduced by 'Wrote the esteemed magistrate', i.e. it is Justice Vitug's ponencia, not CJP's own prose.
  - offending text: `the Court now deems it wise and compelling to provide in these cases a review by the Court of Appeals`
  - suggested: drop it, or use CJP's own words about Mateo, e.g. 'Mateo was Justice Jose C. Vitug's valedictory ponencia' or 'this new Vitug masterpiece grants equal access to justice to those convicted of capital offenses'

### BD061 — Liberty and Prosperity, Ch. 5

- **`entities.people`** — The chapter gives Salonga only as CJP's 'revered guru' and former Senate President who summoned him to address Bantay Katarungan's fifth anniversary and the Kilosbayan monthly forum; it nowhere says he founded either organization.
  - offending text: `Jovito R. Salonga (former Senate President; his 'revered guru'; founder of Bantay Katarungan and Kilosbayan)`
  - suggested: Jovito R. Salonga (former Senate President; his 'revered guru', who invited him to address Bantay Katarungan and Kilosbayan)

### BD062 — Liberty and Prosperity, Ch. 6

- **`one_paragraph_summary`** — The chapter's roll-call names twelve organizations (IBP, AAAAIL, Harvard Law Association, IPAP, Law Asia Philippines, LMCP, MARLAW, PBA, PDRCI, PICA, UIA, WILOCI) and never states a count.
  - offending text: `a testimonial dinner jointly tendered by thirteen Philippine bar and legal organizations`
  - suggested: a testimonial dinner jointly tendered by twelve Philippine bar and legal organizations
- **`notable_anecdotes`** — The text says only 'When I was still practising law a decade ago' -- a decade before this 2006 address -- and says nothing about when he joined the Court.
  - offending text: `The wealthy businessman who visited his law office a decade before he joined the Court`
  - suggested: The wealthy businessman who visited his law office when he was still practising law a decade earlier
- **`notable_anecdotes`** — Same count error: the chapter thanks twelve named organizations and gives no number.
  - offending text: `thirteen of the country's bar and legal organizations brought together under one roof to tender him a single testimonial dinner`
  - suggested: twelve of the country's bar and legal organizations brought together under one roof

### BD070 — Liberty and Prosperity, Ch. 17

- **`signature_phrases`** — The chapter attributes this line to someone else -- 'As the late President Ramon Magsaysay once said' -- so it is a quoted maxim, not one of CJP's own phrases, even though the row's entities and summary do credit Magsaysay.
  - offending text: `those with less in life should have more in law`
  - suggested: Drop it from signature_phrases (or keep it only where it is attributed, as in entities.people and the summary); the surrounding CJP wording 'Every court has the duty to provide the weak and the defenseless the vigilant protection they deserve' is his own.

### BA098 — Liberty and Prosperity, Ch. 19

- **`entities.laws_treaties`** — The chapter never cites Article III, Section 7; it lists the provisions petitioners invoked (Article VI, Secs. 1, 21, 22; Article XI, Sec. 1; Article II, Secs. 4 and 7; Article XIII, Sec. 16; Article II, Sec. 28) and discusses the right to information without any textual citation, so this provision is supplied from outside the chapter.
  - offending text: `1987 Constitution, Article III, Section 7 (right to information)`
  - suggested: Drop the citation and list simply 'the constitutional right to information on matters of public concern (discussed without citation)'.
- **`one_paragraph_summary`** — The chapter identifies the issuer only as 'the President' (and later 'she') and never names her; the only Arroyo in the text is Sen. Joker Arroyo, counsel for the Senate.
  - offending text: `which President Arroyo issued on September 28, 2005`
  - suggested: 'which the President issued on September 28, 2005'.

### BA104 — Liberty and Prosperity, Ch. 25

- **`stances`** — This stance is marked 'reported (not his view)', but the chapter states that the Carpio Dissent was 'joined by the Chief Justice and Justices Morales and Callejo' -- CJP signed that dissent, so the text makes this a position he held, and the row's own entity list and summary say so.
  - offending text: `In dissent, Justice Carpio argued that Smith had already overturned the compelling state interest test, that the State has a compelling interest in exacting the highest standard of conduct from everyone connected with the dispensation of justice, and that the majority effectively condoned a patent violation of the law on concubinage, so that 'today concubinage, tomorrow bigamy' would escape crimin`
  - suggested: Keep the claim as Justice Carpio's opinion but mark the confidence as a dissent CJP joined (e.g. 'asserted -- CJP concurred in the Carpio Dissent'), not as a view that is not his.

### BB041 — Liberty and Prosperity, Ch. 28

- **`notable_anecdotes`** — The chapter says nothing about how the Dissent opened or about the later fame of the 'Ming vase' passage; it only reports that 'In his Dissenting Opinion, Justice Dante O. Tinga lamented' the majority's course, so both the placement and the claim about the line's reception come from outside the text.
  - offending text: `Justice Tinga opened his Dissent with an image that became the case's best-known line`
  - suggested: 'In his Dissenting Opinion Justice Tinga accused the majority of shattering statutes and judicial precedents left and right to protect the precious Ming vase that is the Manila International Airport Authority.'
- **`entities.laws_treaties`** — The chapter cites only Sections 3, 11, 21 and 22 of EO 903; no Section 8 appears anywhere in the text.
  - offending text: `Executive Order No. 903, the Revised Charter of the MIAA, particularly Sections 3, 8, 11, 21 and 22`
  - suggested: 'Executive Order No. 903, the Revised Charter of the MIAA, particularly Sections 3, 11, 21 and 22'.

### BC025 — Love God, Serve Man, Ch. 3

- **`entities.institutions`** — Citibank appears nowhere in this chapter; the speech says only that the local peso donors are listed on Page 32 of the Balita (the Citibank counterpart of P100,000 is a detail from the earlier valedictory chapter).
  - offending text: `Citibank and the local peso donors listed in the Balita`
  - suggested: 'the local peso donors listed on Page 32 of the Balita, and the Paul Harris fellows listed on Page 31'.

### BC027 — Love God, Serve Man, Ch. 9

- **`signature_phrases`** — These are not his words but PCP II's, block-quoted in the chapter ('In the words of PCP II, and I quote: ... For while the majority of our people are Catholics and our churches are filled on Sundays, our society remains a sick society.' (192)) -- the row itself marks the matching stance 'reported (not his view)', so listing the sentence as one of his signature phrases misattributes it.
  - offending text: `our churches are filled on Sundays, our society remains a sick society`
  - suggested: Drop it from signature_phrases and leave it where the row already has it correctly, as the quoted PCP II text in sub_topics and in the stance marked 'reported (not his view)'.

### BC030 — Love God, Serve Man, Ch. 12

- **`signature_phrases`** — These are not his words: the chapter introduces the passage as 'Let me quote the language of the Second Plenary Council on the meaning of the Church of the Poor' and then block-quotes 'A Church where no one is so poor as to have nothing to give, and no one is so rich as to have nothing to receive' -- the row itself elsewhere labels this PCP II's own four-part definition.
  - offending text: `no one is so poor as to have nothing to give`
  - suggested: Remove it from signature_phrases and leave it in sub_topics as PCP II's quoted definition of the Church of the Poor.

### BB010 — Love God, Serve Man, Ch. 13

- **`entities.people`** — The chapter says only 'from Baron Travel Corporation, my company', and the editor's note calls him 'a business entrepreneur, particularly a pioneer in the tourism industry' -- neither gives him the title of president of that company.
  - offending text: `Artemio V. Panganiban (newly elected chairman of ASTA's International Council of Governors; president of Baron Travel Corporation)`
  - suggested: 'Artemio V. Panganiban (newly elected chairman of ASTA's International Council of Governors; Baron Travel Corporation is described only as "my company")'.
- **`signature_phrases`** — These are words the chapter puts in Abraham Lincoln's mouth ('It must have been the same American dream that Abraham Lincoln fulfilled when he said to the lowliest Negro in your society then, "Chin up, for you are free forever"'), not CJP's own phrasing, and the row lists them as one of his signature phrases.
  - offending text: `Chin up, for you are free forever.`
  - suggested: Drop it from signature_phrases; the row already records it correctly under entities.people and notable_anecdotes as Lincoln's quoted line.

### BC034 — Love God, Serve Man, Ch. 20

- **`sub_topics`** — the chapter calls him only 'the Honorable Salvador H. Laurel' and never gives him any office, so 'former Vice President' is imported from outside the text
  - offending text: `It blesses the guest speaker, former Vice President Salvador H. Laurel, asking that he be anointed as he articulates 'his vision of a country transformed and a people renewed in Your Spirit'`
  - suggested: It blesses the guest speaker, 'the Honorable Salvador H. Laurel,' asking that he be anointed as he articulates 'his vision of a country transformed and a people renewed in Your Spirit'

### BC036 — Love God, Serve Man, Ch. 22

- **`signature_phrases`** — these are Salonga's words, quoted by CJP as the reflection Salonga made on waking in his hospital bed after Plaza Miranda, not a phrase of CJP's own
  - offending text: `There must be a reason why God spared my life`
  - suggested: remove it from signature_phrases (it is already correctly reported as Salonga's quoted reflection in the anecdote and summary)

### BD039 — Reforming the Judiciary, Ch. 3

- **`entities.people`** — this chapter never names the Chief Justice; it says only 'our Chief Justice is the recipient of the 2002 Ramon Magsaysay Award,' so the identification is imported from outside the text (the same naming recurs in primary_topics, sub_topics and notable_anecdotes)
  - offending text: `Chief Justice Hilario G. Davide Jr. (recipient of the 2002 Ramon Magsaysay Award for government service)`
  - suggested: the Chief Justice (unnamed in this chapter; recipient of the 2002 Ramon Magsaysay Award for government service)
- **`one_paragraph_summary`** — the chapter identifies the audience only as 'this elite group representing American business in our country' and never names the American Chamber of Commerce; the same unsupported name appears in primary_topics, entities.institutions and target_audience
  - offending text: `reproduces Artemio V. Panganiban's speech to the American Chamber of Commerce of the Philippines`
  - suggested: reproduces Artemio V. Panganiban's speech to a group 'representing American business in our country'

### BD041 — Reforming the Judiciary, Ch. 5

- **`decision_framework_signals`** — the maxim is presented as a quotation but appears nowhere in this chapter, which argues for rationalized compensation without it (the line belongs to a different chapter of the book)
  - offending text: `'from whom much is expected, much should be given' -- proper compensation as the precondition of quality justice`
  - suggested: proper compensation as the precondition of recruiting and keeping the best and the brightest -- 'judicial compensation must be rationalized'

### BD043 — Reforming the Judiciary, Ch. 8

- **`entities.people`** — this chapter says only that 'the Court appointed a Centenary Executive Committee' and that 'it is our hope in the Centenary Execom'; it never states that the speaker chairs it, so the role is supplied from outside the chapter
  - offending text: `Artemio V. Panganiban (author; chairman of the Centenary Executive Committee, delivering the remarks)`
  - suggested: Artemio V. Panganiban (author; speaking for the Centenary Executive Committee at the finals)

### BA079 — Reforming the Judiciary, Ch. 14

- **`entities.events`** — the chapter never mentions the May 14, 2001 elections or any date for the elections the SWS ruling preceded -- it says only that the Court decided SWS v. Comelec 'last year'
  - offending text: `the May 14, 2001 Philippine elections preceded by the SWS ruling`
  - suggested: drop the item, or replace it with an event the chapter does state, such as 'the SWS challenge to Section 5.4 of the Fair Elections Act'

### BA080 — Reforming the Judiciary, Ch. 16

- **`one_paragraph_summary`** — the chapter's Amended Information describes the P545 million as coming 'from illegal gambling ... in exchange for protection from illegal gambling' and never names jueteng; the same word is also used in sub_topics ('P545 million in jueteng protection money')
  - offending text: `set out the charge of more than four billion pesos in jueteng protection money, tobacco excise funds, Belle Corp. commissions and the 'Jose Velarde' deposits`
  - suggested: say 'illegal-gambling protection money' as the chapter does

### BA083 — Reforming the Judiciary, Ch. 22

- **`signature_phrases`** — this is guideline 1 of People v. Pruna, which the chapter expressly says was 'penned by Chief Justice Hilario G. Davide Jr.' and reproduces as a block quotation, so it is not CJP's own phrasing
  - offending text: `The best evidence to prove the age of the offended party is an original or certified true copy of the certificate of live birth`
  - suggested: drop it from signature_phrases (it is already covered in sub_topics as a Pruna guideline)

### BA070 — Transparency, Unanimity & Diversity, Ch. 16

- **`stances`** — The chapter attributes this position to an unnamed Separate Opinion that 'challenged' the Dela Cruz ponencia ('This ruling was, however, challenged by a Separate Opinion which, after citing previous rulings, contended...') and never says the Opinion is his, so listing it with confidence 'asserted with evidence' presents another justice's position as CJP's own.
  - offending text: `Where the victim's alleged age falls between 13 and 18, neither her bare testimony nor her mother's suffices; independent evidence of age is required, because that proof spells the difference between life and death.`
  - suggested: Mark it confidence: 'reported (not his view)' and attribute it to the unnamed Separate Opinion in People v. Dela Cruz.
- **`signature_phrases`** — The line comes from the closing of that same unnamed Separate Opinion reproduced in the chapter ('Be it remembered that the proof of age in the present case spells the difference between life and death!'), not from CJP's own narration or an opinion the chapter says he wrote.
  - offending text: `the proof of age in the present case spells the difference between life and death`
  - suggested: Drop it, or keep it only where the row already treats it as the Separate Opinion's language.
- **`signature_phrases`** — This sentence is inside the block the chapter quotes from the Court's decision in People v. Gallego ('The Court said in Gallego: ...'), a case CJP is reporting, not his own wording.
  - offending text: `Any decision authorizing the State to take life must be as error-free as possible`
  - suggested: Drop it from signature_phrases; it is already correctly placed in sub_topics as the Gallego holding.
- **`one_paragraph_summary`** — In Mendez the Information alleged the victim was the accused's 'daughter' and the proof showed she was only his 'stepdaughter'; it is the separate line of cases (Villanueva, Melendrez, Villaroza, Garcia, Magtrayo, Dela Cuesta) in which stepdaughter was alleged and a common-law relationship proven -- the same conflation appears in sub_topics ('People v. Mendez and a line of cases ... while the proof showed only a common-law relationship with the victim's mother').
  - offending text: `Mendez and its line, where stepdaughter was alleged but only a common-law relationship proven`
  - suggested: 'Mendez, where the Information said daughter but the proof showed only a stepdaughter, and the line of cases in which stepdaughter was alleged but only a common-law relationship with the mother was proven'.

### BA071 — Transparency, Unanimity & Diversity, Ch. 18

- **`signature_phrases`** — The chapter puts this phrase in quotation marks inside its summary of the Melo majority's fifth reason ('Neither the RP-US Extradition Treaty nor the Extradition Law (PD 1069) precluded the "twin due process rights of notice and hearing"'), so it is the ponencia's wording -- the very holding CJP dissented from -- not his own.
  - offending text: `twin due process rights of notice and hearing`
  - suggested: Drop it from signature_phrases; his own phrasings on the point are already listed ('the evaluation stage was not adjudicative in nature', 'In sum, Jimenez was not in danger at all...').

---

## 3. Notes (not failures)

168 note-level observations were recorded across 120 rows — imprecise
phrasing, thin fields, and above all `entities.people` entries that supply a given name or initial the
chapter gives by surname only. None of them asserts anything the text contradicts, so none blocks the
merge. They are listed per row in the review files and are worth a pass if the team wants the entity
names to match the sources exactly.

---

## 4. Spot check — 10 rows, seed 4, one per book

`batch-04/spot_check_books.xlsx`. Columns: doc_id, book, chapter, title, md_path, B4 verdict,
one_paragraph_summary, three signature phrases, two stances, and empty `reviewer` / `OK / fix` / `notes`.

| # | doc_id | Book | Ch. | B4 verdict |
|---:|---|---|---:|---|
| 1 | BA108 | A Centenary of Justice | 20 | pass_with_notes |
| 2 | BA056 | Battles in the Supreme Court | 7 | fail |
| 3 | BA057 | Battles in the Supreme Court | 9 | fail |
| 4 | BA096 | Judicial Renaissance | 22 | pass_with_notes |
| 5 | BD032 | Leadership by Example: The Davide Standard | 2 | pass |
| 6 | BB030 | Leveling the Playing Field | 5 | pass_with_notes |
| 7 | BD067 | Liberty and Prosperity | 13 | pass_with_notes |
| 8 | BB011 | Love God, Serve Man | 14 | pass |
| 9 | BA079 | Reforming the Judiciary | 14 | fail |
| 10 | BA068 | Transparency, Unanimity & Diversity | 14 | pass_with_notes |

Three of the ten (BA056, BA057, BA079) are failing rows, which is deliberate — the sample was drawn
before the verdicts and left unchanged, so the reviewer sees both kinds.

---

## 5. Verdict and what happens next

**B4 does not pass.** 37 of 168 rows carry at least one unsupported or misattributed assertion.

1. **Fix the 54 failures in B3** — 22 of them are one edit each (drop the misattributed phrase, replace it
   with one of his own), and the rest are name, citation, count and summary corrections.
2. **Amend the B3 prompt** to add the attribution test described above, so the next book batch does not
   repeat it.
3. **Re-run P5** on the corrected workbook, then **re-run B4** until it is clean.
4. **Sign the 10-row spot check.**
5. Only then does the books track join the merge queue — which is still gated on correction batch-03,
   and on the D-14 OCR clean-up of `batch-04/data_text/`.

Open decisions unchanged: BA083 (truncated source), BA080 and BB024 (mostly Jovito Salonga's writing),
the 21 chapters over 6,000 words kept whole, and whether the richer field sizes should be trimmed.