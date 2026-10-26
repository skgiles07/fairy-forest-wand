# Fairy Forest Wand: Plan & Decisions

Companion to `README.md` (how to set up and run). This file holds the why,
the decisions made, open items, and the next step, so work can pick up from
any machine.

## Goal

Rebuild the Great Wolf Lodge MagiQuest wand game at home with Liza's own
wand. Long term: an engine where she invents adventures and they become data
files. Short term: one story first.

**Story 1: Fairy Forest Healing.** Dark energy has drained the forest. Liza's
wand carries fairy light. She visits 5 forest spots in order and waves the
wand. Each station glows green and chimes (that patch is healed). Last station:
rainbow + fanfare, forest healed.

## Key facts

- The wand needs no reverse engineering. MagiQuest wands send a 56-bit IR
  packet (wand ID + magnitude) when swung. Arduino's IRremote library already
  decodes it, and `firmware/magiquest.py` is our CircuitPython decoder.
- Wand IR carrier is ~36 kHz. Most receivers (CPX built-in, VS1838B) are
  tuned to 38 kHz. That usually works but isn't guaranteed. **The wand test
  gates every other purchase.**

## Decisions (in order made)

1. **Engine later, one story now.** Adventures will be data, not code.
2. **Stations = lights + sounds only.** No screens, no speech on stations (v1).
3. **Clues on printed cards** (`cards/clues.md`) for the no-hub version.
4. **5 stations.**
5. **Hardware v1 = Adafruit Circuit Playground Express (CPX)**, product 3333,
   ~$25 (or ~$12-15 used on eBay). Built-in IR receiver, 10 LEDs, speaker,
   drag-and-drop programming. Picked because Scott has never built a board and
   has no equipment. No soldering, no breadboard.
6. **Buy ONE board first**, run the wand test, then buy 4 more.
7. **TV hub built** (`hub/`): stdlib Python server on the Mac + SVG forest map
   page on the TV. Story lives in `hub/adventures/fairy-forest.json`. Hub
   enforces station order. Wrong station = map shakes, "not yet." Keys 1-5
   simulate hits; R resets.
8. **Hub implies WiFi stations.** CPX has no WiFi, so if the TV hub is part of
   the real game, the stations must be ESP32 (below). CPX stations work
   standalone with the printed cards.

## Station behavior (CPX firmware, built)

- Idle: slow purple "dark energy" breathing.
- Wand hit: green sparkle + rising chime, stays green 30 s, then resets.
- Station 5: rainbow spin + fanfare.
- Any wand ID accepted (one player). ID is logged so later versions can
  tell wands apart.

## Option B: $8-10 ESP32 station (not built, needed for the TV hub)

Parts per station (Amazon multi-packs):

| Qty | Part | Notes |
|---|---|---|
| 1 | ESP32 DevKit, **30-pin**, headers pre-soldered | 3-pack ~$15. 38-pin won't leave room on the breadboard |
| 1 | KY-022 IR receiver module (VS1838B) | 5-pack ~$6 |
| 1 | WS2812B 8-LED stick **with header pins pre-soldered** | 5-pack ~$10. Bare sticks need soldering |
| 1 | KY-006 passive buzzer module | 5-pack ~$6 |
| 1 | Half-size breadboard | 6-pack ~$8 |
| ~8 | Female-to-male jumper wires | one 40-pack covers all 5 |
| 1 | USB power bank + micro-USB data cable | |

Wiring (no tools, ~10 min):

1. ESP32 straddles the breadboard center channel. Press firmly.
2. IR receiver: `S` to **GPIO15**, middle to **3V3**, `-` to **GND**.
3. LED stick: `DIN` to **GPIO13**, `VCC`/`5V` to **VIN**, `GND` to **GND**.
4. Buzzer: `S` to **GPIO12**, `-` to **GND**.
5. Power bank into ESP32 micro-USB.

Firmware: Arduino IDE + ESP32 board package + IRremote + Adafruit NeoPixel.
Same purple / green / rainbow behavior, plus `POST /hit {"station": N,
"wand_id": "..."}` to the hub. **Sketch not written yet**; write it once parts
are ordered. Gotchas: ~30% of boards need the CP2102 USB driver, and some
need `BOOT` held during upload.

## Option C: pre-built M5StickS3 station (recommended for WiFi stations)

One part per station, nothing to wire. ~$29 each (RobotShop $28.90 US),
~$145 for 5 + chargers. Replaces the discontinued M5StickC Plus2.

- ESP32-S3, WiFi + BLE, 1.14" color screen, speaker, mic, USB-C.
- **IR transmitter + receiver built in** (pins G46/G42, TX vs RX to confirm).
  Receiver part/frequency unpublished, so same 36 vs 38 kHz risk.
- 250 mAh battery = minutes, not hours. Run each on a USB-C phone charger or
  power bank.
- Screen is the light: purple idle, green healed, rainbow finale, can show
  text.
- Arduino with M5Unified + M5PM1 libraries; IR receive via ESP32 RMT
  (IRremoteESP8266 decodes MagiQuest). Same sketch logic as Option B.
- Buy 1 first, test the wand, then 4 more.

## Status (2026-10-26)

- Done: CPX firmware, wand test, decoder + self-check, clue cards, TV hub
  (verified end to end in browser with keyboard simulator). Repo on GitHub
  `skgiles07/fairy-forest-wand`.
- In hand: 1 Adafruit board. Needs a **micro-USB data cable** (USB-C end for
  the Mac) to plug in.
- Not verified: decoder timing against the real wand; 38 kHz receiver hearing
  the 36 kHz wand.

## Next steps

1. Get a micro-USB data cable. Plug the board in and check for a
   `CIRCUITPY` or `CPLAYBOOT` drive.
2. Run the wand test (README Step 1). Green flash = order 4 more. Blue flash =
   paste serial output for a decoder timing fix. Nothing = M5Stack fallback.
3. Decide: CPX standalone stations + printed cards, or ESP32 stations + TV hub.
4. Fill in hiding spots in `cards/clues.md` with Liza.

## Parked (not built)

- ESP32 WiFi station sketch
- Multiple wands / scoring (wand IDs already logged)
- Stations that speak clues (MP3 module + SD card)
- Prettier hub art (current art is flat SVG)
- Adventure generator / Liza-authored stories (format already exists:
  new JSON in `hub/adventures/`)
