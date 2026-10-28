"""Fairy Forest hub. Stdlib only.

    python3 hub/server.py [adventures/campaign.json] [--port 8000]
                          [--state-dir hub/state] [--debug]

TV page:   http://<this-mac-ip>:8000/
Stations:  POST /hit  {"station": 3, "wand_id": "0xDEADBEEF"}  -> heal | wrong | done
Reset:     POST /reset            (chapter)   POST /reset?campaign=1  (wipe progress)
Next:      POST /next {"gen": n}  (leave the realm map early)
State:     GET  /state            (TV page polls this; non-consuming)
Campaign:  GET  /campaign         (chapter list with step modes, read-only)
Log:       POST /log {"level": "error"|"pass"|"fail", "msg": ".."}  (page -> stderr)
Debug:     POST /debug/expire     (only with --debug: force the live timer to expire)
"""
import hashlib
import json
import os
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

HERE = Path(__file__).parent
MODES = ("ordered", "collect", "puzzle", "charge", "boss")
MAP_SECONDS = 20
PROGRESS_VERSION = 1


def _stations_of(step):
    """Stations a step touches, in step order (puzzle may repeat)."""
    mode = step.get("mode", "ordered")
    if mode == "collect":
        return list(step["stations"])
    if mode == "puzzle":
        return list(step["pattern"])
    return [step["station"]]


def _label(step, n):
    spots = step.get("spots") or {}
    return spots.get(str(n)) or spots.get(n) or (step.get("spot") if len(set(_stations_of(step))) == 1 else None)


class Game:
    """One chapter. hit() returns exactly heal | wrong | done; everything richer is in state()."""

    def __init__(self, adventure, counters=None, now=time.monotonic):
        self.adventure = adventure
        self.steps = adventure.get("steps")
        self._validate()
        self.c = counters if counters is not None else {"rev": 0, "gen": 0}
        self.now = now
        self.lock = threading.Lock()
        self.wand_id = None
        self.reset()

    # --- schema ---
    def _validate(self):
        if not isinstance(self.steps, list) or not self.steps:
            raise ValueError("steps: must be a non-empty list")
        for i, s in enumerate(self.steps):
            p = f"step {i}: "
            mode = s.get("mode", "ordered")
            if mode not in MODES:
                raise ValueError(p + f"unknown mode {mode!r}")
            if not s.get("clue"):
                raise ValueError(p + "missing clue")

            def station(n):
                if not isinstance(n, int) or isinstance(n, bool) or not 1 <= n <= 5:
                    raise ValueError(p + f"station {n!r} not in 1-5")
            if mode == "collect":
                st = s.get("stations")
                if not isinstance(st, list) or not 2 <= len(st) <= 5:
                    raise ValueError(p + "collect.stations must list 2-5 stations")
                if len(set(st)) != len(st):
                    raise ValueError(p + "collect.stations must be unique")
                for n in st:
                    station(n)
            elif mode == "puzzle":
                pat = s.get("pattern")
                if not isinstance(pat, list) or not pat:
                    raise ValueError(p + "puzzle.pattern must be non-empty")
                for n in pat:
                    station(n)
            else:
                station(s.get("station"))
                if mode == "charge":
                    h = s.get("hits")
                    if not isinstance(h, int) or isinstance(h, bool) or h < 1:
                        raise ValueError(p + "charge.hits must be a positive int")
                if mode == "boss":
                    hp = s.get("hp")
                    if not isinstance(hp, int) or isinstance(hp, bool) or hp < 1:
                        raise ValueError(p + "boss.hp must be a positive int")
                    w = s.get("window_s", 90)
                    if isinstance(w, bool) or not isinstance(w, (int, float)) or w <= 0:
                        raise ValueError(p + "boss.window_s must be a positive number")
            for n in set(_stations_of(s)):
                if not _label(s, n):
                    raise ValueError(p + f"station {n} has no label (spot / spots)")

    # --- lifecycle ---
    def reset(self):
        self.step = 0
        self.healed = []            # stations of completed steps, in order
        self.event = None           # heal | wrong | done | None
        self.event_station = None
        self.fire_seq = 0
        self.last_step = None
        self._enter_step()
        self.c["gen"] += 1
        self.c["rev"] += 1

    def complete(self):
        """Mark every step done (used when a finished campaign is resumed)."""
        for s in self.steps:
            for n in _stations_of(s):
                if n not in self.healed:
                    self.healed.append(n)
        self.step = len(self.steps)
        self._enter_step()

    def _cur(self):
        return self.steps[self.step] if self.step < len(self.steps) else None

    def _enter_step(self):
        s = self._cur()
        self.items = []
        self.pattern_pos = 0
        self.charge = 0
        self.hp = None
        self.boss_deadline = None
        if s and s.get("mode") == "boss":
            self.hp = s["hp"]
            self.boss_deadline = self.now() + s.get("window_s", 90)

    def _tick(self):
        """Boss window: past the deadline the dragon regrows 2 leaves. Never changes a hit result."""
        s = self._cur()
        if s and s.get("mode") == "boss" and self.hp > 0 and self.now() >= self.boss_deadline:
            self.hp = min(self.hp + 2, s["hp"])
            self.boss_deadline = self.now() + s.get("window_s", 90)
            self.fire_seq += 1
            self.c["rev"] += 1

    def expire(self):
        """--debug only: make the boss window expire on the next evaluation."""
        with self.lock:
            if self.boss_deadline is not None:
                self.boss_deadline = self.now() - 1
                return "boss"
            return None

    def _snapshot(self, s):
        return {
            "mode": s.get("mode", "ordered"), "stations": _stations_of(s),
            "station": s.get("station"), "items": sorted(self.items),
            "pattern": s.get("pattern"), "charge": self.charge, "charge_max": s.get("hits"),
            "hp": self.hp, "hp_max": s.get("hp"),
        }

    # --- play ---
    def hit(self, station, wand_id=None):
        with self.lock:
            return self._hit(station, wand_id)

    def _hit(self, station, wand_id=None):
        self._tick()
        if wand_id is not None:
            self.wand_id = wand_id
        s = self._cur()
        if s is None:
            return "done"
        self.last_step = None
        mode = s.get("mode", "ordered")
        ok = advance = False
        if mode == "ordered":
            ok = advance = station == s["station"]
        elif mode == "collect":
            if station in s["stations"]:
                ok = True
                if station not in self.items:
                    self.items.append(station)
                advance = len(self.items) == len(s["stations"])
        elif mode == "puzzle":
            pat = s["pattern"]
            if station == pat[self.pattern_pos]:
                ok = True
                self.pattern_pos += 1
                advance = self.pattern_pos >= len(pat)
            else:
                self.pattern_pos = 0
        elif mode == "charge":
            if station == s["station"]:
                ok = True
                self.charge += 1
                advance = self.charge >= s["hits"]
        elif mode == "boss":
            if station == s["station"]:
                ok = True
                self.hp -= 1
                self.boss_deadline = self.now() + s.get("window_s", 90)
                advance = self.hp <= 0
        self.event_station = station
        if not ok:
            self.event = "wrong"
        elif advance:
            self.last_step = self._snapshot(s)
            for n in _stations_of(s):
                if n not in self.healed:
                    self.healed.append(n)
            self.step += 1
            self._enter_step()
            self.event = "done" if self.step >= len(self.steps) else "heal"
        else:
            self.event = "heal"
        self.c["rev"] += 1
        return self.event

    def next(self, gen=None):
        return {"ok": True}

    def reset_request(self, campaign=False):
        with self.lock:
            self.reset()
        return {"ok": True}

    def campaign_info(self):
        return {"title": self.adventure["title"], "chapters": [chapter_info(self.adventure)], "lands": []}

    # --- read ---
    def state(self):
        with self.lock:
            return self._state()

    def _state(self):
        self._tick()
        a, s = self.adventure, self._cur()
        done = s is None
        mode = s.get("mode", "ordered") if s else None
        if done:
            targets = []
        elif mode == "collect":
            targets = sorted(n for n in s["stations"] if n not in self.items)
        elif mode == "puzzle":
            targets = [s["pattern"][self.pattern_pos]]
        else:
            targets = [s["station"]]
        healed = list(self.healed) + [n for n in sorted(self.items) if n not in self.healed]
        spots = {}
        for st in self.steps:
            for n in set(_stations_of(st)):
                spots[n] = _label(st, n)
        return {
            "rev": self.c["rev"], "gen": self.c["gen"], "phase": "play",
            "chapter": 0, "chapters_done": [],
            "title": a["title"], "scene": a.get("scene", "forest"),
            "opening": a.get("opening", ""), "not_yet": a.get("not_yet", ""),
            "ending": a.get("ending", ""), "cheer": a.get("cheer", "{spot} is healed!"),
            "mode": mode, "targets": targets, "healed": healed, "done": done,
            "progress": {"done": self.step, "total": len(self.steps)},
            "items": sorted(self.items),
            "pattern": s.get("pattern") if s else None, "pattern_pos": self.pattern_pos,
            "charge": self.charge, "charge_max": s.get("hits") if s else None,
            "hp": self.hp, "hp_max": s.get("hp") if s else None, "fire_seq": self.fire_seq,
            "event": self.event, "event_station": self.event_station,
            "spots": spots, "clue": None if done else s["clue"],
            "map_deadline_s": None, "wand_id": self.wand_id, "save_error": None,
            "last_step": self.last_step,
        }


def chapter_info(adv):
    return {"title": adv["title"], "scene": adv.get("scene", "forest"),
            "steps": [{"mode": s.get("mode", "ordered"), "stations": _stations_of(s)} for s in adv["steps"]]}


class Campaign:
    """Chapters + realm map + saved progress. Transition table: PLAN-CAMPAIGN.md section 4."""

    def __init__(self, cfg, path, state_dir, now=time.monotonic):
        self.title = cfg.get("title", "Magi Quest")
        self.name = Path(path).name
        base = Path(path).parent
        self.files = list(cfg["chapters"])
        raw = [(base / f).read_bytes() for f in self.files]
        self.chapters = [json.loads(b) for b in raw]
        for i, adv in enumerate(self.chapters):
            try:
                Game(adv)
            except ValueError as e:
                raise ValueError(f"{self.files[i]}: {e}")
        self.fingerprint = hashlib.sha256(b"".join(raw)).hexdigest()[:12]
        self.lands = cfg.get("map", {}).get("lands", [])
        self.state_dir = Path(state_dir)
        self.progress_path = self.state_dir / "progress.json"
        self.now = now
        self.lock = threading.Lock()
        self.c = {"rev": 0, "gen": 0}
        self.save_error = None
        self.wand_id = None
        self.map_deadline = None
        self.chapters_done = self._load_progress()
        self._resume()

    # --- progress file ---
    def _load_progress(self):
        if not self.progress_path.exists():
            return []
        try:
            d = json.loads(self.progress_path.read_text())
            if d.get("version") != PROGRESS_VERSION:
                raise ValueError("wrong version")
            if d.get("campaign") != self.name or d.get("fingerprint") != self.fingerprint:
                raise ValueError("different campaign")
            done = d.get("chapters_done")
            if done != list(range(len(done))) or len(done) > len(self.chapters):
                raise ValueError("chapters_done is not a contiguous prefix")
            self.wand_id = d.get("wand_id")
            return list(done)
        except (ValueError, TypeError, AttributeError) as e:
            print(f"progress: ignoring {self.progress_path} ({e}); starting fresh", file=sys.stderr)
            return []

    def _save_progress(self):
        d = {"version": PROGRESS_VERSION, "campaign": self.name, "fingerprint": self.fingerprint,
             "chapters_done": list(self.chapters_done), "wand_id": self.wand_id,
             "saved_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        try:
            self.state_dir.mkdir(parents=True, exist_ok=True)
            tmp = self.progress_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(d, indent=1))
            os.replace(tmp, self.progress_path)
            self.save_error = None
        except OSError as e:
            self.save_error = str(e)
            print(f"progress: save failed: {e}", file=sys.stderr)

    # --- phases ---
    def _load(self, i):
        self.chapter = i
        self.game = Game(self.chapters[i], self.c, self.now)   # bumps gen + rev
        self.game.wand_id = self.wand_id
        self.map_deadline = None

    def _set_phase(self, phase):
        self.phase = phase
        self.c["gen"] += 1
        self.c["rev"] += 1

    def _resume(self):
        k = len(self.chapters_done)
        if k == 0:
            self._load(0)
            self._set_phase("intro")
        elif k < len(self.chapters):
            self._load(k)
            self._set_phase("play")
        else:
            self._load(len(self.chapters) - 1)
            self.game.complete()
            self._set_phase("finished")

    def _advance(self):
        """intro/map -> play the next chapter, or finished."""
        nxt = 0 if self.phase == "intro" else self.chapter + 1
        if nxt < len(self.chapters):
            self._load(nxt)
            self._set_phase("play")
        else:
            self._set_phase("finished")

    def _chapter_done(self):
        if self.chapter not in self.chapters_done:
            self.chapters_done.append(self.chapter)
            self._save_progress()
        self.map_deadline = self.now() + MAP_SECONDS
        self._set_phase("map")

    def hit(self, station, wand_id=None):
        with self.lock:
            if wand_id is not None:
                self.wand_id = wand_id
            if self.phase in ("intro", "map"):
                self._advance()
                return "heal"
            if self.phase == "finished":
                return "done"
            r = self.game._hit(station, wand_id)
            if r == "done":
                self._chapter_done()
            return r

    def next(self, gen=None):
        with self.lock:
            if gen != self.c["gen"]:
                return {"ignored": True}
            if self.phase in ("intro", "map"):
                self._advance()
            return {"ok": True}

    def reset_request(self, campaign=False):
        with self.lock:
            if campaign:
                self.chapters_done = []
                self._save_progress()
                self._load(0)
                self._set_phase("intro")
            elif self.phase in ("play", "map", "finished"):
                self._load(self.chapter)
                self._set_phase("play")
            return {"ok": True}

    def expire(self):
        with self.lock:
            if self.phase == "map":
                self.map_deadline = self.now() - 1
                return "map"
            if self.phase == "play":
                return self.game.expire()
            return None

    def campaign_info(self):
        return {"title": self.title, "lands": self.lands,
                "chapters": [dict(chapter_info(a), file=f) for a, f in zip(self.chapters, self.files)]}

    def state(self):
        with self.lock:
            if self.phase == "map" and self.now() >= self.map_deadline:
                self._advance()
            st = self.game._state()
            on_map = self.phase != "play"
            nxt = 0 if self.phase == "intro" else self.chapter + 1
            lands = [dict(l, done=l.get("chapter") in self.chapters_done,
                          next=(l.get("chapter") == nxt and self.phase in ("intro", "map")))
                     for l in self.lands]
            next_land = next((l["name"] for l in lands if l["next"]), None)
            st.update({
                "rev": self.c["rev"], "gen": self.c["gen"], "phase": self.phase,
                "chapter": self.chapter, "chapters_done": list(self.chapters_done),
                "chapters_total": len(self.chapters),
                "campaign_title": self.title, "title": self.title if on_map else st["title"],
                "chapter_title": st["title"],
                "scene": "map" if on_map else st["scene"],
                "lands": lands, "next_land": next_land,
                "map_deadline_s": (max(0.0, round(self.map_deadline - self.now(), 2))
                                   if self.phase == "map" else None),
                "wand_id": self.wand_id, "save_error": self.save_error,
            })
            return st


class Handler(SimpleHTTPRequestHandler):
    game = None
    debug = False

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(HERE / "static"), **kw)

    def log_message(self, fmt, *args):
        if self.path not in ("/state", "/campaign"):  # polling is noise
            super().log_message(fmt, *args)

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/state":
            return self._json(self.game.state())
        if path == "/campaign":
            return self._json(self.game.campaign_info())
        if path == "/":
            self.path = "/index.html" + (("?" + urlsplit(self.path).query) if urlsplit(self.path).query else "")
        return super().do_GET()

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            return self._json({"error": "bad json"}, 400)
        url = urlsplit(self.path)
        q = parse_qs(url.query)
        if url.path == "/hit":
            try:
                station = int(body.get("station"))
            except (TypeError, ValueError):
                return self._json({"error": "station must be an int"}, 400)
            result = self.game.hit(station, body.get("wand_id"))
            print(f"hit station={station} wand={body.get('wand_id')} -> {result}")
            return self._json({"result": result})
        if url.path == "/reset":
            campaign = q.get("campaign", ["0"])[0] in ("1", "true", "yes")
            print("reset campaign" if campaign else "reset")
            return self._json(self.game.reset_request(campaign))
        if url.path == "/next":
            return self._json(self.game.next(body.get("gen")))
        if url.path == "/log":
            print(f"[page] {body.get('level', 'info')}: {body.get('msg', '')}", file=sys.stderr, flush=True)
            return self._json({"ok": True})
        if url.path == "/debug/expire":
            if not self.debug:
                return self._json({"error": "not in debug mode"}, 404)
            return self._json({"ok": True, "expired": self.game.expire()})
        return self._json({"error": "unknown"}, 404)


def load(path, state_dir=None):
    cfg = json.loads(Path(path).read_text())
    if "chapters" in cfg:
        return Campaign(cfg, path, state_dir or os.environ.get("HUB_STATE_DIR") or (HERE / "state"))
    return Game(cfg)


def main(argv):
    port, state_dir, debug = 8000, None, False
    adv = HERE / "adventures" / "campaign.json"
    args = list(argv)
    for flag in ("--port", "--state-dir"):
        if flag in args:
            i = args.index(flag)
            if flag == "--port":
                port = int(args[i + 1])
            else:
                state_dir = args[i + 1]
            del args[i:i + 2]
    if "--debug" in args:
        debug = True
        args.remove("--debug")
    if args:
        adv = Path(args[0])
    Handler.game = load(adv, state_dir)
    Handler.debug = debug
    title = Handler.game.title if isinstance(Handler.game, Campaign) else Handler.game.adventure["title"]
    print(f"{title}  ->  http://0.0.0.0:{port}/", flush=True)
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main(sys.argv[1:])
