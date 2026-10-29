"""Build offline story narration from campaign JSON using installed macOS voices.

    python3 hub/build_narration.py
    python3 hub/build_narration.py --check

No API, network, credentials, or recordings. Existing content-hashed clips are
reused; the manifest is rewritten atomically after every required clip exists.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
VOICE = "Samantha"
RATE = 155


def passages():
    cfg = json.loads((HERE / "adventures/campaign.json").read_text())
    yield "intro", cfg["intro"]
    if cfg.get("tutorial"):
        tutorial = json.loads((HERE / "adventures" / cfg["tutorial"]).read_text())
        for index, beat in enumerate(tutorial["steps"]):
            yield f"tutorial:beat:{index}", beat.get("dialogue", beat["clue"])
        yield "tutorial:ending", tutorial["ending"]
    chapters = [json.loads((HERE / "adventures" / name).read_text()) for name in cfg["chapters"]]
    for chapter, adventure in enumerate(chapters):
        for index, beat in enumerate(adventure["steps"]):
            yield f"chapter:{chapter}:beat:{index}", beat.get("dialogue", beat["clue"])
        yield f"chapter:{chapter}:ending", adventure["ending"]
    yield "finished", chapters[-1]["ending"]


def digest(text):
    return hashlib.sha256(f"{VOICE}\n{RATE}\n{text}".encode()).hexdigest()[:20]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = HERE / "static/audio"
    manifest_path = output / "manifest.json"
    entries = {}
    for key, text in passages():
        entries[key] = {"text": text, "file": f"audio/{digest(text)}.mp3"}
    manifest = {"version": 1, "voice": VOICE, "rate": RATE, "generator": "macOS say; ffmpeg MP3", "entries": entries}
    if args.check:
        actual = json.loads(manifest_path.read_text())
        assert actual == manifest, "Narration manifest is stale; run python3 hub/build_narration.py"
        for entry in entries.values():
            clip = HERE / "static" / entry["file"]
            assert clip.exists() and clip.stat().st_size > 1000, f"Missing narration: {clip}"
        print(f"narration check ok: {len(entries)} passages, {len(set(v['file'] for v in entries.values()))} unique clips")
        return
    ffmpeg = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
    output.mkdir(parents=True, exist_ok=True)
    made = 0
    with tempfile.TemporaryDirectory(prefix="heartlight-narration-") as tmp:
        for key, entry in entries.items():
            clip = HERE / "static" / entry["file"]
            if clip.exists() and clip.stat().st_size > 1000:
                continue
            aiff = Path(tmp) / "voice.aiff"
            subprocess.run(["/usr/bin/say", "-v", VOICE, "-r", str(RATE), "-o", str(aiff), entry["text"]], check=True, capture_output=True)
            pending = Path(tmp) / "voice.mp3"
            subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(aiff), "-af", "loudnorm=I=-18:TP=-2:LRA=7", "-ar", "44100", "-ac", "1", "-codec:a", "libmp3lame", "-b:a", "96k", str(pending)], check=True, capture_output=True)
            if pending.stat().st_size <= 1000:
                raise RuntimeError("macOS voice service returned empty audio; rerun with local voice-service permission")
            shutil.copyfile(pending, clip)
            made += 1
            print(f"narration {made}: {key}", flush=True)
    pending_manifest = manifest_path.with_suffix(".tmp")
    pending_manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    pending_manifest.replace(manifest_path)
    print(f"narration ready: {len(entries)} passages; {made} clips generated")


if __name__ == "__main__":
    main()
