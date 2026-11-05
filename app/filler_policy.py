"""When and what the "thinking" filler plays (2026-11-05).

The turn-latency study (Research_2026-11/01_latency_map.md, finding C1) found the
single biggest wait in a turn is the answer sitting behind a filler clip: the
40 canned clips run 2.6-5.2 s (median 3.72 s), a clip starts 2.2-3.6 s into the
turn, and FillerLoop.stop() never cuts a clip mid-word, so a first sentence that
is ready at about 4 s waits until about 5-6 s. Lowering CJ_FILLER_FIRST_WAIT_S
alone makes it worse (the clip only starts sooner).

Two rules live here, both pure so they can be tested without a robot:

1. SHORT CLIPS. CJ_FILLER_SHORT_DIR (default ~/fillers_short) holds clips of
   about 1.2 s or less, rendered in the cloned voice by
   scripts/render_short_fillers.py. When that directory has clips, the loop uses
   ONLY them, so a clip is over before the answer is ready. With no short
   clips the old set is used unchanged, and CJ_FILLER_MAX_CLIP_S (0 = off)
   prefers whatever is short enough in it.

2. NO NEW CLIP ONCE THE ANSWER IS COMING. The composer's first token means the
   first sentence follows within about 0.5-1.3 s, so no further clip is started
   (FillerLoop.defer() used to help only while the loop was still in its silent
   hold). To keep a slow synthesis from leaving dead air, a clip is allowed
   again if the answer is still not on air CJ_FILLER_TOKEN_QUIET_MAX_S (2.5 s)
   after the first token.
"""
import glob
import os
import random

SHORT_DIR_DEFAULT = "~/fillers_short"


def _env_num(name, default):
    try:
        return float(os.environ.get(name, "").strip() or default)
    except ValueError:
        return float(default)


def clip_dirs(long_dir, env=None):
    """(short_dir, long_dir) with the short one resolved from the environment."""
    env = os.environ if env is None else env
    short = os.path.expanduser(env.get("CJ_FILLER_SHORT_DIR", SHORT_DIR_DEFAULT) or SHORT_DIR_DEFAULT)
    return short, long_dir


def load_clips(long_dir, env=None):
    """The clip list for a loop: the short set when it exists, else the long set."""
    short, long_ = clip_dirs(long_dir, env)
    shorts = sorted(glob.glob(os.path.join(short, "*.wav")))
    if shorts:
        return shorts
    return glob.glob(os.path.join(long_, "*.wav"))


def build_pool(clips, recent, duration_fn, first, max_clip_s=None, rng=random):
    """The play order: pop() takes the LAST element.

    Skips clips heard in the last few questions (falls back to the full set when
    that empties the pool), shuffles, and for the first clip of a turn sorts so
    the SHORTEST comes out first. max_clip_s > 0 keeps only clips at or under
    that length when any exist; otherwise the whole pool stays (so a set with
    nothing short enough still plays its shortest clip first)."""
    if max_clip_s is None:
        max_clip_s = _env_num("CJ_FILLER_MAX_CLIP_S", 0)
    pool = [c for c in clips if c not in recent] or list(clips)
    if max_clip_s and max_clip_s > 0:
        short = [c for c in pool if duration_fn(c) <= max_clip_s]
        if short:
            pool = short
    rng.shuffle(pool)
    if first:
        pool.sort(key=duration_fn, reverse=True)
    return pool


def stay_quiet(token_ts, now, quiet_max_s=None):
    """True while no new clip should start: the first composer token is in and
    the answer is expected shortly. token_ts is None until the first token.
    After quiet_max_s without the answer reaching the air, clips resume."""
    if token_ts is None:
        return False
    if quiet_max_s is None:
        quiet_max_s = _env_num("CJ_FILLER_TOKEN_QUIET_MAX_S", 2.5)
    return (now - token_ts) < quiet_max_s
