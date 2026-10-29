# Heartlight Quest: active game format

Updated 2026-10-28. Supersedes the five-station format in the prototype plans. Reference review, complete story arc, chapter table, assumptions, and evidence timestamps are in [`story/heartlight-design.md`](story/heartlight-design.md). Setup is in [`../README.md`](../README.md).

One TV portal, one wand, **three fixed sensors**:

| ID | Landmark | Placement |
|---|---|---|
| 1 | Moon Crystal | Set household room in campaign configuration |
| 2 | Elder Tree | Set household room in campaign configuration |
| 3 | Treasure Chest | Set household room in campaign configuration |

The objects stay fixed across the story. Ingredient hunts and spell routes make Liza travel between them. Return-to-TV dialogue scenes separate gathering, forging, encounters, and revelation; sensor hits cannot skip them. No time pressure applies to household travel.

Five preserved lands: Fairy Pools → Crystal Caves → Frozen Mountain → Unicorn Forest → Fire Mountain. The missing Heart Crystal connects their trouble. Six spells carry forward: Glowmend, Truthlight, Frostbind, Wayweave, Starcall, Heartglow. The dragon’s frightened attempt to warm her egg explains the theft, and the Black Briar explains the shared corruption. The ending returns the crystal and heals the original sick-water problem.

The campaign uses 52 beats and chapter checkpoints in `progress-v2.json`. Maps wait for deliberate continuation. Three buttons or keys 1–3 let Scott inspect the same game without hardware. Active story source is `hub/adventures/*.json`; printables are generated from it. Old five-station assets are kept under `cards/legacy-five-station/` as historical reference.

Pending physical validation: sensor reception with Liza’s wand, actual receiver location, three chosen rooms, and a family playtest. Original scene art and browser voice are an adaptation of the reference’s presentation; full CGI character films are not part of this build.
