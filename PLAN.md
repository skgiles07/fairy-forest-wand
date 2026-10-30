> **Superseded 2026-10-28:** Active game now uses three sensors and the Heartlight Quest story/format. See `README.md`, `docs/GAME-PLAN.md`, and `docs/story/heartlight-design.md`. Content below preserves prototype decisions; five-station quantities and timings are historical.

# Fairy Forest Wand: Plan & Decisions

Companion to `README.md` (how to set up and run). This file holds the why,
the decisions made, open items, and the next step, so work can pick up from
any machine.

## Goal

Rebuild the Great Wolf Lodge MagiQuest wand game at home with Liza's own
wand. Long term: an engine where she invents adventures and they become data
files. Short term: one story first.

**Story 1 (standalone stations): Fairy Forest Healing.** Five spots in order,
each station glows green and chimes; last station rainbow + fanfare.

**Campaign (TV hub): Liza's Magi Quest.** Five chapters from Liza's own
outline (`docs/story/liza-outline.md`), plan in `docs/GAME-PLAN.md` and
`PLAN-CAMPAIGN.md`, built 2026-10-27.

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
- **Sketch written** (2026-10-27): `firmware/m5sticks3/station.ino` +
  `magiquest.h` (C++ port of the Python decoder, host test
  `test_magiquest.cpp`). IR RX on G42 via ESP-IDF RMT (M5 docs: GPIO
  polling does not work on this board; IRremoteESP8266 not used). Speaker
  amp must be off while receiving, so sound is bracketed with
  `Speaker.begin()/end()`. EXT 5V output enabled for the receiver. POSTs
  `/hit` to the hub, falls back to local heal if the hub is unreachable.
  Button A = fake hit. Not yet compiled against real hardware.
- Buy 1 first, test the wand, then 4 more. Order from Amazon (M5Stack
  Official Store, $31.90, cart checked 2026-10-27).

## Status (2026-10-28)

- Done: CPX firmware, wand decoder + self-check, M5StickS3 station sketch
  (not yet compiled on hardware), TV hub, and **Liza's Magi Quest campaign**
  (built overnight 2026-10-27 per `PLAN-CAMPAIGN.md` + `wargames/01`):
  five step modes, campaign + realm map + saved progress, five chapters in
  Liza's story, Frost Queen + Good Witch + castle intro, printable sleeves,
  generated clue cards, spellbook, item cards. `hub/test_server.py` ok;
  `hub/verify.py` (headless-Chrome self-drive) `verify ok, skipped: []`.
- In hand: 1 Adafruit board (needs a micro-USB data cable), 1 M5StickS3
  (arrived 10/29, tested, see below).
- Not verified: StickS3 IR window position (sleeves carry a placeholder);
  48 x 24 x 14 mm sleeve size; Button A alone registering a hit at the hub
  (the hub saw a hit, but its `wand_id` was the wand's, not Button A's 0x0).

### M5StickS3 hardware test (2026-10-29)

- `station.ino` compiles clean for `m5stack:esp32:m5stack_sticks3`
  (arduino-cli, `m5stack:esp32` core 3.3.10, M5Unified 0.2.28; 1.26 MB,
  37% of flash).
- Wand IR works on the stick's receiver. The 36 kHz wand vs 38 kHz receiver
  worry is settled. Mark timings: zero ~245-275 us, one ~500-560 us (spec
  288 / 576), so the decoder thresholds in `magiquest.h` hold.
- Wand ID: `0xAF0E4902`. Seen as `0xAF0E0902` at the hub (one flipped bit),
  so exact-ID matching would need tolerance. The hub only stores `wand_id`
  (`server.py:189`), so play is not affected.
- Decode yield was low on casual waves with the strict decoder: about 1
  clean decode in 6 wand-sized frames. Failures are short or weak frames
  (42-55 pairs of 56, marks shrunk to ~140-200 us), the beam far or off-axis,
  not a timing fault. Hold the wand steady 2-6 in away, tip at the IR window,
  and pause on each flick.
- **Known-wand matcher (commit `ccda458`).** `magiquest::match_known()` in
  `magiquest.h`: per-frame mark threshold, lost pairs padded front or back,
  frame accepted only if the ID is within 6 bits of `KNOWN_WAND_ID`
  (`0xAF0E4902` in `station.ino`), and the clean ID is reported. Also stops
  the junk IDs (`0xA8084800`, `0x03000000`) that room IR produced under the
  strict path. `KNOWN_WAND_ID = 0` restores strict any-wand decode. Host
  test: `g++ -std=c++11 -o /tmp/mq firmware/m5sticks3/test_magiquest.cpp &&
  /tmp/mq`.
- Yield after the matcher: ~2 clean decodes per 10 frames, playable; the
  full 12-step wand practice was completed with the real wand on station 1
  (stations 2-3 simulated by POSTing `/hit` with `wand_id: "preview-sim"`).
- Miss signature, now fixed: after the 8-bit preamble, the first one-bit was
  followed by a ~1.8 ms space instead of ~0.6 ms, i.e. the next weak zero
  pulse was swallowed and one bit went missing mid-frame. `match_known()`
  now reinserts a zero for a 1.5-2.4 ms space and two for 2.4-3.4 ms
  (`LOST_ONE_US` / `LOST_TWO_US`); frame gap in known-wand mode is 3.4 ms
  (`KNOWN_GAP_US`). Replay of 38 captured frames: 29 decode (was 3).
- `WRONG_COOLDOWN_MS` 2000 -> 800: a retry right after a red flash was being
  ignored, and in a puzzle step the next wave at the wrong station resets
  the pattern.
- **Three-station playtest (2026-10-29 evening), all three M5StickS3 flashed
  as stations 1-3.** Chapter 1 (collect 1 2 3, pattern 1 2 3, ordered 2 3 1)
  completed with the real wand: 8 hits, 0 wrong, every wave first try, 5-40 s
  apart.
- Cross-talk: with the sticks side by side on a table one wave hit two
  stations in the same second. The wand beam is wide and bounces; placement
  in separate spots and the sleeve's small IR window are the fix, not
  firmware.
- IR window is on the top edge of the StickS3 (by the LED), not the screen
  face. A stick lying screen-up listens sideways; station 2 went "deaf" until
  it was aimed at. Sleeve cutouts must open on that edge.
- Hub server died once mid-play (TV showed "story keeper is disconnected");
  restart `python3 hub/server.py`, it reloads progress. Run it with output
  logged so a crash leaves a trace.
- Stick joins 2.4 GHz WiFi and POSTs `/hit` to the Mac hub (hub `rev`
  advanced). Hub listens on `*:8000`.
- Flashing gotchas (native USB, macOS):
  - `arduino-cli upload` fails: `termios.error: (6, 'Device not
    configured')`. The reset toggle makes the port disappear.
  - Put the stick in download mode (hold the side button next to the green
    LED about 3 s, screen goes black, LED flashes), then flash with esptool
    and no reset:
    `esptool --chip esp32s3 -p /dev/cu.usbmodem* -b 460800 --before no-reset
    --after hard-reset write-flash 0x0 <sketch>.ino.merged.bin`
    (get the merged bin from `arduino-cli compile --export-binaries`).
  - After flashing the stick stays in download mode: unplug and replug the
    cable, then press the side button once (reset). `esptool ... run` did
    not get it out.
  - Power off: the StickS3's side button is reset only (hold = download
    mode); the right-side button does nothing; there is no hardware
    power-off. Firmware: **hold Button A 3 s** -> "power off" ->
    `M5.Power.powerOff()` (verified on all three sticks). Side button once
    powers back on. Button A hits now fire on release of a short press so a
    power-off hold is not a hit.
  - Hub endpoints used for testing: `POST /training/start`,
    `/training/exit`, `/next {"gen": N}`, `/reset?campaign=1` (clears
    progress, back to the chapter 1 intro), `/hit {"station", "wand_id"}`.
  - arduino-cli needs the sketch folder named like the `.ino`; compile from a
    copy. macOS has no `timeout`; use `perl -e 'alarm N; exec @ARGV'`.
  - Serial prints only on events; a heartbeat line helps confirm the link.
- WiFi SSID, password, and `HUB_URL` (Mac LAN IP) are set in a scratch copy
  of the sketch, not in the repo. `station.ino` still has the placeholders.

### Chapters (TV hub, 2026-10-28)

All play on the same 5 physical stations (crystal cluster, magic mushroom,
treasure chest, lantern, fountain), relabelled per chapter on the TV.

| File | Scene | Mode / order |
|---|---|---|
| `01-fairy-pools.json` | forest | ordered 1 2 3 4 5 |
| `02-crystal-caves.json` | cave | collect {1 2 3 4} then 5 |
| `03-frozen-mountain.json` | mountain | 1 2, puzzle 3 1 4, 5 |
| `04-unicorn-forest.json` | pools | 2 4 1 3, charge 5 x5 |
| `05-fire-mountain.json` | forest + dragon | 4 1 3 2, boss 5 hp 8 / 90 s |

`hub/adventures/campaign.json` lists them; `python3 hub/server.py` loads
it. Progress in `hub/state/progress.json` (gitignored). Between chapters:
realm map, 20 s or any wave.

## Next steps

1. Get a micro-USB data cable. Plug the board in and check for a
   `CIRCUITPY` or `CPLAYBOOT` drive.
2. Run the wand test (README Step 1). Green flash = order 4 more. Blue flash =
   paste serial output for a decoder timing fix. Nothing = M5Stack fallback.
3. Three StickS3 stations flashed and chapter 1 played clean 10/29. Still to
   do: fix the IR window in `cards/cutouts/*.svg` (top edge, by the LED) and
   confirm the 48 x 24 x 14 mm sleeve. Play chapter 2 onward.
4. Read the five chapters aloud with Liza; confirm the RESOLVED-pending-
   confirmation choices in `wargames/LEDGER.md` (spot names, chapter 5's
   "dragon smoke made everything sick" tie-in, intro line).
5. Print `cards/chapters/*.md`, fill in hiding spots, print sleeves and
   item cards, family playtest chapter 1, then the campaign.

## Parked (not built)

- Breadboard ESP32 (Option B) station sketch; M5StickS3 sketch covers WiFi stations
- Multiple wands / scoring (wand IDs already logged)
- Stations that speak clues (MP3 module + SD card)
- Adventure generator / Liza-authored stories (format already exists:
  new JSON in `hub/adventures/` + a line in `campaign.json`)
- Multiple wands / scoring, stations that speak clues, phone companion
  app, NFC runes (GAME-PLAN section 8)
- Chapter 0 castle scene as a full scene (today: a static intro card)
