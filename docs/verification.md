# Initial prototype verification

Verified on 2026-10-17 with Windows, Python 3.12.10, pygame-ce 2.5.8, and pytest 9.1.1.

- `python -m pytest -q`: 34 passed. Covers energy, affordability, damage, healing, both Block lifetimes, deck reshuffling, all enemy actions, locked intent and rage, lethal interruption, defeat/retry, stage resets, final victory, and ten seeds of complete five-stage campaigns through public combat actions.
- SDL dummy UI integration renders all scenes/stages, navigates menu and intro by mouse, plays a card, ends a turn, freezes/resumes a pause, and renders a resized window.
- PNG integration imports a 1920Ã—1080 layer plus an animated foreground frame and confirms rendered pixel colors within scaling tolerance.
- `python main.py --headless --frames 120`: passed.
- `python main.py --frames 30`: native window launch and bounded render loop passed.
- A 1600Ã—900 rendered battle screenshot was visually inspected. The enemy intent panel was moved to the top center to keep character faces visible. Played cards now rise and fade during activation.

Limits: No human mouse-driven campaign was completed. Campaign playthroughs are automated model tests, and UI interactions use synthetic mouse events. Native resizing across displays/DPI settings and final partner artwork remain to be evaluated. Original placeholders are intentionally unfinished.

## Low-poly visual architecture update — 2026-10-17

- `python -m pytest -q`: 37 passed, including the unchanged combat/campaign tests.
- New checks exercise cached frame cycling and one-shot return to idle, sprite scale/anchor positioning, transparent hit flashes, shadow placement, actual overlapping sprite draw order, camera edge coverage, paused camera/sprite timing, and card feedback surviving an update.
- `python main.py --headless --frames 120`: passed after the visual update.
- A Stage 1 1600×900 rendered frame was inspected: diagonal elevated clearing, separate front-left/back-right actors with floor-contact shadows, and readable UI.
- No final Blender assets or production character clips are supplied; animation tests use temporary PNG frames. Native human playtesting and artist-export validation remain outstanding for this update.

## Floating HUD update

47 tests passed, including original gameplay checks and new fan geometry, rotated hits, reflow, affordability, and resize integration checks. Both `main.py --headless --frames 120` and native `main.py --frames 30` completed successfully. Three-card idle/hover and six-card rendered screenshots were inspected. No human campaign playthrough was performed for this update.

## Combat feedback milestone

Starting checkpoint f37691d verified clean with 47 tests passing. After changes, 55 tests pass, including rapid input, impact-only mutation, pause/resume, cancellation, lethal interruption, support effects, and heavy impact strength. Native 30-frame and headless 120-frame launches passed. A Heavy Attack sequence was captured and visually inspected across anticipation, execution, impact, and recovery. No human campaign playthrough or final artwork validation was performed.

## Stage 1 manifest parallax — 2026-10-18

73 tests passed after integrating the five aligned layers. Tests cover exact centered master crop, idle stability, manifest ordering, depth factors, actor-to-ground movement, screen-anchored HUD, all four pan-limit corners at 0.95/1.0/1.15 zoom, foreground occlusion, debug controls, pause, Stage 1-only activation, cached loading, missing-layer fallback, and replacement of stale frames during zoom. Alpha coverage checks allow small smoothscale rounding differences while rejecting exposed pixels. A zoom destination-buffer format regression found during testing was fixed and covered by a fresh-scale comparison.

Native 60-frame and headless 120-frame launch checks passed. Captured game frames were inspected at neutral view and maximum positive pan with zoom-out, alongside the static master. A temporary diagnostic actor position confirmed near-rock/grass overlap; that position was not saved. Enemy Stage 1 ground anchor was lowered onto the clearing. Supplied art has pale cutout fringes and a layered composition that differs from the master; details are in stage1_parallax.md. No supplied PNG pixel data was changed and no screenshots were committed. Human mouse-driven campaign playtesting remains outside this verification.
