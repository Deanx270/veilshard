# Floating battle HUD and shallow card fan

The entire 1600×900 world composite renders behind the HUD. No footer, viewport subtraction, aspect change, or background crop is used to accommodate cards. Blender layers, characters, shadows, and camera effects remain unchanged.

`src/ui/card_layout.py` owns pure geometry and inverse-transform hit testing. `FanConfig` exposes portrait dimensions (170×248), spacing, maximum span, curvature, rotation, easing, and hover movement. A three-card hand has 7-degree outer rotations and a 14-pixel center rise. Two cards oppose gently; a single card is centered upright. Larger hands adapt spacing, with angles capped at 8.75 degrees and rise at 17.5 pixels. Zero cards have no hit targets.

`src/ui/card_hand.py` owns presentation instances, preserving the identity of each occurrence when the deck contains repeated references to the same card definition. Playing removes the exact selected occurrence, then surviving poses ease toward the new fan. Hover lifts by 32 pixels, scales to 1.06, and straightens the selected card while drawing it last. Hover retention over the original footprint prevents oscillation as the card moves. Click selection always uses the actual visible topmost card and inverse rotation/scale, excluding transparent corners and shadows. Transform quantization is shared with hit testing; rounding may cause subpixel differences at antialiased edges. Cached faces, transformed images, and shadows use a bounded 160-entry transform cache.

`src/ui/card_art.py` produces original procedural card illustrations and restrained fantasy frames. Heavy Attack has a separate purple crystal identity, while Attack is warm orange, Shield blue, and Heal green. Text comes from card definitions. Affordability darkens a card and adds a label; hover can still inspect it, but the combat model rejects a play without sufficient energy.

`src/ui/battle_hud.py` positions the compact translucent stage/objective at top-left, turn and working pause control at top-right, portrait/HP/Block/energy bottom-left, enemy status relative to the configured character anchor, and a circular End Turn button bottom-right. Its click region is circular and includes a brief pressed treatment. No settings or speed controls are displayed because those features are not implemented.

The gameplay layer is unchanged. Card and camera animations freeze while paused. The existing letterboxed mouse mapping feeds all HUD/card input. All UI coordinates use logical pixels rather than monitor coordinates. Future hand-size changes can use 1–6 cards without new layout coordinates, although gameplay still draws three.

Validation: pytest covers counts 0–6, inverse rotation and transparent corners, duplicate occurrence reflow, overlapping draw/click order, hover, affordability, empty hands, and resized clicks. A rendered background pixel below the former footer confirms the world is visible there. Existing campaign and combat tests still pass. Three-card, hovered, and six-card screenshots were inspected. Final Blender assets remain pending; this is an interface redesign using current procedural scenery.

## Shard Resonance

The post-battle `shop` scene now presents Shard Resonance through `src/ui/shard_resonance.py`. It samples three distinct upgrades on entry, prioritizing those not at maximum level, and keeps them fixed until a new battle result. Campaign.buy, costs, caps, shard rewards and upgrade effects are unchanged. No stage locks exist in the current catalog; unavailable purchases show the missing shard amount, while capped upgrades show Fully attuned. Aether Conduit is available at level zero, not locked.

Cards select on click, ease upward on hover/selection, show actual current-to-next values and diamond progression markers. Enhance activates only on a matching mouse release; cancelled presses and repeated releases do not buy. A short purchase cooldown, glow pulse, status message and interpolated shard balance provide feedback. Numeric upgrade previews immediately use authoritative state. Proceed follows victory; Retry follows defeat, with previous-stage retry only after defeat. F6 battle preview is independent. Icons and the cached background sigil are procedural, with no additional runtime dependencies.

## Moonlit ice identity

Attack/heavy internal IDs and all combat behavior remain unchanged; display names are Frost Bolt and Glacial Bolt. Shared cached geometric icons in resonance_icons.py connect offensive card artwork with Frost Focus and Moonshard Surge. Upgrade keys, costs, caps and scaling are unchanged. The remaining upgrades are Vital Infusion, Crystal Aegis, Lunar Renewal and Resonance Conduit. Existing animations/timing/effects are untouched. Battle card title sizing accommodates longer upgraded names within the original card geometry.
