# R-1 — proposed replacement for the voice card's opening block

**STAGED, NOT APPLIED.** Do not apply until batch-03's promotion eval (CE-12) has run. Changing the
composer prefix and the corpus in the same run confounds the comparison against the standing baseline —
fix this as its own change, with its own baseline.

Target file: `corpus/voice/voice_card.md`, lines 1–14 (everything above the first `---`).
The remaining ~366 lines are unchanged.

---

## Why

The block below is loaded verbatim by `app/answer_pipeline.py` (line 534) into the **cached static
prefix**, so it is sent to the model with **every single answer**. It currently tells the model three
things that stopped being true at W1.8:

| It says | Reality |
|---|---|
| "Haiku has already routed the question" | The Haiku router was removed. Zero model calls before composition (`llm_calls_before_composition == 0`) |
| "no embeddings, no similarity search, no chunking" | Dense (bge-base-en-v1.5 @768d) + sparse BM25 over 9,804 chunks, RRF-fused, with a topic soft prior |
| "the caller has loaded the whole `.md` + `.json` for 1–3 source documents" | Top-p selected chunks, median ~9, never whole documents |
| "(Phase 1 corpus)" · "The corpus is small" | 1,104 documents, going to 1,290 at the batch-04 merge |

The model is being told it received whole documents when it received chunks, and told to "trust the
routing" from a router that no longer exists.

---

## CURRENT (lines 1–14)

```markdown
# Voice Card — Chief Justice Panganiban (Phase 1 corpus)

This is the system prompt for the **Sonnet composition step** in the
runtime pipeline. By the time this prompt fires, Haiku has already (a)
routed the user's question to one or two `topic_paths` in
[topic_map.json](topic_map.json), and (b) the caller has loaded the
whole `.md` + `.json` for 1–3 source documents into the context block.

Your job: answer the user's question **as Chief Justice Artemio V.
Panganiban**, grounded in those documents.

The corpus is small and **fully indexed** — no embeddings, no
similarity search, no chunking. Documents arrive whole. Trust the
routing; if the routing is weak, fall back to the principles below.
```

## PROPOSED

```markdown
# Voice Card — Chief Justice Panganiban

This is the system prompt for the **Sonnet composition step**. It is the
only model call in the pipeline: everything before it — retrieval,
ranking, selection — is deterministic code.

By the time this prompt fires, the caller has already (a) embedded the
question and scored it against the topic centroids as a soft prior,
(b) retrieved and fused dense and sparse results over the chunked
corpus, and (c) placed the selected **passages** in the context block.

Your job: answer the user's question **as Chief Justice Artemio V.
Panganiban**, grounded in those passages.

What you receive are **extracts, not whole documents** — typically
around nine passages, each carrying its source document's id, title and
date. The corpus behind them is large (over a thousand documents across
his columns, books, speeches and biography), so the absence of
something from the context block does not mean he never wrote it. If
the passages do not carry what the question needs, say so in your own
voice rather than reaching beyond them.
```

---

## What changes in behaviour

Nothing mechanical — this is prose in a prompt. Two effects are intended:

1. The model stops being told it has whole documents, which should reduce answers that imply completeness
   the context does not support.
2. The last sentence gives it an explicit, in-voice route to "I do not have that here" — which is what the
   safety boundary already asks for further down the card, but without a matching instruction at the top.

Both are testable. Run the gold set before and after and compare grounding and decline rates. Expect the
difference to be small; if it is large, that is itself worth knowing.

## Also in this file, not fixed here

- The card is still titled for Phase 1 and was written against ~79 documents; other passages further down
  may carry the same assumption. Worth a read-through by someone who knows the voice — that is P3.6's
  outstanding "reviewed by someone who knows the real voice".
- The "Identity rule" section is **correct and stays as it is**: CJ Panganiban wants the robot to say it
  is him (decisions register D-042).
