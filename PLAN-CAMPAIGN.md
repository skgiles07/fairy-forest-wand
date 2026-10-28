# Plan: Liza's Magi Quest campaign (hub engine + content + printables)
_Locked via claudex-loop — by Claude + Scott, 2026-10-27 (all recommendations accepted). Round 3 revision._

Read with: `docs/GAME-PLAN.md` (the what and why), `wargames/01-magi-campaign-build.md`
(the move-by-move route an executor follows). This file is the reviewable
contract; where it and the wargame disagree, this file wins.

## Goal

Turn the five existing single-level adventures into one five-chapter
campaign that tells Liza's story (castle, Fairy Pools, Crystal Caves,
Frozen Mountain, Unicorn Forest, Fire Mountain), played on five fixed wand
stations disguised as paper objects, with a realm map between chapters,
saved progress, four new step modes (collect, puzzle, charge, boss), and
printable sleeves and clue cards generated from the same JSON the TV
reads. Hardware is out of scope for the executor; everything verifies
with `hub/test_server.py` and a self-driving browser walkthrough.

## Approach

1. **`Game` step modes** (`hub/server.py`). `step.mode` is `ordered`
   (default), `collect`, `puzzle`, `charge`, or `boss`. `hit(station,
   wand_id=None)` returns exactly `heal | wrong | done`. Per-mode counters
   initialised by `_enter_step()`. Wrong-station hits return `wrong` in
   every mode (charge included). Boss timeout regrows `min(hp+2, hp_max)`
   and bumps `fire_seq`; it is evaluated inside `hit()` and `state()`
   under `self.lock`, and never changes the hit result.
2. **Per-mode schema validation** in `Game.__init__` (raise `ValueError`
   with the step index): stations in 1-5; `collect.stations` unique and
   2-5 long; `puzzle.pattern` non-empty, each in 1-5; `charge.hits` and
   `boss.hp` positive ints; `boss.window_s` positive number; every step
   has `clue`; every station a step touches has a label in `spot` (single)
   or `spots` (multi).
3. **State schema** (`GET /state`), replacing single-station assumptions:
   ```
   rev            monotonic int across the whole campaign (replaces seq for diffing)
   gen            int, bumps on every chapter load, reset, or phase change
   phase          intro | play | map | finished
   chapter        0-based index; chapters_done: [int]
   scene, title, opening, not_yet, ending, cheer (chapter text)
   mode           current step mode
   targets        stations that currently count as correct (list)
   healed         stations to draw lit in the scene (completed steps' stations + collect items found)
   progress       {done: steps_completed, total: steps}
   items          collect: found stations (sorted);  pattern, pattern_pos (puzzle)
   charge, charge_max (charge);  hp, hp_max, fire_seq (boss)
   event          heal | wrong | done | null — the last hit outcome
   event_station  station of the last hit (renderer never infers it from healed)
   spots          {station: label} for the current chapter (merged single + multi)
   clue           current step's clue
   map_deadline_s seconds left on the map screen (server-owned), null otherwise
   wand_id        last seen wand id
   save_error     string or null (see §5)
   last_step      snapshot of the step that just completed, kept through the
                  map phase and cleared only on the next chapter load, reset,
                  or the next hit inside play phase (tests: complete the final
                  step, read /state three times, snapshot identical each time): {mode, station(s), items, pattern, charge,
                  charge_max, hp, hp_max}; the renderer draws completion effects
                  (full ring, popped bubble, zero leaves, full rune wheel) from it
                  because _enter_step() has already reset the live counters
   ```
   `/state` is non-consuming: nothing changes because a client read it,
   except the server-side timers it evaluates (boss window, map deadline).
4. **`Campaign`** wraps `Game`. Loads `hub/adventures/campaign.json`
   (`title`, `chapters: [files]`, `map.lands`). Transition table (phase ×
   input → result):

   | phase | hit (any station) | `POST /next` | `POST /reset` | `POST /reset?campaign=1` |
   |---|---|---|---|---|
   | intro | → play ch 0, returns `heal` | → play ch 0 | no-op | wipe, stay intro |
   | play | inner `Game.hit`; inner `done` → record chapter, save, → map (deadline 20 s) | no-op | reload current chapter (gen++) | wipe → intro |
   | map | → play next chapter (or finished if none), returns `heal`; the hit is CONSUMED by the transition and never reaches the new chapter, deadline expired or not | same as hit | reload the chapter just completed (chapters_done unchanged; re-completing it is idempotent) | wipe → intro |
   | finished | returns `done` | no-op | reload last chapter | wipe → intro |

   Map deadline is server-owned: a `/state` past it performs the map→play
   transition; a `/hit` in map phase always performs only the transition
   (same row as above, deadline irrelevant). Tests cover a hit 1 ms before
   and 1 ms after the deadline: both return `heal`, neither touches the new
   chapter's step state. `/next` carries `gen`; a mismatched `gen` is
   ignored (`{"ignored": true}`), so stale or duplicate requests are
   harmless. Every transition bumps `gen` and `rev`.
5. **Progress file** `<state_dir>/progress.json` (default `hub/state/`,
   gitignored; overridable with `--state-dir` / `HUB_STATE_DIR` so tests
   and the autoplay run never touch family progress):
   `{"version": 1, "campaign": "<file name>", "fingerprint": "<sha256 of
   the concatenated chapter file bytes, first 12 hex>", "chapters_done":
   [..], "wand_id": "..", "saved_at": iso}`. Written atomically on chapter
   completion and on campaign reset.
   Resume algorithm on load: missing → `intro`. Corrupt JSON, wrong
   version, different campaign name or fingerprint, or `chapters_done`
   not a unique contiguous prefix `[0..k-1]` → one stderr line, fresh
   `intro`. Otherwise `k == 0` → `intro`; `0 < k < n` → `play` chapter `k`;
   `k == n` → `finished`. Re-completing an already-done chapter (after a
   reset in map phase) does not append. A failed write sets
   `save_error: "<msg>"` in `/state` (the TV shows a small amber "progress
   not saved" badge), logs to stderr, and the completing hit still
   succeeds; the badge clears on the next successful save.
   `wand_id` flows `Handler → Campaign.hit(station, wand_id) → Game`.
6. **Single-level mode stays**: `main()` builds `Campaign` when the JSON
   has `chapters`, else `Game`; default path becomes `campaign.json`.
7. **TV page** (`hub/static/index.html`):
   - diff on `rev`, not `seq`; every delayed UI callback (clue after
     cheer, clue after wrong, countdown ticks) captures `rev` and is a
     no-op if `state.rev` has moved (every hit, step advance, or transition
     bumps `rev`, so a callback can never restore a stale clue); callbacks
     read the CURRENT state when they fire, they never carry captured
     text. One `timers[]` is cleared on every `rev` change.
   - the renderer uses `event_station`, `targets`, `healed`, `progress`
     and the per-mode fields; it never indexes `stations[healed.length]`.
     Goblin: stands at `targets[0]` when `targets` is non-empty; when empty
     (chapter complete, reward frame, map) it stays at `event_station`'s
     zone if that zone exists in the mounted scene, else keeps its last
     transform. Every zone lookup is null-guarded; a missing zone logs via
     `/log` and skips the effect rather than throwing.
   - `scene-map` template (five lands, `.done`/`.next`), countdown from
     `map_deadline_s`; `POST /next` with `gen` on key/hit or when the
     countdown reaches 0 (server also advances by itself, so a closed
     browser never stalls the game).
   - per-mode HUD: rune wheel (collect), pattern strip (puzzle), charge
     ring (charge), leaf bar (boss) + fire shake/buzz on `fire_seq` change.
   - castle intro card (`phase === "intro"`), Frost Queen group in
     `scene-mountain` (shown on puzzle steps), Good Witch group in
     `scene-pools` (in the station-5 bubble; revealed when charge completes).
   - `?voice=1` enables Web Speech narration of opening/cheer/clue/ending.
   - **error reporting:** `window.onerror` and a try/catch around
     `render()` `POST /log {"level":"error","msg":..}`; fetch failures show
     "Lost the magic…", render failures show "Spell misfire: <msg>" so the
     two are never confused. Server prints `/log` lines to stderr.
   - **`?autoplay=1` self-drive:** the page dismisses the audio overlay,
     then walks the campaign by dispatching the keyboard simulator. Action
     protocol, every time: (a) read `/state`, remember `rev0`; (b) `await`
     the `/hit`, `/next`, or `/reset` POST and assert its JSON result is
     the expected one (`heal|wrong|done`, `ignored: true`, `ok`); (c) poll
     `/state` until `rev > rev0` (for deliberate no-ops such as a stale
     `/next`, assert `rev === rev0` after one extra poll instead); (d) wait
     until `window.__renderedRev === rev` (the renderer sets it at the end
     of a successful `render()`); only then (e) assert DOM state for the
     mode (`.zone.healed`
     count, rune-wheel filled count, pattern-strip filled count, charge
     ring percent, leaf count, map `.land.done` count, bubble text
     non-empty) and that no `/log` error fired. Scenario list, all
     bounded: per chapter one wrong key; chapter 2 one duplicate collect
     hit (items unchanged, `event === "heal"`); chapter 3 one wrong key
     mid-pattern (`pattern_pos === 0` and the strip empties); chapter 4
     charge completes and the witch group becomes visible; chapter 5 one
     forced boss timeout via `POST /debug/expire` (only served when the
     server runs with `--debug`; returns 404 otherwise) and asserts
     `fire_seq` moved and the leaf count grew by 2; one `/next` with a
     stale `gen` (`ignored: true`); one `/reset` mid-chapter 3 (zones
     unlit, `gen` moved). At the end it compares the visited
     `(chapter, mode)` sequence with the one derived from `campaign.json`
     and writes `#autoplay-result` text plus `POST /log {level: pass|fail,
     msg}`. **Scenario gating:** the self-drive first fetches
     `/campaign` (new read-only endpoint returning the loaded chapter list
     with each step's mode) and runs only the scenarios whose mode is
     present, reporting `skipped: [..]` in the pass message; the final
     gate (after characters exist) requires `skipped` to be empty. Runs in headless Chrome
     (`--headless=new --virtual-time-budget=180000`) against a server
     started with `--debug --state-dir <tmp>` so family progress is never
     read or written.
8. **Tests** (`hub/test_server.py`): keep the ordered regression but as an
   inline fixture (so content files can change); one inline adventure per
   mode; campaign transition table rows; progress save/load including a
   corrupt file; schema validation rejections (`[1,1]` collect, empty
   pattern, hp 0). Validity loop over `hub/adventures/*.json`: skip
   `campaign.json`; construct `Game(adv)` (validation runs) and walk its
   steps with correct stations to `done`.
9. **Move order**: engine + tests → campaign/map/progress using a
   temporary `campaign.json` listing the five EXISTING adventures →
   self-drive passes (ordered scenarios only; others reported skipped) →
   five chapter JSONs, switch `campaign.json` (self-drive passes with
   collect/puzzle/charge/boss scenarios; witch assertion skipped) → delete
   the old five files → characters + intro card → self-drive passes with
   `skipped` empty (the full gate) → printables → docs. Commit after each.
   **Verification harness** `hub/verify.py` (stdlib) owns every browser
   run: creates a temp state dir, picks a free port, starts `server.py
   --debug --state-dir <tmp> --port <p>`, waits for `GET /state` 200,
   runs headless Chrome against `?autoplay=1`, waits for the process,
   greps the captured stderr for exactly one `pass` and zero `error`
   lines, prints `verify ok` or the first failing line, and always kills
   the server (also on exceptions). It reads only the temp checkpoint.
   Nothing else starts a server during the build.
10. **Printables**: `cards/cutouts/station-1..5.svg` (letter size, sleeve
    for 48×24×14 mm, screen + IR windows labelled as placeholders),
    `hub/cards.py` generator with `--check` (builds the full expected set
    of `(chapter, step, station, spot)` tuples from the JSON and requires
    the generated Markdown to contain exactly that set: missing cards,
    omitted stations, or a station paired with the wrong spot all exit 1),
    `cards/spellbook.md`,
    `cards/items/*.svg` (chapter 2's four items). `cards/clues.md` removed
    after `cards/chapters/01-fairy-pools.md` exists.
11. **Docs + commits**: README, PLAN.md, GAME-PLAN §7; small commits on
    `main`; no push. Planning artifacts (`PLAN-CAMPAIGN*.md`, `docs/`,
    `wargames/`, firmware cooldown change) are committed BEFORE handoff so
    Move 1's clean-tree check holds.

## Firmware prerequisite (done 2026-10-27, outside the executor's scope)

`firmware/m5sticks3/station.ino` no longer latches `finished` after `done`
(rainbow 60 s, then rearm) and blocks input only `HIT_COOLDOWN_MS` = 1.5 s
after a hit, with the 30 s green glow visual-only, so charge/boss/puzzle
repeat hits reach the hub. Result strings unchanged. `firmware/code.py`
(CPX) is standalone with no hub contact and is not on the campaign path.

## Key decisions & tradeoffs

- **Modes in the engine, not story dressing.** ~100 lines in `Game` plus
  HUD; buys three chapters that play differently. Rejected: ordered-only.
- **Three result strings forever; richness in `/state`.** Rejected: a
  `fire` result (firmware would misread it).
- **Server owns every timer** (boss window, map deadline) and a `--debug`
  flag exposes `POST /debug/expire` so tests can force a boss timeout
  without waiting 90 s. Browser timers are display only. Rejected: browser-owned map advance (stale requests,
  closed-tab stall).
- **`rev`/`gen` instead of `seq`.** `seq` restarts per chapter; delayed
  callbacks need a generation guard. Rejected: clearing one timer.
- **Non-consuming `/state`; `fire_seq` monotonic.** Rejected: clear-on-read
  flags (a second client eats the event).
- **Self-driving page as the browser test.** No Playwright/Node; the page
  proves itself and reports through `/log`. Rejected: `/state`-only checks
  (cannot catch null zone dereferences) and manual-only walkthroughs
  (unavailable overnight).
- **Fixed physical objects, relabelled per chapter.** Five cutouts once.
- **Boss cannot be lost.** Regrow +2, never reset.
- **Delete the old five adventures** after new chapters pass and the
  ordered regression is inline. Rejected: keeping both.
- **Wrong-station hit during charge returns `wrong`**, same as every
  mode. Rejected: silent ignore (stations would show nothing, confusing).
- **Stdlib Python + one HTML file.** Rejected: frameworks, build steps.
- **Executor is Codex overnight**, commits locally, Scott pushes.

## Assumptions

1. Chapter order = Liza's outline. — `docs/story/liza-outline.md`
2. StickS3 firmware (amended) branches only on `heal|wrong|done`; CPX is
   standalone. — `firmware/m5sticks3/station.ino`, `firmware/code.py`
3. Existing scenes are reused; one map scene, two character groups, one
   intro card are added. — `hub/static/index.html`
4. `Game.state()` today reads `s["station"]` for every step and the
   renderer indexes `stations[healed.length]`; both are replaced by the
   state schema above. — Codex round 1
5. The old validity loop and the `fairy-forest.json` wording assertions in
   `test_server.py` are replaced (content-specific assertions may be
   replaced; behaviour assertions may not be deleted). — Codex round 1
6. Sleeve dims 48×24×14 mm and IR window on the top edge are placeholders.
   — RECON NEEDED, Scott, on hardware arrival
7. `.gitignore` is created for `hub/state/`. — repo
8. Headless Chrome with `--virtual-time-budget` runs page JS; the earlier
   "screenshots don't run the JS" note was about screenshots taken before
   the overlay click, which `?autoplay=1` dismisses itself. — to be proven
   in the first self-drive run; if it does not, the executor falls back to
   `chrome --remote-debugging-port` + a 20-line Python CDP driver (stdlib
   `websocket` is not available, so this fallback uses
   `--dump-dom` polling of a `#autoplay-result` element instead).

## Risks / open questions

- Story taste: defaults exist for every beat; new choices are logged as
  RESOLVED-pending-confirmation, never a stop.
- `virtual-time-budget` and `setTimeout`-driven polling interplay; the
  self-drive uses `await fetch` loops, not wall-clock sleeps, to stay
  deterministic.
- Two browsers open on the TV page both posting `/next` is harmless by
  `gen` check; both rendering is fine.

## Out of scope

Firmware beyond the cooldown change already made, hardware, WiFi,
multiple wands/scoring, station speech, a story editor UI, NFC runes,
pushing to GitHub.
