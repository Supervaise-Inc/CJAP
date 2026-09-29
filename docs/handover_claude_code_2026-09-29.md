# Claude Code handover: 2026-09-29 (alpha handed in)

The latest implementation snapshot. It supersedes the 05-31 and earlier
handovers for **what runs**. Written for a Claude (or a person) picking this
project up on a different machine, with none of the session history.

## 1. State at handover

| | |
|---|---|
| Code | `master` = `feat/operator-console` = **`d7a7eec`** on `Supervaise-Inc/CJAP` |
| GitHub default branch | still `pi/deployment-snapshots`. It shares **no history** with `master`, and the knowledge-base release note says never force-update it. Clone with `-b master`. |
| Alpha (`reachy-cjap`) | runs `d7a7eec` with knowledge base v2. It was restarted on 2026-09-29 and logged `31 topics loaded` with no errors. **This machine was handed in.** |
| Beta (`reachy-2`) | **not** updated. It is still on the v1 corpus and has no Fish key. It was last seen at 192.168.112.47. The 192.168.88.10 address in older docs is stale. |
| Tests | `app/.venv/bin/python -m pytest tests/` → **396 passed** |
| Off-repo machine files | snapshotted in [`deploy/alpha/`](../deploy/alpha/README.md), with a restore guide |
| Secrets | **not in git.** `app/.env` needs `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `ELEVEN_API_KEY`, `FISH_API_KEY` (template: `app/.env.example`). `dashboard/assets/liveavatar.json` needs the LiveAvatar key. The TLS certs are self-signed, so regenerate them. |

## 2. What changed on 2026-09-29

### Knowledge base v2 imported (commit `d465215`)

**Source.** `origin/deliverable/2026-09` @ `febb007`, tag
`release/kb-v2-2026-09-27`. That branch is a separate codebase with no shared
history, so only data was copied, not merged.

**Imported into `corpus/`:**

| Type | Count | Note |
|---|---|---|
| Columns | 803 | |
| Speeches | 153 | |
| Book chapters | 299 | new; ids `B[A-E]nnn` |
| Biography chapters | 35 | |
| **Total** | **1,290** | |

The v2 `topic_map.json` (30 topics) and `router_prompt.md` came across too,
with CRLF line endings stripped.

**Kept ours, not the release's:**
- `voice_card.md`: the release copy reintroduces "Marisita" in place of the
  2026-08-31 Elenita fix.
- `host_card.md`, `duet_script.json`, `intro_variants.json`.

**Not imported:**
- The release's embedding retrieval stack (`CJ_PIPELINE=retrieval`, the
  438 MB `bge-base` encoder in Git LFS, `data/index/`, `corpus/index/`).
- The reason: this app routes with a Haiku call over the topic taxonomy, with
  no embeddings, and the Pi's 14 GB card had 1.8 GB free.

**Code changes, all in `app/answer_pipeline.py` unless noted.** Without these
the new data would have been loaded but silently unused:

- **Book ids.** `_TYPE_DIRS` gained `"B": "books"`, and the id regex is now
  `^[SCGB]`. Every book chapter was unresolvable before this.
- **Router fallback.** `FALLBACK_TOPIC = "twin_beacons_doctrine"` replaces the
  hard-coded `rule_of_law`, which v2 deleted. Before this, a bad routing
  reached the composer with zero documents.
- **Identity intent.** `robot_identity_meta` is injected at load. v2 treats it
  as a router *intent*, not a topic, but the router prompt and
  `force_meta_routing()` still emit it.
- **Document ranking.** `_select_source_doc_ids(..., question=)` now ranks by:
  1. question words shared with each doc's title + keywords (index built once
     at boot, `CorpusArtifacts.doc_index`);
  2. the old topic score (2 × primary topic + 1 per secondary topic);
  3. whether the doc's own `topic_paths.primary` is the routed primary topic;
  4. doc id.

  v2 topics hold up to about 190 docs. With the old alphabetical tiebreak,
  every question on a topic got the same book chapters. With topic score
  first, the secondary-topic bonus buried the right doc: the Lambino question
  got three GMA-era chapters instead of `BA001`, which names
  *Lambino v. Comelec*.
- **Question threading.** `build_context(..., question=)` is passed through at
  every call site, including the fidelity-audit rebuild in
  `app/speech_streaming.py`. Otherwise the audit would check a different set
  of documents from the ones the composer saw.
- **Premise gate.** `app/premise_gate.py` now reads the corpus horizon from
  `date`, because v2 docs have no `year` field.
- **Token budgets.** The table was re-seeded onto the v2 topic ids using the
  same theme rule (A 260, B 240, C 200, D 220, E 240, META 120).
- **Duet provenance.** `duet_script.json` provenance ids were renumbered
  (CA006→CA111, CA012→CA184, CD002→CD016). Metadata only; the audio is
  unchanged.
- **Tests.** New file `tests/test_kb_v2.py`.

### A/B evaluation (same 42 questions, production text path, Sonnet composer, one run each)

| | v1 corpus | v2 corpus |
|---|---|---|
| Haiku audit: hallucination / voice drift / guardrail | 2 / 1 / 8 | **1 / 1 / 1** |
| Fact-gate blocks | 0 | 0 |
| Composer input tokens (median) | 6.3k | 7.4k (+18%) |
| Full-answer compose time (median / max) | 6.7 s / 10.0 s | 7.3 s / 13.9 s |

- **Remaining flags are false positives.** The one remaining v2 hallucination
  flag (Echegaray) is wrong: `BA070` states the claim word for word. The one
  answer-gate trip is rule `lambino-case`, which expects the word "comelec";
  the answer itself is correct.
- **Routing is sharper.** Grace Poe, Bangsamoro, Ressa, DAP and Robredo each
  get their own topic now, instead of a generic "constitutional doctrine".
- **Time to first sentence was not measured.** That is what visitors notice.

### Alpha's off-repo files captured (commit `d7a7eec`)

- **`deploy/alpha/`** holds the systemd units and the `wakeword.conf` drop-in
  (48 `Environment=` settings), `~/bin`, `~/tools`, `.asoundrc`, the filler
  clips (ElevenLabs clone, not reproducible), the dashboard videos, the
  speaker-embedding model, the avatar portrait and the console state.
- **`docs/handover-notes/`** holds the `.docx` working notes and
  `PROJECT_NOTES.txt`.
- **Verified.** Everything was scanned for keys, and three files were checked
  byte-identical to the live machine.
- **Deliberately excluded:** keys, TLS certs, the 521 MB TTS cache, and
  recordings and voiceprints of real people.

## 3. Do not

- **Do not run the old corpus builders.** `scripts/build_topic_map.py` and
  `generate_corpus_files.py` still encode v1 (35 topics) and would overwrite
  v2. v2 is regenerated upstream and re-imported.
- **Do not trust old doc ids.** v2 renumbered them: old `CA001` is now `CA092`,
  and `CA011` now names a *different* column. `CA016` "Rule of, or by, law"
  (2018-02-02) was dropped. Old ids in audits and reports refer to v1.
- **Do not set `CJ_PIPELINE=retrieval`.** That switch belongs to the release
  codebase and does nothing here.
- **Do not force-push or move `pi/deployment-snapshots` or
  `release/kb-v2-2026-09-27`.**
- **Do not re-enable `speaker-watchdog.service`.** It moves audio onto any
  paired Bluetooth speaker mid-event.
- **Do not add a non-clone voice fallback.** All TTS goes through
  `speech_engines.tts_cloned_wav()` and `app/voice_guard.py`.
- **Do not restart `supervaise` mid-answer.** Check
  `journalctl -u supervaise.service --since "-2 min"` for recent
  `[stream-speak]`/`[gesture]` lines first; `cj_speaking.json` can read idle
  while it is speaking.

## 4. Operational facts not obvious from the code

- **Voice.**
  - **Engine.** Alpha is **Fish Audio only** (`CJ_TTS_ORDER=fish`, user
    decision 2026-09-28): silence is preferred over a second,
    different-sounding clone. Fish bills API credit separately from platform
    credit, so a 402 with a visible balance means the API credit is empty.
  - **Beta.** Beta has no Fish key, so never make `fish` the code default.
  - **Speed.** Fish is ~3.8× slower per sentence than ElevenLabs, which adds
    about 1.3 s to the first audio.
  - **Fillers.** The filler clips are the ElevenLabs clone, so the voice changes
    slightly at the filler seam.
  - **Name pin.** The pinned pronunciation of "Panganiban" (`pahng-ngah-NEE-bahn`,
    seed 4242, `CJ_NAME_PIN_SPEED=0.90`, `CJ_NAME_PIN_SYLLABLE=ngah:0.30`) is
    ElevenLabs-only; Fish ignores it.
- **Microphone.**
  - **Floor lease.** The mic only opens while `/console` grants the floor
    (3 s lease, fail closed).
  - **"Deaf" robot.** If the robot seems deaf, check `/console` first: the
    floor must be `alpha` and the mode `direct`.
  - **Wake threshold.** At handover the console override is
    `wake_threshold 0.5`, with `dry_run` off. That is probably too high; see
    open item 1.
- **Audio.**
  - **Internal speaker.** The internal ~5 W speaker is inaudible in a hall.
  - **USB DAC.** `~/bin/audio-out dac` routes to a USB DAC. Echo cancellation
    for that route stays off until `CJ_AEC_REF_DELAY_DAC_MS` is set; calibrate
    at the venue with `~/tools/aec_ref_calib.py`.
  - **Hub devices.** `audio-hub.service` automatically prefers a USB-hub mic
    and speaker.
- **Memory.** `MALLOC_ARENA_MAX=2` and `CJ_EMBED_MAX_S=10` keep RSS bounded.
  The speaker embedding once drove RSS to about 1 GB.
- **Truthfulness.**
  - **Fidelity check off.** The whole-answer fidelity check is off
    (`CJ_SKIP_FIDELITY=1`, for latency). Only the per-sentence gates and the
    audit during playback run.
  - **Premise gate.** It declines stale or unanswerable premises before the
    composer runs.
  - **Runbook.** The answer to a false statement in the room is still "switch
    to DUET".
- **LiveAvatar.** The custom avatar `0c62adc0-…` needs the owning account's key
  **and** production mode (paid credits). Every browser-avatar behaviour is
  unverified.

## 5. Open items, in rough priority

1. **Wake threshold looks too high.** The console override at handover is
   `wake_threshold 0.5`, but genuine "Hi Cee-Jap" calls scored 0.066-0.46 when
   measured on 2026-09-15 (`config/modes/direct.json` note). On 2026-09-29 alpha
   logged two calls at 0.188 and 0.169 as "below threshold". The config default
   is 0.02. Check `/console` before an event; it is an operator setting and was
   left as found.
2. **Default branch.** Set GitHub's default branch to `master` (repo settings).
   Only the owner can do this.
3. **Unroutable documents.** 245 of the 1,290 documents appear in no topic's
   `doc_ids`, so the router can never reach them. This is a gap in the
   release's topic map, not in this code. It needs fixing upstream.
4. **Retrieval quality.** Word matching misses paraphrase. "Growing up poor in
   Sampaloc" does not find GC002 "The Boy Who Slept on Pavement", and "your
   wife Leni" gets a papal-award chapter. The real fix is retrieval with
   meaning (embeddings), which the Pi cannot host. A cheaper fix is richer
   keywords upstream.
5. **Latency.** It is up about 0.6 s median, from longer book chapters. The
   lever is `CJ_CONTEXT_BODY_DOCS` (full text for the top 2 docs today; 1 is
   the fallback).
6. **Beta.** Deploy `d7a7eec` to beta if it is ever used again (it needs about
   40 MB for the corpus). Beta also lacks alpha's DAC-era audio scripts and the
   AEC feed settings.
7. **Release-side gaps, known upstream:**
   - topic routing is 86.7% top-1, and `twin_beacons_doctrine` never wins its
     own question;
   - 18 docs have no topic above the floor;
   - about 222 Inquirer columns from Feb 2007 to Apr 2011 were never sourced.
8. **Answer-gate rule.** The `lambino-case` rule should accept a correct answer
   that omits the word "Comelec".
## 6. Where to look

| Need | File |
|---|---|
| Rebuild a robot | [`deploy/alpha/README.md`](../deploy/alpha/README.md) |
| Corpus layout, v2 caveats | [`corpus/MANIFEST.md`](../corpus/MANIFEST.md) |
| Runtime modules | [`app/MANIFEST.md`](../app/MANIFEST.md) |
| Running an event | [`EVENT_RUNBOOK.md`](EVENT_RUNBOOK.md), [`PRE_EVENT_CHECKLIST.md`](PRE_EVENT_CHECKLIST.md) |
| Why the premise gate exists | [`lessons/LL-012-grounded-but-stale-not-recombination.md`](lessons/LL-012-grounded-but-stale-not-recombination.md) |
| Earlier working notes (Word) | [`handover-notes/`](handover-notes/) |
