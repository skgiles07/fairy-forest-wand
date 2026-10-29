"""Self-driving browser walkthrough. Stdlib only.

    python3 hub/verify.py [hub/adventures/campaign.json] [--keep] [--budget 180000]

Starts server.py --debug on a free port with a TEMP state dir (family
progress in hub/state/ is never read or written), runs headless Chrome
against /?autoplay=1, and greps the captured server stderr for exactly one
"[page] pass:" line and zero "[page] error:" lines. Prints "verify ok" or
the first failing line. Always kills the server. Exit code 0 on ok.
"""
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
CHROME_CANDIDATES = [
    os.environ.get("CHROME"),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    shutil.which("google-chrome"), shutil.which("chromium"), shutil.which("chromium-browser"),
]


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main(argv):
    args = list(argv)
    keep = "--keep" in args
    if keep:
        args.remove("--keep")
    training = "--training" in args
    if training:
        args.remove("--training")
    shot = stop_at = None
    for flag in ("--shot", "--stop-at"):
        if flag in args:
            i = args.index(flag)
            if flag == "--shot":
                shot = args[i + 1]
            else:
                stop_at = args[i + 1]
            del args[i:i + 2]
    budget = 180000
    if "--budget" in args:
        i = args.index("--budget")
        budget = int(args[i + 1])
        del args[i:i + 2]
    campaign = Path(args[0]) if args else HERE / "adventures" / "campaign.json"
    progress_file = json.loads(campaign.read_text()).get("progress_file", "progress.json")
    chrome = next((c for c in CHROME_CANDIDATES if c and Path(c).exists()), None)
    if not chrome:
        print("verify FAIL: no Chrome found (set CHROME=/path/to/chrome)")
        return 2

    tmp = Path(tempfile.mkdtemp(prefix="hub-verify-"))
    state_dir = tmp / "state"
    port = free_port()
    log = open(tmp / "server.log", "w+")
    server = subprocess.Popen(
        [sys.executable, "-u", str(HERE / "server.py"), str(campaign), "--port", str(port),
         "--state-dir", str(state_dir), "--debug"],
        stdout=log, stderr=subprocess.STDOUT, cwd=str(HERE.parent))
    url = f"http://127.0.0.1:{port}"
    try:
        for _ in range(100):
            try:
                with urllib.request.urlopen(url + "/state", timeout=1) as r:
                    if r.status == 200:
                        break
            except Exception:
                if server.poll() is not None:
                    break
                time.sleep(0.1)
        else:
            raise SystemExit("verify FAIL: server never answered /state")
        if server.poll() is not None:
            log.seek(0)
            print("verify FAIL: server exited early\n" + log.read()[-2000:])
            return 1

        dom = tmp / "dom.html"
        cmd = [chrome, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
               "--autoplay-policy=no-user-gesture-required", "--mute-audio",
               f"--user-data-dir={tmp / 'chrome'}", f"--virtual-time-budget={budget}",
               "--window-size=1920,1080", "--hide-scrollbars"]
        if shot:
            Path(shot).parent.mkdir(parents=True, exist_ok=True)
            cmd += [f"--screenshot={Path(shot).resolve()}", f"{url}/?autoplay={'training' if training else '1'}&stop_at={stop_at or 'map'}"]
        else:
            cmd += ["--dump-dom", f"{url}/?autoplay={'training' if training else '1'}"]
        with open(dom, "w") as out, open(tmp / "chrome.log", "w") as cerr:
            try:
                subprocess.run(cmd, stdout=out, stderr=cerr, timeout=max(120, budget // 500))
            except subprocess.TimeoutExpired:
                print("verify FAIL: Chrome timed out (wall clock)")
        time.sleep(0.5)
        log.flush()
        log.seek(0)
        lines = log.read().splitlines()
        page = [l for l in lines if l.startswith("[page] ")]
        passes = [l for l in page if l.startswith("[page] pass:")]
        fails = [l for l in page if l.startswith("[page] fail:")]
        errors = [l for l in page if l.startswith("[page] error:")]
        dom_result = ""
        if dom.exists():
            txt = dom.read_text(errors="replace")
            i = txt.find('id="autoplay-result"')
            if i >= 0:
                j = txt.find(">", i)
                dom_result = txt[j + 1: txt.find("<", j)].strip()
        print(f"temp dir: {tmp}  (progress: {state_dir / progress_file})")
        if errors:
            print("verify FAIL: " + errors[0])
            rc = 1
        elif fails:
            print("verify FAIL: " + fails[0])
            rc = 1
        elif len(passes) != 1:
            print(f"verify FAIL: expected exactly one pass line, got {len(passes)}; dom: {dom_result or '(none)'}")
            for l in page[:10]:
                print("  " + l)
            if not page:
                print("  (no /log lines at all: headless Chrome did not run the page JS)")
            rc = 1
        else:
            print(passes[0])
            if shot:
                print(f"screenshot: {shot} ({Path(shot).stat().st_size if Path(shot).exists() else 0} bytes)")
            p = state_dir / progress_file
            if p.exists():
                d = json.loads(p.read_text())
                print(f"checkpoint: chapters_done={d.get('chapters_done')} fingerprint={d.get('fingerprint')}")
            print("verify ok")
            rc = 0
        if not keep and rc == 0:
            shutil.rmtree(tmp, ignore_errors=True)
        return rc
    finally:
        if server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
        log.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
