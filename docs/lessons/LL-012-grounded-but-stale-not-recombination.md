# LL-012: The worst hallucination was grounded, not recombined — so no output gate could catch it

* Date: 2026-09-13
* Severity: high (the failure the 2026-09-12 audit ranked #2 by event risk)
* Related: [LL-005](LL-005-signature-library-loaded-but-unused.md),
  [TS-007](../test-specs/TS-007-premise-gate-questions.json),
  `app/premise_gate.py`, `scripts/gate_audit.py`

## Symptom

The 2026-09-12 adversarial audit ran 50 questions through the real pipeline.
The gates blocked **0 of 277** composed sentences; 37 invented particulars
reached speech. Its worst case:

> Q: *"Who is the current Solicitor General and what did you tell them?"*
> → names a Solicitor General, then *"that is the mission I entrusted to SolGen
> Berberabe"*, then *"I asked her to chair our new Super Committee."*

The audit read this as the composer recombining real corpus entities into a
pairing that was never true, and CLAUDE.md recorded it that way: *"a real person
given the wrong office."*

## What it actually was

It is not a recombination. Every element is in the corpus, verbatim, in one
document — `corpus/speeches/D_flp_mission_foundation/SD002.md`, dated
**2025-08-29**:

> *"our Board of Trustees formed a new Super Committee to design this new
> project – headed by SolGen Lelen Berberabe"*

The office, the person, the committee and the pairing are all real and all in
the same sentence of the same speech. What is false is only the word **current**
in the question. The corpus can say who held that office in August 2025; it
cannot say who holds it today, and nothing in the document says otherwise.

## Why that matters more than the original diagnosis

A gate that checks a composed sentence against its grounding context must pass
this sentence, correctly, every time. So must a whole-answer fidelity audit. So
would any entity-pairing index built from the corpus — the pairing is in the
corpus. **The measured "0 of 277" was not the gates failing; it was the gates
being asked a question they cannot answer.** Staleness is not visible inside
the text: it lives in the gap between the question's tense and the document's
date.

The same reading applies to the audit's other two outright false claims:
*"December 7, 2006"* conflates his birthday with his retirement (a full date
whose **year** is in the corpus everywhere, so the year gate passes it), and
*"what did you say to Chief Justice Gesmundo last week"* is answered at all
because nothing refused the premise.

## What was done instead (2026-09-13)

1. **`app/premise_gate.py`** — a deterministic gate on the QUESTION, before the
   router and composer. Five refusable premises: who holds an office now, a
   time deixis on a factual ask, a matter still pending, a year past the corpus
   horizon, an election result. A hit is answered from a curated decline pool
   instead of composed. Zero tokens, zero latency, and it removes the failure
   rather than chasing it. This is the *"narrower robot"* the audit recommended
   over a better gate.
2. **Full dates are checked as (year, month, day) triples**, not by year —
   `answer_gate.fact_check` now blocks `December 7, 2006`.
3. **`_FACT_TRIGGER` covers office attributions.** Four of the five documented
   failing sentences carried no year, no number and no quoted title, so they
   never reached the Haiku audit at all. `SolGen Berberabe` now does; his own
   title (*"the twenty-first Chief Justice"*, in half his answers) deliberately
   does not.
4. **Authored lines are gated at render time** (`answer_gate.check_curated`,
   called by `scripts/render_duet.py` and `render_intro.py`) — pre-rendered was
   never pre-verified.
5. **`scripts/gate_audit.py`** makes the number reproducible, offline and free
   for the premise gate, `--live` for the whole pipeline.

## The general lesson

Before building a detector, read the failing output back against its own source.
The audit's conclusion was reasonable from the transcript alone and wrong on
the evidence, and an entity-pairing gate built on it would have shipped, passed
its tests, blocked nothing, and been described to a stakeholder as a safety net
— which is exactly the failure the audit was written to stop.

**A corpus with a date needs a gate on the question's tense, not only on the
answer's content.**
