# OpenAI story narration bank

Paid generation authorized October 29, 2026, with a $2 maximum. Recordings use
Marin and Cedar and replace the local Samantha bank only after complete validation.
The previous bank is preserved for rollback. See `output/openai-narration-usage.json`
for per-request provider usage and conservative reservations for unresolved requests.

## Voice direction

- **Marin:** narrator and Luma (bright, warm, natural storytelling), Frost Queen
  Orielle (calm and gently regal), Good Witch Willow (playful and reassuring).
- **Cedar:** Pip (light mischief), Emberwing (low and warm), Black Briar (gentle
  theatrical mystery). No character announcements or added words.
- Liza pronounced “LYE-zuh” is a **provisional sample direction**, not a confirmed
  family preference. Change `BASE_INSTRUCTIONS` if needed before the full bank.

Story JSON remains authoritative. Every generated transcript must match the
fixed script after case/punctuation normalization. Paraphrases, omissions,
added greetings, and failed/incomplete responses stop the build.

## Run

Dependency-free preview, no authentication or network:

```sh
python3 hub/build_openai_narration.py --dry-run
python3 -m unittest discover -s hub -p test_openai_narration.py -q
```

After credential-source and paid-generation authorization, provide
`OPENAI_API_KEY` only through the process environment. Do not paste it into
commands, documents, source files, or chat. The builder does not read shell
profiles, Keychain, `.env`, browser credentials, or any other auth files.

One Luma opening sample, saved separately and never activated:

```sh
uv run --script hub/build_openai_narration.py --sample
```

A particular script line can be selected with, for example,
`--sample chapter:1:beat:0` (Pip). Sample output is recorded in
`hub/static/audio/openai/sample-manifest.json`; its entry points to a playable
MP3. The sample manifest is **not** the live game manifest.

Build the complete bank without switching the game:

```sh
uv run --script hub/build_openai_narration.py
```

Validate cached clips without credentials or network:

```sh
python3 hub/build_openai_narration.py --check
```

Once all clips are approved, activate the validated full bank:

```sh
uv run --script hub/build_openai_narration.py --activate
```

A full cache makes activation local-only. If clips are missing, `--activate`
first generates and validates them, then switches the live manifest atomically.
Never combine `--sample` with `--activate`.

## Implementation and failure behavior

`hub/build_openai_narration.py` uses **gpt-realtime-2.1-mini** on the server-side
Realtime WebSocket API, with pinned `websockets==15.0.1` and Python 3.11+.
Text-only input requests PCM audio at 24 kHz, 16-bit mono. No microphone,
browser API key, or live conversation is involved. ffmpeg produces cached MP3s;
ffprobe validates duration and decoding.

Cache identity includes model, voice, role, acting instructions, exact story
text, PCM format, and encoding profile. Each clip has a JSON receipt with its
specification, returned transcript, and duration. Successful prior clips are
reused, while altered story text or voice instructions produces a new hash.
There are currently **72 passages and 71 unique clips**.

Network, provider, transcript, or encoding failure leaves the active manifest
untouched. Provider errors are sanitized; headers, credentials, and raw response
exceptions are not logged. No automatic retries incur surprise duplicate usage.
A content-hashed backup preserves the previous non-OpenAI manifest on activation.

Generated manifests include `ai_generated: true` and the parent-settings
wording “Story voices are AI-generated using OpenAI.” Parent settings show this disclosure.

## Current official references

Verified for this implementation on October 28, 2026:

- [Text-to-speech guidance](https://developers.openai.com/api/docs/guides/text-to-speech)
- [Realtime conversations and output events](https://developers.openai.com/api/docs/guides/realtime-conversations)
- [Server-side WebSocket authentication](https://developers.openai.com/api/docs/guides/voice-websockets)

This is a new Realtime integration, not the legacy `/audio/speech` route. The
existing local playback module needs no provider credentials: activation swaps
its manifest to already-rendered files.

## Authorized budgeted run

`uv run --with websockets==15.0.1 python hub/record_openai_bank.py` uses the existing
key explicitly authorized by Scott on October 29. The wrapper reads only the
OPENAI_API_KEY process variable or its literal assignment in ~/.zshrc, without
executing that file. The underlying reusable builder remains environment-only.
No credentials are printed, copied to the game, or stored in the project.

The wrapper serializes runs with a file lock and persists a $0.035 reservation
before each provider request. Requests are capped at 1,200 output tokens and
6,000 input UTF-8 bytes; the reservation exceeds the conservative maximum at
verified rates. Completed usage replaces the reservation with calculated token
charges; unknown or interrupted usage retains its reservation. No request starts
when its reservation would exceed the $2 cap. Failed script validation still
counts provider usage. Cached validated clips incur no new charge.

Pricing: text input $0.60/M, text output $2.40/M, audio input $10/M, audio output
$20/M tokens for gpt-realtime-2.1-mini, verified October 29, 2026. Estimates exclude
tax and unrelated account usage. Budget applies only to this narration run.

## Generation status — October 29

Complete and activated: 72 passages / 71 unique clips, Marin and Cedar. Reported token charges $0.3336332; conservative unresolved reservation $0.035 from the earlier credit-exhausted request. Total counted toward $2 ceiling: $0.3686332. Full-bank validation passed, and the live browser played an OpenAI MP3 unmuted with readyState 4 and no media error. Saved campaign checksum unchanged. Earlier credit issue resolved by user top-up.
