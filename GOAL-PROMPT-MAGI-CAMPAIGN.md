# /goal — Liza's Magi Quest campaign build (overnight)

Short form (3,529 chars, fits a 4,000-char goal box). Paste into a new Claude (Fable 5.1) or Codex session from the repo root, effort xhigh:

```text
Goal: Build Liza's five-chapter Magi Quest campaign for the fairy-forest-wand hub exactly as specified in PLAN-CAMPAIGN.md: step modes (ordered, collect, puzzle, charge, boss), Campaign wrapper with realm map and saved progress, TV page additions, five chapter JSONs in Liza's story, printable station sleeves and clue cards, docs. Verify with hub/test_server.py and the self-driving browser harness hub/verify.py. Commit on main after each move. Do not push.

Project: /Users/scottgiles/Projects/fairy-forest-wand

Read first, in order: PLAN-CAMPAIGN.md (the contract; wins over every other file), wargames/01-magi-campaign-build.md (the route: 8 moves, each with Expect / On failure / Fork; follow it literally), docs/GAME-PLAN.md, docs/story/*.md, hub/server.py, hub/static/index.html, hub/test_server.py, hub/adventures/*.json.

Hard scope:
1. Python stdlib only in hub/. One HTML file, hand-written SVG/JS. No frameworks, build step, npm, or pip.
2. Never edit firmware/. The /hit response strings stay exactly "heal", "wrong", "done"; everything richer goes through GET /state.
3. Every timer is server-owned. Browser timers are display only.
4. Never start hub/server.py by hand; hub/verify.py is the only server launcher during the build (temp state dir, free port, --debug). Family progress in hub/state/ is never read or written by tests.
5. One commit per wargame move, message naming the move. No push. No git config changes.
6. Story text: short read-aloud sentences, six-year-old vocabulary, Liza's phrases where the outline gives them. Where silent, use the defaults in wargame Move 5 and log each choice as RESOLVED-pending-confirmation in wargames/LEDGER.md. Never stop for taste.

Gates (details in the wargame):
M1 clean tree, test_server.py ok. M2 Game modes + state schema + validation. M3 tests for every mode, transition row, validation, progress; gate ok. M4 Campaign, progress file, flags, endpoints, TV page, ?autoplay=1, hub/verify.py, temp campaign.json of the five existing adventures; gate ok + verify ok, skipped [collect,puzzle,charge,boss,witch]. M5 five chapter JSONs, switch campaign.json; gate verify ok, skipped [witch]; then git rm old adventures. M6 Frost Queen, Good Witch, intro card; gate verify ok, skipped []. M7 cutouts, cards.py --check, chapters, spellbook, items; gate check exits 0, xmllint clean. M8 README, PLAN.md, GAME-PLAN §7; final: status clean, both checks green.

Abort (write reason under ABORTED in wargames/LEDGER.md, leave tree committed at last green move): dirty tree or failing baseline at M1; any change to /hit strings or firmware/; a behaviour assertion would have to be deleted; verify.py gets no pass/fail after the M4 fork; a non-stdlib dependency seems required.

Safeguards: apply each move's On failure before anything else; PLAN-CAMPAIGN.md beats the wargame on conflict (note it in LEDGER.md); minimal diffs in the existing style; headless Chrome only.

Acceptance: test_server.py prints ok covering every mode, transition row, validation, progress. verify.py prints verify ok with skipped [] and its temp checkpoint shows chapters_done [0,1,2,3,4] with a fingerprint; hub/state has no progress.json. hub/adventures holds campaign.json plus the five 0N-*.json only; server.py with no args loads the campaign. cards.py --check exits 0; 5 chapter cards, 5 cutout SVGs, 4 item SVGs, spellbook.md exist; clues.md gone. One commit per move, nothing pushed, status clean. LEDGER.md has a dated "Build run" entry with every story choice, or an ABORTED entry.
```

Morning review: `git log --oneline`, `python3 hub/test_server.py`, `python3 hub/verify.py hub/adventures/campaign.json`, then `python3 hub/server.py` and play chapter 1 with keys 1-5; read `wargames/LEDGER.md` for story choices to confirm with Liza.
