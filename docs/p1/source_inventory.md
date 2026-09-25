# P1.1 — Source inventory

Machine-readable version: `docs/p1/source_inventory.csv` (17 rows). Counted from the live corpus and the
batch-04 manifest on 25 Sep 2026, not from memory.

## Where the corpus stands

| | In corpus now | Staged (batch-04) | After the P6 merge |
|---|---:|---:|---:|
| Columns | 785 | 18 | **803** |
| Book chapters | 131 | 168 | **299** |
| Speeches | 153 | 0 | 153 |
| Biography chapters | 35 | 0 | 35 |
| **Total documents** | **1,104** | 186 | **1,290** |

**Books, counted as the team counts them (With Due Respect's seven volumes are one title): 4 of 12 are in
the corpus today. All 12 are in after the merge.**

In: A Centenary of Justice · Justice and Faith · The Bio-Age Dawns on the Judiciary · With Due Respect
Vols. 1–7.
Arriving at merge: Battles in the Supreme Court · Leadership by Example · Transparency, Unanimity &
Diversity · Reforming the Judiciary · Leveling the Playing Field · Judicial Renaissance · Liberty and
Prosperity · Love God, Serve Man.

## The gap worth acting on: ~222 columns

You said "almost 1000 columns". That instinct is right, and the corpus is short of it.

- The column has run in the *Inquirer* **every Monday since February 2007**.
- Mondays from 5 Feb 2007 to 21 Sep 2026: **1,025**.
- The corpus holds **785**, and batch-04 brings it to **803**.
- Coverage by year is essentially complete **from 2012 onward** — 52 or 53 every year.
- **2007, 2008, 2009, 2010: zero. 2011: 36, starting 17 April.**

So the shortfall is one contiguous block: **roughly 222 columns from Feb 2007 to Apr 2011**, his first
four years as a columnist — written immediately after he left the Court, which is likely to be some of
the most quotable material in the whole corpus.

Filling it would take columns to ~1,025 and the corpus to **~1,512 documents**. It is an intake batch
like any other: C0 → C1 → C2 → P5 → P6. Nothing new is needed to do it.

*Caveat:* the 75 *With Due Respect* book chapters (S-05) are collected columns from roughly that period,
so a little of 2007–2011 is present in book form. They are separate documents with their own IDs and do
not close the gap.

## Other gaps, in order of how much they cost

1. **~222 missing columns** (above).
2. **Speeches have never been inventoried.** 153 are in the corpus; nobody has counted what exists on
   cjpanganiban.com or in his files, so we cannot say what fraction that is. This is the one source where
   we do not know the denominator.
3. **D-14 — the book scans are damaged at origin.** Clauses dropped mid-sentence in the publishers'
   `.docx` files; 420 suspect spans across 96 of the 168 staged chapters. Not repairable without re-scans.
   Priority order in `batch-04/book_split/SOURCE_GAPS.md`.
4. **Excluded third-party material** that may or may not belong: Bio-Age Appendices A–D, Judicial
   Renaissance Ch. 4, Reforming the Judiciary Ch. 10. Decisions still open.
5. **Two biographies are by other authors** (S-15, S-16) and the second biographer is not even named in
   the folder. Rights are unevidenced for both — see `docs/p0/consent_evidence_inventory.md`.

## Rights, in one line

Every book and speech row carries "covered by the FLP corpus permission" — **and that permission is not in
the folder**. The 785 columns cite "the same basis as the existing 785", which is circular. The gap list
for Counsel is `docs/p0/consent_evidence_inventory.md`; this inventory is its factual base.
