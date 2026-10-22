"""MagiQuest wand IR decoder. Pure Python, no board imports, so it runs on
the desktop test and on the Circuit Playground Express unchanged.

Protocol (per Arduino IRremote ir_MagiQuest): 36 kHz carrier, 56 bits.
Each bit = mark + space. Zero: 288us mark / 864us space.
One: 576us mark / 576us space. Layout: 8 zero bits, 32-bit wand ID,
16-bit magnitude (swing strength).
"""

ONE_MARK_MIN_US = 432   # halfway between zero mark (288) and one mark (576)
FRAME_GAP_US = 2000     # anything longer than a space is a gap between frames
FRAME_BITS = 56


def frames(pulses):
    """Split a flat [mark, space, mark, space, ...] list into frames
    (lists of (mark, space) pairs) using long gaps as separators."""
    out, cur = [], []
    for i in range(0, len(pulses) - 1, 2):
        mark, space = pulses[i], pulses[i + 1]
        cur.append((mark, space))
        if space > FRAME_GAP_US:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def decode_frame(pairs):
    """Return (wand_id, magnitude) or None if this isn't a full wand frame."""
    if len(pairs) < FRAME_BITS:
        return None
    # ponytail: take the last 56 bits; the wand repeats so partial leading
    # junk is common and the tail is the clean part.
    bits = [1 if mark > ONE_MARK_MIN_US else 0 for mark, _ in pairs[-FRAME_BITS:]]
    if any(bits[:8]):
        return None
    wand_id = 0
    for b in bits[8:40]:
        wand_id = (wand_id << 1) | b
    magnitude = 0
    for b in bits[40:56]:
        magnitude = (magnitude << 1) | b
    return wand_id, magnitude


def decode(pulses):
    """First decodable frame in a pulse buffer, or None."""
    for f in frames(pulses):
        hit = decode_frame(f)
        if hit:
            return hit
    return None
