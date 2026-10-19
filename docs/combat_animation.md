# Combat animation timing

Verified starting checkpoint: `f37691d`, clean and synced; 47 tests passed before changes. The floating HUD layout and combat model are preserved.

`ActionTimeline` is presentation-only and accepts one callback. It marks that callback resolved before invoking it, rejects overlapping starts, and crosses impact exactly once even on a long frame. Ordinary attacks/support actions impact at 0.22 seconds with 0.30 seconds recovery. Heavy Attack and enemy Special impact at 0.34 seconds with 0.42 seconds recovery. Execution occupies the last 0.08 seconds before impact. No sleeps or animation-driven combat rules are used.

On card acceptance the app validates active state, affordability, and input lock; removes the selected visual occurrence; then reserves its model index until impact. The model hand/energy/HP change together at impact through the existing `Battle.play` call. The selected visual moves upward/inward, shrinks, and dissolves over 0.35 seconds. Remaining cards ease into position immediately. Other combat inputs are blocked until recovery ends, so reserved indices cannot change. End Turn similarly calls the existing complete enemy phase exactly once at impact. Its draw/energy reset occurs there; cards remain locked until recovery ends. The displayed enemy intent remains the executed intent throughout anticipation.

Pause freezes timeline, actor movement, card motion, particles, HP bars, and camera. Returning to menu cancels an unresolved callback, clears reservations, and releases the lock. A new battle resets presentation state. Death and victory transitions wait for recovery; defeated enemies cannot retaliate.

The source actor winds back, lunges, and returns to its configured ground position. A short faceted magical streak bridges the battle distance during execution. Targets flash and recoil at impact. Normal damage uses a small slash/ring and seven particles; heavy damage uses a crossed slash, larger ring, fourteen particles, stronger recoil, and stronger camera response. Shield draws a blue polygon ward; Heal draws a green rising ring/cross and particles. Nonattack actions have a restrained lift. Authored frame clips remain supported and start with anticipation; hit clips trigger at impact.

Floating numbers use actual model results, including zero damage against Block and capped healing. HUD numbers update to authoritative HP immediately at impact; bar fill interpolates exponentially toward it. Damage shake/zoom begins only at impact. World effects transform with the battlefield; HUD coordinates and card fan geometry do not change.

Tests cover rapid card/End Turn inputs, delayed mutations, exactly-once long-frame resolution, pause/resume, menu cancellation, lethal attacks with no retaliation, support effects, heavy strength, and HP interpolation. Existing rule/campaign tests remain intact. Procedural effects are placeholders; no final art or audio is included.

Impact tuning: stronger lunge/recoil, larger and thicker ability bursts, longer burst visibility, and larger shadowed numbers. Stage 1 impact pan is 14 source pixels with a 10-pixel jitter cap; heavy attack parallax scales pan kick to ~40 source pixels with directional impact, an elastic rebound pulse, amplified zoom (up to 1.134), and 0.42s duration for heightened layer separation; overscan limits still apply. Normal and heavy camera strengths are 1.1 and 2.4. Combat resolution timing and input locks are unchanged. Visual judgment for this tuning pass is left to the user; no screenshots are captured.


### Stage 1 exported player clips

Stage 1 uses finalized player animation PNGs from `assets/characters/char_01` (organized into `idle/`, `attack/`, `hurt/`, `defend/`, and `heal/`) at the logged bottom-center anchor [741, 939], size [1445, 813], scale 1, and 10 FPS. Idle frames 1–14 loop. Normal attack plays attack1–15 without either heavy variant. Heavy plays 1–9, 11, 12-heavy, 13-heavy, 14, 15. Both return to idle on completion. The old ellipse shadow is replaced by cached, frame-derived silhouette shadows; tuning controls are documented in animation_preview.md.

Clip `impact_frame` is a zero-based presentation setting: normal frame 11 (attack12), heavy frame 10 (attack12-heavy). Loaded clips set the exactly-once action timeline's impact and recovery duration from their FPS, keeping combat locked through the entire clip. Missing/incomplete clips retain default timeline timing. Later stages keep their existing art and timings. The debug preview remains available for future placement experiments.

Stage 1 player sets `procedural_motion: false`: exported frames provide all actor movement, so timeline lunges, support bobbing, and hit knockback do not shift its logged anchor. Shared battlefield camera/parallax still applies. Other actors retain their existing movement.

Attack and heavy clips use a fixed source-canvas registration of [38, -2] on their 1920x1080 exports. Their first frame was exported left/down relative to idle1; the renderer scales this registration with the sprite. This is constant across the clip, preserves its authored motion, and does not change the stage anchor. Idle retains the logged placement.

Stage 1 custom player clips disable `placeholder_projectile`; enemy and legacy actors keep their existing fallback. Stage 1 now uses a shared soft contact shadow instead of the frame silhouette. See animation_preview.md for tuning.

Hurt clips are in `assets/characters/char_01/hurt/` (hurt1.png through hurt16.png). Normal attack damage triggers clip `hit`, which excludes frames 1, 5, 6, 7, 8, 9, 10, 12, and 14 to play a fast 7-frame flinch (hurt2, 3, 4, 11, 13, 15, 16). Heavy/special damage triggers clip `hit_heavy`, which excludes frames 2 and 4 to play the 14-frame full stagger. Both clips use 10 FPS and return to idle. CharacterSprite aliases `hurt`/`hurt_heavy` to `hit`/`hit_heavy`. No procedural knockback is added because `procedural_motion: false` preserves the frame-authored motion.

Defend clip uses `assets/characters/char_01/defend/defend1.png` through `defend15.png` (15 frames, 10 FPS, impact frame 6). Playing a Shield card triggers clip `defend`, setting timeline impact at frame 7 (`defend7.png`, 0.60s) where the barrier forms and block is gained, followed by dissipation and recovery to idle. CharacterSprite aliases `defend`/`block`. No procedural support bobbing is applied due to `procedural_motion: false`.

Heal clip uses `assets/characters/char_01/heal/heal1.png` through `heal14.png` (14 frames, 10 FPS, impact frame 7, source registration [12, -57]). Playing a Heal card triggers clip `heal`, resolving HP recovery at frame 8 (`heal8.png`, 0.70s) at the peak healing energy burst, followed by settling and return to idle. Registration [12, -57] aligns the grounded character pose with idle1. No procedural support bobbing is applied due to `procedural_motion: false`.
