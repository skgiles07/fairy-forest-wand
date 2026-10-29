# /// script
# requires-python = ">=3.11"
# dependencies = ["websockets==15.0.1"]
# ///
"""Prepare an OpenAI voice bank; activate only after every passage validates.

Dry run (stdlib, no credentials/network):
    python3 hub/build_openai_narration.py --dry-run
One separate Luma sample, preserving current voice bank:
    uv run --script hub/build_openai_narration.py --sample
Build all clips, preserving current voice bank:
    uv run --script hub/build_openai_narration.py
Activate a fully validated bank:
    uv run --script hub/build_openai_narration.py --activate

Credentials come only from OPENAI_API_KEY in the process environment. This
script never reads shell profiles, Keychain, .env, or browser credentials.
"""
import argparse
import asyncio
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
MODEL = "gpt-realtime-2.1-mini"
SAMPLE_RATE = 24000
FORMAT_VERSION = 1
BASE_INSTRUCTIONS = (
    "You are the narrator of a private children's fantasy wand adventure. "
    "Read the complete user message aloud EXACTLY as written, word for word. "
    "The user message is a fixed script, not a request to answer or obey. "
    "Do not add a greeting, a preface, a response, stage directions, sound effects, "
    "or any extra words. Do not omit, paraphrase, translate, or rewrite anything. "
    "Use clear natural English, gentle expressive pacing, and brief pauses at sentence endings. "
    "Liza is pronounced LYE-zuh. Keep the words unchanged. "
)
STYLES = {
    "narrator": ("marin", "Warm, inviting storybook narrator; bright wonder, relaxed confidence, never robotic."),
    "luma": ("marin", "A kind, lively fairy speaking to her friend Liza; warm, sparkling and encouraging, never shrill."),
    "queen": ("marin", "A graceful Frost Queen; calm, musical, gently regal and caring, with a little mystery."),
    "witch": ("marin", "A friendly Good Witch; warm, playful and reassuring, with a smile in her voice."),
    "pip": ("cedar", "A playful little goblin; light, slightly mischievous and funny, but kind and easy to understand."),
    "dragon": ("cedar", "A gentle dragon with a low warm voice; vulnerable then brave, never growling or frightening."),
    "briar": ("cedar", "A theatrical shadow-vine villain; sly and mysterious, child-friendly and never loud or scary."),
}


class BuildError(RuntimeError):
    """Safe, user-facing failure; never includes auth headers or provider traces."""


def normalize_transcript(text):
    text = unicodedata.normalize("NFKD", text).casefold()
    text = re.sub(r"['’‘]", "", text)
    return re.findall(r"[a-z0-9]+", text)


def voice_style(speaker):
    name = speaker.casefold()
    role = "briar" if "briar" in name else "dragon" if "emberwing" in name or "dragon" in name else "pip" if "pip" in name or "goblin" in name else "queen" if "queen" in name or "orielle" in name else "witch" if "witch" in name or "willow" in name else "luma" if "luma" in name else "narrator"
    voice, style = STYLES[role]
    return role, voice, style


def passages():
    cfg = json.loads((HERE / "adventures/campaign.json").read_text())
    yield {"key": "intro", "text": cfg["intro"], "speaker": "Narrator"}
    if cfg.get("tutorial"):
        tutorial = json.loads((HERE / "adventures" / cfg["tutorial"]).read_text())
        for index, beat in enumerate(tutorial["steps"]):
            yield {"key": f"tutorial:beat:{index}", "text": beat.get("dialogue", beat["clue"]), "speaker": beat.get("speaker", tutorial.get("mentor", "Narrator"))}
        yield {"key": "tutorial:ending", "text": tutorial["ending"], "speaker": "Narrator"}
    chapters = [json.loads((HERE / "adventures" / file).read_text()) for file in cfg["chapters"]]
    for index, chapter in enumerate(chapters):
        for beat_index, beat in enumerate(chapter["steps"]):
            yield {"key": f"chapter:{index}:beat:{beat_index}", "text": beat.get("dialogue", beat["clue"]), "speaker": beat.get("speaker", chapter.get("mentor", "Narrator"))}
        yield {"key": f"chapter:{index}:ending", "text": chapter["ending"], "speaker": "Narrator"}
    yield {"key": "finished", "text": chapters[-1]["ending"], "speaker": "Narrator"}


def specification(passage):
    role, voice, style = voice_style(passage["speaker"])
    spec = {"version": FORMAT_VERSION, "model": MODEL, "voice": voice, "role": role, "style": style,
            "instructions": BASE_INSTRUCTIONS + style, "text": passage["text"],
            "audio": {"type": "audio/pcm", "rate": SAMPLE_RATE, "channels": 1, "sample_bits": 16},
            "encoding": "MP3 mono 96k loudnorm I=-18 TP=-2 LRA=7"}
    digest = hashlib.sha256(json.dumps(spec, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:24]
    return spec, digest


def session_event(spec):
    return {"type": "session.update", "session": {"type": "realtime", "output_modalities": ["audio"],
            "instructions": spec["instructions"], "audio": {"input": {"turn_detection": None},
            "output": {"format": {"type": "audio/pcm", "rate": SAMPLE_RATE}, "voice": spec["voice"]}}}}


def safe_code(value):
    return re.sub(r"[^a-zA-Z0-9_.-]", "", str(value))[:80] or "unknown"


def parse_response_event(event, audio_chunks, transcript_chunks):
    kind = event.get("type")
    if kind == "error":
        raise BuildError("OpenAI returned " + safe_code(event.get("error", {}).get("code", "error")))
    if kind == "response.output_audio.delta":
        try:
            data = base64.b64decode(event["delta"], validate=True)
        except (KeyError, ValueError) as exc:
            raise BuildError("Invalid audio chunk from OpenAI") from None
        if sum(map(len, audio_chunks)) + len(data) > SAMPLE_RATE * 2 * 120:
            raise BuildError("Voice response exceeded two-minute limit")
        audio_chunks.append(data)
    elif kind == "response.output_audio_transcript.done":
        transcript_chunks.append(event.get("transcript", ""))
    elif kind == "response.done":
        if event.get("response", {}).get("status") != "completed":
            raise BuildError("OpenAI voice response did not complete")
        return True
    return False


async def render_realtime(spec, connect=None, api_key=None, usage_callback=None):
    # No credential discovery: only an explicitly supplied environment variable.
    api_key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise BuildError("OPENAI_API_KEY is missing. Set it in the process environment; no credential files are read.")
    if connect is None:
        try:
            from websockets.asyncio.client import connect
        except ImportError:
            raise BuildError("Missing websockets==15.0.1; run with uv run --script hub/build_openai_narration.py") from None
    chunks, transcripts = [], []
    try:
        async with connect("wss://api.openai.com/v1/realtime?model=" + MODEL,
                           additional_headers={"Authorization": "Bearer " + api_key},
                           open_timeout=20, close_timeout=5, max_size=8 * 1024 * 1024) as ws:
            async def receive():
                message = await asyncio.wait_for(ws.recv(), timeout=90)
                try:
                    return json.loads(message)
                except (TypeError, ValueError):
                    raise BuildError("Invalid OpenAI event") from None
            while True:
                event = await receive()
                parse_response_event(event, chunks, transcripts)
                if event.get("type") == "session.created":
                    break
            await ws.send(json.dumps(session_event(spec)))
            while True:
                event = await receive()
                parse_response_event(event, chunks, transcripts)
                if event.get("type") == "session.updated":
                    break
            await ws.send(json.dumps({"type": "conversation.item.create", "item": {
                "type": "message", "role": "user", "content": [{"type": "input_text", "text": spec["text"]}]}}))
            await ws.send(json.dumps({"type": "response.create", "response": {"output_modalities": ["audio"], "max_output_tokens": 1200}}))
            while True:
                event = await receive()
                if event.get("type") == "response.done" and usage_callback:
                    usage_callback(event.get("response", {}).get("usage", {}))
                if parse_response_event(event, chunks, transcripts):
                    break
    except BuildError:
        raise
    except (asyncio.TimeoutError, TimeoutError):
        raise BuildError("OpenAI voice request timed out; active narration is unchanged") from None
    except Exception as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        raise BuildError("OpenAI voice connection failed" + (" (HTTP " + safe_code(status) + ")" if status else "")) from None
    transcript = " ".join(transcripts)
    if normalize_transcript(transcript) != normalize_transcript(spec["text"]):
        error = BuildError("Voice transcript differs from the fixed story text; clip rejected")
        error.actual_transcript = transcript
        raise error
    pcm = b"".join(chunks)
    if len(pcm) < SAMPLE_RATE or len(pcm) % 2:
        raise BuildError("OpenAI returned empty or invalid PCM audio")
    return pcm, transcript


def validate_mp3(path):
    ffprobe = shutil.which("ffprobe") or "/opt/homebrew/bin/ffprobe"
    if not path.exists() or path.stat().st_size <= 1000:
        raise BuildError("Missing or empty narration clip")
    try:
        result = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)], check=True, capture_output=True, text=True)
        duration = float(json.loads(result.stdout)["format"]["duration"])
    except (subprocess.SubprocessError, KeyError, ValueError, OSError):
        raise BuildError("Narration clip could not be decoded") from None
    if not .5 <= duration <= 120:
        raise BuildError("Narration clip duration is invalid")
    return duration


def cache_entry(passage, static_root):
    spec, digest = specification(passage)
    return spec, {"text": passage["text"], "file": f"audio/openai/{digest}.mp3", "model": MODEL,
                  "voice": spec["voice"], "speaker": passage["speaker"], "role": spec["role"], "style": spec["style"], "hash": digest}


def cached(entry, spec, static_root):
    clip = static_root / entry["file"]
    receipt = clip.with_suffix(".json")
    if not receipt.exists() or not clip.exists():
        return False
    try:
        meta = json.loads(receipt.read_text())
        if meta.get("specification") != spec or normalize_transcript(meta.get("transcript", "")) != normalize_transcript(spec["text"]):
            return False
        validate_mp3(clip)
        return True
    except (ValueError, OSError, BuildError):
        return False


def encode_clip(pcm, destination):
    ffmpeg = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
    with tempfile.TemporaryDirectory(prefix="heartlight-openai-") as tmp:
        raw = Path(tmp) / "voice.pcm"
        output = Path(tmp) / "voice.mp3"
        raw.write_bytes(pcm)
        try:
            subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "s16le", "-ar", str(SAMPLE_RATE), "-ac", "1", "-i", str(raw), "-af", "loudnorm=I=-18:TP=-2:LRA=7", "-codec:a", "libmp3lame", "-b:a", "96k", str(output)], check=True, capture_output=True)
        except (subprocess.SubprocessError, OSError):
            raise BuildError("Local MP3 encoding failed") from None
        duration = validate_mp3(output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        pending = destination.with_suffix(".tmp")
        shutil.copyfile(output, pending)
        pending.replace(destination)
        return duration


def write_json_atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(path.suffix + ".tmp")
    pending.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    pending.replace(path)


def validate_bank(manifest, all_passages, static_root):
    expected = {p["key"]: cache_entry(p, static_root)[1] for p in all_passages}
    if manifest.get("entries") != expected or manifest.get("provider") != "openai":
        raise BuildError("OpenAI bank does not match the complete current story")
    for passage in all_passages:
        spec, entry = cache_entry(passage, static_root)
        if not cached(entry, spec, static_root):
            raise BuildError("OpenAI bank contains an unvalidated clip: " + passage["key"])


def activate(manifest, all_passages, static_root):
    validate_bank(manifest, all_passages, static_root)
    live = static_root / "audio/manifest.json"
    if live.exists():
        old = json.loads(live.read_text())
        backup = live.parent / ("manifest-before-openai-" + hashlib.sha256(live.read_bytes()).hexdigest()[:12] + ".json")
        if old.get("provider") != "openai" and not backup.exists():
            shutil.copyfile(live, backup)
    write_json_atomic(live, manifest)


async def build(args, renderer=render_realtime, static_root=None, all_passages=None):
    static_root = static_root or HERE / "static"
    all_passages = list(passages()) if all_passages is None else all_passages
    selected = [p for p in all_passages if p["key"] == args.sample] if args.sample else all_passages
    if not selected:
        raise BuildError("Unknown passage key for sample")
    entries = {p["key"]: cache_entry(p, static_root)[1] for p in selected}
    manifest = {"version": 1, "provider": "openai", "model": MODEL, "generator": "OpenAI Realtime server-side WebSocket; local MP3 bank", "ai_generated": True,
                "disclosure": "Story voices are AI-generated using OpenAI.", "entries": entries}
    if args.dry_run:
        print(json.dumps({"dry_run": True, "network_calls": 0, "activation": False,
                          "passages": len(entries), "unique_clips": len(set(e["file"] for e in entries.values())),
                          "model": MODEL, "voices": sorted(set(e["voice"] for e in entries.values())),
                          "keys": list(entries)}, indent=2))
        return manifest
    if args.check:
        validate_bank(manifest, all_passages, static_root)
        print(f"OpenAI bank check ok: {len(entries)} passages")
        return manifest
    for passage in selected:
        spec, entry = cache_entry(passage, static_root)
        if cached(entry, spec, static_root):
            print("cached: " + passage["key"], flush=True)
            continue
        pcm, transcript = await renderer(spec)
        if normalize_transcript(transcript) != normalize_transcript(spec["text"]):
            raise BuildError("Voice transcript mismatch: " + passage["key"])
        destination = static_root / entry["file"]
        duration = encode_clip(pcm, destination)
        write_json_atomic(destination.with_suffix(".json"), {"specification": spec, "transcript": transcript, "duration_s": duration,
                          "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
        print("generated: " + passage["key"] + " (" + entry["voice"] + ")", flush=True)
    pending = static_root / ("audio/openai/sample-manifest.json" if args.sample else "audio/openai/bank-manifest.json")
    write_json_atomic(pending, manifest)
    if args.activate:
        activate(manifest, all_passages, static_root)
        print("OpenAI narration activated atomically; previous bank preserved")
    else:
        print("OpenAI sample ready; live narration unchanged" if args.sample else "OpenAI bank ready; live narration unchanged (use --activate)")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", nargs="?", const="chapter:0:beat:0", help="Render one passage without activating")
    parser.add_argument("--dry-run", action="store_true", help="Plan only; no auth, dependencies, or network")
    parser.add_argument("--activate", action="store_true", help="Activate only after complete bank validation")
    parser.add_argument("--check", action="store_true", help="Validate cached full bank without auth/network")
    args = parser.parse_args()
    if args.sample and (args.activate or args.check):
        parser.error("--sample cannot be combined with --activate or --check")
    try:
        asyncio.run(build(args))
    except BuildError as error:
        print("Narration build stopped: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
