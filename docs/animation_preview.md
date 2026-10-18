# Animation placement preview

Enter a battle and click **Test animation (F6)**, or press F6. The tool temporarily replaces the player with PNGs from `assets/test-animation`. All frames play in natural filename order (attack1, attack2, ... attack10; heavy variants are included). Space or Play restarts the whole sequence at 12 FPS by default; playback stops on the final frame. FPS buttons adjust playback speed.

- Arrow keys move the image anchor by 10 logical pixels per press; Shift+arrow moves by 1.
- Size +/- buttons or +/- keys resize by 5%, retaining each source image's aspect ratio.
- Log values writes `animation-preview.json` to the project root and prints the same JSON in the terminal. Send this file with the preferred placement.
- F6 closes the preview and restores the original actor. Adjustments survive toggling during this session, separately per stage, but never edit stages.json.

Position is the bottom-center anchor of the complete image canvas in the game's 1600x900 logical battlefield coordinates, before camera/parallax transforms. Transparent margins count toward image size. The preview uses the ground layer's translation and draws beneath foreground objects. Existing camera debug controls still work, except arrows control the character while preview is open. Use Home in parallax debug to reset the camera before judging placement.

Combat input is disabled during preview. Opening is blocked while an action is resolving. Escape pauses playback; the menu restores the original actor. Images load only on first opening per stage; resizing is cached until size changes. Missing/invalid files show an error without disrupting combat. No stage settings or source images are modified. The exported debug JSON is ignored by Git.

## Frame shadows

Stage 1 uses subtle alpha-silhouette ground shadows. F6 exposes On/off, Lighter/Darker, Flatter/Deeper, Narrower/Wider and directional shadow-offset buttons. These alter only the shadow, not the character placement. Log values includes the shadow configuration; debug changes stay temporary until applied to stages.json. Preview uses the same fixed attack registration as live playback.

Shadows are generated from frame alpha using a 96x96 intermediate and cached as small flattened surfaces. Playback performs a cached blit, without pixel scans or scaling. Only size/shape changes rebuild the cache; opacity/offset changes do not. Stage data configures normalized `crop` to exclude distant attack VFX, normalized `ground` to align the projected silhouette with the feet, `width`, `depth`, `opacity`, and logical-pixel `offset`. Source PNGs are unchanged. The crop may need tuning for new art or extended poses; this is a lightweight silhouette projection, not physical lighting.

Shadow Rotate CW / Rotate CCW buttons adjust `angle` by 5 degrees around the configured ground-contact point. Positive angles are counterclockwise. The angle readout and exported shadow settings use degrees. Rotation rebuilds cached shadows only when adjusted, never during playback; shadow position offsets remain independent.

Stage 1 now defaults to `mode: contact`: a soft radial ground patch, shared by all frames of the same size. It has no silhouette, feet, or attack VFX, and stays at the configured ground contact through clip transitions. Existing opacity, width, depth, offset and angle controls apply; Log values includes the mode. `mode: frame` remains available in stage data for comparison. A future Blender-rendered shadow pass can provide directional lighting accuracy if needed.

Stage 1 restores `mode: frame` with `foot_locked: true`. Each cached shadow finds the ground line in the lower character crop. Direction uses a sheared projection that leaves the contact line in place, instead of rotating both feet away from the ground. Width changes fade out near the feet. Frame-specific grounding and the same clip registration as the actor keep the shadow attached as poses change. Existing direction/shape/opacity controls remain; offsets are optional fine corrections. Detection uses the lower 20% of the configured crop and may need a crop adjustment for future art with low-lying effects or airborne poses.
