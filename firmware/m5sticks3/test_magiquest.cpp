// Host check for the C++ decoder, same vectors as firmware/test_magiquest.py:
//   g++ -std=c++11 -o /tmp/mq firmware/m5sticks3/test_magiquest.cpp && /tmp/mq
#include <cassert>
#include <cstdio>
#include <vector>
#include "magiquest.h"

using namespace magiquest;

static const Pair ZERO = {288, 864};
static const Pair ONE = {576, 576};

static std::vector<Pair> encode(uint32_t wand_id, uint16_t magnitude) {
    std::vector<Pair> out;
    for (int i = 0; i < 8; i++) out.push_back(ZERO);
    for (int i = 0; i < 32; i++) out.push_back(((wand_id >> (31 - i)) & 1) ? ONE : ZERO);
    for (int i = 0; i < 16; i++) out.push_back(((magnitude >> (15 - i)) & 1) ? ONE : ZERO);
    out.back().space = 5000;  // trailing gap
    return out;
}

int main() {
    Hit h;
    std::vector<Pair> f = encode(0xDEADBEEF, 0x1234);
    assert(decode(f.data(), f.size(), &h));
    assert(h.wand_id == 0xDEADBEEF && h.magnitude == 0x1234);

    // noise before the frame still decodes
    std::vector<Pair> noisy = {{300, 300}, {500, 600}};
    noisy.insert(noisy.end(), f.begin(), f.end());
    assert(decode(noisy.data(), noisy.size(), &h) && h.wand_id == 0xDEADBEEF);

    // short buffer is not a hit
    assert(!decode(f.data(), 20, &h));

    // one-bits in the 8-bit preamble reject the frame
    std::vector<Pair> bad;
    for (int i = 0; i < 56; i++) bad.push_back(i < 8 ? ONE : ZERO);
    assert(!decode_frame(bad.data(), bad.size(), &h));

    // two repeated frames in one buffer: first one wins
    std::vector<Pair> two = f;
    std::vector<Pair> g = encode(0x11111111, 1);
    two.insert(two.end(), g.begin(), g.end());
    assert(decode(two.data(), two.size(), &h) && h.wand_id == 0xDEADBEEF);

    // --- known-wand matcher (weak / short frames) ---
    const uint32_t WAND = 0xAF0E4902;
    std::vector<Pair> clean = encode(WAND, 0x01F4);
    assert(decode(clean.data(), clean.size(), &h, WAND) && h.wand_id == WAND && h.magnitude == 0x01F4);

    // weak signal: marks shrink, spaces grow, fixed 432us threshold would fail
    std::vector<Pair> weak = clean;
    for (auto& p : weak) { p.mark = p.mark < 400 ? 150 : 330; p.space = 1152 - p.mark; }
    weak.back().space = 5000;
    assert(!(decode(weak.data(), weak.size(), &h) && h.wand_id == WAND));  // strict path reads every mark as a zero
    assert(decode(weak.data(), weak.size(), &h, WAND) && h.wand_id == WAND);

    // last pair lost (55 pairs): back-padded
    std::vector<Pair> lost_tail(clean.begin(), clean.end() - 1);
    lost_tail.back().space = 5000;
    assert(decode(lost_tail.data(), lost_tail.size(), &h, WAND) && h.wand_id == WAND);

    // first 4 preamble pairs lost (52 pairs): front-padded
    std::vector<Pair> lost_head(clean.begin() + 4, clean.end());
    assert(decode(lost_head.data(), lost_head.size(), &h, WAND) && h.wand_id == WAND);

    // two flipped ID bits still match, and the hub gets the clean ID
    std::vector<Pair> flipped = clean;
    flipped[10] = (flipped[10].mark > 400) ? ZERO : ONE;
    flipped[25] = (flipped[25].mark > 400) ? ZERO : ONE;
    assert(decode(flipped.data(), flipped.size(), &h, WAND) && h.wand_id == WAND);

    // another wand, and noise, are rejected
    std::vector<Pair> other = encode(0x12345678, 7);
    assert(!decode(other.data(), other.size(), &h, WAND));
    assert(decode(other.data(), other.size(), &h) && h.wand_id == 0x12345678);
    std::vector<Pair> junk(60, Pair{300, 900});
    assert(!decode(junk.data(), junk.size(), &h, WAND));
    assert(!decode(clean.data(), 40, &h, WAND));               // too short to hold the ID

    puts("ok");
    return 0;
}
