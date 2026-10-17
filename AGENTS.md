# Working on Veilshard

## Architecture

`main.py` starts `src/core/app.py`. `Campaign` in `src/scenes/campaign.py` owns scene/progression state; `Battle` owns combat; `Card`/`Deck` own card data and piles; `EnemyPlan` chooses intentions. Rendering, effects, widgets, assets, and input mapping are isolated modules. Data lives in three JSON files. Paths resolve through `src/core/resources.py`, never the process working directory. Combat modules must remain free of Pygame imports.

## Invariants

- Start every stage at 30 HP, 2 energy, a fresh shuffled 12-card deck; draw 3 each turn.
- Reject unaffordable, invalid-index, and post-combat plays without mutating state.
- Damage consumes Block before HP. Healing caps at max HP. All values remain nonnegative.
- Player Block expires after every enemy phase. Enemy Block survives the next player turn and clears before the subsequent enemy action.
- Displayed intent must equal executed intent. Guardian threshold changes apply to the next selected intent.
- A lethal card prevents enemy retaliation. Defeat never starts another player turn.
- Pause must not advance effects, lock timers, or combat. All animation uses delta time, never blocking sleeps.
- Window scaling and mouse mapping must share the same letterbox rectangle.

## Conventions and checks

Use Python 3.11+, type hints for model APIs, dataclasses for small value types, and straightforward modules. Preserve editable data, existing user changes, and `TASK.md`. Do not add empty modules just for organization. For mechanics changes, add meaningful model tests. For renderer/input changes, exercise SDL dummy integration tests and inspect a rendered screenshot when possible.

```powershell
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python main.py --headless --frames 120
```

No remote services are needed at runtime. Never commit `.venv`, caches, credentials, or generated testing screenshots. Verify `git diff --check`, staged file lists, and test results before committing. Do not force-push. Coordinate branches and file ownership with the other developer before shared edits. Fetch/inspect remote state before publication. Avoid modifying a teammate's binary source without agreement.

## Asset ownership

The environment developer owns Blender sources and exports. The gameplay/UI developer owns code, card data, and illustrations. Confirm real assignments with the team; these are suggested boundaries. Replace images at configured paths instead of hardcoding new rendering branches. Follow `docs/blender_pipeline.md` for cameras, anchors, layers, and sequences. Missing assets must remain playable. Large `.blend` sources are ignored until the team agrees on LFS or external storage.

## Extensions

Likely next steps are final illustrations, audio, saving progress, status effects, card rewards, balance, data validation, and richer feedback. Keep changes scoped; avoid coupling story to combat or introducing a real-time 3D engine. Do not require Blender to play the game.

## Current visual architecture

The low-poly 2.5D direction in `docs/visual_direction.md` supersedes the art direction of the original TASK.md. Preserve completed combat. `Battlefield` composites backgrounds, ordered `CharacterSprite` actors/shadows, foregrounds, and effects before `Camera` applies impact zoom/shake. UI draws afterward. Animation frames, alpha-preserving hit variants, and shadows are cached; update timers only while unpaused. Actor clip events are presentation-only and never change combat outcomes. Configure positions, normalized ground anchors, scale, order, shadow, and clips through stages.json. Prioritize Stage 1 composition and final exports before producing finished art for later stages. No runtime Blender or real-time 3D dependencies.

## Floating HUD

See `docs/battle_ui.md`. Keep card geometry in card_layout.py, presentation/easing/input in card_hand.py, face art in card_art.py, and status/buttons in battle_hud.py. Never reserve a footer or shrink the world for HUD. Preserve exact duplicate-card occurrence removal and topmost transformed hit testing. Keep the fan shallow (three cards: about 7 degrees and 14 pixels rise).
