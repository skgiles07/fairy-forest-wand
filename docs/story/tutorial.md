# Great Wolf Lodge: The Wand Hall

A replayable training prologue for Liza and tomorrow’s three-sensor test, 2026-10-29. This is separate from the five-chapter story: `campaign.json` references `00-great-wolf-lodge.json` through `tutorial`, without inserting it into `chapters` or changing those chapter files.

## Story and teaching sequence

Liza arrives in a cozy Wand Hall inside Great Wolf Lodge. Luma gives her a wand. A first spark at the Moon Crystal lets Luma announce that the wand chose Liza. The Elder Tree and Treasure Chest then answer in turn. Three slow waves build a small practice version of Glowmend. Luma explains that the TV is the place to return for characters and lessons, while each landmark lives in its own room. A short ordered route teaches changing destinations; an any-order hunt teaches gathering. Luma welcomes Liza as a Wand Hall apprentice and sends her toward the Fairy Pools.

The lodge setting is the user’s requested personal story setting. All tutorial dialogue and artwork are original; the tutorial is not official Great Wolf Lodge content. No affiliation notice is placed in Liza’s story flow.

| Beat | Teaching moment | Input |
|---|---|---|
| 0 | Arrival and wand gift | Continue at TV |
| 1 | First gentle wave | Moon Crystal, sensor 1 |
| 2 | “The wand chose you” | Continue at TV |
| 3 | Learn second landmark | Elder Tree, sensor 2 |
| 4 | Learn third landmark | Treasure Chest, sensor 3 |
| 5 | Learn repeated, separate waves | Continue at TV |
| 6 | Build practice Glowmend | Sensor 1 three times, at least two seconds apart |
| 7 | Return to TV and carry clues between rooms | Continue at TV |
| 8 | Follow the next destination | 2 → 3 → 1 |
| 9 | Learn an any-order hunt | Continue at TV |
| 10 | Find Moon, Leaf, and Treasure Sparks | 1, 2, and 3 in any order |
| 11 | Apprentice graduation | Continue at TV |

There are 12 authored beats and 12 accepted sensor hits in a clean run: six at sensor 1 and three each at sensors 2 and 3. Allow roughly 5–8 minutes including walking and listening; this is a planning estimate, not a timed or measured requirement. Nothing counts down while Liza moves around the house.

Wrong destinations receive a gentle clue. Ordered steps and collected sparks keep their existing progress. The short puzzle restarts its three-step sequence on a wrong landmark, which its clue explains. A repeated visit to a collected landmark cannot award a second spark. Mentor dialogue requires returning to the TV and continuing deliberately; wand hits cannot skip it.

## Safe separation from the adventure

Training grants no campaign spell reward. `Practice Glowmend` is an instruction label on the charge exercise, not a permanent spellbook entry. Exiting training must restore the exact campaign state, including a partially completed chapter. Replaying training must not reset the adventure or overwrite its saved progress. Completion waits for an explicit exit or replay choice.

Engine routes are `/training/start` and `/training/exit`; the frontend supplies the parent controls. Training state uses `scene: "lodge"`, `chapter: -1`, and a `training_complete` flag when finished. Narration uses `tutorial:beat:0` through `tutorial:beat:11`, then `tutorial:ending`. These keys do not replace the main five chapters’ narration keys.

## Tomorrow’s check

Use [`../../cards/tutorial.md`](../../cards/tutorial.md) as the parent test sheet. Preview clicks prove only game transitions. Button A proves station-to-hub delivery. An actual wand wave proves the IR path. Keep those results separate, and identify which board reported each hit rather than relying only on its local light.

Set real room names before Liza plays. Use three accessible locations with clear walking paths, leave receivers uncovered, and stand more than 30 cm away when testing the wand. The firmware ignores input for 1.5 seconds after a hit, so the repeated-wave exercise explicitly waits two seconds between waves. Local offline lights are not proof that the hub received the hit.

## Verified build

Backend tests passed the complete lesson, all three sensor IDs, source classification, three separate charge hits, wrong destinations, stale requests, and exact restoration of campaign progress. Browser checks passed the complete tutorial and all five existing story chapters. A hash check also confirmed that launching practice on the family server left its existing story checkpoint unchanged. Physical sensors remain to be tested.

Original lodge artwork was generated with the built-in image tool. Asset: `hub/static/assets/lodge-hall.png`; prompt: `hub/static/assets/lodge-hall-prompt.txt`; provenance: `hub/static/assets/art-source.json`. Screenshot: `docs/screenshots/wand-hall-tutorial.jpg`.
