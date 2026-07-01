#!/usr/bin/env python3
"""Generate test/test.ch8 — a tiny public-domain CHIP-8 ROM (written for this
project) that scrolls a box sprite across the screen using the delay timer.
Exercises display, draw/XOR, timers, and main-loop pacing."""

import os

rom = bytes([
    0xA2, 0x20,   # 200: LD I, 0x220     ; sprite data
    0x60, 0x00,   # 202: LD V0, 0        ; x
    0x61, 0x0D,   # 204: LD V1, 13       ; y
    0xD0, 0x15,   # 206: DRW V0,V1,5     ; draw box
    0x62, 0x05,   # 208: LD V2, 5
    0xF2, 0x15,   # 20A: LD DT, V2       ; delay 5 ticks (~83 ms)
    0xF3, 0x07,   # 20C: LD V3, DT
    0x33, 0x00,   # 20E: SE V3, 0        ; wait for timer
    0x12, 0x0C,   # 210: JP 0x20C
    0xD0, 0x15,   # 212: DRW V0,V1,5     ; erase (XOR)
    0x70, 0x02,   # 214: ADD V0, 2       ; move right, wraps at 64
    0x12, 0x06,   # 216: JP 0x206
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,  # 218: pad
    0xF0, 0x90, 0x90, 0x90, 0xF0,                    # 220: box sprite
])

out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   '..', 'test', 'test.ch8')
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, 'wb') as f:
    f.write(rom)
print(f'wrote {os.path.normpath(out)} ({len(rom)} bytes)')
