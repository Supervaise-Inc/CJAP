# ADR-0019: A numbered chapter stays a chapter, whoever wrote it

* Status: accepted
* Date: 2026-09-24
* Deciders: SV Dev2, Claude

## Context and Problem Statement

B0 (book split) rule 2 lists `introduction or commentary written by
someone else` among the parts that are classified SKIP rather than turned
into documents. That clause was written with front and back matter in
mind — a foreword by the Chief Justice, a publisher's note, blurbs on the
dust jacket.

Four of CJP's twelve books do something the rule did not anticipate: they
give a **numbered chapter** to a piece written by somebody else. The book
prints "Chapter 9" above it and lists it in the Contents between Chapter 8
and Chapter 10. Applied literally, rule 2 deleted those chapters from the
split and left holes in the numbering:

| Book | Ch. | Words | What it is |
|---|---|---|---|
| Leveling the Playing Field | 9 | 1,022 | "Law Without Borders" — Atty. Ismael G. Khan Jr.'s *Philippine Daily Inquirer* commentary of 30 May 2004, behind a ~90-word CJP headnote |
| Reforming the Judiciary | 2 | 7,558 | "Forum on the APJR" — CJP's ~350-word introduction, CJ Davide's Ramon Magsaysay Awardee Lecture, and reactions by Sen. Jovito R. Salonga and Malou Mangahas (PCIJ) |
| Reforming the Judiciary | 10 | 4,014 | Two reprinted PDI articles behind a ~140-word CJP introduction |
| Judicial Renaissance | 4 | 8,803 | "Judicial Reform — Issues to Consider: The Philippines and Indonesia", by A. G. Toft |

The team found the first two by reading the split plans. That is the
problem: **nothing in the pipeline could have found them.** The B0
coverage self-check adds chapter words to skipped words and compares the
total against the book, so it passes whether a part is a chapter or a
skip. A hole in the chapter numbering is indistinguishable from a book
that simply has no Chapter 9.

## Decision Drivers

* The split is the **traceable record of the book**, not the corpus. What
  is registered into the corpus is B1's decision, made later and with the
  text in hand.
* Silent loss is the worst failure mode here. A reader of
  `split_plan.csv` must be able to tell "this book has no Chapter 9" from
  "we decided not to keep Chapter 9".
* Voice fidelity is enforced at B1 and B3, not B0. Keeping a document is
  not the same as letting it into the voice palette.
* Rights differ per author. Text by Khan, Davide, Salonga, Mangahas or
  Toft is not covered by the FLP corpus permission that covers CJP's own
  writing.

## Considered Options

* SKIP them, as rule 2 read before — the status quo.
* Split the chapter so that only CJP's own headnote becomes a document.
* Keep the whole chapter as a CHAPTER document, flagged by author.

## Decision Outcome

Chosen option: **keep the whole chapter as a CHAPTER document, flagged
`by-another-author`**, because authorship is metadata about a document,
not a reason for the document to be absent. Rule 2's other-author clause
now applies only to **unnumbered** parts — foreword, preface,
acknowledgments, appendices, editors' notes, blurbs, reviews.

Three things travel with such a document:

1. `classification = CHAPTER` and its real chapter number, so the
   numbering runs unbroken and a remaining gap means the book itself
   skipped a number.
2. `flags` contains `by-another-author` — a machine-readable filter, so
   B3 can exclude these from the signature-phrase palette and B4 can
   assert that none of them fed the voice card.
3. The printed byline stays as the document's first body line, so the
   authorship survives even if the flag is lost in a later hop.

### Consequences

* Good: the split mirrors the book, and `split_plan.csv` is a complete
  account of every part of every book.
* Good: B1 gets the full text and decides with evidence instead of
  inheriting a decision B0 made silently.
* Good: `by-another-author` is queryable, so "prove no third-party prose
  reached the voice card" becomes a check rather than an assurance.
* Bad: B1 now faces a judgement it never used to see — whether prose not
  in CJP's voice belongs in a corpus built to speak as him. That judgement
  is real and the register is the right place for it, but it is new work.
* Bad: rights status is no longer uniform across book chapters. A
  registered other-author chapter needs its own rights line naming the
  author; the FLP permission does not reach it.
* Neutral: the other-author chapters are all `long` or near it, so any
  that are registered will also hit the 6,000-word review under rule 6.

### Confirmation

`split_plan.csv` for every book lists a `chapter_no` for each CHAPTER row.
Any remaining gap in a book's numbering must be explained in that book's
`split_report.md` as a gap **the book itself** has. A reviewer can check
this in one pass across the twelve plans.

## Pros and Cons of the Options

### SKIP them (the rule as written)

* Good, because no third-party prose can reach the corpus by accident.
* Bad, because the loss is silent — the coverage check cannot see it, and
  the numbering gap reads as a property of the book.
* Bad, because it puts a corpus-membership decision inside a step whose
  job is transcription fidelity.

### Keep only CJP's headnote

* Good, because every document stays in his voice.
* Bad, because the headnotes are 60–350 words — below any useful
  threshold, and rule 4 already sets 800 words as the bar for a piece
  worth keeping on its own.
* Bad, because the headnote alone is unintelligible: it introduces a
  piece that would no longer exist anywhere in the corpus.

### Keep the whole chapter, flagged (chosen)

* Good, because nothing is lost and the decision moves to the step
  equipped to make it.
* Good, because the flag is explicit and testable.
* Bad, because it needs a new rule in the B0 prompt and a new habit at
  B1 — the cost of making a hidden decision visible.

## More Information

* Applied 24 Sep 2026 to **Leveling the Playing Field Ch. 9** and
  **Reforming the Judiciary Ch. 2**. Both books re-passed every B0
  self-check: 100% coverage, no overlap, no empty files, no word-count
  drift. Book chapter documents across the twelve books went from 287
  to 289.
* **Still pending the same treatment:** Judicial Renaissance Ch. 4 and
  Reforming the Judiciary Ch. 10. Until they are restored, those two
  books carry gaps at 4 and 10 respectively.
* Reforming the Judiciary Ch. 2 holds four pieces by three authors under
  one chapter number. It is kept as one document under rule 1, but its
  `##` section headings separate the four cleanly, so B1 can split it per
  author without going back to the book.
* Rule source: `batch-04/BATCH-04_BOOKS_PROMPTS.md`, B0 rules 2 and 7.
* Evidence: `batch-04/book_split/leveling-the-playing-field/split_report.md`
  and `batch-04/book_split/reforming-the-judiciary/split_report.md`,
  decision 1 in each.
* Related: [ADR-0011](0011-corpus-id-format-type-theme-number.md) (IDs
  carry no authorship, so the flag is the only carrier) and
  [ADR-0016](0016-theme-anchored-register-selection.md) (theme drives
  register — a document not in his voice must not reach it).
