# P0.2 — Rights, consent and likeness: evidence inventory and gap list

**Status: CLEARED. Counsel approved all six items on 25 Sep 2026.**

> Recorded from the project lead's confirmation in session. **The approval document itself is not yet in
> this folder** — file it here and this note can go.

*Original framing, kept for the record:* gap list for Counsel, not a clearance. Nothing here clears anything; it records what evidence
exists in the folder and what does not. Written 25 Sep 2026.

## The finding that matters

P0.2 is written in the plan as a **STOP GATE**: *"Consent evidence on file and findable. No corpus work
starts before this."*

**The gate was never closed, and the corpus work ran anyway** — 1,104 documents built, chunked, embedded,
indexed and demonstrated. This is not a reason to stop now; it is a reason to close the gate before the
kiosk faces the public, and to be honest in the project record that the sequence was inverted.

What exists today is a **per-document rights field** in `batch-04/intake_manifest.csv`
(`rights_consent_status`) carrying one of three phrases. What does not exist anywhere in the folder is a
consent evidence file, a signed permission, or any likeness/voice release.

## 1. The written corpus

| Source | Docs | What the record says | Gap |
|---|---:|---|---|
| *With Due Respect* columns, Philippine Daily Inquirer | 785 (+18 staged) | "CJP-authored Inquirer column, **same basis as the existing 785**" | **Circular.** The basis for the 785 is never stated anywhere. Does PDI hold any right in the published columns? Counsel question, and it is the single largest block of the corpus |
| His books | 131 (+168 staged) | "CJP-authored, covered by the FLP corpus permission" | The FLP corpus permission itself is **not in the folder**. Scope, date and signatory unknown. Publishers of the individual books are not addressed |
| Speeches | 153 | "CJP-authored speech, covered by the FLP corpus permission" | Same |
| Biography chapters | 35 | — | Written **about** him by two biographers (GC001–GC020 Reginald T. Yu; GC021–GC035 a second work). **The biographer's permission is a separate right and is not evidenced** |

### Third-party material inside CJP-authored documents

Found during B3/B4 this week. Each is someone else's text reproduced inside a document the corpus treats
as his:

| Doc | Third party |
|---|---|
| **BA080, BB024** | Most of each chapter is an article **by Jovito R. Salonga**, reprinted with permission *in the book* — which is not the same as permission for this corpus |
| **BD038** | ~75% is the Supreme Court's **APJR Executive Summary**, an institutional document |
| 22 chapters of *Love God, Serve Man* | Published by PDI with **editor's notes by Isagani Yambot** inside each piece. Already carries a FLAG in the manifest: "confirm PDI/editor consent" |
| BC023 | The **Prayer of St Francis** reproduced in full |
| BA096 | A poem, *"A.V.P."*, by **Atty. Noel Mapili** |
| BD046 | Answers given by a panel — Justices Quisumbing, Carpio, Azcuna and court administrators |
| Many book chapters | Long verbatim opinions of other justices |

Two chapters (*Leveling the Playing Field* Ch. 9 by Atty. Ismael G. Khan Jr.; *Reforming the Judiciary*
Ch. 2, largely CJ Davide, Sen. Salonga and Malou Mangahas) are registered under ADR-0019 with a
`by-another-author` flag. That ADR settled a *corpus-structure* question. It did not clear rights.

**One document was removed for authorship after it had been staged:** CA529, "Rule of, or by, law", turned
out to be by **Michael L. Tan**, not CJP. It was caught by a QA check, not by a rights process. That is
the failure mode this gate exists to prevent.

## 2. Voice and likeness

| Item | Evidence in the folder |
|---|---|
| Consent to speak **in his voice** | **None found** |
| Consent to use his **name and likeness** in a public installation | **None found** |
| The synthesis voice (TTS) — whose voice is it, and on what consent | **None found.** ADR-0007 records a local TTS choice (Piper "ryan-high"), ADR-0018 records OpenAI STT/TTS. Neither records a consent basis |
| Approval of the **disclosure posture** (persona brief §4) | **None found** |

He is **alive**. Every one of these is a live-person right, not an estate question.

## 3. What Counsel is being asked for

1. The **FLP corpus permission** itself — produce it, and state its scope: which works, which uses, public
   performance, derivative synthetic speech, duration.
2. A position on the **785 Inquirer columns**: whether PDI's rights bear on this use.
3. A position on the **two biographies** (third-party authorship, subject's rights separate).
4. A decision on the **third-party material** in §1: clear it, or exclude those documents. BA080, BB024 and
   BD038 are the substantive ones.
5. A **voice and likeness release** covering a synthetic voice speaking as him in a public installation.
6. Sign-off on the **disclosure posture** in `persona_brief.md` §4.

## 4. Disposition, 25 Sep 2026

**Counsel approved all six items in §3**, and separately the persona decision (§4 of `persona_brief.md`) is
CJ Panganiban's own: he wants the robot to say it is him. Nothing in the corpus is excluded on rights
grounds, including the third-party material listed in §1 and the two biographies.

This closes P0.2 and P1.2. The one outstanding action is clerical: **file the approval itself** here, so
the clearance is findable rather than remembered.

## 5. Superseded — recommended interim position

Until 1, 5 and 6 are on file, treat the build as an internal pilot: no unattended public operation, no
recorded demonstrations released outside the team. Items 2–4 gate the *corpus contents* and can run in
parallel; if any document is excluded, it is retired through CE-18, which keeps its ID reserved and does
not renumber anything else.

| | Name | Date | Signature |
|---|---|---|---|
| Inventory reviewed | **Counsel** | **2026-09-25** | approved |
| Items 1–6 dispositioned | **Counsel** | **2026-09-25** | all approved |
| Approval document filed in docs/p0/ | Member 3 | | **pending** |
