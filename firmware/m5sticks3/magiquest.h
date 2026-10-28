// MagiQuest wand IR decoder, C++ port of firmware/magiquest.py.
// Header-only, no Arduino includes, so the same file compiles on the host
// for test_magiquest.cpp and inside the M5StickS3 sketch.
//
// Protocol (per Arduino IRremote ir_MagiQuest): 36 kHz carrier, 56 bits.
// Each bit = mark + space. Zero: 288us mark / 864us space.
// One: 576us mark / 576us space. Layout: 8 zero bits, 32-bit wand ID,
// 16-bit magnitude (swing strength).
#pragma once
#include <stdint.h>
#include <stddef.h>

namespace magiquest {

static const uint32_t ONE_MARK_MIN_US = 432;  // halfway between 288 and 576
static const uint32_t FRAME_GAP_US = 2000;    // longer than any space = frame gap
static const size_t FRAME_BITS = 56;

struct Pair { uint32_t mark, space; };
struct Hit { uint32_t wand_id; uint16_t magnitude; };

// Decode the LAST 56 pairs of one frame (pairs[0..n)). Returns false if the
// frame is short or the 8-bit preamble has a one-bit in it.
// ponytail: tail-only like the Python version; the wand repeats, so leading
// junk is common and the tail is the clean part.
inline bool decode_frame(const Pair* pairs, size_t n, Hit* out) {
    if (n < FRAME_BITS) return false;
    const Pair* p = pairs + (n - FRAME_BITS);
    uint64_t bits = 0;
    for (size_t i = 0; i < FRAME_BITS; i++)
        bits = (bits << 1) | (p[i].mark > ONE_MARK_MIN_US ? 1 : 0);
    if (bits >> 48) return false;  // preamble must be 8 zero bits
    out->wand_id = (uint32_t)(bits >> 16);
    out->magnitude = (uint16_t)(bits & 0xFFFF);
    return true;
}

// Split pairs into frames on long gaps and return the first that decodes.
inline bool decode(const Pair* pairs, size_t n, Hit* out) {
    size_t start = 0;
    for (size_t i = 0; i < n; i++) {
        bool last = (i + 1 == n);
        if (pairs[i].space > FRAME_GAP_US || last) {
            if (decode_frame(pairs + start, i + 1 - start, out)) return true;
            start = i + 1;
        }
    }
    return false;
}

}  // namespace magiquest
