"""/stage and /monitor — two read-only display views (2026-09-14).

/stage    full-bleed face only, for a visitor. No text, no chrome, no cursor,
          no error state ever. The four states — idle, listening, thinking,
          speaking — must be legible at two metres with no labels, which is
          the whole job of the view.
/monitor  avatar + camera + the question and answer, for an operator.

Both consume ONE endpoint, /api/display, and nothing else. That endpoint is
read-only: it reads the same /dev/shm files the dashboard already reads and
the console object already in this process. It starts no LiveAvatar session,
issues no command, writes no file, and calls nothing in the pipeline.

Three things learned from reading the existing avatar page, which shaped all
of this (see docs — ~/display_notes.docx):

  * avatar_session() (ui_page_face.py:855) creates a NEW PAID session on every
    call, with no registry and no reference count. Three pages open would be
    three paid sessions. Neither view here ever calls it.
  * the existing page WRITES: a 5 s heartbeat, a global avatar_cmd file where a
    Stop meant for one screen stops all of them, and an idle-loop recorder.
    These views write nothing, so they cannot disturb a turn or another screen.
  * EXHIBIT_JS hard-binds DOM ids with no null guards (its own comment says so
    at ui_page_audience.py:290). Reusing it piecemeal is how you get a blank
    page, so /stage carries its own small renderer instead.

The avatar picture itself: with no live session there is NO face image anywhere
on disk — the "portrait still" on /face-avatar is a canvas the page snapshots
out of the live video, so it is black until a session has run in that same
browser. The backdrop here is therefore PLUGGABLE: drop a file at
assets/portrait.{jpg,png,webp,mp4,webm} and both views use it; with no file
they fall back to a non-photographic form that carries the same four states.
Nothing needs to change in this file when the portrait appears.
"""
from __future__ import annotations

import json
import os
import time

from ui_common import (ASSETS, MUTED_FLAG, SPEAKING, TRANSCRIPT, TURN_META,
                       UI_REV, WAKE_LIVE, _read_json, _tail_jsonl, _health,
                       camera_off, cam_backend, motion_get)

STAGE_DOC = "/dev/shm/cj_stage.json"

# A backdrop, if one has been provided. Checked per request (cheap: one stat)
# so a portrait can be dropped in without restarting the dashboard.
PORTRAIT_NAMES = ("portrait.webm", "portrait.mp4", "portrait.webp",
                  "portrait.png", "portrait.jpg", "portrait.jpeg")
_VIDEO_EXT = (".webm", ".mp4")


def portrait():
    """-> {"file": name, "kind": "video"|"image"} or None when none is present."""
    try:
        for n in PORTRAIT_NAMES:
            if os.path.exists(os.path.join(ASSETS, n)):
                return {"file": n,
                        "kind": "video" if n.endswith(_VIDEO_EXT) else "image"}
    except OSError:
        pass
    return None


# ---------------------------------------------------------------------------
# Robot state — one definition, server side
# ---------------------------------------------------------------------------
# A server-side mirror of robotMode() from ui_page_maintenance.py:936, so that
# /stage and /monitor cannot drift apart from each other or from /maintain, and
# so neither has to re-implement the brittle version in the browser.
_STEP_ORDER = ("transcribe", "route", "compose", "fidelity")


def _robot_state(sp, stg, turns, health, muted, now):
    """-> {"st", "since", "detail"} where st is one of
    down | speaking | listening | thinking | muted | idle."""
    if health.get("supervaise") is False:
        return {"st": "down", "since": None, "detail": "the voice app is not running"}

    users = [t for t in turns if t.get("role") == "user"]
    cjs = [t for t in turns if t.get("role") == "cj"]
    last_u = users[-1] if users else None
    last_c = cjs[-1] if cjs else None
    steps = (stg or {}).get("steps") or {}
    tr = steps.get("transcribe") or {}

    spoken = (sp or {}).get("spoken") or []
    if sp and not sp.get("done") and spoken:
        return {"st": "speaking", "since": sp.get("play_ts") or sp.get("ts"),
                "detail": f"sentence {len(spoken)}"}

    listening = (tr.get("state") == "active"
                 and stg and (now - (stg.get("ts") or 0)) < 60)
    q_now = bool(last_u and stg and last_u.get("ts", 0) >= (stg.get("turn_ts") or 0) - 1)
    if listening and not q_now:
        return {"st": "listening", "since": stg.get("ts"),
                "detail": tr.get("detail") or "mic open"}

    if last_u and (not sp or last_u.get("ts", 0) > (sp.get("ts") or 0)) \
            and (not last_c or last_u.get("ts", 0) > last_c.get("ts", 0)):
        active = [k for k in _STEP_ORDER
                  if (steps.get(k) or {}).get("state") == "active"]
        return {"st": "thinking", "since": last_u.get("ts"),
                "detail": (active[-1] if active else "working")}

    if muted:
        return {"st": "muted", "since": None, "detail": "microphone muted"}

    end_ts = (sp or {}).get("ts") if (sp and sp.get("done") and spoken) else (
        last_c.get("ts") if last_c else None)
    return {"st": "idle", "since": end_ts, "detail": ""}


# ---------------------------------------------------------------------------
# Turn assembly — question, answer, gates, latency
# ---------------------------------------------------------------------------
# A gate leaves its mark as a transcript NOTE (main_voice_robot.py:3107-3120
# for the answer gate and the fidelity audit, and :3268 for a premise decline),
# so the notes are matched back to the turn they belong to rather than invented.
_GATE_MARKS = (
    ("answer gate blocked", "answer gate"),
    ("full-answer audit", "answer audit"),
    ("fidelity audit flagged", "fidelity"),
    ("premise declined", "declined"),
    ("offline during compose", "offline"),
    ("API error during compose", "api error"),
    ("canned answer", "curated"),
    ("interrupted by wake phrase", "interrupted"),
    ("raw ASR", None),        # carries the pre-correction transcript; never public
)


def _gate_tags(note_text):
    out = []
    low = (note_text or "").lower()
    for needle, tag in _GATE_MARKS:
        if tag and needle.lower() in low:
            out.append(tag)
    return out


def _turns(turns, metas, public):
    """Fold the flat transcript feed into [{ts, q, a, gates, raw, latency_s}],
    oldest first. The transcript is a TAIL, not a log — /dev/shm holds what the
    running process has published, so this is a session scrollback and does not
    survive a reboot."""
    composed = {}
    for m in metas:
        if m.get("phase") == "composed" and m.get("question"):
            composed[m["question"]] = m

    out, cur = [], None
    for t in turns:
        role, text, ts = t.get("role"), t.get("text") or "", t.get("ts")
        if role == "user":
            if cur:
                out.append(cur)
            cur = {"ts": ts, "q": text, "a": "", "gates": [], "raw": None,
                   "latency_s": None}
        elif role == "cj" and cur is not None:
            cur["a"] = text
        elif role == "note" and cur is not None:
            if "raw ASR" in text:
                cur["raw"] = text
            cur["gates"].extend(_gate_tags(text))
    if cur:
        out.append(cur)

    for t in out:
        m = composed.get(t["q"])
        if m:
            t["latency_s"] = m.get("first_audio_s")
        t["gates"] = sorted(set(t["gates"]))
        if public:
            # A misheard question rendered on screen is worse than a misheard
            # one spoken, because it is legible and photographable. In public
            # mode a question appears only once the robot has answered it, and
            # never if a guardrail fired on that turn.
            t.pop("raw", None)
            t.pop("latency_s", None)
            if t["gates"] or not t["a"]:
                t["q"], t["a"] = "", ""
            t["gates"] = []
    return [t for t in out if t["q"] or t["a"]]


# ---------------------------------------------------------------------------
# The document
# ---------------------------------------------------------------------------
def display_doc(public=False, console=None):
    """Everything /stage and /monitor need, and nothing else.

    ~1-3 KB against /api/state's 11.7 KB, because a wall display polling for
    four hours should not pull the whole maintenance document to read six
    fields."""
    now = time.time()
    sp = _read_json(SPEAKING) or {}
    stg = _read_json(STAGE_DOC) or {}
    turns = _tail_jsonl(TRANSCRIPT, 80)
    metas = _tail_jsonl(TURN_META, 24)
    health = _health() or {}
    muted = os.path.exists(MUTED_FLAG)
    st = _robot_state(sp, stg, turns, health, muted, now)

    doc = {
        "ts": now,
        "rev": UI_REV,
        "public": bool(public),
        "state": st["st"],
        "state_since": st["since"],
        "portrait": portrait(),
        # the caption feed, trimmed to what a view renders
        "speaking": {
            "current": sp.get("current"),
            "n": len(sp.get("spoken") or []),
            "done": bool(sp.get("done", True)),
            "interrupted": bool(sp.get("interrupted")),
            "words": sp.get("words"),
            "wav": sp.get("wav"),
            "dur": sp.get("dur"),
            # the moment audio TRULY started, on the robot's clock
            # (speech_streaming.py:119) — the anchor the envelope syncs to
            "play_ts": sp.get("play_ts"),
            "ts": sp.get("ts"),
        },
        "turns": _turns(turns, metas, public),
        "camera": bool(cam_backend()) and not camera_off(),
    }
    # the two presentation knobs the browser acts on, so /stage and /monitor
    # pick up a /tune change without being reloaded (the robot's own head knobs
    # are not sent — nothing in a browser can act on them)
    try:
        m = motion_get()
        doc["motion"] = {"lipsync_gain": m.get("lipsync_gain", 1.0),
                         "avatar_offset": m.get("avatar_offset", 0.0)}
    except Exception:
        doc["motion"] = {"lipsync_gain": 1.0, "avatar_offset": 0.0}
    if not public:
        doc["state_detail"] = st["detail"]
        doc["muted"] = muted
        doc["health"] = {"supervaise": health.get("supervaise")}
        w = _read_json(WAKE_LIVE) or {}
        doc["wake_armed"] = bool(w.get("ts") and (now - w["ts"]) < 3)

    # Which robot, which role, which mode — from the console object already in
    # this process. No second HTTP call, and it follows a role swap because the
    # console is the authority for cjap_is.
    try:
        if console is not None and console.is_authority():
            c = console.get_console()
            cjap = c.cjap_is
            doc["robot"] = {
                "slot": cjap,
                "machine": c.sources.machine_of(cjap),
                "label": c.name(cjap),
                "role": "cjap",
            }
            doc["mode"] = c.mode
            doc["profile"] = c.profile
            obs = (c.observed or {}).get(cjap) or {}
            doc["online"] = obs.get("online")
        else:
            doc["robot"] = None
    except Exception:
        doc["robot"] = None          # never let the console break a display
    return doc


# ===========================================================================
# The state layer — shared by both views
# ===========================================================================
# This is the product for /stage: a visitor must tell idle from listening from
# thinking from speaking with no labels and no text, at two metres. So the four
# states are carried on THREE independent channels — colour, motion character
# and brightness — not on colour alone, which fails at distance and for a
# colour-blind viewer.
#
#   idle       deep indigo    slow breath only                  dim
#   listening  cool cyan      breath + a ring expanding outward  medium
#   thinking   warm amber     breath + an arc orbiting           medium
#   speaking   warm gold      breath + the envelope of the voice bright
#
# Breathing runs in ALL FOUR, including speaking, and never stops: a portrait
# that stops moving reads as a crashed screen, which is the failure this view
# exists to avoid.
DISPLAY_JS = r"""
// ---- state layer -------------------------------------------------------
// Draws into a canvas sized to its parent. Works with no backdrop, over a
// portrait image/video, and over live avatar video if one is ever present:
// it only ever composites ON TOP, never replaces.
function StateLayer(canvas, opts){
  opts = opts || {};
  const ctx = canvas.getContext('2d');
  let st='idle', env=0, envTarget=0, t0=performance.now(), raf=null, alive=Date.now();
  const PAL = {
    idle:      {r:146, g:112, b:216, glow:0.42},
    listening: {r:72,  g:190, b:210, glow:0.56},
    thinking:  {r:236, g:166, b:74,  glow:0.56},
    speaking:  {r:246, g:198, b:110, glow:0.78},
    muted:     {r:120, g:120, b:130, glow:0.26},
    down:      {r:120, g:120, b:130, glow:0.26}
  };
  function fit(){
    const d = Math.max(1, window.devicePixelRatio||1);
    const w = canvas.clientWidth||window.innerWidth, h = canvas.clientHeight||window.innerHeight;
    if(canvas.width!==Math.round(w*d)||canvas.height!==Math.round(h*d)){
      canvas.width=Math.round(w*d); canvas.height=Math.round(h*d);
    }
  }
  function draw(now){
    alive = Date.now();
    fit();
    const W=canvas.width, H=canvas.height, t=(now-t0)/1000;
    const cx=W/2, cy=H*(opts.centerY||0.5), R=Math.min(W,H)*(opts.scale||0.34);
    // BREATHING — every state, always. ~0.22 Hz, and it is never gated.
    const breath = 1 + 0.055*Math.sin(t*2*Math.PI*0.22) + 0.014*Math.sin(t*2*Math.PI*0.37);
    // idle carries the breath in BRIGHTNESS too — at rest there is no other
    // motion, and an unlit form reads as a screen that has failed
    const bGlow = (st==='idle') ? (1 + 0.22*Math.sin(t*2*Math.PI*0.22)) : 1;
    env += (envTarget-env)*0.35;                  // smooth the envelope
    const p = PAL[st] || PAL.idle;
    ctx.clearRect(0,0,W,H);

    // the field: a soft radial bloom, brightness carries state
    const speak = (st==='speaking') ? env : 0;
    const glow = p.glow*(1 + speak*0.85)*bGlow;
    const rad = R*breath*(1 + speak*0.10);
    let g = ctx.createRadialGradient(cx,cy,rad*0.10, cx,cy,rad*1.95);
    g.addColorStop(0,   'rgba('+p.r+','+p.g+','+p.b+','+(glow).toFixed(3)+')');
    g.addColorStop(0.45,'rgba('+p.r+','+p.g+','+p.b+','+(glow*0.30).toFixed(3)+')');
    g.addColorStop(1,   'rgba('+p.r+','+p.g+','+p.b+',0)');
    ctx.fillStyle=g; ctx.beginPath(); ctx.arc(cx,cy,rad*1.95,0,7); ctx.fill();

    // the core, so there is a definite form and not only a haze
    ctx.beginPath(); ctx.arc(cx,cy,rad*0.52,0,7);
    ctx.fillStyle='rgba('+p.r+','+p.g+','+p.b+','+(0.16+speak*0.34).toFixed(3)+')';
    ctx.fill();

    // LISTENING — rings travelling outward. Reads as "open, waiting".
    if(st==='listening'){
      for(let i=0;i<3;i++){
        const ph=((t*0.45)+i/3)%1;
        ctx.beginPath(); ctx.arc(cx,cy,rad*(0.55+ph*1.25),0,7);
        ctx.lineWidth=Math.max(3,R*0.034*(1-ph*0.55));
        ctx.strokeStyle='rgba(150,240,255,'+(0.80*(1-ph)).toFixed(3)+')';
        ctx.stroke();
      }
    }
    // THINKING — an arc orbiting. Reads as "working", and cannot be mistaken
    // for the rings because it travels around rather than outward.
    if(st==='thinking'){
      const a=t*1.5;
      for(let i=0;i<3;i++){
        ctx.beginPath();
        ctx.arc(cx,cy,rad*(0.88+i*0.20), a+i*2.1, a+i*2.1+1.5);
        ctx.lineWidth=Math.max(3,R*0.038); ctx.lineCap='round';
        ctx.strokeStyle='rgba(255,214,150,'+(0.82-i*0.20).toFixed(3)+')';
        ctx.stroke();
      }
    }
    // SPEAKING — the voice itself. A band across the form that opens with the
    // amplitude of what is being said right now.
    if(st==='speaking'){
      const bw=rad*(1.05), bh=Math.max(R*0.012, rad*0.30*env);
      const bg=ctx.createLinearGradient(cx-bw,cy,cx+bw,cy);
      bg.addColorStop(0,'rgba('+p.r+','+p.g+','+p.b+',0)');
      bg.addColorStop(0.5,'rgba(255,236,196,'+(0.30+env*0.55).toFixed(3)+')');
      bg.addColorStop(1,'rgba('+p.r+','+p.g+','+p.b+',0)');
      ctx.fillStyle=bg;
      ctx.beginPath();
      if(ctx.ellipse) ctx.ellipse(cx,cy+rad*0.20,bw*0.55,bh,0,0,7);
      else ctx.arc(cx,cy+rad*0.20,bh,0,7);
      ctx.fill();
    }
    raf=requestAnimationFrame(draw);
  }
  raf=requestAnimationFrame(draw);
  return {
    set:(s)=>{ if(PAL[s]) st=s; },
    envelope:(v)=>{ envTarget=Math.max(0,Math.min(1,v||0)); },
    state:()=>st,
    lastFrame:()=>alive
  };
}

// ---- envelope from the sentence actually being spoken -------------------
// The browser fetches the same wav the robot is playing (/api/sentence.wav)
// and measures it locally. Nothing is added to the pipeline and no audio is
// played here — this is analysis only, the sound comes from the robot.
//
// Sync anchor: speaking.play_ts is the moment audio TRULY started, on the
// robot's clock (app/speech_streaming.py:119). The dashboard runs on the same
// machine as the robot, so doc.ts and play_ts share a clock; elapsed time is
// taken from that and then advanced locally. OFFSET_MS trims the rest — the
// speaker path differs between the internal speaker and an external one, so
// it is a URL parameter, never a constant.
function Envelope(offsetMs){
  let frames=null, dur=0, startedAt=0, name=null, ac=null, busy=false;
  const HZ=60;
  function ctxOf(){
    if(!ac){ try{ ac=new (window.AudioContext||window.webkitAudioContext)(); }catch(e){ ac=null; } }
    return ac;
  }
  async function load(wav){
    if(!wav || wav===name || busy) return;
    busy=true;
    try{
      const a=ctxOf(); if(!a) return;
      const r=await fetch('/api/sentence.wav?name='+encodeURIComponent(wav),{cache:'no-store'});
      if(!r.ok) return;
      const buf=await a.decodeAudioData(await r.arrayBuffer());
      const ch=buf.getChannelData(0), step=Math.max(1,Math.floor(buf.sampleRate/HZ));
      const out=new Float32Array(Math.ceil(ch.length/step));
      let peak=1e-6;
      for(let i=0,k=0;i<ch.length;i+=step,k++){
        let s=0; const end=Math.min(ch.length,i+step);
        for(let j=i;j<end;j++) s+=ch[j]*ch[j];
        out[k]=Math.sqrt(s/Math.max(1,end-i)); if(out[k]>peak) peak=out[k];
      }
      for(let i=0;i<out.length;i++) out[i]=Math.min(1,(out[i]/peak)*1.15);
      frames=out; dur=buf.duration; name=wav;
      startedAt=0;                      // not started: waiting for play_ts
    }catch(e){ /* a display never shows an error */ }
    finally{ busy=false; }
  }
  // Anchor to the moment audio TRULY began, on the robot's clock. Called only
  // once play_ts appears; before that the envelope stays silent rather than
  // running ahead of the voice.
  function start(elapsed){
    if(!frames || startedAt) return;
    startedAt=performance.now()-Math.max(0,(elapsed||0)*1000);
  }
  function value(){
    if(!frames || !startedAt) return null;
    const tms=performance.now()-startedAt-(offsetMs()||0);
    if(tms<0) return 0;
    const i=Math.floor((tms/1000)*HZ);
    if(i>=frames.length) return null;        // clip finished; caller falls back
    return frames[i];
  }
  return {load, start, value,
          clear:()=>{frames=null;name=null;startedAt=0;}, name:()=>name};
}

// ---- the feed ----------------------------------------------------------
// One endpoint, /api/display. On failure it keeps the last good document and
// backs off; it never renders an error, and it recovers on its own when the
// backend comes back, with no refresh.
function Feed(url, onDoc, onHealth){
  let last=null, fails=0, timer=null, stop=false;
  async function tick(){
    if(stop) return;
    try{
      const r=await fetch(url+(url.indexOf('?')<0?'?':'&')+'t='+Date.now(),{cache:'no-store'});
      if(!r.ok) throw new Error('http '+r.status);
      const d=await r.json();
      last=d; fails=0; onDoc(d); if(onHealth) onHealth(true,0);
    }catch(e){
      fails++;
      if(onHealth) onHealth(false,fails);
      // hold the last good document; after ~30 s with no backend, settle to
      // idle rather than freeze on a stale "speaking"
      if(fails>30 && last){ last.state='idle'; last.speaking={done:true}; onDoc(last); }
    }
    const wait = fails===0 ? 1000 : Math.min(8000, 1000*Math.pow(1.6,Math.min(fails,6)));
    timer=setTimeout(tick, wait);
  }
  tick();
  return {stop:()=>{stop=true; if(timer)clearTimeout(timer);}, last:()=>last};
}

// ---- keeping a display awake and alive ---------------------------------
async function keepAwake(){
  try{
    if('wakeLock' in navigator){
      let lock=await navigator.wakeLock.request('screen');
      document.addEventListener('visibilitychange', async ()=>{
        if(document.visibilityState==='visible'){
          try{ lock=await navigator.wakeLock.request('screen'); }catch(e){}
        }
      });
    }
  }catch(e){ /* older browser: the venue note says disable sleep in the OS */ }
}
// If the page throws or the animation stalls, come back by itself. Nobody is
// standing at these screens with a keyboard.
function selfHeal(layer){
  window.addEventListener('error', ()=>setTimeout(()=>location.reload(), 5000));
  window.addEventListener('unhandledrejection', ()=>setTimeout(()=>location.reload(), 5000));
  setInterval(()=>{ if(Date.now()-layer.lastFrame()>30000) location.reload(); }, 10000);
}
"""


# ===========================================================================
# /stage — the visitor's view
# ===========================================================================
STAGE_PAGE = r"""<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>CJAP</title>
<style>
  html,body{margin:0;padding:0;height:100%;width:100%;overflow:hidden;background:#000}
  body.transparent,body.transparent #wrap{background:transparent}
  /* full bleed at ANY aspect ratio: the backdrop covers, the layer overlays.
     No letterboxing and no scrollbars at 16:9, 4:3, 21:9 or portrait. */
  #wrap{position:fixed;inset:0;background:#000;overflow:hidden}
  #back{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:none}
  #layer{position:absolute;inset:0;width:100%;height:100%;display:block}
  /* a visitor never sees a pointer on an exhibit screen */
  body.hidecursor,body.hidecursor *{cursor:none!important}
</style></head><body>
<div id="wrap">
  <img id="back" alt=""><video id="backv" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:none" muted loop playsinline autoplay></video>
  <canvas id="layer"></canvas>
</div>
<script>
""" + DISPLAY_JS + r"""
(function(){
  const Q=new URLSearchParams(location.search);
  if((Q.get('bg')||'black')==='transparent') document.body.classList.add('transparent');
  const URLOFF=Q.has('offset')?(parseInt(Q.get('offset'),10)||0):null;
  let OFFSET=URLOFF||0, GAIN=1;   // /tune sets these live unless the URL pins them

  const layer=StateLayer(document.getElementById('layer'),{scale:0.34});
  const env=Envelope(()=>OFFSET);
  keepAwake(); selfHeal(layer);

  // hide the cursor after 3 s without movement
  let curTimer=null;
  function armCursor(){
    document.body.classList.remove('hidecursor');
    clearTimeout(curTimer);
    curTimer=setTimeout(()=>document.body.classList.add('hidecursor'),3000);
  }
  ['mousemove','touchstart','pointerdown'].forEach(e=>window.addEventListener(e,armCursor,{passive:true}));
  armCursor();

  // backdrop, if one has been provided. Absent, the state layer stands alone.
  let backShown=null;
  function backdrop(p){
    const img=document.getElementById('back'), vid=document.getElementById('backv');
    const want=p?p.file:null;
    if(want===backShown) return;
    backShown=want;
    if(!p){ img.style.display='none'; vid.style.display='none'; return; }
    if(p.kind==='video'){ vid.src='/assets/portrait'; vid.style.display='block'; img.style.display='none'; }
    else { img.src='/assets/portrait'; img.style.display='block'; vid.style.display='none'; }
  }
  // a missing/corrupt backdrop must not take the page down
  document.getElementById('back').onerror=()=>{document.getElementById('back').style.display='none';};
  document.getElementById('backv').onerror=()=>{document.getElementById('backv').style.display='none';};

  let lastWav=null;
  Feed('/api/display?public_display=1', function(d){
    // muted and down are operator concerns; a visitor should simply see a
    // resting exhibit, never a fault
    const s=d.state==='muted'||d.state==='down'?'idle':d.state;
    layer.set(s);
    backdrop(d.portrait);
    const mo=d.motion||{};
    if(URLOFF===null && mo.avatar_offset!=null) OFFSET=Math.round(mo.avatar_offset*1000);
    if(mo.lipsync_gain!=null) GAIN=mo.lipsync_gain;
    const sp=d.speaking||{};
    if(s==='speaking' && sp.wav){
      if(sp.wav!==lastWav){ lastWav=sp.wav; env.load(sp.wav); }   // decode now
      if(sp.play_ts && d.ts) env.start(Math.max(0, d.ts-sp.play_ts));  // start on real audio
    } else if(s!=='speaking'){ lastWav=null; env.clear(); }
  });

  // drive the envelope every frame; when the measured clip runs out (or was
  // never available — a curated line has no per-sentence wav) fall back to a
  // gentle voiced motion so SPEAKING still reads as speaking.
  (function pump(){
    const st=layer.state();
    if(st==='speaking'){
      const v=env.value();
      layer.envelope((v===null ? 0.28+0.22*Math.abs(Math.sin(performance.now()/240)) : v)*GAIN);
    } else layer.envelope(0);
    requestAnimationFrame(pump);
  })();
})();
</script></body></html>"""


# ===========================================================================
# /monitor — the operator's view
# ===========================================================================
MONITOR_PAGE = r"""<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CJAP monitor</title>
<style>
  :root{--bg:#12131a;--panel:#191b24;--line:#2b2e3c;--ink:#e8e6e1;--dim:#9aa0ae;
        --ok:#6ad39f;--warn:#e3b341;--bad:#e5747c}
  *{box-sizing:border-box}
  html,body{margin:0;height:100%;background:var(--bg);color:var(--ink);
    font:15px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
  #grid{display:grid;height:100vh;gap:10px;padding:10px;
    grid-template-rows:minmax(0,46fr) minmax(0,54fr);
    grid-template-columns:1fr 1fr}
  .panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;
    position:relative;overflow:hidden;min-height:0}
  #avatar{grid-column:1;grid-row:1}
  #cam{grid-column:2;grid-row:1}
  #talk{grid-column:1 / span 2;grid-row:2;display:flex;flex-direction:column;padding:12px}
  #layer{position:absolute;inset:0;width:100%;height:100%}
  #camimg{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;background:#000}
  #camoff{position:absolute;inset:0;display:none;align-items:center;justify-content:center;
    text-align:center;color:var(--dim);padding:20px;font-size:17px}
  .tag{position:absolute;top:8px;left:10px;font-size:12px;letter-spacing:.06em;
    text-transform:uppercase;color:var(--dim);z-index:3}
  #head{position:absolute;top:8px;right:10px;z-index:3;text-align:right;font-size:13px}
  .chip{display:inline-block;padding:2px 9px;border-radius:999px;border:1px solid var(--line);
    margin-left:6px;font-size:12px}
  .chip.on{border-color:var(--ok);color:var(--ok)} .chip.bad{border-color:var(--bad);color:var(--bad)}
  .chip.warn{border-color:var(--warn);color:var(--warn)}
  #now{font-size:16px;margin-bottom:8px;color:var(--dim);flex:0 0 auto}
  #q{font-size:20px;margin:0 0 6px;flex:0 0 auto}
  #a{font-size:19px;line-height:1.5;flex:0 0 auto;min-height:2.6em}
  #a .pending{color:var(--dim)}
  #log{margin-top:10px;border-top:1px solid var(--line);padding-top:8px;
    overflow-y:auto;flex:1 1 auto;min-height:0;font-size:14px}
  .turn{padding:7px 0;border-bottom:1px solid rgba(255,255,255,.05)}
  .turn .qq{color:var(--ink)} .turn .aa{color:var(--dim)}
  .meta{font-size:12px;color:var(--dim);margin-top:3px}
  .gate{color:var(--warn);border:1px solid var(--warn);border-radius:4px;
    padding:0 5px;margin-right:5px;font-size:11px;text-transform:uppercase}
  #ctl{position:absolute;bottom:8px;left:10px;right:10px;z-index:3;font-size:12px;color:var(--dim)}
  #ctl input{vertical-align:middle;width:52%}
  .public #ctl,.public .meta,.public .gate,.public #raw{display:none!important}
</style></head><body>
<div id="grid">
  <div class="panel" id="avatar"><span class="tag">avatar</span>
    <canvas id="layer"></canvas>
    <div id="ctl">mouth offset <input id="off" type="range" min="-1000" max="1500" step="25" value="0">
      <span id="offv">0 ms</span> · <span id="stageurl"></span></div>
  </div>
  <div class="panel" id="cam"><span class="tag">camera</span>
    <img id="camimg" alt=""><div id="camoff">camera unavailable</div>
  </div>
  <div class="panel" id="talk">
    <div id="head"></div>
    <div id="now">—</div>
    <div id="q"></div>
    <div id="a"></div>
    <div id="log"></div>
  </div>
</div>
<script>
""" + DISPLAY_JS + r"""
(function(){
  const Q=new URLSearchParams(location.search);
  const PUBLIC=(Q.get('public_display')||'').toLowerCase();
  const isPublic=PUBLIC==='1'||PUBLIC==='true'||PUBLIC==='yes';
  if(isPublic) document.body.classList.add('public');
  const $=(id)=>document.getElementById(id);
  const esc=(s)=>(s==null?'':String(s)).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

  // offset slider — the drift between the robot's speaker and the browser's
  // measurement differs between the internal speaker and an external one, so
  // it is adjustable here and carried to /stage in its URL.
  let OFFSET=parseInt(localStorage.getItem('cj_off')||'0',10)||0;
  $('off').value=OFFSET;
  function showOff(){
    $('offv').textContent=OFFSET+' ms';
    $('stageurl').textContent='/stage?offset='+OFFSET;
  }
  $('off').addEventListener('input',()=>{
    OFFSET=parseInt($('off').value,10)||0;
    try{localStorage.setItem('cj_off',String(OFFSET));}catch(e){}
    showOff();
  });
  showOff();

  let MGAIN=1;
  const layer=StateLayer($('layer'),{scale:0.30});
  const env=Envelope(()=>OFFSET);
  keepAwake(); selfHeal(layer);

  // camera: an MJPEG stream that must fail visibly rather than as a black box
  const cam=$('camimg');
  let camOnce=false;
  function camStart(){ if(camOnce)return; camOnce=true;
    cam.src='/api/camera.mjpg?t='+Date.now(); }
  cam.onerror=()=>{ cam.style.display='none'; $('camoff').style.display='flex';
    camOnce=false; setTimeout(camStart, 8000); };     // keep trying, quietly
  cam.onload=()=>{ cam.style.display='block'; $('camoff').style.display='none'; };

  let lastWav=null, lastTurnKey=null;
  Feed('/api/display'+(isPublic?'?public_display=1':''), function(d){
    layer.set(d.state==='muted'||d.state==='down'?'idle':d.state);

    // who / what / where
    const r=d.robot||{}, bits=[];
    if(r.machine) bits.push('<b>'+esc(r.machine)+'</b> · '+esc(r.label||r.role||''));
    if(d.mode) bits.push('<span class="chip">'+esc(d.mode)+(d.profile?' / '+esc(d.profile):'')+'</span>');
    const stcls=d.state==='speaking'?'on':(d.state==='down'?'bad':(d.state==='muted'?'warn':''));
    bits.push('<span class="chip '+stcls+'">'+esc(d.state)+'</span>');
    if(!isPublic && d.online===false) bits.push('<span class="chip bad">no internet</span>');
    if(!isPublic && d.muted) bits.push('<span class="chip warn">mic muted</span>');
    $('head').innerHTML=bits.join(' ');
    if(!isPublic) $('now').textContent=(d.state_detail||'');

    // the live turn: the answer appears as it is spoken, not all at once
    const turns=d.turns||[], cur=turns.length?turns[turns.length-1]:null;
    const sp=d.speaking||{};
    $('q').innerHTML=cur&&cur.q?'<span style="color:var(--dim)">Q</span> '+esc(cur.q):'';
    let ans=cur&&cur.a?esc(cur.a):'';
    if(d.state==='speaking'&&sp.current) ans=esc(sp.current)+'<span class="pending"> …</span>';
    $('a').innerHTML=ans?'<span style="color:var(--dim)">A</span> '+ans:'';

    // scrollback
    const key=turns.map(t=>t.ts).join(',');
    if(key!==lastTurnKey){
      lastTurnKey=key;
      $('log').innerHTML=turns.slice(0,-1).reverse().map(t=>{
        const g=(t.gates||[]).map(x=>'<span class="gate">'+esc(x)+'</span>').join('');
        const lat=(t.latency_s!=null)?('first audio '+(+t.latency_s).toFixed(1)+'s'):'';
        const raw=t.raw?('<div class="meta" id="raw">'+esc(t.raw)+'</div>'):'';
        return '<div class="turn"><div class="qq">'+esc(t.q)+'</div>'+
               '<div class="aa">'+esc(t.a)+'</div>'+
               (g||lat?'<div class="meta">'+g+lat+'</div>':'')+raw+'</div>';
      }).join('')||'<div class="meta">no turns yet this session</div>';
    }

    if(d.state==='speaking'&&sp.wav){
      if(sp.wav!==lastWav){ lastWav=sp.wav; env.load(sp.wav); }
      if(sp.play_ts && d.ts) env.start(Math.max(0, d.ts-sp.play_ts));
    } else if(d.state!=='speaking'){ lastWav=null; env.clear(); }
    const mo=d.motion||{};
    if(mo.lipsync_gain!=null) MGAIN=mo.lipsync_gain;
    if(d.camera) camStart();
  }, function(okNow,fails){
    // an operator SHOULD see that the backend is gone; a public screen must not
    if(!isPublic && !okNow && fails>2) $('now').textContent='dashboard unreachable — holding last state ('+fails+')';
  });

  (function pump(){
    if(layer.state()==='speaking'){
      const v=env.value();
      layer.envelope((v===null?0.28+0.22*Math.abs(Math.sin(performance.now()/240)):v)*MGAIN);
    } else layer.envelope(0);
    requestAnimationFrame(pump);
  })();
})();
</script></body></html>"""


# ===========================================================================
# /tune — the motion tuning panel
# ===========================================================================
# Sliders that apply to the RUNNING robot with no restart: each drag POSTs to
# /api/motion, which writes /dev/shm/cj_motion.json, which the robot's breath
# loop re-reads every cycle (app/main_voice_robot.py:_motion, mtime-cached).
#
# The preview beside them is the /stage state layer, NOT the robot's head — it
# shows what the browser-side knobs (lip-sync, response delay) do and lets you
# step through the four states without waiting for a turn. The head knobs
# (sway, breath, voice emphasis) act on the robot itself: watch the robot for
# those, which is why this panel is meant to be open next to it.
TUNE_PAGE = r"""<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CJAP motion</title>
<style>
  :root{--bg:#12131a;--panel:#191b24;--line:#2b2e3c;--ink:#e8e6e1;--dim:#9aa0ae;
        --ok:#6ad39f;--warn:#e3b341;--bad:#e5747c}
  *{box-sizing:border-box}
  html,body{margin:0;min-height:100%;background:var(--bg);color:var(--ink);
    font:15px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
  #wrap{display:grid;grid-template-columns:minmax(320px,1fr) minmax(320px,460px);
    gap:14px;padding:14px;align-items:start}
  @media(max-width:820px){#wrap{grid-template-columns:1fr}}
  .panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px}
  h1{font-size:18px;margin:0 0 4px} h2{font-size:14px;margin:0 0 10px;color:var(--dim);
    text-transform:uppercase;letter-spacing:.06em}
  #prev{position:relative;aspect-ratio:16/10;background:#000;border-radius:8px;overflow:hidden}
  #layer{position:absolute;inset:0;width:100%;height:100%}
  .states{display:flex;gap:6px;margin:10px 0 4px;flex-wrap:wrap}
  .states button{flex:1 1 auto;padding:8px 6px;background:#20232e;color:var(--ink);
    border:1px solid var(--line);border-radius:7px;font-size:13px;cursor:pointer}
  .states button.on{border-color:var(--ok);color:var(--ok)}
  .row{margin:13px 0}
  .row label{display:flex;justify-content:space-between;font-size:13px;margin-bottom:3px}
  .row .v{color:var(--ok);font-variant-numeric:tabular-nums}
  .row input[type=range]{width:100%}
  .row .h{font-size:11.5px;color:var(--dim);margin-top:2px}
  .btns{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
  button.act{padding:9px 13px;background:#20232e;color:var(--ink);border:1px solid var(--line);
    border-radius:8px;cursor:pointer;font-size:13px}
  button.act:hover{border-color:var(--ok)}
  select,input[type=text]{background:#20232e;color:var(--ink);border:1px solid var(--line);
    border-radius:7px;padding:8px;font-size:13px}
  #msg{margin-top:10px;font-size:13px;color:var(--dim);min-height:1.3em}
  .note{font-size:12px;color:var(--dim);margin-top:8px;line-height:1.5}
  .warn{color:var(--warn)}
</style></head><body>
<div id="wrap">
  <div class="panel">
    <h1>Motion</h1>
    <div class="note" style="margin-top:0">Sliders apply to the running robot immediately &mdash;
    no restart. <b>Watch the robot</b> for head sway, breathing and voice emphasis; the preview
    here shows the state layer and what lip-sync and response delay do.</div>
    <div id="sliders"></div>
    <div class="btns">
      <button class="act" id="reset">Reset to defaults</button>
      <select id="presets"></select>
      <button class="act" id="load">Apply preset</button>
    </div>
    <div class="btns">
      <input type="text" id="pname" placeholder="preset name" style="flex:1">
      <button class="act" id="save">Save preset &rarr; repo</button>
    </div>
    <div id="msg"></div>
    <div class="note" id="pnote"></div>
  </div>
  <div class="panel">
    <h2>preview &mdash; state layer</h2>
    <div id="prev"><canvas id="layer"></canvas></div>
    <div class="states">
      <button data-s="idle">idle</button><button data-s="listening">listening</button>
      <button data-s="thinking">thinking</button><button data-s="speaking">speaking</button>
      <button data-s="live">follow robot</button>
    </div>
    <div class="note">
      <b>Response delay</b> is the one to set by ear: play a real answer, then drag until the
      mouth stops leading or trailing the voice. It differs per audio route &mdash; the internal
      speaker and an external one are not the same path &mdash; so note the value for each in
      <code>config/avatar_motion.json</code>.<br><br>
      <span class="warn">Breathing stops when the microphone is muted.</span> That is deliberate:
      the robot has no lights, so going still is how it shows it is muted.
    </div>
  </div>
</div>
<script>
""" + DISPLAY_JS + r"""
(function(){
  const $=(id)=>document.getElementById(id);
  const KEY=new URLSearchParams(location.search).get('key')||localStorage.getItem('cjkey')||'';
  let KNOBS={}, VAL={}, follow=true, forced=null;
  const dirty=new Set();
  function mark(){
    for(const k of Object.keys(KNOBS)){
      const v=$('v-'+k); if(!v) continue;
      v.style.color = dirty.has(k) ? 'var(--warn)' : 'var(--ok)';
      v.title = dirty.has(k) ? 'unsaved — release the slider to save' : 'saved';
    }
  }

  const layer=StateLayer($('layer'),{scale:0.32});
  const env=Envelope(()=>((VAL.avatar_offset||0)*1000));
  selfHeal(layer);

  function msg(t,cls){ $('msg').innerHTML='<span class="'+(cls||'')+'">'+t+'</span>'; }

  async function post(body){
    const r=await fetch('/api/motion',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify(Object.assign({key:KEY},body))});
    return r.json();
  }
  async function load(){
    const r=await fetch('/api/motion?key='+encodeURIComponent(KEY));
    if(!r.ok){ msg('bad key — open this page as /tune?key=…','warn'); return; }
    const d=await r.json();
    KNOBS=d.knobs; VAL=d.motion;
    $('presets').innerHTML=Object.keys(d.presets||{}).map(n=>
      '<option'+(n===d.active?' selected':'')+'>'+n+'</option>').join('');
    $('pnote').textContent=(d.preset_notes||{})[d.active]||'';
    draw();
  }
  function draw(){
    $('sliders').innerHTML=Object.keys(KNOBS).map(k=>{
      const [lo,hi,def,lbl]=KNOBS[k];
      const step=(hi-lo)/200;
      return '<div class="row"><label><span>'+lbl+'</span>'+
             '<span class="v" id="v-'+k+'"></span></label>'+
             '<input type="range" id="s-'+k+'" min="'+lo+'" max="'+hi+'" step="'+step+'">'+
             '<div class="h">default '+def+'</div></div>';
    }).join('');
    for(const k of Object.keys(KNOBS)) bind(k);
    mark();
  }
  function show(k){
    const v=VAL[k];
    $('v-'+k).textContent=(k==='motion_scale')?Math.round(v*100)+'%'
      :(k==='avatar_offset')?(v>=0?'+':'')+Math.round(v*1000)+' ms'
      :(+v).toFixed( (KNOBS[k][1]-KNOBS[k][0])>5?2:3 );
  }
  function bind(k){
    const el=$('s-'+k); el.value=VAL[k]; show(k);
    let t=null;
    // Drag = live but UNSAVED (and the value says so). Release = persisted to
    // the active preset, so a number tuned by ear survives a reboot.
    el.addEventListener('input',()=>{
      VAL[k]=parseFloat(el.value); show(k); dirty.add(k); mark();
      clearTimeout(t);
      t=setTimeout(async()=>{                      // coalesce a drag into one write
        const o={}; o[k]=VAL[k];
        const d=await post(o);
        msg(d.ok?'live — release to save':('FAILED — '+(d.output||'')), d.ok?'warn':'warn');
      },120);
    });
    const commit=async()=>{
      if(!dirty.has(k)) return;
      const o={}; o[k]=VAL[k]; o.persist=true;
      const d=await post(o);
      if(d.ok){ dirty.delete(k); mark(); }
      msg(d.ok?(d.output||'saved'):('FAILED — '+(d.output||'')), d.ok?'':'warn');
    };
    el.addEventListener('change', commit);
    el.addEventListener('pointerup', commit);
  }
  $('reset').onclick=async()=>{ const d=await post({reset:true}); msg(d.output||''); load(); };
  $('load').onclick=async()=>{ const d=await post({preset_load:$('presets').value});
    msg(d.output||''); load(); };
  $('save').onclick=async()=>{
    const n=$('pname').value.trim()||$('presets').value;
    const d=await post({preset_save:n}); msg(d.output||'', d.ok?'':'warn'); load();
  };
  document.querySelectorAll('.states button').forEach(b=>{
    b.onclick=()=>{
      document.querySelectorAll('.states button').forEach(x=>x.classList.remove('on'));
      b.classList.add('on');
      const s=b.dataset.s;
      if(s==='live'){ follow=true; forced=null; }
      else { follow=false; forced=s; layer.set(s); }
    };
  });

  let lastWav=null;
  Feed('/api/display', function(d){
    if(follow){
      const s=(d.state==='muted'||d.state==='down')?'idle':d.state;
      layer.set(s);
    }
    const sp=d.speaking||{};
    if(d.state==='speaking'&&sp.wav){
      if(sp.wav!==lastWav){ lastWav=sp.wav; env.load(sp.wav); }
      if(sp.play_ts&&d.ts) env.start(Math.max(0,d.ts-sp.play_ts));
    } else if(d.state!=='speaking'){ lastWav=null; env.clear(); }
  });

  (function pump(){
    const st=layer.state();
    const g=(VAL.lipsync_gain==null?1:VAL.lipsync_gain);
    if(st==='speaking'){
      const v=env.value();
      const base=(v===null?0.28+0.22*Math.abs(Math.sin(performance.now()/240)):v);
      layer.envelope(base*g);
    } else layer.envelope(0);
    requestAnimationFrame(pump);
  })();
  load();
})();
</script></body></html>"""
