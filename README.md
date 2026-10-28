# Fairy Forest Wand

Decisions, status, and next steps: see `PLAN.md`.

Home MagiQuest-style scavenger hunt. Liza's Great Wolf Lodge wand, five
wand stations hidden in paper objects, a TV hub, and one five-chapter
story: Liza's Magi Quest (fairy pools, crystal caves, frozen mountain,
unicorn forest, fire mountain).

No soldering, no wiring. Each station is one board in a jar.

## Parts (5 stations)

| Qty | Part | Where | ~Price |
|---|---|---|---|
| 5 | Adafruit Circuit Playground Express (product 3333) | adafruit.com, Amazon, eBay used ($12-15) | $25 |
| 5 | Small USB power bank | Amazon | $8 |
| 5 | Micro-USB cable (data, not charge-only, for the first flash) | Amazon | $3 |
| 5 | Jar / box to hide the board in, decorated | house | $0 |

**Buy ONE board first.** Run the wand test (below) before buying the rest.
Risk: the wand sends IR at 36 kHz, the board's receiver is tuned to 38 kHz.
Usually fine, not guaranteed.

Fallback if the test fails: M5Stack Core + Grove IR receiver unit (plug-in
cable, still no soldering). Firmware would need a port; ask before buying.

## One-time setup (per board, ~5 min)

1. Install [Mu editor](https://codewith.mu) (gives you a serial console).
2. Plug the board in. A drive named `CIRCUITPY` appears. If instead you see
   `CPLAYBOOT`, download the latest CircuitPython `.uf2` for Circuit
   Playground Express from circuitpython.org/board/circuitplayground_express
   and drag it onto `CPLAYBOOT`; it reboots as `CIRCUITPY`.
3. Download the CircuitPython library bundle (circuitpython.org/libraries,
   match the major version on the board). Copy these from the bundle into
   `CIRCUITPY/lib/`: `adafruit_circuitplayground/`, `neopixel.mpy`,
   `adafruit_lis3dh.mpy`, `adafruit_thermistor.mpy`.
4. Copy `firmware/magiquest.py` to the root of `CIRCUITPY`.

## Step 1: wand test (the spike)

Copy `firmware/test_wand.py` to `CIRCUITPY/code.py`. Open Mu > Serial.
Swing the wand at the board from a few feet away.

- Green flash + `WAND id=0x........` printed: success. Buy the other four.
- Blue flash + `ir pulses heard: N (no full frame)`: receiver hears it,
  decoder timing is off. Paste the serial output back here, easy fix.
- Nothing: receiver can't hear the wand. Fallback board.

## Step 2: stations

Edit `STATION = 1` at the top of `firmware/code.py` (1 to 5), copy it to
`CIRCUITPY/code.py` on that board. Repeat per board. Station 5 plays the
rainbow finale.

Behavior: purple breathing while idle; wand hit = green sparkle + chime,
stays green 30 s, resets itself. Game replays with no button presses.

## Step 3: clue cards and sleeves

Generated from the same JSON the TV reads, so cards and screen never
disagree:

```
python3 hub/cards.py hub/adventures/campaign.json --check   # writes cards/chapters/*.md, exit 0 = cards match the JSON
```

- `cards/chapters/NN-<land>.md`: one file per chapter: opening, one card
  per step (collect / puzzle steps list all their stations), ending. Each
  card names the physical object (crystal cluster, magic mushroom, treasure
  chest, lantern, fountain) and the chapter's spot name. Fill in the hiding
  spot line with Liza, print, cut.
- `cards/cutouts/station-1..5.svg`: letter-size face panel + 1:1 fold-around
  sleeve for the M5StickS3 (48 x 24 x 14 mm placeholder, screen and IR
  windows marked; move the IR window once the unit arrives).
- `cards/items/*.svg`: the four Crystal Caves clue items (3 x 4 in).
- `cards/spellbook.md`: five sticker pages, one per healed land.

## Dev check

`python3 firmware/test_magiquest.py` prints `ok` if the decoder is sane.
C++ port (used by the M5StickS3 sketch):
`g++ -std=c++11 -o /tmp/mq firmware/m5sticks3/test_magiquest.cpp && /tmp/mq`.

## WiFi stations (M5StickS3, for the TV hub)

`firmware/m5sticks3/station.ino`. One board per station, nothing to wire.

1. Arduino IDE: add `https://static-cdn.m5stack.com/resource/arduino/package_m5stack_index.json`
   to Board Manager URLs, install **M5Stack** boards (>= 3.2.5) and the
   **M5Unified** library (>= 0.2.12). Board: `M5Stack > M5StickS3`.
2. Edit the config block at the top of `station.ino`: `STATION` (1-5),
   `WIFI_SSID`, `WIFI_PASS`, `HUB_URL` (the Mac's IP, port 8000).
3. Plug in over USB-C, Upload. Repeat per board, changing only `STATION`.
4. Run the hub (`python3 hub/server.py ...`). Screen breathes purple and
   says `waiting` once WiFi is up (`no wifi` otherwise).
5. Button A fakes a wand hit for testing without the wand.

Hub offline: a hit heals locally (rainbow on station 5), so the printed-card
game still works. Serial Monitor at 115200 shows wand IDs; if it prints
`undecoded frame` with pulse pairs, paste that for a decoder timing fix.
Keep the wand > 30 cm from the board; too close and the receiver saturates.

## TV hub (web app): Liza's Magi Quest

```
python3 hub/server.py                      # loads hub/adventures/campaign.json on port 8000
python3 hub/server.py --port 8080          # other port
python3 hub/server.py hub/adventures/03-frozen-mountain.json   # one chapter on its own
```

Then on the TV: Fire Stick / Chromecast browser (or cast a tab) to
`http://<mac-ip>:8000/` (Mac IP: System Settings > Wi-Fi > Details).
Tap once to turn sound on. Add `?voice=1` for spoken clues (Web Speech).

One campaign, five chapters, one realm map between them, progress saved in
`hub/state/progress.json` (gitignored; a chapter per evening works). Castle
intro card: any wave starts chapter 1. After a chapter the map shows for
20 s (or until a wave / `N`), then the next chapter loads. Finish all five
and the realm is healed.

| # | Chapter | Scene | Steps |
|---|---|---|---|
| 1 | The Fairy Pools | forest | ordered 1 2 3 4 5 |
| 2 | The Crystal Caves | cave | **collect** clues at 1 2 3 4 (any order), then goblin at 5 |
| 3 | The Frozen Mountain | mountain | ordered 1 2, **puzzle** 3 1 4 (Frost Queen's riddle), ordered 5 |
| 4 | The Unicorn Forest | pools | ordered 2 4 1 3, **charge** 5 waves at the Big Bubble (Good Witch) |
| 5 | Fire Mountain | forest + dragon | ordered 4 1 3 2, **boss** dragon at 5, 8 leaves, 90 s window |

Step modes (`"mode"` on a step in the chapter JSON):

| mode | fields | plays |
|---|---|---|
| `ordered` (default) | `station` | wave at that station next |
| `collect` | `stations: [..]`, `spots: {station: name}` | all of them, any order; rune wheel fills |
| `puzzle` | `pattern: [..]`, `spots` | the pattern in order; a wrong wave starts it over |
| `charge` | `station`, `hits` | N waves at one station; charge ring |
| `boss` | `station`, `hp`, `window_s` | one leaf per wave; no wave for `window_s` = fire, +2 leaves (never full, can't be lost) |

Keys: `1`-`5` fake station hits, `r` restarts the chapter, `N` / Enter
leaves the map early, `R` (shift) wipes progress and returns to the castle.

Stations only ever see three answers to `POST /hit {"station": N,
"wand_id": ".."}`: `heal`, `wrong`, `done`. Everything richer (mode,
targets, items, pattern, charge, leaves, map countdown, saved-progress
errors) is in `GET /state`. Other endpoints: `POST /reset`,
`POST /reset?campaign=1`, `POST /next {"gen": n}`, `GET /campaign`,
`POST /log`. `--state-dir <dir>` (or `HUB_STATE_DIR`) moves the progress
file; `--debug` adds `POST /debug/expire` for tests.

Scene art lives in `<template id="scene-...">` blocks in
`hub/static/index.html`; a chapter picks one with `"scene"`. New story =
new JSON in `hub/adventures/` listed in `campaign.json`.

Dev checks (no hardware, no server of your own):

```
python3 hub/test_server.py     # engine: every mode, campaign transitions, progress, each chapter winnable -> ok
python3 hub/verify.py          # self-driving browser walkthrough in headless Chrome -> verify ok, skipped: []
python3 hub/verify.py --shot docs/screenshots/map.png --stop-at map     # visual canary (map | puzzle | charge_done)
```

`verify.py` starts its own server on a free port with a temp state dir, so
family progress is never touched.

## Later (not built)

Breadboard ESP32 station sketch (M5StickS3 sketch exists instead), multiple
wands (IDs already logged), stations that speak clues.
