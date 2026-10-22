"""Fairy Forest hub. Stdlib only.

    python3 hub/server.py [adventures/fairy-forest.json] [--port 8000]

TV page:   http://<this-mac-ip>:8000/
Stations:  POST /hit  {"station": 3, "wand_id": "0xDEADBEEF"}
Reset:     POST /reset
State:     GET  /state   (TV page polls this)
"""
import json
import sys
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

HERE = Path(__file__).parent


class Game:
    def __init__(self, adventure):
        self.adventure = adventure
        self.lock = threading.Lock()
        self.reset()

    def reset(self):
        self.step = 0           # index into steps
        self.healed = []        # station numbers in order healed
        self.last_event = None  # "heal" | "wrong" | "done", cleared by TV page
        self.seq = 0            # bumps on every event so the page can diff

    def hit(self, station):
        with self.lock:
            steps = self.adventure["steps"]
            if self.step >= len(steps):
                return "done"
            expected = steps[self.step]["station"]
            if station == expected:
                self.healed.append(station)
                self.step += 1
                self.last_event = "done" if self.step >= len(steps) else "heal"
            else:
                self.last_event = "wrong"
            self.seq += 1
            return self.last_event

    def state(self):
        steps = self.adventure["steps"]
        done = self.step >= len(steps)
        return {
            "title": self.adventure["title"],
            "stations": [s["station"] for s in steps],
            "spots": {s["station"]: s["spot"] for s in steps},
            "healed": self.healed,
            "done": done,
            "message": self.adventure["ending"] if done
                       else (self.adventure["opening"] if self.step == 0 else None),
            "clue": None if done else steps[self.step]["clue"],
            "not_yet": self.adventure["not_yet"],
            "event": self.last_event,
            "seq": self.seq,
        }


class Handler(SimpleHTTPRequestHandler):
    game = None

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(HERE / "static"), **kw)

    def log_message(self, fmt, *args):
        if self.path != "/state":  # polling is noise
            super().log_message(fmt, *args)

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/state":
            return self._json(self.game.state())
        if self.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(n) or b"{}")
        if self.path == "/hit":
            try:
                station = int(body.get("station"))
            except (TypeError, ValueError):
                return self._json({"error": "station must be an int"}, 400)
            result = self.game.hit(station)
            print(f"hit station={station} wand={body.get('wand_id')} -> {result}")
            return self._json({"result": result})
        if self.path == "/reset":
            with self.game.lock:
                self.game.reset()
            print("reset")
            return self._json({"ok": True})
        return self._json({"error": "unknown"}, 404)


def main(argv):
    port = 8000
    adv = HERE / "adventures" / "fairy-forest.json"
    args = list(argv)
    if "--port" in args:
        i = args.index("--port")
        port = int(args[i + 1])
        del args[i:i + 2]
    if args:
        adv = Path(args[0])
    Handler.game = Game(json.loads(adv.read_text()))
    print(f"{Handler.game.adventure['title']}  ->  http://0.0.0.0:{port}/")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main(sys.argv[1:])
