# Liza's Magi Quest: campaign plan

Companion to `PLAN.md` (decisions so far) and `README.md` (setup). This file
is the full build plan for turning the five existing levels into one
MagiQuest-style campaign played on five wand stations around the house.

Sources: Liza's story outline (`docs/story/liza-outline.md`), the MagiQuest
Plus story template (`docs/story/magiquest-template.md`), screenshots of the
real game screens (realm map, mentor dialog, rune wheel with 4 items, boss
with a health bar of leaves).

## 1. What we are building

One campaign, five chapters, one wand, five stations, one TV.

| Chapter | Liza's outline | Existing level (reuse) | New mechanic |
|---|---|---|---|
| 0 Castle | Leave the castle after getting the wand | none (new intro scene) | Wand registration: first wave anywhere = "the wand chose you" |
| 1 Fairy Pools | Fairies sick, water poisoned, cure it | `fairy-forest.json` scene **forest** | ordered heal (as today) |
| 2 Crystal Caves | Who stole the crystal? Solve the mystery | `goblin.json` scene **cave** | **collect** mode: gather 4 clue items in any order, then the goblin reveal |
| 3 Frozen Mountain | Climb to the Frost Queen, solve her puzzle | `mountain.json` scene **mountain** | **puzzle** mode: Frost Queen shows a 3-step pattern, repeat it at the stations |
| 4 Unicorn Forest | Forest got zapped, restore magic, Good Witch in a bubble | `unicorns.json` scene **pools** | ordered heal + **charge** at the bubble (wave 5 times) |
| 5 Fire Mountain | Witch clears the rockslide, climb Fire Mountain | `dragon.json` scene **forest+dragon** | **boss** mode: dragon has a leaf health bar, drain it with hits at the lair station |

Between chapters: a **realm map** scene (like the MagiQuest intro map) with
the five lands; cleared lands glow, the next one pulses. Progress is saved
on the Mac so a chapter per evening works.

Mentors (from the template's 4-mentor pattern, cut to what the story needs):
Fairy guide (already drawn, chapters 0-1), Frost Queen (chapter 3), Good
Witch (chapters 4-5). Villains: the Goblin (chapter 2, already drawn), the
Dragon (chapter 5, already drawn). "Dark energy" is the Shadow Spore
equivalent and stays the campaign-wide threat.

## 2. The five stations as objects

MagiQuest hides sensors inside chests, crystals, and runes. Ours hide inside
paper cutouts. Each station is one FIXED landmark in the house; every
chapter re-labels it on the TV but the physical object never changes, so
Liza learns five places and the cutouts are made once.

| Station | Object (cutout) | TV label examples across chapters |
|---|---|---|
| 1 | Crystal cluster | Moonlight Pool, Icicle Tunnel, Ice Steps |
| 2 | Magic mushroom / tree stump | Lily Pool, Glowworm Pool, Snow Pine |
| 3 | Treasure chest | Sparkle Pool, Rock Stairs, Frost Bridge |
| 4 | Lantern | Starlight Pool, Goblin's Nest, Summit |
| 5 | Fountain / spring | Crystal Spring, Crystal Pedestal, Dragon Lair |

Cutout = a printable letter-size SVG (`cards/cutouts/station-N.svg`) folded
into a sleeve around the M5StickS3 with two windows: one for the screen
(the glow) and one for the IR receiver (must stay uncovered; the receiver
position on the StickS3 body is RECON NEEDED, see wargame). Art style
matches the hub: glossy 3D-cartoon, printed on cardstock, optional tape to
a jar or box.

Clue cards point at the physical place ("the lantern in the hallway"); the
TV says the story name. Both are generated from the chapter JSON so they
never disagree.

## 3. Engine changes (hub)

Today: `hub/server.py` holds one adventure, ordered steps, `/hit` returns
`heal | wrong | done`. The page polls `/state` and renders one scene.

Add, in this order (each one testable with the keyboard simulator):

1. **Step modes** in the adventure JSON. `mode` on a step, default `ordered`:
   - `ordered` (existing): hit the named station next.
   - `collect`: `"stations": [1,2,3,4]`, any order, each hit adds an item to
     the rune wheel; the step completes when all are found.
   - `puzzle`: `"pattern": [3,1,4]`; the TV shows the pattern (Frost Queen
     waves her staff at three lands); a wrong station resets the pattern
     and replays it. Completes on the full pattern in order.
   - `charge`: `"station": 5, "hits": 5`; each hit at that station grows a
     charge ring on screen; completes at N hits. Any other station returns
     `wrong` (same rule as every mode, so stations behave consistently).
   - `boss`: `"station": 5, "hp": 8, "window_s": 90`; a leaf bar of `hp`
     leaves, one leaf per hit at the lair; hits elsewhere do nothing; if
     the window expires the dragon "breathes fire" and regrows 2 leaves
     (never resets to full, so a 6-year-old always wins eventually).
   `/hit` keeps returning `heal | wrong | done` to the stations; the TV page
   reads the richer `state` (`items`, `pattern_pos`, `charge`, `hp`).
2. **Campaign file** `hub/adventures/campaign.json`: ordered chapter list
   plus the realm-map scene. `GET /state` gains `chapter`, `chapters_done`.
   When a chapter ends, the hub shows the realm map for 20 s (or until any
   hit / key), then loads the next chapter. `POST /reset` resets the
   chapter; `POST /reset?campaign=1` wipes progress.
3. **Progress save** `hub/state/progress.json` (gitignored): chapters done,
   wand id. Written on chapter completion only.
4. **Realm map scene** `<template id="scene-map">`: five lands in a row,
   same palette family as the five scenes, `.land[data-chapter]` with
   `.done` / `.next` states.
5. **Mentor dialog** lines live in the chapter JSON (`opening`, `cheer`,
   `not_yet`, `ending` already exist; add `mentor` name + portrait id and
   optional `beats[]` keyed by step index). Browser speech via the Web
   Speech API behind a toggle (`?voice=1`), free and no hardware.
6. **Stations: result strings unchanged** (`heal | wrong | done`). The
   StickS3 firmware was amended 2026-10-27 so `done` no longer latches the
   station off (rainbow glows 60 s then rearms, chapters need station 5
   again) and input is only blocked 1.5 s after a hit (the 30 s glow is
   visual only) so charge and boss steps can take repeat waves. The CPX
   firmware is standalone (no hub) and is not part of the campaign path.

## 4. Content

Rewrite the five adventure JSONs into chapters with Liza's names and the
modes above. Keep the existing five scenes; add `scene-map` and the castle
intro (a static card, not a full scene). Add two character drawings
(Frost Queen, Good Witch) in the existing SVG style, placed in the mountain
and pools scenes.

Voice rules for all text: Liza's words where she gave them ("the fairies
are all sick", "something is poisoning the water", "who stole the
crystal", "the Good Witch comes out of the bubble"), short sentences,
one idea per bubble, read-aloud rhythm.

## 5. Printables (`cards/`)

- `cards/cutouts/station-1..5.svg`: the five object sleeves.
- `cards/chapters/NN-<slug>.md`: clue cards per chapter, generated by
  `python3 hub/cards.py <chapter.json>` from the JSON so cards and TV match.
- `cards/spellbook.md`: one page per chapter for Liza to sticker when done.
- `cards/items/`: the collect-mode item cards for chapter 2 (4 clue items),
  so there is something physical to find and hold.

## 6. Hardware path (gates, not tasks)

1. Wand test on the CPX (needs the micro-USB data cable) OR on the first
   M5StickS3 (arrives Thu 10/29). Green = buy 4 more StickS3.
2. Flash `firmware/m5sticks3/station.ino` x5, one `STATION` each.
3. Place stations, fit sleeves, verify IR line of sight through the window.
4. Family playtest: chapter 1 only, then the campaign.

## 7. Build order and what runs unattended

Everything in sections 3-5 runs with zero hardware (keyboard simulator +
`hub/test_server.py`), so it is the overnight job. Section 6 is Scott's.

| Step | Output | Check |
|---|---|---|
| A | step modes + tests | `python3 hub/test_server.py` green, one test per mode |
| B | campaign + progress + map scene | play chapters 1-5 end to end with keys, map shows between |
| C | five chapter JSONs rewritten | each plays through; text read aloud sounds like Liza's outline |
| D | Frost Queen + Good Witch art, castle intro card | visible in Chrome at 1920x1080 |
| E | cutout SVGs + cards generator + spellbook | SVGs open in Chrome; `cards.py` output matches JSON spot names |
| F | README + PLAN updated | next-session pickup reads clean |

## 8. Out of scope (parked)

Multiple wands / scoring, stations that speak, a story editor for Liza (the
JSON is the editor for now), phone companion app, physical runes with NFC.
