# Veilshard â€” Fractured Oath

A single-player, anime-inspired low-poly 2.5D turn-based card RPG prototype made with Python and Pygame Community Edition. Recover five fragments through Ember Forest, Frozen Ruins, Storm Tower, Corrupted Grove, and Shattered Citadel.

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

A 12-card deck (5 Attack, 2 Heavy Attack, 3 Shield, 2 Heal), shuffled draw/discard cycle, visible enemy intentions, five enemy patterns, six navigation scenes, health/Block/energy UI, a shallow animated portrait-card fan, transformed hover/click detection, and affordability feedback, floating damage/heal/Block numbers, alpha-preserving sprite hit flashes, camera shake and impact zoom, scene fades, and pause-safe animation timing.

Pure Python combat is separate from rendering. JSON defines cards, stage layouts, enemies, story, and the displayed title. PNG backgrounds, transparent foregrounds, parallax layers, and optional frame sequences are cached at load time. Independent transparent character sprites support ground anchors, scale, draw order, shadows, and optional frame animation clips. Missing art falls back to procedural environments and faceted character stand-ins. Stage 1 has a three-quarter clearing composition; final Blender art remains pending.

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

Art is intentionally temporary: faceted stand-ins and procedural scenery, no final low-poly Blender renders. No sound, save system, rewards, deck upgrades, dialogue trees, or skeletal animation. Played cards rise and fade during a short input lock. Enemy turns resolve atomically, followed by a short nonblocking presentation delay. Balance is provisional, and playthrough tests do not guarantee every random draw is winnable. PNG sequences preload all frames and should stay small. The world composite is scaled during camera effects and the logical canvas for window presentation; source assets are cached at load time.

See [visual direction](docs/visual_direction.md), [game rules](docs/game_design.md) and the [Blender pipeline](docs/blender_pipeline.md) before replacing assets.

The battle HUD floats above the full viewport: compact player status bottom-left, enemy health/intent near the sprite, and a circular End Turn bottom-right. Three cards use a restrained 7-degree fan with a 14-pixel arc. See [battle UI](docs/battle_ui.md) for tuning and input behavior.
