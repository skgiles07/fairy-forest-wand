"""Fairy Forest Healing: station firmware for Circuit Playground Express.

Set STATION below (1-5), copy this file + magiquest.py to CIRCUITPY, done.

  Idle        : slow purple breathing (dark energy)
  Wand hit    : green sparkle + rising chime, glow green HEALED_SECONDS, back to idle
  Station 5   : rainbow spin + fanfare instead
"""
import time
import random
import board
import pulseio
from adafruit_circuitplayground import cp
from magiquest import decode

STATION = 1            # <-- change per board, 1..5
FINAL_STATION = 5
HEALED_SECONDS = 30

ir = pulseio.PulseIn(board.IR_RX, maxlen=400, idle_state=True)
cp.pixels.brightness = 0.4
cp.pixels.auto_write = False
N = cp.pixels.n


def wheel(pos):
    pos = pos % 256
    if pos < 85:
        return (255 - pos * 3, pos * 3, 0)
    if pos < 170:
        pos -= 85
        return (0, 255 - pos * 3, pos * 3)
    pos -= 170
    return (pos * 3, 0, 255 - pos * 3)


def breathe(t):
    # purple, brightness follows a slow triangle wave
    phase = (t % 3.0) / 3.0
    level = phase * 2 if phase < 0.5 else (1 - phase) * 2
    v = int(10 + 60 * level)
    cp.pixels.fill((v, 0, v))
    cp.pixels.show()


def heal_sparkle():
    for i in range(40):
        for p in range(N):
            cp.pixels[p] = (0, random.randint(40, 255), random.randint(0, 60))
        cp.pixels.show()
        time.sleep(0.04)
    for f in (523, 659, 784, 1047):
        cp.play_tone(f, 0.12)
    cp.pixels.fill((0, 200, 20))
    cp.pixels.show()


def final_rainbow():
    for j in range(96):
        for p in range(N):
            cp.pixels[p] = wheel(p * 256 // N + j * 8)
        cp.pixels.show()
        time.sleep(0.03)
    for f in (523, 523, 523, 659, 784, 1047, 784, 1047):
        cp.play_tone(f, 0.15)
        time.sleep(0.03)
    for p in range(N):
        cp.pixels[p] = wheel(p * 256 // N)
    cp.pixels.show()


def wand_hit():
    if len(ir) == 0:
        return False
    time.sleep(0.15)
    ir.pause()
    pulses = list(ir)
    ir.clear()
    ir.resume()
    hit = decode(pulses)
    if hit:
        print("wand id=0x%08X" % hit[0])  # logged for v2 (multi-wand)
    return hit is not None


healed_until = 0
while True:
    now = time.monotonic()
    if now < healed_until:
        ir.clear()  # ignore re-swings while healed
        time.sleep(0.1)
        continue
    if wand_hit():
        if STATION == FINAL_STATION:
            final_rainbow()
        else:
            heal_sparkle()
        healed_until = time.monotonic() + HEALED_SECONDS
        continue
    breathe(now)
    time.sleep(0.03)
