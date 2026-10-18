# Stage 1 manifest parallax

## Assets and crop

Muse Spark's supplied assets are stored together under `assets/backgrounds/stage_01/`: sky.png, distant.png, ground.png, midground.png, foreground.png, expanded_master.png, and the unchanged Parallax-Manifest.json. Identical root copies were removed after SHA-256 verification. The supplied snippet is retained as Prepare-parallax-layers.example.py for reference only and is not imported or executed.

The manifest defines a 2304×1296 canvas with a 1920×1080 original view at (192,108). Assets are scaled once by 1600/1920, yielding a 1920×1080 overscan surface with a (160,90) inset around the game's 1600×900 viewport. At neutral zoom/pan the exact central viewport is presented, rather than squeezing the expanded canvas into the game window. Zoom-out uses the extra border before cropping, so it does not expose an empty letterbox inside the battlefield.

Gameplay-layer PNG dimensions are checked against the manifest. The comparison-only master may use a different resolution and is scaled to the expanded canvas; use the same framing/aspect ratio for a faithful comparison. Render order follows render_order; z_index is the fallback. Layer factors, default positions, movement bounds (40 horizontal / 25 vertical source pixels), jitter (6 source pixels), zoom range (0.95–1.15), and zoom pivot come from the manifest. No runtime Blender dependency exists.

## Composition and camera

The foreground group draws after independent character sprites; other layers draw behind them. Actors, shadows, and combat effects translate using ground's factor (0.5 x / 0.4 y). A single composite zoom applies consistently to scenery, actors, and effects. HUD and cards draw afterward in unchanged screen coordinates. Stage 1's enemy ground anchor was lowered from y=500 to y=580 to stand on the new clearing instead of the river edge; the player and remaining stage layouts are unchanged.

Neutral idle pan is zero, with no periodic camera drift. Impact produces restrained depth-dependent displacement and jitter, with existing impact zoom. Pan and debug zoom approach their targets using delta-time smoothing. Pause freezes updates. Requested movement is clamped against available overscan at minimum zoom. Zoom is uniform across the composite rather than adding the manifest's optional depth-specific scaling suggestion, preserving layer alignment and actor floor contact. Depth separation comes from translation.

Layer images are cached at load time; unchanged integer layer positions reuse background/foreground composites. Composite surfaces are reused when movement requires rebuilding; pans only blit cached source surfaces. Zoom scales the complete world once, using a reusable destination buffer and quantized zoom values. Missing layers trigger a warning and a complete static-master fallback, avoiding mixed partial layers and duplicate objects. If the master is also absent, a neutral fill remains playable.

## Temporary debug controls

Available only in manifest stages with `debug_controls: true` (currently Stage 1):

| Key | Action |
| --- | --- |
| F1 | Show/hide camera debug mode; other debug keys require this mode |
| Left / Right | Smoothly move to negative/positive horizontal limit |
| Up / Down | Smoothly move to negative/positive vertical limit |
| F2 | Toggle depth separation; disabled layers move together with the ground |
| F3 | Compare layered composition against the single expanded master |
| F4 | Trigger impact shake/zoom without changing combat |
| F5 | Cycle zoom target: 0.95, 1.15, neutral |
| Home | Reset pan, zoom, and shake to neutral |

The debug panel reports mode, pan in source pixels, and zoom. F3 shows a flattened master, so foreground occlusion is intentionally unavailable in that comparison mode. Neither debug mode nor comparison changes combat or writes files. Set debug_controls false to remove the temporary controls before release.

## Tuning / reuse

`data/stages.json` enables a manifest via `background.manifest`. Optional overrides live in `background.parallax`: enabled, foreground_layers, actor_layer, smoothing, impact_pan, max_offset_px, max_jitter, zoom_range, impact_zoom, debug_controls. Per-layer overrides are keyed by layer name under `layers`, e.g. `"layers": {"foreground": {"parallax_factor": {"x": 1.0, "y": 0.8}}}`. Keep PNGs aligned on identical expanded canvases. Preserve sane positive zoom limits and factors; change the manifest's source dimensions/inset when reauthoring the crop. Stages without a manifest use the existing background/camera path unchanged.

## Visual issues in the supplied art

The centered layer composite differs substantially from the static master: the ground covers much of the river, trees/bridge have different proportions and positions, and the skyline differs. These differences exist in the PNGs at zero camera movement, not in crop or parallax math. The manifest describes re-interpretation, so the master is a comparison reference rather than an exact pixel target.

Thin pale fringes are visible along tree, building, fence, grass, and rock cutouts. Those edge colors are in the supplied layers. The master also has visible rectangular transitions around its generated expanded border, most apparent when zooming out. No source artwork was repainted or silently modified. A future art pass should clean edge mattes, harmonize the layer composite with the intended master, and improve the expanded-border continuity. Default gameplay movement remains restrained to minimize those artifacts.

A headless software-render timing check on the development machine measured approximately 32 ms per idle frame and 44 ms at 0.95 zoom after composite caching (60-frame samples). These are local observations, not a guaranteed frame rate; sustained 60 FPS is not yet verified.
