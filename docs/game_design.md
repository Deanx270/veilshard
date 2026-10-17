# Prototype rules and extension points

Each stage starts at 30 HP with a fresh 12-card deck. Each player turn restores energy to 2 and draws 3 cards. Attack costs 1 and deals 6; Heavy Attack costs 2 and deals 10; Shield costs 1 and grants 6 Block; Heal costs 1 and restores up to 6 HP. Played cards enter discard immediately. Unplayed cards enter discard at End Turn. Draws refill an exhausted pile from shuffled discards, including when exhaustion happens partway through a draw.

Damage consumes Block first, then HP; values never fall below zero. Player Block expires after the enemy action, including Charge, Defend, and Heal. Enemy Block expires at the start of its next enemy action, after protecting through one complete player turn. A Defend action then grants new Block. Enemy healing cannot exceed maximum HP.

An intent is selected at the start of a player turn and remains fixed until executed. Killing the enemy prevents its action. The Guardian enters its alternate pattern when choosing its next intent below 50% HP; a threshold-crossing hit does not secretly change the already displayed action. Charge is a telegraph/no-op; the configured following Special action specifies the full damage, with no hidden multiplier.

All five stages use deterministic cyclic patterns configured in `data/stages.json`. The Guardian starts its alternate cycle at Charge. Stage victories unlock the next introduction, and the fifth victory opens the ending. Defeat offers a retry of the current stage. A new journey starts from stage one. Progress is session-only.

The model has no Pygame dependency. `Battle.play` and `Battle.end_turn` return presentation effects; `Campaign` manages navigation independently. The app locks input briefly after actions and defers scene resolution until feedback has been displayed. Pause freezes combat presentation and locks without taking another turn.

Future work: card status effects, richer enemy models, audio, persistent progress, data validation, localization, controller support, final art, and accessible text sizing. Add distinct effect dispatch before adding card categories beyond attack/block/heal. Current JSON is trusted project configuration, not a mod-loading format.

Visual direction is now anime-inspired low-poly 2.5D; see `visual_direction.md`. This changes only rendering and asset contracts, not these rules.
