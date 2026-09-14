# Venue runbook — Panganiban exhibit

For one person, alone, with no engineer. Written 2026-09-13.

The full illustrated version is `~/event_runbook.docx` on the alpha robot
(also handed to the project owner). This is the version-controlled copy so the
procedure cannot be lost with a laptop.

## The two robots

| You will hear it called | What it is |
|---|---|
| alpha, `reachy-cjap` | The LEFT robot. Also runs the console and is **in charge of both**. |
| beta, `reachy-2` (192.168.88.10) | The other robot. Only ever plays prepared audio. |
| Panganiban / CJAP | The character that answers. Normally alpha plays it. |
| Host | The character that introduces and asks. Normally beta plays it. |

**alpha is in charge. If alpha is off, BOTH robots go silent**, even though
beta is fine. That is deliberate: better silent than both talking at once.

## Starting from cold

1. **Travel router first.** Wait for its lights to settle. Both robots join the
   router, not the venue network — a guest network blocks them finding each other.
2. **Power on alpha.** Wait two minutes; it brings up the console as well as itself.
3. **Power on beta.** Wait one minute.
4. Join the same network and open
   `https://reachy-cjap.local:8443/console?key=cjap`. Accept the certificate warning.
5. **Both robot rows must be reporting**, age one or two seconds. A stale row means
   that robot did not join the network — back to step 1.
6. **Choose the mode.** DUET for an empty room, DIRECT for visitors, then the
   profile: EVENT for a hall, KIOSK for a quiet room.
7. **Run the room calibration** (below), in the room, with the room as noisy as it
   will really be.
8. **Test one answer** with the Host asks box before anyone arrives.

If step 8 gives an apology rather than an answer, the internet is down or the API
account is empty. **DUET works with no internet at all** — fall back to it.

Before walking away: both rows reporting, heads moving gently, sound audible at the
back of the room, mode and profile as chosen.

## Room calibration

Teaches the robot how loud the room is. **It has never been run at a venue.**

1. Get the room to its real state — crowd, music, everything.
2. Make sure the robot you are calibrating **holds the floor** (its mic must be open).
3. Start calibration, leave it two minutes, do not talk into the mic.
4. Accept the proposal if the room is genuinely noisy; reject it if you ran it in a
   quiet room by mistake.

An accepted calibration **persists across mode changes** until cleared.

## Modes

| Mode | The room sees | Internet? |
|---|---|---|
| DUET | The robots perform a scripted exchange. ~4.5 min, then repeats. | **No** |
| DIRECT + KIOSK | Visitor says "Hi Cee-Jap", asks, and can follow up. | Yes |
| DIRECT + EVENT | No wake phrase. Handheld mic starts a question. One question, one answer. | Yes |

Switching takes effect in a second or two on both robots. Nothing restarts.

## Swapping roles

Console → change who plays Panganiban → apply. Both robots switch within a second,
**no restart, no reload**. Both machines carry both characters.

## The five most likely failures

| Symptom | Almost always | Check first |
|---|---|---|
| **Both robots silent and still** | Network between them, or alpha down | Router lights; can you load the console? Which robot row is stale? |
| **Nobody can hear it** | The internal speaker is ~5 W and a hall needs a PA | Is an external speaker actually plugged in? Then `~/bin/audio-out dac` |
| **Answers when nobody is talking** | Room louder than the threshold | Re-run calibration with the crowd in; raise the loudness setting; else switch to DUET |
| **Says something untrue** | The gates do NOT reliably catch this | Switch to DUET immediately; write down exactly what it said |
| **One robot stops mid-sentence** | Network dropped mid-answer | Is that robot still reporting? If stale, power-cycle it |
| **The robot looks frozen / dead** | **The microphone is muted.** Muting deliberately stops the breathing — the robot has no lights, so going still is how it shows it is muted | **Check the mute button on /maintain FIRST.** Unmute and the breathing returns within a second |

## If you lose the network and cannot reach the console

The robot raises its own WiFi network when it has no connection for about a
minute. This is how you get back in with no keyboard and no monitor.

| | |
|---|---|
| Network name | **CJAP Reachy** (on beta: **reachy-2**) |
| Password | **reachymini** |
| Dashboard | **http://10.42.0.1:8080** |

1. On your phone, join **CJAP Reachy**. It can take a minute to appear.
2. Open **http://10.42.0.1:8080** — the WiFi card is on the System tab.
3. **Type the network name by hand.** Scanning does not work while the robot is
   running its own network, so the list will be empty. Tick *hidden network*
   only if the venue network really does not broadcast its name.
4. Submit. The page will drop — that is expected, the robot is switching.
   Rejoin the venue network on your phone and reopen the dashboard: it will
   tell you whether the join worked, in words.
5. If it failed, **CJAP Reachy** comes back within a minute and you can retry.

The robot's own network disappears for about 45 seconds every five minutes
while it checks whether a known network has come back. If it vanishes, wait a
minute and look again.

**It will not appear if the robot is joined to the wrong network** — from the
robot's point of view it has WiFi. Move it out of range of that network, or
power-cycle it somewhere the wrong network cannot be heard.

## If the robot looks frozen

Check this in order. The first one is not a fault and costs ten seconds to rule
out; people have gone looking for a crash when the answer was a muted mic.

1. **Is the microphone muted?** Open `/maintain` and look at the mute button.
   Muting stops the breathing on purpose — the robot has no lights, so a still
   body is the only way it can show it is muted. A muted robot and a crashed
   robot look **identical** from across a room. Unmute, and the head starts
   breathing again within a second.
2. **Is the app running?** `/console` shows the robot as reporting or stale. A
   stale row means the app is down, not muted.
3. **Are the motors off?** `/maintain` has an idle-motion switch. Off means the
   head holds still while everything else works normally.
4. **Is it holding the floor?** A robot without the floor closes its mic and
   goes quiet — that is the one-microphone rule working, not a fault.

Only after all four should anyone power-cycle anything.

## Not problems

- Heads drifting and swaying constantly — deliberate, a still robot looks broken.
- Five to ten seconds before an answer starts — normal, covered by a filler phrase.
- The duet repeating every ~4.5 minutes.
- The robot declining a question — it is designed to decline rather than guess.

## What to tell visitors

It is a recreation of a real, living person, built only from what he actually
published. The Host says exactly that before anyone asks anything, in all six of its
introductions. If asked whether it is really him, the answer is no.
