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

// Known-wand matcher for weak signals. Far or off-axis waves shrink the marks
// (zeros ~140-200us instead of 288) and drop pairs, so frames arrive 48-55
// pairs long and the fixed 432us threshold misreads ones. Here the threshold
// is the midpoint of this frame's own short and long marks, missing pairs are
// assumed lost at the front (preamble) or the back (magnitude), and the frame
// counts only if the ID is within MAX_ID_DIST bits of known_id. A match
// reports known_id itself, so one flipped bit never leaks to the hub.
// ponytail: one wand ID; keep a list if a second wand joins the game.
static const size_t MIN_MATCH_PAIRS = 48;   // ID field must be fully present
static const size_t MAX_MATCH_PAIRS = 128;  // RX_SYMBOLS in station.ino
static const int MAX_ID_DIST = 6;           // 6 of 32 bits: ~3e-4 chance on random noise

inline bool match_known(const Pair* pairs, size_t n, uint32_t known_id, Hit* out) {
    if (n < MIN_MATCH_PAIRS || n > MAX_MATCH_PAIRS) return false;
    uint32_t sorted[MAX_MATCH_PAIRS];
    for (size_t i = 0; i < n; i++) sorted[i] = pairs[i].mark;
    for (size_t i = 1; i < n; i++) {  // insertion sort, n <= 128
        uint32_t v = sorted[i];
        size_t j = i;
        while (j > 0 && sorted[j - 1] > v) { sorted[j] = sorted[j - 1]; j--; }
        sorted[j] = v;
    }
    uint32_t lo = sorted[n / 8], hi = sorted[n - 1 - n / 8];
    uint32_t thr = (hi - lo > 120) ? (lo + hi) / 2 : ONE_MARK_MIN_US;

    uint8_t b[MAX_MATCH_PAIRS];
    for (size_t i = 0; i < n; i++) b[i] = pairs[i].mark > thr ? 1 : 0;

    // candidate 56-bit words: [0] front-padded or tail of b, [1] back-padded or head of b
    uint64_t cand[2] = {0, 0};
    for (int k = 0; k < FRAME_BITS; k++) {
        int front = (int)k - (int)(FRAME_BITS - (n < FRAME_BITS ? n : FRAME_BITS));
        int src0 = n >= FRAME_BITS ? (int)(n - FRAME_BITS) + k : front;  // pad zeros at front
        int src1 = k;                                                    // pad zeros at back
        cand[0] = (cand[0] << 1) | (src0 >= 0 && src0 < (int)n ? b[src0] : 0);
        cand[1] = (cand[1] << 1) | (src1 < (int)n ? b[src1] : 0);
    }
    int best = MAX_ID_DIST + 1;
    for (int c = 0; c < 2; c++) {
        int d = __builtin_popcount((uint32_t)(cand[c] >> 16) ^ known_id);
        if (d < best) { best = d; out->magnitude = (uint16_t)(cand[c] & 0xFFFF); }
    }
    if (best > MAX_ID_DIST) return false;
    out->wand_id = known_id;
    return true;
}

// Split pairs into frames on long gaps and return the first that decodes.
// known_id == 0: strict decode of full 56-pair frames (any wand).
// known_id != 0: only that wand, tolerant of weak and short frames.
inline bool decode(const Pair* pairs, size_t n, Hit* out, uint32_t known_id = 0) {
    size_t start = 0;
    for (size_t i = 0; i < n; i++) {
        bool last = (i + 1 == n);
        if (pairs[i].space > FRAME_GAP_US || last) {
            bool ok = known_id ? match_known(pairs + start, i + 1 - start, known_id, out)
                               : decode_frame(pairs + start, i + 1 - start, out);
            if (ok) return true;
            start = i + 1;
        }
    }
    return false;
}

}  // namespace magiquest
