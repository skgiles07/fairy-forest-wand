"""STEP 1 SPIKE: does the Circuit Playground Express hear the wand?

Copy this file to the CIRCUITPY drive as code.py (alongside magiquest.py).
Open the serial console (Mu editor > Serial) and swing the wand at the board.

  Any IR pulses heard  -> blue flash + pulse count printed
  Full wand frame read -> green flash + wand ID printed  (SUCCESS, buy the rest)
  Nothing ever         -> receiver can't hear the 36 kHz wand; use the M5Stack fallback
"""
import time
import board
import pulseio
from adafruit_circuitplayground import cp
from magiquest import decode

ir = pulseio.PulseIn(board.IR_RX, maxlen=400, idle_state=True)
cp.pixels.brightness = 0.3
print("listening... swing the wand at the board")

while True:
    if len(ir) == 0:
        time.sleep(0.05)
        continue
    time.sleep(0.15)  # let the whole burst land
    ir.pause()
    pulses = list(ir)
    ir.clear()
    ir.resume()

    hit = decode(pulses)
    if hit:
        wand_id, mag = hit
        print("WAND  id=0x%08X  magnitude=%d" % (wand_id, mag))
        cp.pixels.fill((0, 255, 0))
        cp.play_tone(880, 0.2)
    else:
        print("ir pulses heard:", len(pulses), "(no full frame)")
        cp.pixels.fill((0, 0, 255))
    time.sleep(0.3)
    cp.pixels.fill(0)
