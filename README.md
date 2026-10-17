# Veilshard â€” Fractured Oath

A single-player, anime-inspired turn-based card RPG prototype made with Python and Pygame Community Edition. Recover five fragments through Ember Forest, Frozen Ruins, Storm Tower, Corrupted Grove, and Shattered Citadel.

## Install and run

Python 3.11+ is required (tested with Python 3.12.10).

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python main.py
```

On macOS/Linux, use `.venv/bin/python` in place of `.\.venv\Scripts\python`. No Blender installation, downloaded art, or external font is required. Assets resolve relative to the project, regardless of working directory.

## Controls

- Click **Begin journey**, then **Enter battle**.
- Hover over cards to highlight them; click a card to play it.
- Each turn gives 2 energy and 3 cards. Click **End turn** to execute the displayed enemy intent.
- Press **Escape** in combat to pause/resume. The pause menu can return to the main menu.
- Retry the current stage after defeat. HP and the starting deck reset for each stage.
- Resize the window freely; the 1600Ã—900 canvas is letterboxed with corrected mouse coordinates.

## Implemented

A 12-card deck (5 Attack, 2 Heavy Attack, 3 Shield, 2 Heal), shuffled draw/discard cycle, visible enemy intentions, five enemy patterns, six navigation scenes, health/Block/energy UI, card hover and affordability feedback, floating damage/heal/Block numbers, impact flashes, camera shake, scene fades, and pause-safe animation timing.

Pure Python combat is separate from rendering. JSON defines cards, stage layouts, enemies, story, and the displayed title. PNG backgrounds, transparent foregrounds, parallax layers, and optional frame sequences are cached at load time. Missing art falls back to original procedural environments and stylized character silhouettes.

## Tests

```powershell
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python main.py --headless --frames 120
```

Tests cover combat invariants, all enemy actions, deck recycling, campaign outcomes, ten seeded full campaign playthroughs, navigation/clicks/pause, resizing math, rendering every scene, and 1920Ã—1080 PNG/frame-sequence imports using SDL dummy drivers.

## Structure

```text
main.py                 Entry point and headless launch options
src/core/               Main loop, input coordinate mapping, resources
src/combat/             Pure battle state, fighters, turn resolution
src/cards/              Card definitions and deck handling
src/enemies/            Locked intentions and behavior patterns
src/scenes/             Campaign navigation and stage progression
src/rendering/          Cached assets, backgrounds, characters, effects
src/ui/                 Text, panels, buttons, health bars, cards
data/                   Editable cards, stages, and story JSON
assets/                 Replacement art and audio directories
art_sources/blender/    Reserved for partner source projects
tests/                  Combat and headless UI integration tests
docs/                   Game rules and Blender export contract
AGENTS.md               Contributor and coding-agent guide
TASK.md                 Original project brief
```

## Current limitations

Art is intentionally temporary: geometric silhouettes and procedural scenery, no finished anime illustrations. No sound, save system, rewards, deck upgrades, dialogue trees, or skeletal animation. Played cards rise and fade during a short input lock. Enemy turns resolve atomically, followed by a short nonblocking presentation delay. Balance is provisional, and playthrough tests do not guarantee every random draw is winnable. PNG sequences preload all frames and should stay small. The full logical canvas is scaled once per frame for window presentation; large source assets are never rescaled each frame.

See [game rules](docs/game_design.md) and the [Blender pipeline](docs/blender_pipeline.md) before replacing assets.
