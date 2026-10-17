# Blender environment export contract

The game renders only 2D images. Do not load `.blend`, `.fbx`, or `.glb` into Pygame. Blender is an authoring tool and is not required on players' machines.

## Composition

Use a 16:9 camera, preferably 1920×1080 or 3200×1800. The game scales complete layers once to its 1600×900 logical canvas. Preserve the same camera, resolution, color management, and framing across every layer and animation frame. Use an orthographic or low-perspective camera suited to character illustrations. Bake lighting into the export. Avoid aspect ratios other than 16:9, as imported layers currently scale to fit rather than crop.

Reserve the bottom 240 logical pixels for opaque card UI and the upper corners for health panels. Default character feet are near (360,625) and (1200,625), with the environment horizon around y=570. Keep these surfaces plausible for standing characters. Character `position`, normalized `anchor`, and `size` can be changed independently for each stage in `data/stages.json`. An anchor of [0.5,1.0] means bottom-center. Positions and sizes use logical pixels.

## Static image workflow

1. Render a complete background PNG with opaque sky and ground.
2. Export it to `assets/backgrounds/stage_01/background.png` (stage_02 through stage_05 use the same naming).
3. Launch the game. Its configured path automatically replaces the generated fallback; no combat edits are needed.
4. For a foreground, isolate near-camera scenery, enable transparent film, and render RGBA PNG to `foreground.png` using the identical camera and canvas. Do not trim transparent bounds.
5. Add the foreground entry to that stage's `background.layers`. Set `foreground` to true and `depth` to zero for strict alignment.

Example:

```json
"background": {
  "layers": [
    {"path": "assets/backgrounds/stage_01/background.png", "depth": 0, "foreground": false},
    {"path": "assets/backgrounds/stage_01/midground.png", "depth": 0.3, "foreground": false},
    {"path": "assets/backgrounds/stage_01/foreground.png", "depth": 0, "foreground": true}
  ],
  "sequences": []
}
```

Layers draw in array order within their background/foreground group. Distant layers draw before environmental motes, characters, foregrounds, impact effects, then opaque UI. The fallback is always behind loaded layers, so missing art remains playable. One opaque background is sufficient. Keep base layers at depth zero if edge movement is undesirable. Optional `depth` controls a small horizontal sinusoidal offset; supply a little edge-safe scenery/transparent padding and test seams. All layers share camera shake while UI stays fixed.

## Animated exports

Render a short looping image sequence such as `mist_0001.png`, `mist_0002.png`, and so on. Export full-frame RGBA PNGs with the same camera. List ordered paths explicitly:

```json
"sequences": [{
  "frames": ["assets/backgrounds/stage_01/mist_0001.png", "assets/backgrounds/stage_01/mist_0002.png"],
  "fps": 8,
  "foreground": false,
  "depth": 0
}]
```

Playback uses elapsed game time and pauses with the game. Frames are cached in memory at 1600×900 (~5.5 MiB each), so start with small sequences; future streaming/video support is outside this prototype. Sequences render after static layers within each group. Missing frames are skipped. Restart the application after replacing art to clear caches.

## Adding environments and collaboration

Copy a stage entry, assign a unique ID, configure its enemy and character layout, and add an introduction at the matching index in `data/story.json`. Campaign completion follows the last stage entry; combat code does not need to change for existing action types. Each enemy needs positive HP and a nonempty pattern of [action, nonnegative amount] pairs. Supported actions: attack, defend, charge, heal, special.

Keep source projects under `art_sources/blender/`; `.blend` files there are ignored by default. Coordinate ownership before editing another student's scene. Commit optimized runtime PNG exports. For large source scenes, textures, or long frame sequences, agree on Git LFS tracking and installation before adding files, or use shared external asset storage and document its location. Do not blindly commit huge binaries. No Blender sources are generated in this prototype.
