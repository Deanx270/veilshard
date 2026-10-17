# Combat animation timing

Verified starting checkpoint: `f37691d`, clean and synced; 47 tests passed before changes. The floating HUD layout and combat model are preserved.

`ActionTimeline` is presentation-only and accepts one callback. It marks that callback resolved before invoking it, rejects overlapping starts, and crosses impact exactly once even on a long frame. Ordinary attacks/support actions impact at 0.22 seconds with 0.30 seconds recovery. Heavy Attack and enemy Special impact at 0.34 seconds with 0.42 seconds recovery. Execution occupies the last 0.08 seconds before impact. No sleeps or animation-driven combat rules are used.

On card acceptance the app validates active state, affordability, and input lock; removes the selected visual occurrence; then reserves its model index until impact. The model hand/energy/HP change together at impact through the existing `Battle.play` call. The selected visual moves upward/inward, shrinks, and dissolves over 0.35 seconds. Remaining cards ease into position immediately. Other combat inputs are blocked until recovery ends, so reserved indices cannot change. End Turn similarly calls the existing complete enemy phase exactly once at impact. Its draw/energy reset occurs there; cards remain locked until recovery ends. The displayed enemy intent remains the executed intent throughout anticipation.

Pause freezes timeline, actor movement, card motion, particles, HP bars, and camera. Returning to menu cancels an unresolved callback, clears reservations, and releases the lock. A new battle resets presentation state. Death and victory transitions wait for recovery; defeated enemies cannot retaliate.

The source actor winds back, lunges, and returns to its configured ground position. A short faceted magical streak bridges the battle distance during execution. Targets flash and recoil at impact. Normal damage uses a small slash/ring and seven particles; heavy damage uses a crossed slash, larger ring, fourteen particles, stronger recoil, and stronger camera response. Shield draws a blue polygon ward; Heal draws a green rising ring/cross and particles. Nonattack actions have a restrained lift. Authored frame clips remain supported and start with anticipation; hit clips trigger at impact.

Floating numbers use actual model results, including zero damage against Block and capped healing. HUD numbers update to authoritative HP immediately at impact; bar fill interpolates exponentially toward it. Damage shake/zoom begins only at impact. World effects transform with the battlefield; HUD coordinates and card fan geometry do not change.

Tests cover rapid card/End Turn inputs, delayed mutations, exactly-once long-frame resolution, pause/resume, menu cancellation, lethal attacks with no retaliation, support effects, heavy strength, and HP interpolation. Existing rule/campaign tests remain intact. Procedural effects are placeholders; no final art or audio is included.
