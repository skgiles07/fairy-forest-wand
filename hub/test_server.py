"""python3 hub/test_server.py  -> prints ok

Covers: ordered regression (inline fixture), every step mode, schema
validation, the campaign transition table (PLAN-CAMPAIGN.md section 4),
progress save / load / corrupt file, and a validity walk of every
adventure JSON on disk.
"""
import contextlib
import io
import json
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from server import Game, Campaign, MAP_SECONDS  # noqa: E402

ADV = Path(__file__).parent / "adventures"


def raises(fn, needle):
    try:
        fn()
    except ValueError as e:
        assert needle in str(e), (needle, str(e))
        return
    raise AssertionError(f"expected ValueError containing {needle!r}")


def stations(a, **kw):
    """Tiny ordered adventure factory."""
    return dict(title="t", opening="o", not_yet="n", ending="e",
                steps=[dict(station=n, spot=f"S{n}", clue=f"c{n}") for n in a], **kw)


# ---------------------------------------------------------------- ordered regression (inline copy of the old fairy-forest.json)
forest = {
    "title": "Fairy Forest Healing",
    "opening": "Dark energy has crept into the Fairy Forest and the glow has gone out. Your wand still holds fairy light. Heal the five forest places one by one!",
    "not_yet": "Not yet! That part of the forest isn't ready. Follow the clue.",
    "steps": [
        {"station": 1, "spot": "The Old Oak", "clue": "Where the Old Oak sits so still, a patch of forest, cold and ill. Wave your wand and watch it gleam!"},
        {"station": 2, "spot": "The Mushroom Ring", "clue": "The Oak is healed, but hear the plea: the Mushroom Ring needs you and me. Find where the little caps grow round."},
        {"station": 3, "spot": "The Dark Cave", "clue": "Two are healed, three more to go. The darkest place is the Cave, you know. Creep up quiet, hold wand high!"},
        {"station": 4, "spot": "The Waterfall", "clue": "Halfway home, the fairies cheer, but the Waterfall still hides fear. Bring your light where water falls."},
        {"station": 5, "spot": "The Fairy Throne", "clue": "One last place the darkness keeps, where the Fairy Throne silently sleeps. Heal it now with all your might!"},
    ],
    "ending": "The Fairy Forest is healed! Every tree and flower glows again because of you. The fairies name you Guardian of the Forest!",
}
g = Game(forest)
assert g.state()["clue"].startswith("Where the Old Oak")
assert g.hit(3) == "wrong" and g.healed == []
assert g.hit(1) == "heal" and g.healed == [1]
assert g.state()["clue"].startswith("The Oak is healed")
for s in (2, 3, 4):
    assert g.hit(s) == "heal"
assert g.hit(5) == "done" and g.state()["done"]
assert g.hit(1) == "done"  # ignored after finish
g.reset()
assert g.healed == [] and not g.state()["done"]

# state schema basics
st = g.state()
for k in ("rev", "gen", "phase", "chapter", "chapters_done", "scene", "title", "opening", "not_yet", "ending",
          "cheer", "mode", "targets", "healed", "progress", "items", "pattern", "pattern_pos", "charge",
          "charge_max", "hp", "hp_max", "fire_seq", "event", "event_station", "spots", "clue",
          "map_deadline_s", "wand_id", "save_error", "last_step"):
    assert k in st, k
assert st["mode"] == "ordered" and st["targets"] == [1] and st["progress"] == {"done": 0, "total": 5}
assert st["spots"] == {1: "The Old Oak", 2: "The Mushroom Ring", 3: "The Dark Cave", 4: "The Waterfall", 5: "The Fairy Throne"}
r0 = st["rev"]
g.hit(2, wand_id="0xABC")
st = g.state()
assert st["rev"] == r0 + 1 and st["event"] == "wrong" and st["event_station"] == 2 and st["wand_id"] == "0xABC"
assert g.state()["rev"] == r0 + 1, "/state is non-consuming"
g.hit(1)
assert g.state()["last_step"]["station"] == 1 and g.state()["targets"] == [2]
g.hit(4)  # wrong hit clears last_step
assert g.state()["last_step"] is None

# ---------------------------------------------------------------- collect
collect = dict(title="t", opening="o", not_yet="n", ending="e", steps=[
    {"mode": "collect", "stations": [1, 2, 3], "spot": "Clues", "spots": {"1": "A", "2": "B", "3": "C"}, "clue": "find three"},
    {"station": 5, "spot": "Pedestal", "clue": "pedestal"},
])
g = Game(collect)
st = g.state()
assert st["mode"] == "collect" and st["targets"] == [1, 2, 3] and st["spots"] == {1: "A", 2: "B", 3: "C", 5: "Pedestal"}
assert g.hit(4) == "wrong" and g.state()["items"] == []
assert g.hit(2) == "heal" and g.state()["items"] == [2] and g.state()["targets"] == [1, 3] and g.state()["healed"] == [2]
assert g.hit(2) == "heal" and g.state()["items"] == [2], "re-hit of a found station is heal, no change"
assert g.state()["event"] == "heal"
assert g.hit(3) == "heal" and g.state()["items"] == [2, 3]
assert g.hit(1) == "heal", "third item completes the step"
st = g.state()
assert st["clue"] == "pedestal" and st["progress"]["done"] == 1 and st["targets"] == [5]
assert sorted(st["healed"]) == [1, 2, 3] and st["items"] == []
assert st["last_step"]["mode"] == "collect" and st["last_step"]["items"] == [1, 2, 3]
assert g.hit(5) == "done"

# ---------------------------------------------------------------- puzzle
puzzle = dict(title="t", opening="o", not_yet="n", ending="e", steps=[
    {"station": 2, "spot": "Climb", "clue": "climb"},
    {"mode": "puzzle", "pattern": [3, 1, 4], "spot": "Riddle", "spots": {"3": "Bridge", "1": "Grove", "4": "Summit"}, "clue": "bridge grove summit"},
])
g = Game(puzzle)
assert g.hit(2) == "heal"
st = g.state()
assert st["mode"] == "puzzle" and st["pattern"] == [3, 1, 4] and st["pattern_pos"] == 0 and st["targets"] == [3]
assert g.hit(3) == "heal" and g.state()["pattern_pos"] == 1 and g.state()["targets"] == [1]
assert g.hit(2) == "wrong" and g.state()["pattern_pos"] == 0 and g.state()["targets"] == [3]
assert g.hit(3) == "heal" and g.hit(1) == "heal" and g.state()["pattern_pos"] == 2
assert g.hit(4) == "done" and g.state()["done"]
assert g.state()["healed"] == [2, 3, 1, 4] and g.state()["last_step"]["pattern"] == [3, 1, 4]
# snapshot stays identical across repeated reads after the final step
assert g.state()["last_step"] == g.state()["last_step"] == g.state()["last_step"]

# ---------------------------------------------------------------- charge
charge = dict(title="t", opening="o", not_yet="n", ending="e", steps=[
    {"mode": "charge", "station": 5, "hits": 3, "spot": "Bubble", "clue": "wave wave wave"},
])
g = Game(charge)
assert g.state()["charge"] == 0 and g.state()["charge_max"] == 3 and g.state()["targets"] == [5]
assert g.hit(5) == "heal" and g.hit(5) == "heal" and g.state()["charge"] == 2
assert g.hit(1) == "wrong" and g.state()["charge"] == 2, "wrong station during charge is wrong"
assert g.hit(5) == "done"
assert g.state()["last_step"]["charge"] == 3 and g.state()["last_step"]["charge_max"] == 3

# ---------------------------------------------------------------- boss
boss = dict(title="t", opening="o", not_yet="n", ending="e", steps=[
    {"mode": "boss", "station": 5, "hp": 3, "window_s": 0.05, "spot": "Lair", "clue": "zap the dragon"},
])
g = Game(boss)
assert g.state()["hp"] == 3 and g.state()["hp_max"] == 3 and g.state()["fire_seq"] == 0
assert g.hit(5) == "heal" and g.state()["hp"] == 2
assert g.hit(2) == "wrong" and g.state()["hp"] == 2
time.sleep(0.1)
st = g.state()
assert st["hp"] == 3 and st["fire_seq"] == 1, st          # regrow min(2+2, 3)
assert g.state()["fire_seq"] == 1, "non-consuming"
assert g.hit(5) == "heal" and g.hit(5) == "heal" and g.hit(5) == "done"
assert g.state()["hp"] is None and g.state()["last_step"]["hp"] == 0 and g.state()["last_step"]["hp_max"] == 3
time.sleep(0.1)
assert g.state()["fire_seq"] == 1, "no regrow after the boss is down"
# expire() forces the timeout without waiting; hit result unaffected
g = Game(boss)
assert g.hit(5) == "heal" and g.hit(5) == "heal" and g.state()["hp"] == 1
assert g.expire() == "boss"
assert g.hit(5) == "heal" and g.state()["hp"] == 2 and g.state()["fire_seq"] == 1   # regrew to 3, then -1

# ---------------------------------------------------------------- validation
base = dict(title="t", opening="o", not_yet="n", ending="e")
raises(lambda: Game(dict(base, steps=[{"mode": "collect", "stations": [1, 1], "spots": {"1": "a"}, "clue": "c"}])), "step 0")
raises(lambda: Game(dict(base, steps=[{"mode": "collect", "stations": [1], "spots": {"1": "a"}, "clue": "c"}])), "2-5")
raises(lambda: Game(dict(base, steps=[{"station": 1, "spot": "a", "clue": "c"}, {"mode": "puzzle", "pattern": [], "clue": "c"}])), "step 1")
raises(lambda: Game(dict(base, steps=[{"mode": "boss", "station": 5, "hp": 0, "spot": "a", "clue": "c"}])), "hp")
raises(lambda: Game(dict(base, steps=[{"mode": "boss", "station": 5, "hp": 2, "window_s": 0, "spot": "a", "clue": "c"}])), "window_s")
raises(lambda: Game(dict(base, steps=[{"mode": "charge", "station": 5, "hits": 0, "spot": "a", "clue": "c"}])), "hits")
raises(lambda: Game(dict(base, steps=[{"station": 6, "spot": "a", "clue": "c"}])), "1-5")
raises(lambda: Game(dict(base, steps=[{"station": 1, "spot": "a"}])), "clue")
raises(lambda: Game(dict(base, steps=[{"station": 1, "clue": "c"}])), "label")
raises(lambda: Game(dict(base, steps=[{"mode": "puzzle", "pattern": [1, 2], "spots": {"1": "a"}, "clue": "c"}])), "station 2 has no label")
raises(lambda: Game(dict(base, steps=[{"mode": "flying", "station": 1, "spot": "a", "clue": "c"}])), "mode")
raises(lambda: Game(dict(base, steps=[])), "steps")

# ---------------------------------------------------------------- campaign
clock = {"t": 1000.0}
now = lambda: clock["t"]  # noqa: E731


def make_campaign(tmp, chapters=None, state="state"):
    tmp = Path(tmp)
    chapters = chapters or [stations([1, 2]), dict(stations([5]), title="two")]
    files = []
    for i, c in enumerate(chapters):
        f = tmp / f"ch{i}.json"
        f.write_text(json.dumps(c))
        files.append(f.name)
    cfg = {"title": "Camp", "chapters": files,
           "map": {"lands": [{"name": f"Land {i}", "chapter": i} for i in range(len(files))]}}
    (tmp / "campaign.json").write_text(json.dumps(cfg))
    return Campaign(cfg, tmp / "campaign.json", tmp / state, now=now)


with tempfile.TemporaryDirectory() as tmp:
    c = make_campaign(tmp)
    st = c.state()
    assert st["phase"] == "intro" and st["scene"] == "map" and st["chapter"] == 0 and st["chapters_done"] == []
    assert st["lands"][0]["next"] and not st["lands"][0]["done"] and st["next_land"] == "Land 0"
    assert st["map_deadline_s"] is None and st["title"] == "Camp"
    gen0, rev0 = st["gen"], st["rev"]
    # intro: reset is a no-op; /next with stale gen ignored; hit -> play ch0, consumed
    c.reset_request()
    assert c.state()["phase"] == "intro" and c.state()["gen"] == gen0
    assert c.next(gen0 - 1) == {"ignored": True} and c.state()["phase"] == "intro"
    assert c.hit(4, wand_id="0x1") == "heal"
    st = c.state()
    assert st["phase"] == "play" and st["chapter"] == 0 and st["healed"] == [] and st["event"] is None
    assert st["gen"] > gen0 and st["rev"] > rev0 and st["scene"] == "forest" and st["title"] == "t"
    assert st["wand_id"] == "0x1"
    # play: /next no-op; inner hits; reset reloads chapter (gen++)
    gen1 = st["gen"]
    assert c.next(gen1) == {"ok": True} and c.state()["phase"] == "play"
    assert c.hit(1) == "heal" and c.state()["healed"] == [1]
    c.reset_request()
    st = c.state()
    assert st["healed"] == [] and st["gen"] > gen1 and st["phase"] == "play"
    # play done -> map with deadline, progress saved, last_step kept through map
    assert c.hit(1) == "heal" and c.hit(2) == "done"
    st = c.state()
    assert st["phase"] == "map" and st["scene"] == "map" and st["chapters_done"] == [0]
    assert 19 < st["map_deadline_s"] <= MAP_SECONDS and st["lands"][0]["done"] and st["lands"][1]["next"]
    assert st["event"] == "done" and st["last_step"]["station"] == 2 and st["title"] == "Camp"
    assert st["last_step"] == c.state()["last_step"] == c.state()["last_step"]
    p = json.loads((Path(tmp) / "state" / "progress.json").read_text())
    assert p["chapters_done"] == [0] and p["campaign"] == "campaign.json" and len(p["fingerprint"]) == 12
    assert p["version"] == 1 and p["wand_id"] == "0x1" and p["saved_at"]
    # map: reset reloads the chapter just completed; re-completing it is idempotent
    c.reset_request()
    assert c.state()["phase"] == "play" and c.state()["chapter"] == 0 and c.state()["chapters_done"] == [0]
    assert c.hit(1) == "heal" and c.hit(2) == "done" and c.state()["chapters_done"] == [0]
    # map: hit 1 ms before the deadline -> heal, transition only, new chapter untouched
    clock["t"] += MAP_SECONDS - 0.001
    assert c.hit(5) == "heal"
    st = c.state()
    assert st["phase"] == "play" and st["chapter"] == 1 and st["healed"] == [] and st["event"] is None
    assert st["last_step"] is None and st["progress"]["done"] == 0
    # back to map (finish chapter 1 would end the campaign, so rebuild and test the after-deadline hit)
    c.reset_request(campaign=True)
    assert c.state()["phase"] == "intro" and c.state()["chapters_done"] == []
    assert json.loads((Path(tmp) / "state" / "progress.json").read_text())["chapters_done"] == []
    assert c.hit(1) == "heal" and c.hit(1) == "heal" and c.hit(2) == "done" and c.state()["phase"] == "map"
    clock["t"] += MAP_SECONDS + 0.001
    assert c.hit(5) == "heal", "hit after the deadline still only transitions"
    st = c.state()
    assert st["phase"] == "play" and st["chapter"] == 1 and st["healed"] == [] and st["progress"]["done"] == 0
    # map: deadline expiry on /state advances by itself
    c.reset_request(campaign=True)
    assert c.hit(1) == "heal" and c.hit(1) == "heal" and c.hit(2) == "done"
    clock["t"] += MAP_SECONDS + 1
    assert c.state()["phase"] == "play" and c.state()["chapter"] == 1
    # map: /next with the live gen advances; stale ignored
    c.reset_request(campaign=True)
    assert c.hit(1) == "heal" and c.hit(1) == "heal" and c.hit(2) == "done"
    gmap = c.state()["gen"]
    assert c.next(gmap - 1) == {"ignored": True} and c.state()["phase"] == "map"
    assert c.next(gmap) == {"ok": True} and c.state()["phase"] == "play" and c.state()["chapter"] == 1
    # expire() on the map forces the transition on the next /state
    c.reset_request(campaign=True)
    assert c.hit(1) == "heal" and c.hit(1) == "heal" and c.hit(2) == "done" and c.expire() == "map"
    assert c.state()["phase"] == "play"
    # finished: last chapter done -> map -> hit -> finished; hit returns done; reset reloads last chapter
    assert c.hit(5) == "done" and c.state()["phase"] == "map" and c.state()["chapters_done"] == [0, 1]
    assert c.hit(3) == "heal" and c.state()["phase"] == "finished" and c.state()["scene"] == "map"
    assert all(l["done"] for l in c.state()["lands"]) and c.state()["next_land"] is None
    assert c.hit(3) == "done" and c.state()["phase"] == "finished"
    assert c.next(c.state()["gen"]) == {"ok": True} and c.state()["phase"] == "finished"
    c.reset_request()
    assert c.state()["phase"] == "play" and c.state()["chapter"] == 1 and c.state()["chapters_done"] == [0, 1]
    # resume: k == n -> finished; k in the middle -> play chapter k; k == 0 -> intro
    c2 = make_campaign(tmp)
    assert c2.state()["phase"] == "finished" and c2.state()["healed"] == [5] and c2.state()["wand_id"] == "0x1"
    (Path(tmp) / "state" / "progress.json").write_text(json.dumps(dict(p, chapters_done=[0])))
    c3 = make_campaign(tmp)
    assert c3.state()["phase"] == "play" and c3.state()["chapter"] == 1
    (Path(tmp) / "state" / "progress.json").write_text(json.dumps(dict(p, chapters_done=[])))
    assert make_campaign(tmp).state()["phase"] == "intro"
    # corrupt / foreign progress -> one stderr line, fresh intro
    for bad in ("{not json", json.dumps(dict(p, version=9)), json.dumps(dict(p, fingerprint="000000000000")),
                json.dumps(dict(p, chapters_done=[1])), json.dumps(dict(p, chapters_done=[0, 0])), json.dumps([1, 2])):
        (Path(tmp) / "state" / "progress.json").write_text(bad)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            cb = make_campaign(tmp)
        assert cb.state()["phase"] == "intro", bad
        assert err.getvalue().count("\n") == 1 and "starting fresh" in err.getvalue(), err.getvalue()
    # failed save -> save_error in state, hit still succeeds, cleared on the next good save
    blocker = Path(tmp) / "blocked"
    blocker.write_text("not a dir")
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        cf = make_campaign(tmp, state="blocked")
        assert cf.hit(1) == "heal" and cf.hit(1) == "heal" and cf.hit(2) == "done"
    assert cf.state()["phase"] == "map" and cf.state()["save_error"] and "save failed" in err.getvalue()
    cf.state_dir = Path(tmp) / "ok"
    cf.progress_path = cf.state_dir / "progress.json"
    cf.hit(1)
    assert cf.hit(5) == "done" and cf.state()["save_error"] is None
    # a bad chapter file names itself
    raises(lambda: make_campaign(tmp, [stations([1]), dict(stations([2]), steps=[{"station": 9, "spot": "x", "clue": "c"}])]), "ch1.json: step 0")
    # /campaign info
    (Path(tmp) / "state" / "progress.json").unlink()
    info = make_campaign(tmp).campaign_info()
    assert info["title"] == "Camp" and info["chapters"][0]["steps"][0] == {"mode": "ordered", "stations": [1]}

# ---------------------------------------------------------------- every adventure on disk is valid and winnable
for f in sorted(ADV.glob("*.json")):
    if f.name == "campaign.json":
        continue
    a = json.loads(f.read_text())
    assert a["ending"] and a["opening"], f
    g = Game(a)
    touched = set()
    for s in a["steps"]:
        mode = s.get("mode", "ordered")
        hits = ({"collect": s.get("stations"), "puzzle": s.get("pattern"),
                 "charge": [s.get("station")] * s.get("hits", 0),
                 "boss": [s.get("station")] * s.get("hp", 0)}.get(mode) or [s["station"]])
        touched.update(hits)
        for n in hits:
            r = g.hit(n)
            assert r in ("heal", "done"), (f, s, n, r)
    assert touched and touched <= {1, 2, 3, 4, 5}, f
    assert g.state()["done"], f
campaign_file = ADV / "campaign.json"
if campaign_file.exists():
    with tempfile.TemporaryDirectory() as tmp:
        c = Campaign(json.loads(campaign_file.read_text()), campaign_file, tmp)
        assert c.state()["phase"] == "intro" and len(c.chapters) == 5
        assert sorted(l["chapter"] for l in c.lands) == [0, 1, 2, 3, 4]
print("ok")
