# Liza’s Heartlight Quest

A five-chapter wand adventure played around the house, with one TV portal and **three sensors**. Liza meets mentors, hunts ingredients, learns six spells, solves physical routes, and restores the realm.

Current story and reference comparison: [`docs/story/heartlight-design.md`](docs/story/heartlight-design.md). Liza’s original outline is preserved in [`docs/story/liza-outline.md`](docs/story/liza-outline.md).

## Play now, without sensors

```sh
python3 hub/server.py
```

Open `http://localhost:8000/` on the Mac. For a TV browser or cast tab, use `http://<mac-ip>:8000/` on the same local network. Voice defaults on. Click **Tap to hear story**, **Begin**, or a game control to permit audio playback. Voice off remembers an explicit mute choice. Narration uses bundled MP3s, so playback does not need an installed browser speech voice or an external service.

- **1, 2, 3:** simulate Moon Crystal, Elder Tree, Treasure Chest.
- **Continue / Enter:** advance a TV dialogue, start a chapter, or leave the realm map.
- **r:** restart the current chapter.
- Campaign restart is a parent action; it clears saved campaign progress.

Sensor hits do not skip mentor dialogue. Hunts accept any order; route puzzles show the order to follow. Chapter maps wait for you. There is no countdown for walking around the house.

## Wand Hall tutorial and sensor practice

Choose **Wand practice** in the top bar, **Visit the Wand Hall first** before a new adventure, or the Wand Hall entry in parent settings. Liza receives her wand at Great Wolf Lodge, tries each of the three landmarks, practices three separate waves, follows a short route, and graduates from an any-order hunt. The twelve-beat lesson can be replayed independently of the five story chapters.

For physical testing, switch **Preview mode** to **Wand mode**. The three signal runes show received messages; **Wand signals** opens parent diagnostics with separate preview, station-button, and reported-wand counts plus the last message time. A button or preview click is not proof that the infrared receiver works. Use the actual wand to check all three station IDs and repeat waves about two seconds apart.

**Practice again** clears only the lesson and its signal counters. **Return to your adventure** restores the exact suspended story position. The lesson never rewrites the story checkpoint and is not inserted into the saved chapter sequence. Restarting the server resumes the main adventure; use Wand practice to start a fresh test.

Print the [sensor test sheet](cards/tutorial.md). Story notes: [tutorial structure](docs/story/tutorial.md). The original lodge illustration and its generation prompt live in `hub/static/assets/lodge-hall.png` and `lodge-hall-prompt.txt`.

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
python3 hub/build_narration.py --check
node hub/test_narration.js
node hub/test_motion.cjs
```

`hub/verify.py` provides browser walkthrough checks when its browser dependencies are available; it starts a separate temporary-state server so family progress is not touched.

`python3 hub/verify.py --training` checks the complete Wand Hall lesson and exact return to the suspended adventure. `python3 hub/test_server.py --http` also checks sensor-source diagnostics and the training HTTP routes with temporary state.

The JSON defines the story. `dialogue` beats wait for Continue; `collect` finds all station ingredients; `ordered` visits one landmark; `puzzle` follows a landmark sequence; `boss` follows a repeated route to remove knots. Spell rewards belong to completed forge scenes. `/hit` keeps the station firmware response contract `heal | wrong | done`; `/state` supplies the richer TV state.

## Voice and animated assets

`hub/build_narration.py` creates offline narration with the installed macOS Samantha voice and ffmpeg. The 59 story passages share 58 content-hashed MP3s under `hub/static/audio/`. Rerun the builder after changing dialogue; `--check` detects stale passages. The game cancels old audio on story changes, supports replay and mute, and shows a tap action if browser autoplay is blocked.

Three original Blender models animate live inside the rune wheel and during landmark actions: floating Moon Crystal, swaying Elder Tree, and opening Treasure Chest. `landmarks3d.js` plays their four-second GLB animations with locally bundled model-viewer 4.4.0. The parent **Motion** setting pauses motion; reduced-motion preferences apply by default. All runtime files are local.

Editable source, builder, and preview: `assets/blender/`. These assets were created through the local [MCP for Blender](https://github.com/ahujasid/mcp-for-blender) connection, using Blender 5.2.3 and pinned MCP package 2.2.6. See `assets/blender/README.md` for reproducible authoring and export details. Blender MCP is configured for Codex; its native tools appear after restarting Codex. The verified SDK bridge can author assets in the current session.

Original environment and character illustrations remain in `hub/static/assets/`, alongside prompts and provenance. The landmark models are real animated 3D meshes; mentor portraits are still illustrations. Rigged character bodies, face animation, and lip-sync are not included yet. Optional rendered-video support is ready, but the initial external fairy-video generation failed and no clip is shipped. Hardware reception still needs a real sensor test.

### Luma character

The illustrated Luma remains active, with OpenAI narration. An experimental procedural 3D character was rejected during visual review and is not loaded by the game. Its source remains available locally for reference; a replacement needs a finished character asset matching the existing artwork.

Luma’s illustrated art flies into view on page load and when entering a new Luma chapter or tutorial, then gently hovers. Sensor hits and subsequent dialogue lines do not replay the entrance. Parent Motion-off and reduced-motion preferences disable the effect. No additional model downloads or external generation are needed.
