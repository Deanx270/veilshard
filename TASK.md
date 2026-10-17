# VEILSHARD — INITIAL GAME PROTOTYPE

## Role and objective

You are an autonomous software-development agent with access to the user's local project directory, terminal, and development tools.

Initialize and implement the first playable prototype of **Veilshard**, a single-player anime-style, turn-based card-battle RPG developed in Python using Pygame Community Edition (`pygame-ce`).

Target GitHub repository name: `veilshard-card-rpg`.

This is a university project being developed by two students with AI coding agents. The target development period is approximately 10 days, with potential additional time for improvements.

Your immediate objective is to deliver a **working, well-structured, expandable prototype**, not a finished commercial game.

Write and test actual project files. Do not respond with source-code suggestions instead of implementing them.

## 1. Creative direction

### Visual identity

Veilshard is an anime-fantasy card-battling RPG inspired by the general presentation and strategic gameplay of Morimens and the card-battle mode of Honkai: Star Rail's Fate collaboration.

These titles are references only. Do not copy their copyrighted characters, artwork, UI assets, or proprietary content.

The game uses:

- 2D anime-style character illustrations.
- A mixture of humanoid and non-humanoid enemies.
- Visually appealing, modern gacha-inspired character designs.
- Illustrated magical cards with distinct visual identities.
- Highly atmospheric fantasy environments.
- Layered visual effects, impact animations, particles, and UI transitions.
- A predominantly 2D presentation enhanced by pre-rendered 3D environments.

The art direction should not default to traditional Western fantasy aesthetics or pixel art.

### 2.5D environment pipeline

**Critical architectural requirement: support Blender-rendered backgrounds from the beginning.**

A second developer will independently model and render the environments using Blender.

Do not attempt to load `.blend`, `.fbx`, or `.glb` assets directly into Pygame, and do not introduce a real-time 3D engine.

Instead, build a flexible background system that supports:

1. A complete static PNG background for each stage.
2. Optional transparent foreground PNG overlays.
3. Optional multiple depth layers for subtle parallax.
4. Optional animated image sequences for atmospheric elements in future development.
5. Lightweight camera shake and screen-space effects.

The system must function even when only one background PNG exists.

Use a rendering order similar to:

- Background and distant layers
- Environmental effects behind characters
- Player and enemy illustrations
- Foreground environmental overlays
- Battle particles and effects
- Cards and user interface

Keep the UI readable regardless of environmental layering.

For now, create temporary original backgrounds with procedural shapes or simple graphical placeholders. These will later be replaced by the partner's Blender exports.

Do not require Blender to be installed to run the game.

### Resolution

- Logical game resolution: 1600×900.
- Aspect ratio: 16:9.
- Target frame rate: 60 FPS.
- Support resizing with aspect-ratio preservation and letterboxing where necessary.
- Correctly map mouse interactions between window coordinates and logical coordinates.
- Support importing backgrounds exported at 1920×1080 or higher.

Avoid repeatedly scaling large assets every frame. Cache loaded and appropriately scaled surfaces.

## 2. Provisional game story

A powerful magical crystal called the Core protects the balance of the world.

After the Core unexpectedly shatters, corruption spreads across different regions, altering their environments and turning formerly peaceful guardians hostile.

A young card-wielding duelist sets out to uncover the truth and restore the Core.

This premise is provisional. Keep the story modular and editable through external data files.

The five initial stages are:

| Stage | Environment | Enemy |
|---|---|---|
| 1 | Ember Forest | Flame Warden |
| 2 | Frozen Ruins | Frozen Beast |
| 3 | Storm Tower | Stormcaller |
| 4 | Corrupted Grove | Corrupted Ancient |
| 5 | Shattered Citadel | Shattered Guardian |

Provide a short introductory story scene before each battle.

Do not generate extensive dialogue or permanently establish detailed lore, as these will be revised later.

The provisional game title is Veilshard, with the optional subtitle Fractured Oath. Make the displayed title configurable.

## 3. Core gameplay

Build a fully functional turn-based card-battle system.

### Player mechanics

- The player starts each stage with 30/30 HP.
- The player starts each turn with 2 energy.
- The player draws 3 cards each turn.
- Multiple cards may be played during one turn as long as sufficient energy remains.
- The player ends their turn using an End Turn button.
- The enemy performs one intended action during its turn.
- Card effects resolve before enemy actions.
- Player Block absorbs incoming damage before HP.
- Healing cannot exceed maximum HP.
- Defeating an enemy advances the story and eventually unlocks the next stage.
- HP resets to 30 at the beginning of each new stage.
- Reaching zero HP causes defeat.
- Defeating Stage 5 completes the game.

### Starting deck

Provide an initial 12-card deck:

- 5 Attack
- 2 Heavy Attack
- 3 Shield
- 2 Heal

| Card | Energy cost | Effect |
|---|---|---|
| Attack | 1 | Deal 6 damage |
| Heavy Attack | 2 | Deal 10 damage |
| Shield | 1 | Gain 6 Block |
| Heal | 1 | Recover up to 6 HP |

Implement a draw pile, discard pile, and hand.

Shuffle the starting deck at the beginning of each battle. Draw 3 cards at the beginning of the player turn. Played cards go into the discard pile; unplayed cards are discarded at the end of the turn. Reshuffle the discard pile when the draw pile is insufficient.

Cards must not be usable without enough energy.

The initial deck resets at the beginning of each stage. Keep deck progression extensible, but do not implement permanent card rewards yet.

### Defense behavior

- Block is consumed before HP.
- Player Block expires after the next enemy phase, whether or not an attack occurs.
- Enemy Block persists long enough to defend against the next player attacks; do not clear it immediately after the enemy creates it.
- Define Block lifetime unambiguously in the combat code and tests.
- All HP and Block values must remain nonnegative.

### Enemy mechanics

Each enemy has configurable HP, attack values, and a predictable behavior pattern.

Implement visible enemy intentions so players can anticipate enemy actions.

Possible intentions:

- Attack
- Defend
- Charge
- Heal
- Special Attack

The enemy intention must be shown during the player's turn and executed after End Turn.

Stage-specific mechanics:

1. **Flame Warden:** basic attack pattern introducing combat.
2. **Frozen Beast:** occasionally creates defensive Block.
3. **Stormcaller:** charges before performing stronger attacks.
4. **Corrupted Ancient:** periodically restores HP.
5. **Shattered Guardian:** changes its attack behavior below 50% HP.

Choose reasonable provisional HP and damage values. Store them outside the combat logic.

Prioritize predictable, correctly implemented combat over complicated enemy AI.

## 4. Battle presentation

Implement an anime-style battle layout.

### Composition

- Player illustration on the left.
- Enemy illustration on the right.
- Atmospheric environment in the background.
- Player and enemy health indicators.
- Block indicators when applicable.
- Enemy intention indicator.
- Energy counter.
- Three-card hand along the lower center.
- End Turn button near the lower-right.
- Small stage identification.

Allow character positions, anchor points, scales, and background layers to be configured per stage.

This is important because Blender scenes may have different compositions.

### Card UI

Each card should display:

- Card name
- Energy cost
- Card category
- Short ability description
- Placeholder illustration or icon

Implement:

- Hover highlighting
- Visually disabled unaffordable cards
- Click-to-play interaction
- Card activation feedback
- Hand updates after each turn
- Distinct basic color treatment by card category

### Animation

Use a simple nonblocking animation system based on delta time.

Prioritize:

- Attack impact flashes
- Lightweight screen shake
- Damage number popups
- Floating heal indicators
- Block gain animation
- Card-play transitions
- Smooth screen transitions

Avoid expensive animation pipelines and full skeletal character animation.

The prototype must work correctly without completed artwork.

## 5. Scenes and navigation

Implement these scenes:

1. Main Menu
2. Stage Introduction
3. Battle
4. Stage Clear
5. Game Over
6. Final Victory

The player must be able to start a game, play through all five battles, and reach an ending.

Include a way to restart after defeat.

Support a basic Escape/pause interaction without interfering with the game's turn state.

## 6. Project architecture

Use Python 3.11+ with `pygame-ce`.

Organize the code into appropriately separated modules for:

- Application initialization and main loop
- Scene management
- Battle state
- Player and enemy data
- Turn processing
- Card definitions and effects
- Deck and hand handling
- Enemy intentions
- UI rendering
- Input handling
- Asset loading
- Background composition and animation
- General utility functions

Keep the combat rules independent of Pygame rendering so they can be tested without a graphical display.

Use reasonable type hints, dataclasses where useful, and clear naming conventions.

Avoid giant files containing unrelated systems.

Prefer straightforward, maintainable architecture over elaborate design patterns.

### Data files

Place editable game definitions in `data/`, including:

- `cards.json`
- `stages.json`
- `story.json`

Use relative asset paths and a centralized resource loader.

Add fallback rendering when an asset file is missing.

## 7. Suggested directory organization

Create an organized structure similar to:

```text
veilshard-card-rpg/
├── assets/
│   ├── backgrounds/
│   │   ├── stage_01/
│   │   ├── stage_02/
│   │   ├── stage_03/
│   │   ├── stage_04/
│   │   └── stage_05/
│   ├── characters/
│   ├── enemies/
│   ├── cards/
│   ├── effects/
│   ├── ui/
│   └── audio/
├── art_sources/
│   └── blender/
├── data/
├── src/
│   ├── core/
│   ├── combat/
│   ├── cards/
│   ├── enemies/
│   ├── scenes/
│   ├── rendering/
│   └── ui/
├── tests/
├── docs/
│   ├── game_design.md
│   └── blender_pipeline.md
├── main.py
├── requirements.txt
├── README.md
├── AGENTS.md
└── .gitignore
```

Adapt this structure if necessary to keep implementation clean.

Do not create useless empty Python modules solely to match the proposed tree.

Use `.gitkeep` for asset directories that must be tracked while empty.

`art_sources/blender/` is intended for source projects, but large `.blend` files should not be committed blindly. Document when Git LFS or separate asset storage may be appropriate.

### Blender integration documentation

Create `docs/blender_pipeline.md`, explaining:

- Recommended Blender scene resolution and camera framing.
- Exporting stage backgrounds as PNG.
- Using RGBA PNG for transparent foreground layers.
- Layer naming and expected file paths.
- Recommended export workflow for animation frames.
- How the agent-generated game will load replacement backgrounds.
- How to preserve image alignment and camera composition.
- How developers should add new environments without modifying combat code.

Do not create actual Blender source scenes in this initial task.

## 8. Documentation and collaborative agents

Create a useful `README.md` covering:

- Game overview
- Dependencies
- Installation
- Running the game
- Controls
- Current implemented features
- Limitations
- Project structure

Create `AGENTS.md` explaining:

- Code architecture
- Important game invariants
- Development conventions
- Testing commands
- File ownership and asset replacement practices
- Safe collaboration workflows
- Areas that future agents can extend

Future agents should be able to understand the project without having to reverse engineer the entire codebase.

## 9. Testing

Use pytest for combat logic.

Tests should cover at least:

- Energy consumption
- Card affordability
- Correct damage calculations
- Block absorption and expiration
- Healing limits
- Card drawing and reshuffling
- Enemy action resolution
- Enemy defeat before its action
- Stage transitions
- Player defeat
- Final victory conditions
- Stage HP restoration

Verify that the application launches and that the battle can be played through.

If the environment lacks a graphical display, perform headless testing using an appropriate SDL configuration and explain any untested visual behavior.

Do not claim a test passes without executing it.

## 10. Implementation order

Use the following priorities.

**Phase 1 — Working core**

Create the application entry point, window, scene manager, combat models, and card rules.

**Phase 2 — Playable first stage**

Build a fully functional Stage 1 battle with cards, energy, enemy intentions, and victory/defeat handling.

**Phase 3 — Five-stage campaign**

Implement the remaining four enemy configurations, stage progression, and provisional story introductions.

**Phase 4 — Visual foundation**

Implement a presentable anime-inspired interface using original placeholders, smooth interactions, and support for Blender-rendered backgrounds.

**Phase 5 — Testing and documentation**

Validate the gameplay, fix errors, document the repository, and prepare an initial commit.

Do not spend excessive time generating decorative assets. The second developer will produce Blender environments later, while the other developer continues improving the game's illustrations, interface, and effects.

The most important deliverable is a working game whose artwork can be replaced without rewriting the game logic.

## 11. GitHub workflow

Target repository: `veilshard-card-rpg`.

The student project owner will create this repository separately.

Before making changes, inspect the existing project directory and Git state.

If no Git repository exists, initialize one locally.

Do not create a GitHub repository unless explicitly instructed.

Once implementation and testing are complete:

1. Review modified files.
2. Ensure caches, virtual environments, and unnecessary large files are excluded.
3. Create a descriptive initial Git commit.
4. If an authorized remote has been provided, verify it and push the appropriate branch.
5. If no remote exists, leave the project committed locally and provide the commands needed to connect it later.

Do not invent repository URLs, force-push, or overwrite unrelated files.

## 12. Completion criteria

The prototype is complete when:

- It launches successfully.
- The user can navigate from the main menu into combat.
- All four card types function.
- Energy and Block are handled correctly.
- Enemy intentions work.
- The five provisional battles can be completed.
- Stage transitions and story scenes function.
- Victory and Game Over screens function.
- Temporary character and background visuals render correctly.
- Blender background replacement paths are documented.
- Automated gameplay tests pass.
- The Git repository is prepared for collaborative development.

Report the final file structure, implemented features, remaining placeholders, executed tests, run commands, and Git status.

**Begin implementing the initial playable Veilshard prototype inside the current project directory. Prioritize functionality, maintainability, and future asset integration.**