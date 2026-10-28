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
