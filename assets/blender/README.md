# Editable Heartlight landmarks

Original Blender geometry for the three household landmarks in Liza’s Heartlight Quest. Authored entirely from procedural meshes, named materials, and transform animation; no external textures, stock models, downloads, or paid asset services.

## Files

- `build_landmarks.py`: authored scene builder, sent as source through the local Blender MCP `execute_blender_code` tool.
- `heartlight-landmarks.blend`: editable source scene containing three separate landmark collections and an unexported hero camera/light studio.
- `heartlight-landmarks-preview.png`: single rendered hero view for visual review.
- `../../hub/static/assets/models/moon-crystal.glb`: centered standalone crystal cluster.
- `../../hub/static/assets/models/elder-tree.glb`: centered standalone tree.
- `../../hub/static/assets/models/treasure-chest.glb`: centered standalone chest.

Generated files exist only after successful execution. A builder script is not evidence of completed exports; check the files and live model decoding before reporting delivery.

## Asset contract

All three assets stand on Z=0 in Blender with a centered root, roughly 1.3–2.2 Blender units high. Each GLB is exported with Y-up, only its landmark’s selected collection, and no hero floor, camera, lights, or neighboring props. Geometry and physically based materials are embedded; network textures are unnecessary.

Each landmark has one four-second transform animation at 24 FPS (frames 1–97, matching first/last pose):

| Asset | Animated assembly | Motion |
|---|---|---|
| Moon Crystal | Floating crystal group | Gentle bob and partial rotation above a fixed moss/brass plinth |
| Elder Tree | Leaf crown and little lanterns | Slow compound sway above a fixed trunk and roots |
| Treasure Chest | Lid hinge with curved planks and brass straps | Soft opening/closing, revealing cyan light and gems |

Objects remain separately named and editable in Blender. Modest polygon counts and simple materials keep browser playback light. These are actual geometric 3D models; they are distinct from flat rendered video clips handled by `motion.js`.

## Design

**Moon Crystal:** a six-sided central prism and five smaller tilted crystals, faceted cyan/lilac surfaces, moonlit sparkle shapes, floating brass orbit, and moss cushions on a slate reliquary.

**Elder Tree:** a curved tapered trunk with spreading roots, three branching limbs, bark grooves, small friendly eyes, overlapping emerald/jade leaf masses, pointed individual leaves, and lilac lights hanging in brass halos.

**Treasure Chest:** separate honey/amber oak boards, an arched double-skin lid, brass bindings and rivets, rounded claw feet, a jeweled front key plate, dark velvet, small gems, and an emissive cyan interior.

The deep woodland, old brass, cyan, and lilac material system matches the game’s original illustrated world while preserving a distinct three-dimensional silhouette for each object.

## Rebuild and validation

1. Create the two output directories from the shell if absent: `assets/blender/` and `hub/static/assets/models/`.
2. Connect to the installed local Blender MCP session and inspect the live scene.
3. Send the complete `build_landmarks.py` source through `execute_blender_code`. The source uses allowed Blender/math imports, creates a new scene, and never deletes existing user objects. Its absolute output paths target this project only.
4. Confirm three nonempty GLBs, the editable `.blend`, and the preview PNG. Inspect each export’s animation and bounds in the browser renderer; inspect the preview for composition/material defects.

The script selects a newly created scene and modifies only its generated objects. Re-running creates another isolated scene and refreshes only its named project outputs. The saved hero composition moves the three roots apart **after** centered GLB exports, so the source’s studio layout cannot leak into exported bounds.

Blender 5.x uses a version-dependent render-engine identifier; the builder attempts Eevee’s previous identifier and falls back to Cycles if unsupported. GLB export is independent of that preview renderer. Browser live rendering uses the embedded glTF geometry/materials/animation rather than the preview image.

## Delivered validation

Created through the verified local Blender 5.2.3 MCP session on 2026-10-28. The `.blend`, three GLBs, and 960×540 hero PNG were written successfully. The hero render was visually inspected.

The first export pass measured approximately 110–134 KiB per GLB and 2,000–3,600 triangles each, below the 2 MiB/10,000-face target. Each contained exactly one animation with two transform channels and a four-second sampled span. All three exported scenes had one correctly named landmark root, no cameras, and no texture dependencies. Live browser decoding is checked separately by the game integrator.
