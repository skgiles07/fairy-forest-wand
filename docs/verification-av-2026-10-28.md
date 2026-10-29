# Voice and Blender assets — verification, 2026-10-28

- Narration: 59 passages and 58 local MP3s; manifest check passed. Browser replay on the family server showed `paused=false`, `readyState=4`, `muted=false`, advancing playback, a 7.64-second duration, and no media error. Replay did not advance the story.
- Three original GLBs were built through the local Blender MCP connection in safe mode. Authoring details: `assets/blender/README.md`. Setup receipts: `/Users/scottgiles/Projects/tooling/mcp-for-blender-local-setup/README.md`.
- Browser checks used isolated port 8001 and separate game progress. Each GLB loaded into a real model-viewer canvas and played its four-second animation: Moon Crystal floating, Elder Tree swaying, Treasure Chest opening. The actual animation clock advanced; Motion off paused playback.
- Full browser campaign passed: five chapters, three sensors, dialogue, hunts, forging, puzzles, boss encounter, and saved ending. No page errors. Receipt: `/var/folders/84/jd4cn9815cvf7c2wzg83wzxw0000gn/T/hub-verify-5z_zujtv/server.log`.
- Narration and motion lifecycle tests pass. Backend tests and the narration manifest check also pass.
- The external fairy-video pilot failed; no video clip is shipped. Live 3D landmarks are complete. Mentor illustrations are not rigged and have no lip-sync. Physical sensors remain untested.
- Voice and Blender changes remain local and uncommitted. Earlier game commit `ec98060` remains on origin/main.
