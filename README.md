# Fairy Forest Wand

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

## Later (v2, not built)

Adventures as data files, WiFi hub enforcing station order, multiple wands
(IDs are already logged to serial), stations that speak clues.
