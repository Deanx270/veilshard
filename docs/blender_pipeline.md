# Low-poly Blender-to-Pygame pipeline

See [visual direction](visual_direction.md) for the current art brief. Blender independently produces pre-rendered assets; the game reads only PNGs. No `.blend`, `.fbx`, `.glb`, Blender installation, or 3D engine is needed during gameplay.

## Camera and export contract

Use one fixed elevated three-quarter camera for the environment and character renders. Begin around 35 degrees elevation and 45 degrees azimuth with an orthographic lens, then agree on a Stage 1 composition. Export 16:9 backgrounds at 1920×1080 or 3200×1800. All environment layers must use exactly the same camera, dimensions, color management, and pixel alignment. Do not crop transparent foreground canvases. The loader scales full environment images to 1600×900 once.

Render the complete 1600×900 battlefield with no reserved footer or vertical crop. Cards float near the bottom center; player status sits bottom-left, End Turn bottom-right, and enemy status above its sprite. Keep faces and focal action above the card fan when composing assets. Stage 1 defaults put the player feet at (470,610) and the enemy at (1100,500). These are logical screen coordinates, not Blender world coordinates. The player appears closer, with the enemy farther across the clearing. Use flat shading and matching key/fill lights when separately rendering characters. Camera orientation is baked into the images; `camera.composition` is descriptive metadata only.

## Background and foreground

Export an opaque `assets/backgrounds/stage_01/background.png`. It replaces the procedural composition automatically. Other stages use stage_02 through stage_05. Enable transparent film and export RGBA PNGs for foreground objects, maintaining the exact background camera and full canvas. Use `depth: 0` for locked alignment. A nonzero depth gives optional subtle horizontal parallax, but may separate contact edges; only use it on suitable distant layers.

```json
"background": {
  "layers": [
    {"path": "assets/backgrounds/stage_01/background.png", "depth": 0, "foreground": false},
    {"path": "assets/backgrounds/stage_01/foreground.png", "depth": 0, "foreground": true}
  ],
  "sequences": [{
    "frames": ["assets/backgrounds/stage_01/mist_0001.png", "assets/backgrounds/stage_01/mist_0002.png"],
    "fps": 8, "foreground": false, "depth": 0
  }]
}
```

Layer order follows the array within each background/foreground group; sequences follow static layers. One opaque PNG is sufficient. Missing layers are skipped and procedural scenery remains underneath. Foregrounds can cover actors but never the UI.

## Characters, ground anchors, and shadows

Export each character separately as RGBA PNG. Character images can use a smaller transparent canvas with consistent dimensions and ground location across every animation frame. Preserve the camera angle and intended facing. `size` is the logical display size at scale 1; preserve the source aspect ratio to avoid distortion. `scale` multiplies sprite and shadow dimensions at load time. `position` locates the ground anchor. `anchor` is its normalized location inside the character canvas: [0.5,0.95] means 50% across and 95% down. Crop all frames identically or the character will jitter.

```json
"player": {
  "path": "assets/characters/duelist.png",
  "position": [470,610], "size": [290,390], "scale": 1.0,
  "anchor": [0.5,0.95], "render_order": 20, "flip_x": false,
  "shadow": {"size": [160,42], "offset": [0,0], "opacity": 100, "enabled": true},
  "animations": {
    "idle": {"frames": ["assets/characters/idle_01.png", "assets/characters/idle_02.png"], "fps": 8, "loop": true},
    "attack": {"frames": ["assets/characters/attack_01.png", "assets/characters/attack_02.png"], "fps": 12, "loop": false},
    "hit": {"frames": ["assets/characters/hit_01.png"], "fps": 8, "loop": false}
  }
}
```

Both `player` and `opponent` accept these fields. Ascending `render_order` draws far actors first; it defaults to ground y when omitted. Each actor's shadow is drawn immediately before its sprite. The shadow stays at the ground anchor without idle bobbing. Add a `shadow.path` for a custom transparent PNG; missing shadow files fall back to a cached ellipse. `offset` is in logical pixels and `size` is scaled by the actor's scale. `opacity` controls the generated ellipse; custom images retain authored alpha. Set `enabled: false` if the character already includes a shadow. Do not bake a duplicate shadow into both environment and character.

`flip_x` mirrors the image before anchoring, so specify the normalized ground location for the mirrored canvas. It is convenient for placeholders; export properly facing lit characters and disable mirroring for final art.

## Character animation events

Supported optional clip names: `idle`, `attack`, `hit`, `heal`, `defend`, and `charge`. Player cards trigger attack/heal/defend. Enemy actions trigger matching clips; Special uses attack. Damage triggers hit and an alpha-preserving flash. Nonlooping clips return to idle at the end; idle defaults to looping. Missing clips leave the current/idle sprite available, and missing files within clips are skipped. Use `loop: false` for action clips so they return to idle. Match action clips to the presentation timeline: ordinary actions impact at 0.22 seconds and finish at 0.52; Heavy Attack and enemy Special impact at 0.34 and finish at 0.76. The final 0.08 seconds before impact are execution. Rules resolve once at impact; clip length never controls combat state. Procedural translation and a magical streak provide fallback movement for static sprites. See combat_animation.md.

All frames are cached in memory, including flipped/tinted variants; keep sequences modest. Background RGBA frames cost about 5.5 MiB each at logical resolution. Restart the application after replacing files.

## Camera effects

Stage-level configuration:

```json
"camera": {"composition": "fixed_three_quarter", "zoom": 1.0, "impact_zoom": 0.035, "focus": [800,430]}
```

`zoom` is bounded to 1–1.25; `impact_zoom` is bounded to 0–0.12. Damage triggers a 0.28-second zoom pulse and slight shake. World layers, actors, shadows, and effects transform together. UI remains fixed. The renderer clamps the image to cover the frame, preventing exposed edges. This scales the composite only; it does not re-load or re-scale source assets each frame. Focus is in logical pixels; keep it inside the canvas. Pause freezes camera and sprite playback.

## Collaboration and new stages

Approve Stage 1 framing before final art for stages 2–5. Replace files at configured paths or change JSON; no combat edits are necessary. To add an environment, append a stage with a unique ID, nonempty enemy pattern, character layout, and matching story introduction. The last entry determines campaign completion.

Store Blender projects in `art_sources/blender/`. `.blend` files there remain ignored until the team agrees on Git LFS or external source storage. Commit optimized runtime exports; avoid blindly adding large source scenes or animation sequences. Coordinate ownership before altering a teammate's assets. No Blender source scenes are generated by this visual update.
