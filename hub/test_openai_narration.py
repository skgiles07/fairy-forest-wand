"""Offline mocked tests; never reads auth files or makes network calls."""
import argparse
import base64
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import build_openai_narration as builder


class Socket:
    def __init__(self, events):
        self.events = iter(events)
        self.sent = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def recv(self):
        return json.dumps(next(self.events))

    async def send(self, value):
        self.sent.append(json.loads(value))


def args(**kwargs):
    values = dict(sample=None, dry_run=False, activate=False, check=False)
    values.update(kwargs)
    return argparse.Namespace(**values)


def fake_encode(pcm, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(b'mocked decoded MP3' * 150)
    return 2.0


class OpenAINarrationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.passage = {"key": "chapter:0:beat:0", "text": "Liza, the light is yours!", "speaker": "Luma"}
        self.spec, _ = builder.specification(self.passage)

    def test_voice_cast_and_cache_identity(self):
        self.assertEqual(builder.voice_style("Luma")[1], "marin")
        self.assertEqual(builder.voice_style("Good Witch Willow")[1], "marin")
        self.assertEqual(builder.voice_style("Pip")[1], "cedar")
        self.assertEqual(builder.voice_style("Emberwing")[1], "cedar")
        self.assertEqual(builder.voice_style("Black Briar")[1], "cedar")
        changed = dict(self.passage, text="Another line.")
        self.assertNotEqual(builder.specification(self.passage)[1], builder.specification(changed)[1])

    def test_transcript_normalization_never_paraphrases(self):
        self.assertEqual(builder.normalize_transcript("Liza’s light!"), builder.normalize_transcript("LIZA'S LIGHT."))
        self.assertNotEqual(builder.normalize_transcript("Your light is warm."), builder.normalize_transcript("You have warm light."))

    async def test_server_websocket_protocol_and_exact_transcript(self):
        pcm = b'\x01\x02' * 24000
        socket = Socket([{"type": "session.created"}, {"type": "session.updated"},
                         {"type": "response.output_audio.delta", "delta": base64.b64encode(pcm).decode()},
                         {"type": "response.output_audio_transcript.done", "transcript": self.passage["text"]},
                         {"type": "response.done", "response": {"status": "completed"}}])
        calls = []
        def connect(url, **kwargs):
            calls.append((url, kwargs))
            return socket
        actual, transcript = await builder.render_realtime(self.spec, connect=connect, api_key="test-key-not-real")
        self.assertEqual(actual, pcm)
        self.assertEqual(transcript, self.passage["text"])
        self.assertIn("gpt-realtime-2.1-mini", calls[0][0])
        self.assertEqual(calls[0][1]["additional_headers"]["Authorization"], "Bearer test-key-not-real")
        self.assertEqual(socket.sent[0]["session"]["audio"]["output"]["voice"], "marin")
        self.assertIsNone(socket.sent[0]["session"]["audio"]["input"]["turn_detection"])
        self.assertEqual(socket.sent[1]["item"]["content"][0]["text"], self.passage["text"])
        self.assertEqual(socket.sent[2]["type"], "response.create")

    async def test_missing_environment_key_aborts_without_connection(self):
        with patch.dict(builder.os.environ, {}, clear=True):
            with self.assertRaisesRegex(builder.BuildError, "OPENAI_API_KEY is missing"):
                await builder.render_realtime(self.spec, connect=lambda *a, **k: self.fail("connected without key"))

    async def test_transcript_rewrite_rejected(self):
        socket = Socket([{"type":"session.created"},{"type":"session.updated"},
                         {"type":"response.output_audio.delta","delta":base64.b64encode(b'\0\0'*24000).decode()},
                         {"type":"response.output_audio_transcript.done","transcript":"Let me tell you a different story."},
                         {"type":"response.done","response":{"status":"completed"}}])
        with self.assertRaisesRegex(builder.BuildError, "transcript differs"):
            await builder.render_realtime(self.spec, connect=lambda *a, **k: socket, api_key="test")

    def test_incomplete_and_provider_errors_sanitized(self):
        with self.assertRaisesRegex(builder.BuildError, "did not complete"):
            builder.parse_response_event({"type":"response.done","response":{"status":"incomplete"}},[],[])
        with self.assertRaises(builder.BuildError) as caught:
            builder.parse_response_event({"type":"error","error":{"code":"invalid_request","message":"Authorization Bearer SECRET"}},[],[])
        self.assertNotIn("SECRET", str(caught.exception))
        self.assertNotIn("Bearer", str(caught.exception))

    async def test_sample_does_not_activate(self):
        async def renderer(spec):
            return b'pcm', spec["text"]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            live = root / 'audio/manifest.json'
            live.parent.mkdir()
            live.write_text('{"voice":"Samantha"}')
            original = live.read_bytes()
            with patch.object(builder, 'encode_clip', fake_encode), patch.object(builder, 'validate_mp3', return_value=2):
                await builder.build(args(sample=self.passage['key']), renderer=renderer, static_root=root, all_passages=[self.passage])
            self.assertEqual(live.read_bytes(), original)
            self.assertTrue((root/'audio/openai/sample-manifest.json').exists())

    async def test_generation_failure_preserves_live_manifest(self):
        other = dict(self.passage, key='chapter:0:beat:1', text='Bring back the star.')
        async def renderer(spec):
            if spec['text'] == other['text']:
                raise builder.BuildError('Mock generation failure')
            return b'pcm', spec['text']
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            live = root/'audio/manifest.json'; live.parent.mkdir(); live.write_text('{"voice":"Samantha"}')
            before = live.read_bytes()
            with patch.object(builder, 'encode_clip', fake_encode), patch.object(builder, 'validate_mp3', return_value=2):
                with self.assertRaisesRegex(builder.BuildError, 'Mock generation failure'):
                    await builder.build(args(activate=True), renderer=renderer, static_root=root, all_passages=[self.passage,other])
            self.assertEqual(live.read_bytes(), before)

    async def test_activation_full_validation_and_backup(self):
        async def renderer(spec):
            return b'pcm', spec['text']
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);live=root/'audio/manifest.json';live.parent.mkdir();live.write_text('{"voice":"Samantha"}')
            with patch.object(builder,'encode_clip',fake_encode),patch.object(builder,'validate_mp3',return_value=2):
                manifest=await builder.build(args(activate=True),renderer=renderer,static_root=root,all_passages=[self.passage])
                builder.validate_bank(manifest,[self.passage],root)
                missing=dict(manifest, entries={})
                with self.assertRaisesRegex(builder.BuildError,'complete current story'):
                    builder.activate(missing,[self.passage],root)
            self.assertEqual(json.loads(live.read_text())['provider'],'openai')
            self.assertEqual(len(list(live.parent.glob('manifest-before-openai-*.json'))),1)

    async def test_dry_run_no_auth_no_network_no_writes(self):
        async def renderer(spec):
            self.fail('dry run called provider')
        with tempfile.TemporaryDirectory() as temp, patch.dict(builder.os.environ,{},clear=True):
            root=Path(temp)
            await builder.build(args(dry_run=True),renderer=renderer,static_root=root,all_passages=[self.passage])
            self.assertEqual(list(root.iterdir()),[])


if __name__ == '__main__':
    unittest.main()
