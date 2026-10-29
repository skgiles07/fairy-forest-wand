# Liza’s Heartlight Quest

A five-chapter wand adventure played around the house, with one TV portal and **three sensors**. Liza meets mentors, hunts ingredients, learns six spells, solves physical routes, and restores the realm.

Current story and reference comparison: [`docs/story/heartlight-design.md`](docs/story/heartlight-design.md). Liza’s original outline is preserved in [`docs/story/liza-outline.md`](docs/story/liza-outline.md).

## Play now, without sensors

```sh
python3 hub/server.py
```

Open `http://localhost:8000/` on the Mac. For a TV browser or cast tab, use `http://<mac-ip>:8000/` on the same local network. Tap the game once to enable audio. Browser voice depends on the installed voices and browser support.

- **1, 2, 3:** simulate Moon Crystal, Elder Tree, Treasure Chest.
- **Continue / Enter:** advance a TV dialogue, start a chapter, or leave the realm map.
- **r:** restart the current chapter.
- Campaign restart is a parent action; it clears saved campaign progress.

Sensor hits do not skip mentor dialogue. Hunts accept any order; route puzzles show the order to follow. Chapter maps wait for you. There is no countdown for walking around the house.

## Three household landmarks

| Sensor | Fixed object | Room |
|---|---|---|
| 1 | Moon Crystal | Choose when placing hardware |
| 2 | Elder Tree | Choose when placing hardware |
| 3 | Treasure Chest | Choose when placing hardware |

Place the three signs in separate, accessible locations. Keep the TV as the place to return for characters and spell lessons. Objects stay in the same rooms across every chapter. Ingredients and fictional scenes change around them.

Open the gear button to save the three room names. The hub stores them in `hub/state/stations.json` and shares them with every screen. The default “Choose a room” leaves placement up to you. The campaign JSON provides initial defaults; saved settings take precedence.

## Chapter structure

1. **Fairy Pools:** collect three lights, learn Glowmend, heal the pools, discover a missing crystal.
2. **Crystal Caves:** follow clues, listen to Pip, learn Truthlight, discover where the crystal went.
3. **Frozen Mountain:** learn Frostbind, solve the queen’s four-note riddle, reveal the trapped unicorns.
4. **Unicorn Forest:** learn Wayweave and Starcall, restore paths, open the Good Witch’s bubble, clear the rockslide.
5. **Fire Mountain:** gather old signs, learn Heartglow, free the crystal, help Emberwing’s egg, restore all five lands.

The campaign contains 52 story/action beats and six persistent spells. Chapter progress, found ingredients, route position, and encounter progress save to `hub/state/progress-v2.json`; the five-station prototype’s `progress.json` remains separate. Changing story files invalidates the old story checkpoint rather than loading it into a different quest.

## Printables

```sh
python3 hub/cards.py hub/adventures/campaign.json --check
```

- `cards/cutouts/station-1.svg` through `station-3.svg`: three letter-size landmark signs. These are signs, **not measured hardware sleeves**; actual IR placement must be checked on the delivered board.
- `cards/chapters/*.md`: clue and dialogue cards generated from the same chapter JSON the TV reads.
- `cards/items/chapter-*-hunt-*.svg`: three ingredient cards per hunt. Put each beside its matching landmark.
- `cards/spellbook.md`: six-spell checklist and five chapter sticker spaces.
- `cards/legacy-five-station/`: retired assets preserved for reference; do not use for the active campaign.

## Hardware path

The networked TV path uses **three M5StickS3 stations**, each with the existing `firmware/m5sticks3/station.ino`. Actual wand reception is still unverified until hardware arrives. Test one board before assembling all three.

1. Configure `STATION` as 1, 2, or 3, local Wi-Fi credentials, and `HUB_URL` pointing to the Mac on port 8000.
2. Upload the sketch with the M5Stack board support and M5Unified library described in its source comments.
3. Start the Mac hub, then test Button A (simulated hit) and the actual wand at each station.
4. Keep the IR receiver uncovered and the wand more than 30 cm from it; closer placement can saturate reception.
5. Play chapter one around the house before a full campaign session.

The older Circuit Playground Express files under `firmware/` are a standalone IR test/prototype. They do not provide the networked TV campaign. A receiver lighting locally while the hub is offline does not advance the story.

## Development

```sh
python3 hub/test_server.py
python3 hub/cards.py hub/adventures/campaign.json --check
python3 firmware/test_magiquest.py
```

`hub/verify.py` provides browser walkthrough checks when its browser dependencies are available; it starts a separate temporary-state server so family progress is not touched.

The JSON defines the story. `dialogue` beats wait for Continue; `collect` finds all station ingredients; `ordered` visits one landmark; `puzzle` follows a landmark sequence; `boss` follows a repeated route to remove knots. Spell rewards belong to completed forge scenes. `/hit` keeps the station firmware response contract `heal | wrong | done`; `/state` supplies the richer TV state.

Original environment and character art lives in `hub/static/assets/`, alongside the generation prompts and provenance. These are illustrated scenes with web effects and optional browser speech; character animation and recorded voice acting are future work. Hardware reception still needs a real sensor test.
