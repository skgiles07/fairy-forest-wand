# Wargame ledger

## 2026-10-27: 01-magi-campaign-build

- Mission: build `docs/GAME-PLAN.md` sections 3, 4, 5, 7 (hub engine step
  modes, campaign + map + progress, five chapter JSONs in Liza's story,
  printables, docs). Hardware explicitly out of scope.
- Draft: `wargames/01-magi-campaign-build.md`
- Status: **DONE** (executable blind). No BLOCKED inputs: every story beat
  the outline leaves open has a default in Move 5.
- RESOLVED assumptions the user should confirm:
  - Chapter order follows Liza's outline (pools, caves, mountain,
    unicorns, fire mountain), not the order the levels were built.
  - The five stations are fixed objects (crystal, mushroom, chest,
    lantern, fountain) relabeled per chapter, not re-dressed per chapter.
  - Boss fights never reset to full health (regrow +2 on timeout) so the
    game cannot be lost.
  - M5StickS3 sleeve dimensions 48 x 24 x 14 mm and IR window on the top
    edge are placeholders until the unit arrives.
- Self-grade (SUCCESS.md): 1 pass, 2 pass, 3 pass, 4 pass (two RECON
  NEEDED, hardware, owner Scott), 5 pass, 6 pass, 7 pass (one failed
  attack, two landed + patched), 8 pass.
- Red-team cycles: 2. Second cycle found the goblin-render crash; third
  cycle found nothing new, stopped.
- Claudex-loop: PLAN-CAMPAIGN.md approved by Codex (gpt-6.1-sol) on round 4
  of 5; 28 findings across rounds 1-3, all accepted (see
  PLAN-CAMPAIGN-REVIEW-LOG.md). Wargame patched in step. Handoff prompt:
  GOAL-PROMPT-MAGI-CAMPAIGN.md.

## 2026-10-27: Build run (01-magi-campaign-build)

Executor: Claude Fable 5.1, in-session, `~/Projects/fairy-forest-wand`,
started 2026-10-27 evening. Baseline (Move 1): clean tree at `86d2bfa`,
`test_server.py` ok, Chrome 156, Python 3.9.6.

Moves and gates:
- M2 `f600b2a` step modes in `Game` (Campaign class scaffold shipped in
  the same commit so M3 could test the transition table). Gate ok.
- M3 `04494bd` tests: every mode, every transition row, validation,
  progress. One test bug fixed (asserted live `hp` after done; the spec
  keeps it in `last_step`). Gate ok.
- M4 `b90bf0c` campaign + map + page + verify.py. Gate: `verify ok`,
  `skipped: [collect, puzzle, charge, boss, witch]`, checkpoint
  `chapters_done [0,1,2,3,4]` with fingerprint, `hub/state/` absent.
  Headless Chrome `--headless=new --virtual-time-budget --dump-dom` ran
  the page JS on the first try (PLAN-CAMPAIGN assumption 8 proven; the
  CDP fallback was not needed). Whole run ~3 s wall clock.
- M5 chapters. One engine gap found by the self-drive: live `/state` had
  no `stations` for the current step, so the rune wheel drew zero slots;
  added `stations` (current step) to the schema. Gate: `verify ok`,
  `skipped: [witch]`. Old five adventures `git rm`'d after the gate.

- M6 `efe3922` Frost Queen, Good Witch, reward frame. Two self-drive
  findings: (a) the chapter ends on the charge step and the server is on
  the map instantly, so the witch was never on screen; applied the
  wargame's fanfare-before-map fork (page holds the chapter scene 6 s as a
  reward frame, then mounts the map); (b) CSS opacity transitions do not
  advance under headless virtual time, so the witch assertion checks the
  class toggle + popped bubble, not computed opacity. Gate: `verify ok`,
  `skipped: []`. Three PNG canaries written.
- M7 `5ab6ca4` printables. `cards.py --check` exit 0 (26 station cards);
  mutation test: a wrong spot and an omitted station both fail the check.
  xmllint clean on 9 SVGs. `clues.md` removed after `01-fairy-pools.md`
  existed.
- M8 docs (this commit). Final: status clean, `test_server.py` ok,
  `verify.py` ok, nothing pushed.

Deviations from the wargame (PLAN-CAMPAIGN.md wins; none conflicted):
- `Campaign` class landed in the M2 commit instead of M4 (same code, one
  move earlier) so M3 could cover the transition table in one pass.
- Castle intro card shipped in M4 (the self-drive needed the intro phase
  on screen); M6 only verified it.
- The self-drive posts `/hit` / `/next` / `/reset` directly and asserts the
  JSON result (PLAN-CAMPAIGN section 7 action protocol); a dispatched
  keyboard event cannot await the POST.
- `/state` gained `stations` (current step), `chapter_scene`,
  `chapter_title`, `campaign_title`, `chapters_total`, `lands`, `next_land`,
  `intro` beyond the section 3 list; all additive.

RESOLVED-pending-confirmation (story choices the outline left silent):
- Spot names per chapter are new (e.g. Old Oak Pool, Mushroom Spring,
  Cave Pool, Waterfall Pool, Fairy Spring; Pine Grove, Warm Springs,
  Frost Bridge, Summit, Frost Throne; Big Bubble; Cool Waterfall, Burnt
  Oak, Smoky Cave, Lava Mushrooms, Dragon Lair). They match the existing
  scene art for each zone, so no scene was redrawn.
- Chapter 2 clue items follow the wargame default: Muddy Footprint, Torn
  Sock, Dropped Spoon, Giggle Jar, at stations 1-4; goblin at station 5.
- Chapter 3 riddle order is Bridge (3), Grove (1), Summit (4) per the
  wargame; station 1 is labelled Pine Grove for both the climb step and
  the riddle so the TV label never changes mid-chapter.
- Chapter 5 names the dragon's smoke as the thing that "made everything
  sick" to tie the five chapters into one cause; Liza's outline stops at
  the rockslide.
- Campaign intro line: "You got your wand at the castle. The whole realm
  needs your help! Wave your wand to begin."
- Ending of chapter 5 names Liza as Master Magi (GAME-PLAN section 1).
- `mentor` / `villain` keys were added to the chapter JSONs as plain
  metadata (GAME-PLAN 3.5); the engine ignores them.
