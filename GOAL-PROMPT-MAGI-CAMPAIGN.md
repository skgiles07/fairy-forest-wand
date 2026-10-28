# /goal — Liza's Magi Quest campaign build (overnight)

Use this prompt in a new Claude (Fable 5.1) or Codex context, high effort, from the repo root:

```text
Goal: Build the five-chapter campaign described in PLAN-CAMPAIGN.md for the fairy-forest-wand hub: step modes (ordered, collect, puzzle, charge, boss), a Campaign wrapper with realm map and saved progress, the TV page additions, five chapter JSONs telling Liza's story, printable station sleeves and clue cards, and docs. Verify with hub/test_server.py and the self-driving browser harness hub/verify.py. Commit on main. Do not push.

Project: /Users/scottgiles/Projects/fairy-forest-wand

Read first, in this order: PLAN-CAMPAIGN.md (the contract; it wins over every other file), wargames/01-magi-campaign-build.md (the move-by-move route with Expect / On failure / Fork for each move; follow it literally), docs/GAME-PLAN.md (the why), docs/story/liza-outline.md and docs/story/magiquest-template.md (story sources), hub/server.py, hub/static/index.html, hub/test_server.py, hub/adventures/*.json, cards/clues.md.

Hard scope:
1. Python stdlib only in hub/. One HTML file, hand-written SVG/JS, no frameworks, no build step, no npm, no pip.
2. Never edit anything under firmware/. The /hit response strings stay exactly "heal", "wrong", "done". All richer state goes through GET /state.
3. Every timer is server-owned (boss window, map deadline). Browser timers are display only.
4. Never start hub/server.py by hand. hub/verify.py is the only thing that starts a server during this build (temp state dir, free port, --debug). Family progress in hub/state/ must never be read or written by tests.
5. Commit after every wargame move with a one-line message naming the move. No push. No global git config changes; the repo already carries the right identity.
6. Story text: short read-aloud sentences, a six-year-old's vocabulary, Liza's own phrases where the outline gives them (sick fairies, poisoned water, who stole the crystal, Frost Queen puzzle, unicorn forest zapped, Good Witch in a bubble, rockslide, fire mountain). Where the outline is silent, use the defaults in wargame Move 5 and log the choice as RESOLVED-pending-confirmation in wargames/LEDGER.md. Never stop for taste.

Route (full detail in the wargame; these are the gates):
Move 1  Baseline: clean tree, python3 hub/test_server.py prints ok.
Move 2  Game step modes + state schema (PLAN §1-3), hit(station, wand_id), per-mode validation raising ValueError("step N: ...").
Move 3  Tests: inline ordered regression, one inline adventure per mode, validation rejections, transition table rows, progress round-trip + corrupt file. Validity loop rewritten. Gate: ok.
Move 4  Campaign wrapper (PLAN §4 transition table exactly), progress file (PLAN §5), --state-dir/HUB_STATE_DIR/--debug/--port flags, POST /next {gen}, POST /reset, POST /reset?campaign=1, POST /log, GET /campaign, POST /debug/expire (only with --debug). TV page: rev diffing, rev-guarded callbacks, event_station/targets/healed/progress rendering, null-guarded goblin, scene-map, per-mode HUD, save_error badge, error reporting, ?voice=1, ?autoplay=1 self-drive with the action protocol in PLAN §7. hub/verify.py harness (PLAN §9). Temporary campaign.json lists the five EXISTING adventures. Gate: ok + verify ok with skipped: [collect, puzzle, charge, boss, witch].
Move 5  Five chapter JSONs 01-fairy-pools … 05-fire-mountain per wargame Move 5; switch campaign.json. Gate: ok + verify ok with skipped: [witch]. Then git rm the five old adventure files.
Move 6  Frost Queen group (scene-mountain, shown on puzzle steps), Good Witch group (scene-pools bubble at station 5, revealed on charge completion from last_step), castle intro card. Gate: verify ok with skipped: [] plus docs/screenshots/{map,frost-queen,good-witch}.png as parse canaries.
Move 7  cards/cutouts/station-1..5.svg, hub/cards.py with --check (exact tuple coverage), cards/chapters/*.md generated, cards/spellbook.md, cards/items/*.svg; remove cards/clues.md after 01-fairy-pools.md exists. Gate: cards.py --check exits 0; xmllint --noout on every SVG prints nothing.
Move 8  README.md, PLAN.md, docs/GAME-PLAN.md §7 "New since 2026-10-27" block. Final: git status clean, python3 hub/test_server.py ok, hub/verify.py verify ok.

Abort conditions (stop, write the reason under "ABORTED" in wargames/LEDGER.md, leave the tree committed up to the last green move):
- Move 1 finds a dirty tree or a failing baseline.
- A change would alter the /hit result strings or touch firmware/.
- test_server.py cannot go green without deleting a behaviour assertion.
- hub/verify.py cannot get a pass or fail line out of headless Chrome after the Move 4 fork (--dump-dom on #autoplay-result).
- A dependency outside the Python stdlib or a JS framework seems required.

Required safeguards:
- Follow each move's Expect; on mismatch apply that move's On failure before trying anything else.
- When the wargame and PLAN-CAMPAIGN.md disagree, PLAN-CAMPAIGN.md wins; note the conflict in LEDGER.md.
- Keep diffs minimal and readable; match the existing code's style (compact, commented only where non-obvious). Do not refactor what you do not need to touch.
- Do not run chrome with a profile; headless only, as verify.py does.

Acceptance criteria (all must hold at the end):
- python3 hub/test_server.py prints ok and covers every mode, every transition-table row, validation, and progress.
- python3 hub/verify.py hub/adventures/campaign.json prints verify ok with skipped: [] and the printed temp checkpoint shows chapters_done [0,1,2,3,4] with a fingerprint; ls hub/state shows no progress.json.
- hub/adventures/ contains campaign.json and the five 0N-*.json chapters only; python3 hub/server.py (no args) loads the campaign.
- python3 hub/cards.py hub/adventures/campaign.json --check exits 0; five files in cards/chapters/; five SVGs in cards/cutouts/; four in cards/items/; cards/spellbook.md exists; cards/clues.md is gone.
- git log shows one commit per move above the baseline commit; nothing pushed; git status clean.
- wargames/LEDGER.md has a dated "Build run" entry listing every RESOLVED-pending-confirmation story choice and any skipped item, or an ABORTED entry with the reason.
```

Morning review for Scott: `git log --oneline`, `python3 hub/test_server.py`,
`python3 hub/verify.py hub/adventures/campaign.json`, then open
`http://localhost:8000/` after `python3 hub/server.py` and play chapter 1 with
keys 1-5; read `wargames/LEDGER.md` for the story choices to confirm with Liza.
