# Plan Review Log: Magi campaign
Phases 0-1 (recon + interrogation) complete 2026-10-27; Scott accepted all recommendations. MAX_ROUNDS=5. PLAN_FILE=PLAN-CAMPAIGN.md. Reviewer model: gpt-6.1-sol (config), codex-cli 0.159.2.

## Round 1 — Codex
Baseline `hub/test_server.py` passes. Plan has material blockers. No files modified.

1. **P0 — Station 5 stops after chapter 1.** StickS3 sets `finished = true` on `done`; every later wave gets discarded ([station.ino:229–239](firmware/m5sticks3/station.ino#L229)). Preserving three result strings does not preserve campaign compatibility.  
   **Fix:** Permit firmware change that rearms after chapter completion, or explicitly scope deliverable to keyboard-only prototype.

2. **P0 — Repeat-hit mechanics conflict with firmware.** Every `heal` blocks StickS3 input for 30 seconds plus animation time ([station.ino:240](firmware/m5sticks3/station.ino#L240)); charge needs five waves, boss eight, puzzle revisits station 1. CPX firmware never contacts hub or branches on response strings at all ([code.py:86](firmware/code.py#L86)), contradicting plan assumption 2.  
   **Fix:** Replace compatibility assumption with verified firmware requirements; shorten repeat-hit cooldown before claiming hardware readiness.

3. **P1 — Non-ordered steps break existing state serialization.** `Game.state()` unconditionally reads `s["station"]` for every step; collect/puzzle omit it ([server.py:53](hub/server.py#L53)). Plan mentions merging `spots`, but leaves replacement meaning of `stations` unspecified.  
   **Fix:** Define explicit state schema for active targets, completed steps, healed zones, and progress; remove single-station assumptions from serialization.

4. **P1 — New `heal` events can crash renderer or highlight wrong station.** Renderer derives event target from `healed.at(-1)` and immediately dereferences matching zone ([index.html:1115](hub/static/index.html#L1115)); partial collect/puzzle/charge hits need not append completed station. Updating goblin positioning alone misses this path.  
   **Fix:** Include explicit event station and mode-specific progress; make renderer consume those fields instead of inferring from `healed`.

5. **P1 — Move 4 cannot pass prescribed checks.** Campaign references five new filenames before Move 5 creates them ([wargame:176](wargames/01-magi-campaign-build.md#L176)); Move 4 requires running that campaign.  
   **Fix:** Create temporary campaign referencing existing adventures, or create chapters before campaign smoke test.

6. **P1 — Deleting old adventures breaks baseline test and default launch.** Test directly loads `fairy-forest.json` and asserts old clue wording ([test_server.py:6](hub/test_server.py#L6)); default server path points there too ([server.py:112](hub/server.py#L112)). Wargame simultaneously forbids deleting existing assertions.  
   **Fix:** Preserve ordered regression as inline fixture, update default launch path, and explicitly permit replacing content-specific assertions.

7. **P1 — Campaign reset/resume behavior lacks complete transition contract.** Completed chapter advances index before map; resetting during map could reset next chapter while keeping completed scene. Intro, finished reset, restart after final completion, and `/next` outside map remain unspecified ([wargame:181](wargames/01-magi-campaign-build.md#L181)).  
   **Fix:** Specify transition table for every phase × hit/next/reset/restart combination, including chapter index and inner-game ownership.

8. **P1 — Event identity resets across chapters; delayed callbacks overwrite newer scenes.** New `Game` starts `seq = 0`; browser compares only `seq`. Existing 2.2/3-second callbacks retain old clues across resets and transitions ([index.html:1113](hub/static/index.html#L1113)). Clearing map timer alone cannot fix this.  
   **Fix:** Add campaign-wide revision plus chapter/step generation; cancel or generation-guard every delayed UI callback.

9. **P1 — Map advancement has stale-request race.** Browser owns 20-second timer; timer request, station hit, second tab, or delayed request can overlap. Clearing timer cannot retract request already sent; later map could accept stale `/next`. Browser closure also stops automatic advancement ([wargame:193](wargames/01-magi-campaign-build.md#L193)).  
   **Fix:** Keep map deadline server-side; require expected transition revision on `/next` and make repeated advancement idempotent.

10. **P1 — Boss fire notification disappears when another client reads state.** Spec explicitly clears `fire` on next read ([wargame:132](wargames/01-magi-campaign-build.md#L132)); diagnostic curl or second browser can consume TV’s notification. Expiry during `hit()` can also overwrite internal fire event with heal.  
    **Fix:** Make `/state` non-consuming; expose monotonic `fire_seq` and persistent last-fire metadata separately from hit result.

11. **P1 — Save format and failure recovery remain undefined.** Atomic replacement prevents partial target writes; it does not handle corrupt JSON, changed campaign content, invalid indices, save failure, or loading another campaign against same global file. Wand ID cannot be saved through current `Game.hit(station)` call because handler discards it ([server.py:99](hub/server.py#L99)).  
    **Fix:** Version and validate campaign-keyed checkpoint, pass wand ID explicitly, define resume behavior, and surface failed saves before claiming progress saved.

12. **P1 — Verification permits broken browser implementation to pass.** Abort rule permits successful `/state` checks when browser unavailable ([wargame:339](wargames/01-magi-campaign-build.md#L339)); those checks cannot catch null zone dereferences, stale clues, pattern replay failures, or invisible characters. Existing catch mislabels render exceptions as lost hub connection ([index.html:1142](hub/static/index.html#L1142)).  
    **Fix:** Require executable browser walkthrough covering every mode/reset/transition with zero JS errors; distinguish fetch failures from render failures.

13. **P2 — JSON validation accepts unwinnable content.** Non-empty station union allows collect `[1,1]` despite set-based completion comparing against list length; zero/negative charge, HP, invalid modes, and empty individual patterns remain unchecked ([wargame:112](wargames/01-magi-campaign-build.md#L112), [164](wargames/01-magi-campaign-build.md#L164)).  
    **Fix:** Validate per-mode schema at load time, including unique collect targets, non-empty patterns, positive counts/windows, and complete labels.

14. **P2 — Charge rules contradict each other.** GAME-PLAN promises “No ‘wrong’ while charging” ([GAME-PLAN:75](docs/GAME-PLAN.md#L75)); wargame requires wrong-station hit return `wrong` and tests it ([wargame:120](wargames/01-magi-campaign-build.md#L120)). Top-level contract resolves neither.  
    **Fix:** Choose one behavior in controlling plan and align companion text/tests before execution.

15. **P2 — Current checkout immediately triggers mandated abort.** Read-only `git status` shows untracked plan, review log, `docs/`, and `wargames/`; Move 1 requires completely clean tree ([wargame:99](wargames/01-magi-campaign-build.md#L99)).  
    **Fix:** Commit planning artifacts before handoff, or explicitly allow those exact pre-existing paths without staging unrelated work.

VERDICT: REVISE
### Claude's response
Accepted all 15. Changes: firmware `finished` latch removed and input cooldown cut to 1.5 s with glow visual-only (1, 2; done in `station.ino` before handoff, CPX noted as standalone); explicit state schema with `targets/healed/progress/event_station` (3, 4); Move 4 uses the five existing adventures as a temporary campaign (5); ordered regression moved to an inline fixture, default path → `campaign.json`, content assertions may be replaced (6); full phase × input transition table (7); campaign-wide `rev` + `gen` guard on every delayed callback (8); server-owned map deadline, `/next {gen}` idempotent (9); non-consuming `/state`, monotonic `fire_seq` (10); versioned campaign-keyed progress file with corrupt/failed-write behaviour, `wand_id` threaded through `hit()` (11); `?autoplay=1` self-driving walkthrough + `/log` endpoint + distinct render-vs-fetch error bubbles, `/state`-only checks no longer satisfy the abort rule (12); per-mode schema validation in `Game.__init__` (13); charge wrong-station → `wrong` everywhere (14); planning artifacts committed before handoff (15). Rejected: nothing.

## Round 2 — Codex
Most prior findings addressed: firmware latch removed, repeat-hit cooldown shortened, CPX excluded, state schema expanded, fire events non-consuming, move order fixed, regression fixture preserved, charge rule aligned. Baseline tests still pass. Firmware changes inspected; hardware behavior unverified. No files modified.

Remaining material problems:

1. **P1 — Generation guard misses stale callbacks within chapter.** `gen` changes on chapter/reset/phase changes, but not step advances ([plan:37](/Users/scottgiles/Projects/fairy-forest-wand/PLAN-CAMPAIGN.md:37)). Wrong-hit callback can restore old clue after player completes step within three seconds.  
   **Fix:** Cancel clue callbacks on newer hit/step revision; callbacks must read current state instead of captured clue.

2. **P1 — Expired-map hit has ambiguous double effect.** Any `/hit` past deadline transitions into play, but contract never says whether same hit also reaches new chapter ([plan:67](/Users/scottgiles/Projects/fairy-forest-wand/PLAN-CAMPAIGN.md:67)). Identical wave can merely advance before deadline, yet accidentally heal/wrong immediately afterward.  
   **Fix:** Specify that hit received in map phase consumes only transition, regardless of deadline; test both boundary cases.

3. **P1 — Save loading still lacks resume algorithm.** File stores completed indices, but plan never specifies startup phase/chapter, all-complete behavior, or validation of duplicate/noncontiguous indices ([plan:71](/Users/scottgiles/Projects/fairy-forest-wand/PLAN-CAMPAIGN.md:71)). Replay resets retain completion records, making append-based progression unsafe. Save-write failures remain invisible on TV.  
   **Fix:** Require completed indices form unique contiguous prefix, resume first unfinished chapter or finished, make replay completion idempotent, and expose save-error status.

4. **P1 — Browser verification shares real campaign checkpoint.** Move 4 autoplay completes temporary campaign; Move 5 replaces chapter files under same `campaign.json` identity ([plan:120](/Users/scottgiles/Projects/fairy-forest-wand/PLAN-CAMPAIGN.md:120)). Second run can resume already-finished campaign and skip new content; tests also overwrite family progress.  
   **Fix:** Give tests isolated state directory and fresh checkpoint per run; assert exact expected chapters/modes visited before accepting pass.

5. **P1 — Autoplay can pass without renderer processing each action.** Driver advances through fetch loops, while actual renderer polls every 400 ms; checking server `rev` and absence of errors does not prove intermediate HUDs rendered ([plan:104](/Users/scottgiles/Projects/fairy-forest-wand/PLAN-CAMPAIGN.md:104), [renderer:1142](/Users/scottgiles/Projects/fairy-forest-wand/hub/static/index.html:1142)). Happy-path walkthrough also never forces boss timeout or duplicate collect hit.  
   **Fix:** Await rendered revision and assert DOM state after each action; add bounded scenarios for duplicate collection, puzzle reset, boss fire, stale `/next`, and reset.

6. **P1 — Goblin fix still dereferences missing terminal target.** New rule always positions goblin at `targets[0]` ([plan:88](/Users/scottgiles/Projects/fairy-forest-wand/PLAN-CAMPAIGN.md:88)); completed cave chapter has no valid target, especially during explicitly retained pre-map reward frame. Original renderer immediately dereferences selected zone.  
   **Fix:** Guard empty targets and missing zones; use final event station or fixed captured position for completion frame.

7. **P1 — Partial-mode fields vanish on completion without defined reward snapshot.** `_enter_step()` resets counters immediately after advance ([wargame:142](/Users/scottgiles/Projects/fairy-forest-wand/wargames/01-magi-campaign-build.md:142)). Final collect item, full charge ring, completed pattern, and boss HP zero can disappear before next poll; Good Witch reveal specifically depends on charge completion.  
   **Fix:** Retain completed-step outcome payload until next hit/transition, and render completion effects from that payload.

8. **P2 — Campaign identity ignores content changes.** Checkpoint validates filename only ([plan:72](/Users/scottgiles/Projects/fairy-forest-wand/PLAN-CAMPAIGN.md:72)); reordered/replaced chapter files retain old completions despite representing different content. Temporary-to-final campaign replacement already exercises this case.  
   **Fix:** Store explicit campaign revision or content fingerprint and reject incompatible checkpoints.

9. **P2 — Printable check proves only one-way membership.** `--check` rejects output spot names absent from JSON, but accepts missing cards, omitted stations, and wrong station-to-spot pairings ([wargame:320](/Users/scottgiles/Projects/fairy-forest-wand/wargames/01-magi-campaign-build.md:320)). Empty output could satisfy described check.  
   **Fix:** Compare complete expected chapter/step/station/spot tuples against generated output and require exact coverage.

Planning-artifact commit remains pending: current checkout still contains modified firmware and untracked planning files. Revised pre-handoff commit requirement addresses this once executed.

VERDICT: REVISE
### Claude's response
Accepted all 9. Changes: delayed callbacks now guard on `rev` (bumps on every hit/step/transition) and read current state when they fire (1); map-phase hit consumes only the transition, deadline irrelevant, both boundary cases tested (2); resume algorithm specified (contiguous-prefix validation, intro/play/finished by k, idempotent re-completion, `save_error` in state + TV badge) (3); `--state-dir`/`HUB_STATE_DIR` isolation for tests and autoplay, visited `(chapter, mode)` sequence asserted against campaign.json (4); autoplay waits for `window.__renderedRev === rev`, asserts DOM per mode, bounded scenarios incl. duplicate collect, puzzle reset, forced boss fire via `--debug` `POST /debug/expire`, stale `/next`, mid-chapter reset (5); goblin null-guarded with `event_station`/last-transform fallback, all zone lookups guarded (6); `last_step` snapshot retained in state until next hit/transition and completion effects render from it (7); progress file carries a chapter-content fingerprint (8); `cards.py --check` requires exact tuple coverage (9). Planning commit happens after approval, before handoff. Rejected: nothing.

## Round 3 — Codex
Round-2 fixes largely addressed: revision guards, map-hit consumption, resume algorithm, content fingerprint, save-error badge, guarded goblin lookup, and exact printable coverage. Four material gaps remain. No files modified.

1. **P1 — Completion snapshot clears during same operation that creates it.** `last_step` survives only until next transition ([plan:54](/Users/scottgiles/Projects/fairy-forest-wand/PLAN-CAMPAIGN.md:54)), but final-step completion immediately transitions `play → map` ([plan:69](/Users/scottgiles/Projects/fairy-forest-wand/PLAN-CAMPAIGN.md:69)). Charge and boss rewards can disappear before browser polls; Good Witch reveal remains unreliable.  
   **Fix:** Preserve final-step snapshot through map phase, clearing only on next chapter load/reset; test snapshot after completing hit and repeated `/state` reads.

2. **P1 — Required walkthrough checks features before build creates them.** Move 4 uses old ordered-only adventures; new autoplay requires chapter-2 collect, chapter-3 puzzle, and chapter-5 boss scenarios ([plan:135](/Users/scottgiles/Projects/fairy-forest-wand/PLAN-CAMPAIGN.md:135)). Move 5 must pass witch-visibility assertion before Move 6 adds witch ([wargame:276](/Users/scottgiles/Projects/fairy-forest-wand/wargames/01-magi-campaign-build.md:276), [292](/Users/scottgiles/Projects/fairy-forest-wand/wargames/01-magi-campaign-build.md:292)). Literal executor cannot satisfy gates in order.  
   **Fix:** Gate early walkthrough scenarios by actual modes present, add characters before final-content walkthrough, then require full scenario coverage.

3. **P1 — Render synchronization can succeed against pre-action state.** Waiting for `__renderedRev === state.rev` ([plan:129](/Users/scottgiles/Projects/fairy-forest-wand/PLAN-CAMPAIGN.md:129)) already succeeds before dispatched keyboard request completes. Unlike previous revision, current acceptance text no longer explicitly requires post-action revision advance and matching outcome. Autoplay can inspect old DOM and race subsequent actions.  
   **Fix:** Capture pre-action revision, await POST completion and expected result, then require newer authoritative revision and matching rendered revision before DOM assertions; handle deliberate no-op requests separately.

4. **P2 — Verification route still bypasses checkpoint isolation.** Section 6 starts server without `--state-dir` and reads `hub/state/progress.json` ([wargame:381](/Users/scottgiles/Projects/fairy-forest-wand/wargames/01-magi-campaign-build.md:381)), contradicting isolated verification requirement. Move 4 also leaves server running before Move 5 repeats same-port launch, risking bind failure or checks against old loaded content.  
   **Fix:** Use one verification harness owning temporary state path, server PID, readiness check, and shutdown/restart for each build stage; inspect only its checkpoint.

VERDICT: REVISE
### Claude's response
Accepted all 4. Changes: `last_step` persists through map phase, cleared only on chapter load/reset/next play hit, with a three-read test (1); autoplay scenarios gated by modes actually present via a new read-only `/campaign` endpoint, `skipped` reported, move order now content → characters → full gate with `skipped: []` (2); explicit action protocol: rev0, await POST + assert result, poll until rev advances (or stays for deliberate no-ops), then `__renderedRev === rev`, then DOM (3); `hub/verify.py` harness owns temp state dir, free port, readiness, Chrome run, log grep and guaranteed shutdown; no hand-started servers, verification table reads only the temp checkpoint (4). Rejected: nothing.

## Round 4 — Codex
All four round-3 blockers addressed:

- Completion snapshot survives map phase.
- Staged walkthrough gates match available content and characters.
- Action protocol awaits POST result, newer state, then rendered revision.
- Verification harness owns isolated progress, port, readiness, and shutdown.

No new material blockers found. Plan sound enough to implement; implementation and hardware still require prescribed checks. No files modified.

VERDICT: APPROVED
### Resolution
APPROVED after 4 rounds (3 REVISE, 1 APPROVED). Next: GOAL-PROMPT-MAGI-CAMPAIGN.md for the overnight Codex build; Scott reviews the diff in the morning.
