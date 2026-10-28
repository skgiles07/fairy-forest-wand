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

    puts("ok");
    return 0;
}
