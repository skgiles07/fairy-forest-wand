# Fairy Forest Wand

Decisions, status, and next steps: see `PLAN.md`.

Home MagiQuest-style scavenger hunt. Liza's Great Wolf Lodge wand, five
light-and-sound stations, one story: the fairies healing the forest.

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

## Step 3: clue cards

`cards/clues.md`. Fill in hiding spots with Liza, print, cut.

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

## TV hub (web app)

```
python3 hub/server.py
```

Then on the TV: Fire Stick / Chromecast browser (or cast a tab) to
`http://<mac-ip>:8000/` (Mac IP: System Settings > Wi-Fi > Details).
Tap once to turn sound on. Forest map lights up zone by zone, fairy reads
the clue, rainbow finale. Hub enforces station order; wrong station shakes
the map and says "not yet."

Test tonight with no hardware: keys `1`-`5` fire fake station hits, `R`
resets.

Levels: `fairy-forest.json` (default), `dragon.json` (chase the dragon off the
throne), `mountain.json` (thaw the Frozen Mountain, own scene):
`python3 hub/server.py hub/adventures/mountain.json`, `goblin.json` (chase the
goblin through the Crystal Cave, sequel to the mountain), `unicorns.json`
(break the evil magic and free the unicorns from their bubbles). Scene art lives in
`<template id="scene-...">` blocks in `hub/static/index.html`; an adventure picks
one with `"scene"`.

New story = new JSON in `hub/adventures/` (title, opening, 5 steps with
station/spot/clue, ending). Run `python3 hub/server.py hub/adventures/x.json`.

Stations report hits with `POST /hit {"station": N, "wand_id": "..."}`.
Hub needs WiFi stations, so this path = ESP32 build, not CPX.

Dev check: `python3 hub/test_server.py`.

## Later (not built)

Breadboard ESP32 station sketch (M5StickS3 sketch exists instead), multiple
wands (IDs already logged), stations that speak clues.
