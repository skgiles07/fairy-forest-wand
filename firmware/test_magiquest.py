"""Desktop check for the decoder: python3 firmware/test_magiquest.py"""
from magiquest import decode, decode_frame

ZERO = (288, 864)
ONE = (576, 576)


def encode(wand_id, magnitude):
    bits = [0] * 8
    bits += [(wand_id >> (31 - i)) & 1 for i in range(32)]
    bits += [(magnitude >> (15 - i)) & 1 for i in range(16)]
    pairs = [ONE if b else ZERO for b in bits]
    pairs[-1] = (pairs[-1][0], 5000)  # trailing gap
    return [v for p in pairs for v in p]


if __name__ == "__main__":
    pulses = encode(0xDEADBEEF, 0x1234)
    assert decode(pulses) == (0xDEADBEEF, 0x1234)
    # noise before the frame still decodes
    assert decode([300, 300, 500, 600] + pulses) == (0xDEADBEEF, 0x1234)
    # short buffer is not a hit
    assert decode(pulses[:40]) is None
    # one-bits in the 8-bit preamble reject the frame
    bad = [ONE if i < 8 else ZERO for i in range(56)]
    assert decode_frame(bad) is None
    print("ok")
