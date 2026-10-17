# Visual direction — anime-inspired low-poly 2.5D

This update supersedes the illustration-oriented visual brief in the original `TASK.md`. Preserve that file as the original project record. Gameplay remains Python/Pygame CE with a fully 2D renderer, and the five-stage campaign remains intact.

## Camera and composition

Use a fixed, elevated three-quarter Blender camera, looking diagonally across the battlefield. Start with an orthographic camera at roughly 35 degrees elevation and 45 degrees azimuth; tune framing together before producing assets. Camera angle is baked into PNGs, never synthesized by the runtime. The runtime `camera.composition` field documents this convention; it is not a 3D camera control.

Stage 1 places the Duelist closer to the front-left and the Flame Warden farther back-right. Transparent character renders stand at explicit ground anchors. Flat-shaded facets, restrained silhouettes, stylized anime proportions, warm ember light, and cool shadow planes establish the direction. Avoid detailed painted illustration and pixel-art treatments.

The Stage 1 procedural diamond clearing, faceted trees, crystal plinth, and faceted character stand-ins are composition studies, not final Blender renders. Stages 2–5 retain provisional environments. Polish and approve the Stage 1 camera, lighting, character scale, floor contact, and UI clearance before commissioning the remaining final art.

## Runtime layers and feedback

1. Background layers and atmosphere.
2. Characters in ascending `render_order`, each with its own ground shadow.
3. Foreground PNG layers and sequences.
4. Combat effects in the same world coordinates.
5. One world composite transform for impact zoom and screen shake.
6. Untransformed floating player status, enemy-local intention/health, shallow card fan, and circular End Turn. No opaque footer or reserved battlefield region.

Frame clips, shadows, and hit-tinted variants are prepared at load time. Delta-time playback pauses with combat. Missing clips fall back to the static sprite or idle; missing sprites use geometric stand-ins. White hit flashes preserve the sprite alpha. Brief impact zoom returns to the configured baseline without altering card coordinates.

## Scope

No gameplay rewrite, Blender installation, runtime 3D engine, skeleton, or model loading. Artists deliver PNGs and JSON configuration. Ground-plane perspective and lighting must match across exports. Future art approval should compare a static frame and attack/hit clips at the actual 1600×900 logical layout.
