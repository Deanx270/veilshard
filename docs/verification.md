# Initial prototype verification

Verified on 2026-10-17 with Windows, Python 3.12.10, pygame-ce 2.5.8, and pytest 9.1.1.

- `python -m pytest -q`: 34 passed. Covers energy, affordability, damage, healing, both Block lifetimes, deck reshuffling, all enemy actions, locked intent and rage, lethal interruption, defeat/retry, stage resets, final victory, and ten seeds of complete five-stage campaigns through public combat actions.
- SDL dummy UI integration renders all scenes/stages, navigates menu and intro by mouse, plays a card, ends a turn, freezes/resumes a pause, and renders a resized window.
- PNG integration imports a 1920×1080 layer plus an animated foreground frame and confirms rendered pixel colors within scaling tolerance.
- `python main.py --headless --frames 120`: passed.
- `python main.py --frames 30`: native window launch and bounded render loop passed.
- A 1600×900 rendered battle screenshot was visually inspected. The enemy intent panel was moved to the top center to keep character faces visible. Played cards now rise and fade during activation.

Limits: No human mouse-driven campaign was completed. Campaign playthroughs are automated model tests, and UI interactions use synthetic mouse events. Native resizing across displays/DPI settings and final partner artwork remain to be evaluated. Original placeholders are intentionally unfinished.
