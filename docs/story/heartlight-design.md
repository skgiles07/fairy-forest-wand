# Liza’s Heartlight Quest — reference, story, and play structure

Rewritten 2026-10-28 for three physical sensors. This document describes the authored game; timings below refer to the reference video, not promised play duration.

Reference: [MagiQuest Plus full walkthrough, Grand Mound](https://www.youtube.com/watch?v=4K4CFEDP2D4), 41:43. The review used its full exported transcript and sampled gameplay frames. It did not inspect every frame in real time. Automatic captions can misname characters; the design relies on the observed structure rather than treating every transcribed word as exact.

## What the reference does

| Reference time | Evidence from transcript / sampled footage | Design consequence for our game |
|---|---|---|
| 1:51–3:30 | A caretaker introduces a connected realm, gives the problem personal stakes, recognizes the player’s wand, then sends the player to a named guide. | Liza enters through the castle and meets Luma. Sick fairies make the missing light matter immediately. |
| 3:30–5:11 | A distinctive mentor introduces runes, sends the player for ingredients, and forges a power after the hunt. At 4:10, sampled footage shows a wand used at a physical wall sensor. | Three fixed household landmarks hold changing ingredients. Each hunt ends with a deliberate return to the TV to learn a named spell. |
| 5:11–9:48 | Learned powers solve a multi-stage encounter; repairing the landmark follows combat. At 8:20, sampled footage shows crystalline blossoms and a leaf vitality display. | Encounters use an earned power and several destinations. Success visibly restores the chapter’s world, with gentle progress rather than a travel countdown. |
| 9:48–10:26; 21:22–22:15 | The player returns to the central caretaker. Restored landmarks change the world and reveal the next threat. | Each chapter ends on a realm map that waits. Progress becomes a story milestone rather than an automatic 20-second slideshow. |
| 10:26–16:49 | Multiple mentors provide different rune recipes before a dragon encounter. At 12:35, sampled footage shows a large character against a lush forest; 25:01 shows a luminous floating rune handoff. | Distinct mentors, large scene artwork, clear dialogue, and a spell-forging moment take priority over prototype UI. Powers persist in Liza’s spellbook. |
| 17:31–21:22; 27:29–32:04 | A dragon and a goblin have distinct encounters. Restoration continues after the enemy is stopped. At 29:12, sampled footage shows a goblin arena and leaf vitality. | The cave chapter centers on listening and evidence; the mountain finale centers on freeing the crystal. A boss is an objective with stages, not repeated hits on one stationary sensor. |
| 32:16–35:58 | Revisiting earlier places uncovers hidden signs, a new tracking rune, and the common cause behind previous trouble. At 33:22, sampled footage includes an in-world parchment clue/rhyme. | Earlier clues return in chapter five. The three landmarks contain the Pool, Forest, and Cave marks; together they explain the Heart Crystal and Black Briar. |
| 35:58–41:28 | Mentors return to help, familiar powers solve the final encounter, and a new seed completes the world’s restoration. A sampled 37:32 frame shows the final shadow-tree arena. | The finale calls back to friends and spells Liza earned. Returning the crystal and growing a Heart Seed resolve the original sick-water problem. |

These are structural and presentation references. Luma, Pip, Orielle, Willow, Emberwing, the Heart Crystal, the six spells, and all dialogue are original story choices. The old `magiquest-template.md` remains historical reference; current executable story lives in `hub/adventures/*.json`.

## What changes from the prototype

The prototype moved through five simple station lists. Heartlight Quest has 52 authored beats: mentor scenes, ingredient hunts, spell lessons, physical routes, revelations, and restoration. The same three physical places recur throughout five fantasy lands. Their names do not change; only the things discovered there change.

The TV is a portal for characters and revelations, not the location of every action. Liza receives a short instruction, travels to one or more landmarks, waves her wand, and returns to the TV when a mentor needs to speak. A parent can read the line aloud; browser speech is optional. No countdown pressures travel around the house.

The active landmarks are:

1. **Moon Crystal** — sensor 1.
2. **Elder Tree** — sensor 2.
3. **Treasure Chest** — sensor 3.

Room names are intentionally unspecified until Scott places the hardware. Put the signs in three separate, accessible household locations, keeping the receiver visible. Use the same places for the whole campaign. Place ingredient cards beside the matching sensor when desired; physical cards are optional because the TV tracks the hunt.

## The story spine

**Act I — Something is missing.** Liza leaves the castle and finds sick fairies. Gathering little lights teaches her **Glowmend**. Healing the pools uncovers an empty crystal cradle and three clues: tiny boots, blue ribbon, and a warm scale. The initial repair helps the fairies immediately, but the missing Heart Crystal keeps the larger mystery open.

**Act II — Listen, learn, and connect.** In the Crystal Caves, evidence leads to Pip. He admits carrying the crystal to Emberwing because she feared her egg would go cold. **Truthlight** reveals that a black vine is draining the crystal. The Frost Queen’s **Frostbind** lesson and repeated-landmark riddle teach careful magic, with a bridge repaired rather than smashed. In the Unicorn Forest, **Wayweave** restores the paths. **Starcall** opens the protective bubble gently, and the Good Witch clears the rockslide. Black leaves bearing the same heart-shaped mark connect all the disasters.

**Act III — Share the light.** At Fire Mountain, Emberwing is frightened rather than cruel. The three old marks unlock **Heartglow**: the crystal carries shared life; it does not create endless power to keep for oneself. Removing it from its cycle let the Black Briar grow. Liza opens the path, cools the stones, and travels among the three landmarks to untangle six knots. The dragon realizes her own warmth can care for her egg. Liza brings the crystal home and shares its light across the realm, growing a new Heart Seed. Each earlier problem receives a payoff. Liza earns the title **Keeper of the Heartlight** through listening, repair, and courage.

## Chapter rhythm

| Chapter | Opening problem | Hunt / spell | Main physical play | Payoff and handoff |
|---|---|---|---|---|
| Fairy Pools | Poisoned water; sick fairies | Three lights → Glowmend | Three-pool route, then three clue locations | Fairies recover; crystal theft discovered |
| Crystal Caves | Silent crystals; hidden thief | Evidence hunt, then lens ingredients → Truthlight | Three echoes, bell, hidden stair | Pip explains his choice; dragon and vines revealed |
| Frozen Mountain | Ice bridge; queen’s riddle | Three winter gifts → Frostbind | Four-note route, mend bridge, wake mirror, make lantern | Queen guides Liza toward the trapped unicorns |
| Unicorn Forest | Zapped paths; witch and unicorns inside bubble | Path ingredients → Wayweave; song ingredients → Starcall | Two three-landmark routes, rockslide, shared vine mark | Unicorns freed; way to Fire Mountain opens |
| Fire Mountain | Dragon and egg trapped beside crystal | Three old signs → Heartglow | Open road, cool stones, six alternating knots, lift crystal, final three-landmark sharing route | Dragon helps; crystal returned; five lands healed |

Ingredient hunts accept any order. Pattern routes require the displayed order and can be retried. The finale alternates locations rather than rewarding repeated waving at one sensor. Six spells persist across the campaign, and earlier powers appear again in later chapters. Every forge scene requires returning to the TV; sensor hits cannot skip that scene.

## Presentation targets and limits

The reference’s strongest qualities are character presence, saturated painted environments, diegetic magical objects, deliberate reveals, and immediate feedback. Our adaptation uses original illustrated scenes, browser speech, and web animation. It is a household quest with a TV portal and three IR inputs; it does not reproduce the reference’s distributed screens or full animated films. Hardware reception and physical placement still require a real wand test when sensors arrive.

Playable desktop preview uses the same server transitions as hardware: keys or buttons 1–3 simulate the landmarks, and Continue / Enter advances TV dialogue. It is for inspecting the story now; room-to-room motion begins when the sensors are placed.
