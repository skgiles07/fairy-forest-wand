# Rendered motion scenes

Heartlight Quest supports rendered video scenes beneath the game interface. `motion.js` plays local video from `assets/motion/manifest.json`; the illustrated atlas remains the fallback. CSS transitions are not presented as 3D rendering.

## Initial scene

The manifest is currently empty. A five-second generated fairy-video preview failed on 2026-10-28; no completed clip was delivered or included in the game. Scott selected Blender MCP for the asset pipeline. Future Blender-rendered scenes can use this video layer, while actual animated GLB landmarks use `landmarks3d.js` and the locally bundled model-viewer runtime.

A delivered rendered scene loops with its source audio muted. Story narration remains a separate channel, so a clip never competes with the character’s spoken clue. This is ambient character/environment animation, not dialogue lip sync. A rendered clip is a flat video of a 3D scene; it is not a live 3D model, editable camera, or browser-side 3D renderer.

Only delivered, decodable clips appear. A missing file, unsupported codec, download failure, or rejected autoplay keeps the existing static scene and portrait visible. Chapters without a matching clip retain their illustrated scenes. A manifest entry alone is not evidence that its video has been delivered or decoded.

## Selection and controls

The game dispatches `game-state` after render and stores its latest state in `window.LizaGameState`. Motion consumes those events without a second game-state poll. Exact speaker-and-chapter matches take priority. A `backgroundOnly` clip can animate a chapter environment while preserving its static character. A same-speaker clip can be reused outside its chapter only when explicitly marked `crossChapter: true`; this avoids showing an unrelated character over a scene.

The **Motion** checkbox in parent settings persists locally as `liza-motion`. With no saved choice, the browser’s reduced-motion preference disables video. An explicit parent choice takes precedence. Hidden tabs pause playback; returning resumes the selected clip. Changing mentors or leaving active play tears down the old source. Repeated game revisions do not reload or restart a selected video.

The video is decorative, muted, `playsinline`, unfocusable, and behind all controls. Its portrait replaces the illustrated portrait only when both depict the same speaker. `object-fit: cover` and a scene-specific `objectPosition` keep the main character in frame at narrow widths; composition still needs visual inspection on the target TV and side panel.

## Manifest format

```json
{
  "version": 1,
  "clips": {
    "luma-pools": {
      "src": "assets/motion/luma-pools.mp4",
      "chapter": 0,
      "speakers": ["Luma"],
      "phases": ["play"],
      "objectPosition": "32% center",
      "loop": true
    }
  }
}
```

Sources must be local under `/assets/motion/`. Optional `backgroundOnly` and `crossChapter` are false unless explicitly set. Speaker names match authored story metadata; chapter indices start at zero.

## Validation

`node --check hub/static/motion.js` checks syntax. `node hub/test_motion.cjs` runs a mocked-DOM lifecycle pass covering stable source selection across 25 revisions, exact portrait matching, hidden-tab pause/resume, missing-match fallback, failed-source suppression, reduced-motion defaults, explicit override, persisted toggle, map teardown, and rejected autoplay fallback.

Actual media integration is verified separately after delivery. Read-only browser diagnostics are exposed as `window.QuestMotion.state`: selected clip, enabled state, playback state, decoder readiness, visible layer, and failed clip IDs. A real-playback check should require a nonzero `videoWidth`, `readyState >= 2`, and advancing `currentTime`; test source selection alone does not prove rendered playback.
