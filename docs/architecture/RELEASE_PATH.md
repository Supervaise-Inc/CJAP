# The release path — proposed, not executed

Phase 8 found that `deploy/pi/install.sh:5` clones `-b pi/deployment-snapshots`, and that branch carries
the May-era 79-document corpus and none of the five retrieval-stack modules. Phase 9 tagged the branch's
current tip before touching anything else, then evaluated the options below. **Nothing past the tag has
been executed** — this is a proposal, stopped for a decision, per the phase's own instruction.

## The safety tag

```
git tag pi-snapshot-pre-kbv2-2026-09-27 pi/deployment-snapshots
```

Created locally, pointing at `2545882` (`pi snapshot 2026-08-31-0135`), the current tip of
`pi/deployment-snapshots` — confirmed unchanged by the tag (`git rev-parse` before and after the tag
matches). **This tag exists only on this machine.** It should be pushed to `origin`
(`git push origin pi-snapshot-pre-kbv2-2026-09-27`) before it can serve as a real rollback point for
anyone else — that push was not done here, since it is an outward-facing action on the shared remote
and this document is itself part of a "stop for a decision" step.

## What the two branches actually look like

```
git merge-base pi/deployment-snapshots deliverable/2026-09   →  (empty — no common ancestor)
git rev-list --count pi/deployment-snapshots ^deliverable/2026-09   →  113
git rev-list --count deliverable/2026-09 ^pi/deployment-snapshots   →  44
```

**The two branches share no common ancestor at all.** `pi/deployment-snapshots` has 113 commits
`deliverable/2026-09` does not; `deliverable/2026-09` has 44 `pi/deployment-snapshots` does not; and
there is no point where they fork from a shared history. Every one of `pi/deployment-snapshots`'s
commits is a `snapshot-push.sh` auto-commit ("pi snapshot `<timestamp>`") — a full-tree capture of a
live robot's filesystem, not an incremental feature commit meant to be reviewed or merged commit-by-commit.

## The options

### Option A — update `pi/deployment-snapshots` to match `deliverable/2026-09`

Matches the existing convention (`install.sh` needs no change). But because the histories share no
common ancestor, this is not a mergeable pair of branches in any normal sense:

- `git merge deliverable/2026-09` from `pi/deployment-snapshots` would need
  `--allow-unrelated-histories` and would then attempt a 3-way merge with no shared base — every path
  that exists in both trees with different content (essentially the whole tree: 79 vs. 1,290 corpus
  documents, `app/service.py` absent vs. present) becomes a conflict. This is not "clean"; it is a
  wholesale manual reconciliation dressed as a merge.
- A force-update (`git branch -f pi/deployment-snapshots deliverable/2026-09` + `git push --force`)
  avoids the conflict problem by discarding the question rather than answering it, but it also discards
  `pi/deployment-snapshots`'s own purpose: `snapshot-push.sh` writes to this branch *from* a live robot,
  so it is the record of what is actually deployed in the field, not a target engineering pushes *to*.
  Overwriting it conflates the two.
- **A robot currently tracking this branch via `git pull`** (`deploy/pi/TRANSFER.md` §6's "keeping two
  robots in sync" flow) would, after a force-update to an unrelated history, find `git pull` fails
  outright — git refuses a fast-forward across unrelated histories — and would need a fresh clone or a
  hard reset to recover. That is the exact "breaking a robot already in service" case the phase warns
  against.

### Option B — point `install.sh` at an immutable tag cut from `deliverable/2026-09`

E.g. `release/kb-v2-2026-09-27`. A deployed robot then tracks a ref that cannot move under it; a new
release is a new tag, not a mutation of the one an existing robot may already reference. Cost: one line
in `install.sh` (the `git clone -b pi/deployment-snapshots` becomes a clone plus
`git checkout release/kb-v2-2026-09-27`, or a direct `git clone -b release/kb-v2-2026-09-27`), and a new
"cut a release tag from deliverable/2026-09" step in whatever runbook governs shipping a batch. Rollback
is exactly as simple as pointing `install.sh` back at `pi-snapshot-pre-kbv2-2026-09-27` (or at
`pi/deployment-snapshots` unchanged, since Option B never touches it).

### Option C — retire `pi/deployment-snapshots` as an install source, keep it as the field-state record

A variant of B, not a genuinely different mechanism: `install.sh` stops referencing
`pi/deployment-snapshots` for new installs (pointing at release tags on `deliverable/2026-09` instead),
while `snapshot-push.sh` keeps writing to `pi/deployment-snapshots` from live robots exactly as it does
today, so that branch's actual, current purpose — "what a robot's filesystem look like when it was last
pushed" — stops being conflated with "what a fresh install should get". This is Option B with the
naming/roles made explicit rather than left implicit; it does not require deciding anything B does not.

## Recommendation

**Option B (with the framing from C).** The no-common-ancestor finding makes Option A not a merge in any
meaningful sense — it is a forced overwrite of a branch whose actual job is recording field state, and
it would break `git pull`-based sync for any robot already tracking it. An immutable release tag costs
one line of `install.sh` and one new runbook step, never moves under a deployed robot, and has a
one-line rollback. It also cleanly separates two things that are currently tangled under one branch
name: "what a fresh install gets" and "what robot X actually has right now."

**Confirmed for whichever ref is chosen:** a fresh clone of `deliverable/2026-09` (the source a release
tag would be cut from) already contains all five retrieval-stack modules and `config.py`:

```
app/service.py        present
app/retrieval.py      present
app/embeddings.py     present
app/sparse.py         present
app/centering.py      present
config.py             present
```

## Stopped here

No branch was updated, no tag was pushed to `origin`, and `install.sh` was not edited. This document
records the analysis and the recommendation; the decision itself is the user's, per the phase's explicit
instruction to stop before executing it.
