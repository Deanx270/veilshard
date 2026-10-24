import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
import pytest
from src.core.app import App
from src.enemies.intentions import Intent
from src.rendering.animation_preview import AnimationPreview


@pytest.fixture
def app(tmp_path):
    a = App()
    a.campaign.stage["debug"] = True
    a.action("start")
    a.action("battle")
    a.update(.3)
    for name in ("attack10.png", "attack2.png", "attack1.png"):
        pygame.image.save(pygame.Surface((160,90), pygame.SRCALPHA), str(tmp_path/name))
    a.preview_cache[a.campaign.stage["id"]] = AnimationPreview(a.battlefield.actors["player"], a.campaign.stage["id"], tmp_path)
    yield a
    pygame.quit()


def test_preview_order_ratio_playback_and_restore(app):
    original = app.battlefield.actors["player"]
    app.action("preview_toggle")
    p = app.preview
    assert [path.name for path in p.paths] == ["attack1.png", "attack2.png", "attack10.png"]
    app.event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_SPACE))
    app.update(.09)
    assert p.index == 1
    app.action("pause")
    app.update(2)
    assert p.index == 1
    app.action("resume")
    app.update(.2)
    assert p.index == 2 and not p.playing
    x,y = p.spec["position"]
    app.event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RIGHT))
    app.event(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_UP,mod=pygame.KMOD_SHIFT))
    assert p.spec["position"] == [x+10,y-1]
    app.action("preview_larger")
    w,h = p.frames[0].get_size()
    assert abs(w-h*16/9) <= .5
    app.draw()
    assert "preview_log" in app.buttons and "end" not in app.buttons
    app.action("preview_toggle")
    assert app.battlefield.actors["player"] is original
    assert original.spec["position"] == [x,y]


def test_preview_blocks_combat_and_cannot_interrupt_action(app):
    b = app.campaign.battle
    app.action("preview_toggle")
    for _ in range(10):
        app.action("end")
        app.update(.1)
    assert b.turn == 1 and b.player.hp == 30 and not app.timeline.active
    app.action("menu")
    assert app.preview is None
    app.action("start")
    app.action("battle")
    app.action("end")
    app.action("preview_toggle")
    assert app.preview is None and app.timeline.active
    app.update(3)
    assert app.campaign.battle.turn == 2


def test_stage_one_clips_and_logged_placement(app):
    actor = app.battlefield.actors["player"]
    assert actor.spec["position"] == [741, 939]
    assert actor.size == (1445, 813)
    assert actor.spec["anchor"] == [0.5, 1.0]
    clips = actor.spec["animations"]
    assert len(clips["idle"]["frames"]) == 14 and clips["idle"]["loop"]
    assert len(clips["attack"]["frames"]) == 15
    assert all("heavy" not in path for path in clips["attack"]["frames"])
    assert len(clips["heavy"]["frames"]) == 14
    assert not any(path.endswith(("attack10.png", "attack12.png", "attack13.png")) for path in clips["heavy"]["frames"])
    actor.trigger("idle")
    actor.update(1.5)
    assert actor.state == "idle" and actor.frame() is actor.clips["idle"][0][1]
    for kind, damage in (("attack", 6), ("heavy", 11)):
        b = app.campaign.battle
        b.energy = 2
        b.deck.hand = [next(c for c in app.campaign.cards if c.id == kind)]
        hp = b.enemy.hp
        app.begin_action(kind, "player", lambda: b.play(0))
        assert actor.state == kind
        impact = app.timeline.impact
        app.update(impact-.01)
        assert b.enemy.hp == hp
        app.action("end")
        app.update(.011)
        assert b.enemy.hp == hp-damage
        assert actor.frame() is actor.clips[kind][0][clips[kind]["impact_frame"]]
        app.update(app.lock+.01)
        assert not app.lock and actor.state == "idle" and b.turn == 1


def test_exported_actor_keeps_anchor_during_actions_and_hits(app, monkeypatch):
    field = app.battlefield
    actor = field.actors["player"]
    offsets = []
    monkeypatch.setattr(actor, "draw", lambda surface, displacement: offsets.append(displacement))
    for kind in ("attack", "heavy", "block", "heal"):
        app.timeline.start(kind, "player", lambda: None)
        app.timeline.update(.1)
        field.motion = app.timeline
        field.reactions["player"] = (.15, 36)
        field.draw(app.canvas, 0, app.effects, app.ui.font(24))
        assert offsets[-1] == field.background.actor_offset
        assert actor.spec["position"] == [741, 939]
        app.timeline.cancel()


def test_attack_canvas_registration_is_fixed_and_matches_idle(app):
    actor = app.battlefield.actors["player"]
    idle = actor.clips["idle"][0][0].get_bounding_rect(min_alpha=100)
    for kind in ("attack", "heavy"):
        first = actor.clips[kind][0][0].get_bounding_rect(min_alpha=100)
        offset = actor.clip_offsets[kind]
        assert abs(first.left + offset[0] - idle.left) <= 1
        assert abs(first.top + offset[1] - idle.top) <= 1
        actor.trigger(kind)
        for _ in range(8):
            actor.update(.1)
            assert actor.clip_offsets[kind] == offset
            assert actor.spec["position"] == [741, 939]


def test_frame_shadows_cached_and_debug_logged(app, monkeypatch):
    actor = app.battlefield.actors["player"]
    shadows = actor.frame_shadows
    assert shadows and len(shadows.cache) >= 29
    assert len({id(s) for s, _ in shadows.cache.values()}) > 1
    assert all(s.get_width()*s.get_height() < actor.size[0]*actor.size[1]*.1 for s, _ in shadows.cache.values())
    def unexpected(*args, **kwargs):
        raise AssertionError("Playback must not regenerate shadow surfaces")
    with monkeypatch.context() as m:
        m.setattr(pygame.transform, "smoothscale", unexpected)
        for state in ("idle", "attack", "heavy"):
            actor.trigger(state)
            actor.update(.2)
            actor.draw(app.canvas)
    app.action("preview_toggle")
    p = app.preview
    before = p.spec["position"][:]
    original_shadow = actor.spec["shadow"]
    app.action("preview_shadow_darker")
    app.action("preview_shadow_right")
    app.action("preview_shadow_deeper")
    assert p.report()["shadow"]["opacity"] == original_shadow["opacity"]+5
    assert p.report()["shadow"]["offset"] == [original_shadow["offset"][0]+3, original_shadow["offset"][1]]
    assert p.report()["shadow"]["depth"] == round(original_shadow["depth"]+.02,2)
    assert p.spec["position"] == before
    assert actor.spec["shadow"]["opacity"] == original_shadow["opacity"]
    app.draw()
    assert "preview_shadow_toggle" in app.buttons


def test_shadow_rotation_pivot_and_debug(app, monkeypatch):
    from src.rendering.frame_shadow import FrameShadows
    frame = pygame.Surface((100,100), pygame.SRCALPHA)
    frame.fill((255,255,255,255))
    config = {"ground":[.5,1], "depth":.2, "angle":90}
    shadow, origin = FrameShadows([frame], config).cache[id(frame)]
    assert shadow.get_size() == (20,100)
    assert origin == (30,50)  # Ground pivot (50,100) stays fixed.
    app.action("preview_toggle")
    position = app.preview.spec["position"][:]
    original_angle = app.preview.original.spec["shadow"]["angle"]
    app.action("preview_shadow_clockwise")
    assert app.preview.report()["shadow"]["angle"] == (original_angle-5+180)%360-180
    assert app.preview.spec["position"] == position
    assert app.preview.original.spec["shadow"]["angle"] == original_angle
    def fail(*args, **kwargs): raise AssertionError("Rotation must be cached")
    monkeypatch.setattr(pygame.transform, "rotate", fail)
    app.preview.draw(app.canvas)
    app.draw()
    assert "preview_shadow_clockwise" in app.buttons


def test_custom_attacks_skip_placeholder_projectile(app, monkeypatch):
    field = app.battlefield
    def fail(*args, **kwargs): raise AssertionError("Custom clip must not draw the old projectile")
    monkeypatch.setattr(pygame.draw, "line", fail)
    for kind in ("attack", "heavy"):
        app.begin_action(kind, "player", lambda: [])
        app.update(app.timeline.impact-.04)
        field.draw(app.canvas,0,app.effects,app.ui.font(24))
        app.timeline.cancel()


def test_contact_shadow_has_soft_edges_and_ignores_frame_art():
    from src.rendering.frame_shadow import FrameShadows
    frames = [pygame.Surface((100,100),pygame.SRCALPHA) for _ in range(2)]
    frames[1].fill((255,255,255,255))
    shadows = FrameShadows(frames,{"mode":"contact"})
    first, origin = shadows.cache[id(frames[0])]
    assert first is shadows.cache[id(frames[1])][0]
    assert first.get_at((0,0)).a == 0
    assert first.get_at(first.get_rect().center).a > 100


def test_grounded_shadow_tracks_feet_without_rotating_them_away():
    from src.rendering.frame_shadow import FrameShadows
    frames = []
    for dx,dy in ((0,0),(15,-10)):
        frame = pygame.Surface((160,160),pygame.SRCALPHA)
        pygame.draw.rect(frame,(255,255,255,255),(50+dx,30+dy,40,110))
        frames.append(frame)
    for angle in (0,45,-45,90,180):
        config={"mode":"frame","foot_locked":True,"angle":angle,"depth":.3,"opacity":255}
        shadows=FrameShadows(frames,config)
        for frame,(dx,dy) in zip(frames,((0,0),(15,-10))):
            canvas=pygame.Surface((300,300),pygame.SRCALPHA)
            shadows.draw(canvas,frame,(50,50))
            # Both feet retain contact despite changes in pose/direction.
            for x in (55+dx,84+dx):
                assert any(canvas.get_at((50+x,50+140+dy+d)).a>20 for d in range(-4,5))


def test_stage_one_hurt_animation_and_exclusions(app):
    from src.combat.battle import Effect
    actor = app.battlefield.actors["player"]
    clips = actor.spec["animations"]
    hit_frames = [path.split("/")[-1] for path in clips["hit"]["frames"]]
    hit_heavy_frames = [path.split("/")[-1] for path in clips["hit_heavy"]["frames"]]

    # Normal attack exclusions: hurt1, 5, 6, 7, 8, 9, 10, 12, 14
    assert len(hit_frames) == 7
    assert hit_frames == ["hurt_02.png", "hurt_03.png", "hurt_04.png", "hurt_11.png", "hurt_13.png", "hurt_15.png", "hurt_16.png"]
    assert not any(f in hit_frames for f in ("hurt_01.png", "hurt_05.png", "hurt_06.png", "hurt_07.png", "hurt_08.png", "hurt_09.png", "hurt_10.png", "hurt_12.png", "hurt_14.png"))

    # Heavy attack exclusions: hurt2, 4
    assert len(hit_heavy_frames) == 14
    assert hit_heavy_frames == ["hurt_01.png", "hurt_03.png", "hurt_05.png", "hurt_06.png", "hurt_07.png", "hurt_08.png", "hurt_09.png", "hurt_10.png", "hurt_11.png", "hurt_12.png", "hurt_13.png", "hurt_14.png", "hurt_15.png", "hurt_16.png"]
    assert "hurt_02.png" not in hit_heavy_frames and "hurt_04.png" not in hit_heavy_frames

    # Triggering and auto-return to idle
    actor.trigger("hit")
    assert actor.state in ("hit", "hurt") and actor.hit_time > 0
    actor.update(0.71)
    assert actor.state == "idle" and actor.spec["position"] == [741, 939]

    actor.trigger("hit_heavy")
    assert actor.state in ("hit_heavy", "hurt_heavy") and actor.hit_time > 0
    actor.update(1.41)
    assert actor.state == "idle" and actor.spec["position"] == [741, 939]

    # Feedback triggers appropriate clip without procedural knockback
    field = app.battlefield
    field.feedback([Effect("player", "damage", 5)], "opponent", "attack")
    assert actor.state in ("hit", "hurt")
    assert actor.spec["position"] == [741, 939]

    field.feedback([Effect("player", "damage", 12)], "opponent", "special")
    assert actor.state in ("hit_heavy", "hurt_heavy")
    assert actor.spec["position"] == [741, 939]


def test_stage_one_defend_animation(app):
    actor = app.battlefield.actors["player"]
    clips = actor.spec["animations"]
    assert "defend" in clips
    defend_frames = [path.split("/")[-1] for path in clips["defend"]["frames"]]
    assert len(defend_frames) == 15
    assert defend_frames == [f"defend_{i:02d}.png" for i in range(1, 16)]
    assert clips["defend"]["impact_frame"] == 6

    # Test playing shield card triggers defend animation
    b = app.campaign.battle
    b.energy = 2
    b.player.block = 0
    b.deck.hand = [next(c for c in app.campaign.cards if c.category == "block")]
    app.begin_action("block", "player", lambda: b.play(0))
    assert actor.state in ("defend", "block")
    impact = app.timeline.impact
    app.update(impact - .01)
    assert b.player.block == 0
    app.update(.02)
    assert b.player.block == 6
    assert actor.frame() is actor.clips["defend"][0][6]
    app.update(app.timeline.remaining + .01)
    assert not app.lock and actor.state == "idle" and actor.spec["position"] == [741, 939]


def test_stage_one_heal_animation(app):
    actor = app.battlefield.actors["player"]
    clips = actor.spec["animations"]
    assert "heal" in clips
    heal_frames = [path.split("/")[-1] for path in clips["heal"]["frames"]]
    assert len(heal_frames) == 14
    assert heal_frames == [f"heal_{i:02d}.png" for i in range(1, 15)]
    assert clips["heal"]["impact_frame"] == 7
    assert "canvas_offset" not in clips["heal"] or clips["heal"]["canvas_offset"] == [0, 0]
    assert actor.clip_offsets.get("heal", (0, 0)) == (0, 0)

    # Test playing heal card triggers heal animation and resolves at impact
    b = app.campaign.battle
    b.energy = 2
    b.player.hp = 20
    b.deck.hand = [next(c for c in app.campaign.cards if c.category == "heal")]
    app.begin_action("heal", "player", lambda: b.play(0))
    assert actor.state == "heal"
    impact = app.timeline.impact
    app.update(impact - .01)
    assert b.player.hp == 20
    app.update(.02)
    assert b.player.hp == 26
    assert actor.frame() is actor.clips["heal"][0][7]
    app.update(app.timeline.remaining + .01)
    assert not app.lock and actor.state == "idle" and actor.spec["position"] == [741, 939]


def test_stage_one_damage_skips_placeholder_hit_effect(app):
    b = app.campaign.battle
    for kind in ("attack", "heavy"):
        b.deck.hand = [next(c for c in app.campaign.cards if c.id == kind)]
        app.hand.sync(b.deck.hand)
        b.energy = 2
        hp = b.enemy.hp
        app.begin_action(kind, "player", lambda: b.play(0))
        impact = app.timeline.impact
        app.update(impact - .01)
        assert b.enemy.hp == hp
        app.update(.02)
        assert b.enemy.hp < hp
        # Damage popup is present
        assert len(app.effects.popups) > 0
        # Placeholder hit effect burst is skipped for stage 1 enemy damage
        assert len(app.effects.bursts) == 0
        app.effects.popups.clear()
        app.update(app.lock + .01)

def test_preview_switch_target_to_enemy(app):
    player_actor = app.battlefield.actors["player"]
    original_opponent = app.battlefield.actors["opponent"]
    app.action("preview_toggle")
    assert app.preview is not None
    assert app.preview.target == "player"

    # Switch target to opponent via action button
    app.action("preview_switch_target")
    assert app.preview.target == "opponent"
    assert app.preview.stage_id == 1
    assert app.battlefield.actors["opponent"] is app.preview
    assert app.battlefield.actors["player"] is not app.preview
    # Check that enemy_01 frames are loaded
    assert len(app.preview.paths) == 57
    assert any("attack_01.png" in p.name for p in app.preview.paths)
    assert any("hurt_01.png" in p.name for p in app.preview.paths)
    assert any("idle_01.png" in p.name for p in app.preview.paths)
    rep = app.preview.report()
    assert rep["target"] == "opponent"
    assert rep["stage_id"] == 1

    # Test stepping
    app.action("preview_step_forward")
    assert app.preview.index == 1
    app.action("preview_step_back")
    assert app.preview.index == 0

    # Test Tab switches back to player
    app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_TAB))
    assert app.preview.target == "player"
    assert app.battlefield.actors["player"] is app.preview
    assert app.battlefield.actors["opponent"] is original_opponent

    # Enemy preview layer is above player during attack frames and below during idle/hurt
    app.action("preview_switch_target")
    app.preview.index = next(i for i, p in enumerate(app.preview.paths) if p.name.startswith("attack"))
    assert app.preview.order > player_actor.order
    app.preview.index = next(i for i, p in enumerate(app.preview.paths) if p.name.startswith("idle"))
    assert app.preview.order < player_actor.order

    # Close preview restores both actors
    app.action("preview_toggle")
    assert app.preview is None
    assert app.battlefield.actors["player"] is player_actor
    assert app.battlefield.actors["opponent"] is original_opponent
    app.draw()
    assert app.buttons["preview_toggle"].centerx == 800 and app.buttons["preview_toggle"].top < 60

    # Live opponent preserves aspect ratio and renders above player only when attacking
    assert original_opponent.size == (1363, 669)
    assert original_opponent.order < player_actor.order
    original_opponent.trigger("attack")
    assert original_opponent.order > player_actor.order
    original_opponent.trigger("hit")
    assert original_opponent.order < player_actor.order
    original_opponent.trigger("idle")
    assert original_opponent.order < player_actor.order


def test_stage_one_enemy_clips_lock_and_rightward_parallax(app):
    from src.core.input import viewport
    player = app.battlefield.actors["player"]
    enemy = app.battlefield.actors["opponent"]
    assert enemy.spec["position"] == [711, 859]
    assert enemy.size == (1363, 669)
    assert enemy.spec["shadow"]["angle"] == 125
    assert enemy.spec["shadow"]["width"] == 0.7
    assert enemy.spec["shadow"]["depth"] == 0.6

    clips = enemy.spec["animations"]
    attack_frames = [p.split("/")[-1] for p in clips["attack"]["frames"]]
    heavy_frames = [p.split("/")[-1] for p in clips["heavy"]["frames"]]
    hit_frames = [p.split("/")[-1] for p in clips["hit"]["frames"]]
    hit_heavy_frames = [p.split("/")[-1] for p in clips["hit_heavy"]["frames"]]

    # Normal attack skips attack_03 to attack_11 (except attack_04), impact at sequence index 6 (attack_15.png)
    assert len(attack_frames) == 15
    assert attack_frames == ["attack_01.png", "attack_02.png", "attack_04.png", *[f"attack_{i:02d}.png" for i in range(12, 24)]]
    assert clips["attack"]["impact_frame"] == 6
    assert attack_frames[clips["attack"]["impact_frame"]] == "attack_15.png"

    # Heavy attack uses all 23 frames, impact at sequence index 14 (attack_15.png)
    assert len(heavy_frames) == 23
    assert heavy_frames == [f"attack_{i:02d}.png" for i in range(1, 24)]
    assert clips["heavy"]["impact_frame"] == 14
    assert heavy_frames[clips["heavy"]["impact_frame"]] == "attack_15.png"

    # Normal hurt skips 2, 4, 6, 8, 9 to 13, 15, 17 -> 8 frames
    assert len(hit_frames) == 8
    assert hit_frames == ["hurt_01.png", "hurt_03.png", "hurt_05.png", "hurt_07.png", "hurt_14.png", "hurt_16.png", "hurt_18.png", "hurt_19.png"]

    # Heavy hurt uses all 19 frames
    assert len(hit_heavy_frames) == 19
    assert hit_heavy_frames == [f"hurt_{i:02d}.png" for i in range(1, 20)]

    # Test normal and heavy enemy attacks: impact at attack_15, parallax right, card locked while enemy non-idle
    b = app.campaign.battle
    for kind, amount, expected_impact, expected_hit_state in (("attack", 5, 0.6, "hit"), ("heavy", 14, 1.4, "hit_heavy")):
        b.player.hp = 30
        b.intent = Intent(kind, amount)
        app.action("end")
        assert enemy.state == kind
        assert pytest.approx(app.timeline.impact) == expected_impact

        # Before impact_frame (attack_15): no damage, player still idle
        app.update(expected_impact - 0.05)
        assert b.player.hp == 30 and player.state == "idle"

        # At impact_frame (attack_15): damage dealt, player hurt starts, parallax kicks right (+x)
        app.update(0.06)
        assert b.player.hp == 30 - amount
        assert player.state == expected_hit_state
        assert enemy.frame() is enemy.clips[kind][0][clips[kind]["impact_frame"]]
        assert app.battlefield.camera.direction == 1
        if kind == "attack":
            normal_strength = app.battlefield.camera.strength
        else:
            assert app.battlefield.camera.strength > normal_strength
        app.update(0.05)
        assert app.background.shift[0] > 0

        # While enemy is still in attack animation after impact, cards are not drawn yet
        assert enemy.state == kind and app.lock > 0
        assert app.visible_hand() == []

        # Finish animations
        app.update(app.lock + 0.05)
        assert enemy.state == "idle" and player.state == "idle" and not app.lock
        assert len(app.visible_hand()) == 3


def test_stage_one_debug_menu_disabled_by_default():
    a = App()
    try:
        a.action("start")
        a.action("battle")
        a.update(.3)
        assert not a.campaign.stage.get("debug", False)
        assert not a.battlefield.background.options.get("debug_controls", False)
        a.draw()
        assert "preview_toggle" not in a.buttons
        a.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F6))
        assert a.preview is None
        a.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F1))
        assert not a.battlefield.camera.debug
    finally:
        pygame.quit()
def test_stage_two_debug_menus_and_opponent_preview():
    a = App()
    try:
        a.action("start")
        a.campaign.index = 1
        a.load_stage()
        a.action("battle")
        a.update(.3)
        assert not a.campaign.stage.get("debug", False)
        assert not a.battlefield.background.options.get("debug_controls", False)
        a.draw()
        assert "preview_toggle" not in a.buttons
        a.campaign.stage["debug"] = True
        a.draw()
        assert "preview_toggle" in a.buttons
        a.action("preview_toggle")
        assert a.preview is not None
        assert a.preview.target == "player"
        a.action("preview_switch_target")
        assert a.preview.target == "opponent"
        assert len(a.preview.paths) == 83
        assert a.preview.spec["shadow"].get("foot_locked") is True
        assert a.preview.spec["shadow"].get("foot_band") == 0.9
        a.action("preview_larger")
        expected_size = tuple(a.preview.spec["size"])
        a.preview.original.apply_preview(a.preview)
        a.action("preview_toggle")
        assert a.preview is None
        assert a.battlefield.actors["opponent"].size == expected_size
        assert a.battlefield.actors["opponent"].frame().get_size() == expected_size
    finally:
        pygame.quit()
def test_bold_damage_text_on_heavy_attacks(app):
    from src.combat.battle import Effect
    app.effects.popups.clear()
    app.effects.add([Effect("enemy", "damage", 6)], app.campaign.stage, "attack", "player")
    assert len(app.effects.popups) == 1
    assert app.effects.popups[0].bold is False

    app.effects.popups.clear()
    app.effects.add([Effect("enemy", "damage", 10)], app.campaign.stage, "heavy", "player")
    assert len(app.effects.popups) == 1
    assert app.effects.popups[0].bold is True

    app.effects.popups.clear()
    app.effects.add([Effect("player", "damage", 14)], app.campaign.stage, "heavy", "opponent")
    assert len(app.effects.popups) == 1
    assert app.effects.popups[0].bold is True

def test_stage_two_skips_placeholder_hit_effect_and_defend_offset():
    from src.combat.battle import Effect
    from src.rendering.effects import Effects
    import json
    stages = json.load(open("data/stages.json"))
    s2 = stages[1]
    effects = Effects()

    effects.add([Effect("enemy", "damage", 6)], s2, "attack", "player")
    assert len(effects.popups) == 1
    assert len(effects.bursts) == 0

    effects.popups.clear()
    effects.add([Effect("player", "damage", 8)], s2, "attack", "opponent")
    assert len(effects.popups) == 1
    assert len(effects.bursts) == 0

    effects.popups.clear()
    effects.bursts.clear()
    effects.add([Effect("enemy", "block", 7)], s2, "defend", "opponent")
    assert len(effects.bursts) == 1
    spec = s2["opponent"]
    anchor = spec.get("anchor", [0.5, 1.0])
    ground = spec.get("shadow", {}).get("ground", anchor)
    expected_x = round(spec["position"][0] + (ground[0] - anchor[0]) * spec["size"][0] * spec.get("scale", 1.0)) - 80
    assert effects.bursts[0]["center"][0] == expected_x
    assert effects.popups[0].position[0] == expected_x

def test_stage_two_enemy_hurt_frames_and_attack_impact():
    import json
    stages = json.load(open("data/stages.json"))
    s2 = stages[1]
    clips = s2["opponent"]["animations"]

    assert clips["attack"]["impact_frame"] == 9
    attack_frames = [p.split("/")[-1] for p in clips["attack"]["frames"]]
    assert attack_frames[clips["attack"]["impact_frame"]] == "attack_10.png"

    hit_frames = [p.split("/")[-1] for p in clips["hit"]["frames"]]
    assert len(hit_frames) == 10
    assert hit_frames == ["hurt_01.png", "hurt_03.png", "hurt_05.png", "hurt_07.png", "hurt_08.png", "hurt_10.png", "hurt_12.png", "hurt_14.png", "hurt_16.png", "hurt_18.png"]

    hit_heavy_frames = [p.split("/")[-1] for p in clips["hit_heavy"]["frames"]]
    assert len(hit_heavy_frames) == 19
    assert hit_heavy_frames == [f"hurt_{i:02d}.png" for i in range(1, 20)]

def test_stage_three_stormcaller_animations_and_shake():
    import json
    stages = json.load(open("data/stages.json"))
    s3 = stages[2]
    assert s3["debug"] is False
    assert s3["background"]["parallax"]["debug_controls"] is False

    clips = s3["opponent"]["animations"]

    # Normal hurt skips every 2nd frame (9 frames)
    hit_frames = [p.split("/")[-1] for p in clips["hit"]["frames"]]
    assert len(hit_frames) == 9
    assert hit_frames == [f"hurt_{i:02d}.png" for i in range(1, 18, 2)]

    # Heavy hurt plays whole animation (17 frames)
    hit_heavy_frames = [p.split("/")[-1] for p in clips["hit_heavy"]["frames"]]
    assert len(hit_heavy_frames) == 17
    assert hit_heavy_frames == [f"hurt_{i:02d}.png" for i in range(1, 18)]

    # Normal attack impact at 10th frame (index 9)
    assert clips["attack"]["impact_frame"] == 9

    # Charge moved 170 pixels to right, block effect starts at 13th frame (index 12)
    assert clips["defend"]["canvas_offset"] == [170, 0]
    assert clips["defend"]["impact_frame"] == 12

    # Heavy attack 2670x1280 canvas with downward shift reverted to align with idle, impact at 17th frame (index 16)
    assert clips["heavy"]["canvas_offset"] == [0, -60]
    assert clips["heavy"]["source_size"] == [2670, 1280]
    assert clips["heavy"]["impact_frame"] == 16

    # Battlefield thunderfall shake values test
    from src.rendering.battlefield import Battlefield
    from unittest.mock import MagicMock
    bf = MagicMock(spec=Battlefield)
    bf.actors = {"opponent": MagicMock()}
    bf.thunderfall_shake_y = Battlefield.thunderfall_shake_y.__get__(bf, Battlefield)

    bf.actors["opponent"].state = "heavy"
    # 16th frame (idx 15) moves map 20 pixels down
    bf.actors["opponent"].frame_index.return_value = 15
    assert bf.thunderfall_shake_y() == 20

    # 17th frame (idx 16) moves 10 pixels up (-10)
    bf.actors["opponent"].frame_index.return_value = 16
    assert bf.thunderfall_shake_y() == -10

    # 18th frame (idx 17) moves 10 pixels down (+10)
    bf.actors["opponent"].frame_index.return_value = 17
    assert bf.thunderfall_shake_y() == 10

    # 19th frame (idx 18) stays same as 18th (+10)
    bf.actors["opponent"].frame_index.return_value = 18
    assert bf.thunderfall_shake_y() == 10

    # 20th frame (idx 19) returns to original position (0)
    bf.actors["opponent"].frame_index.return_value = 19
    assert bf.thunderfall_shake_y() == 0

    # Ground and crop defined for HUD and effect centering
    assert s3["opponent"]["shadow"]["ground"] == [0.851, 0.722]
    assert s3["opponent"]["shadow"]["crop"] == [0.6, 0.08, 0.39, 0.68]

def test_card_draw_timing_and_defeat_text():
    from src.core.app import App
    a = App(start_stage=1)
    a.action("start")
    a.action("battle")
    b = a.campaign.battle
    # Empty hand
    b.deck.hand = []
    a.draw_battle((0, 0))
    # Now simulate loss
    b.player.hp = 0
    b.status = "lost"
    # When HP is depleted, visible hand is empty
    assert a.visible_hand() == []

def test_enemy_turn_card_draw_waits_for_animation():
    from src.core.app import App
    a = App(start_stage=1)
    a.action("start")
    a.action("battle")
    b = a.campaign.battle
    # Player ends turn
    a.action("end")
    assert a.enemy_turn_in_progress is True
    # While enemy turn is in progress, visible_hand is empty (player does not see cards early)
    assert a.visible_hand() == []
    # Advance time through the animation
    for _ in range(30):
        a.update(0.1)
    # Once enemy animation is over, enemy_turn_in_progress becomes False and cards appear
    assert a.enemy_turn_in_progress is False
    assert len(a.visible_hand()) == 3


def test_stage_three_debug_menu_disabled_by_default():
    from src.core.app import App
    a = App(start_stage=3)
    try:
        a.action("start")
        a.action("battle")
        a.update(.3)
        assert not a.campaign.stage.get("debug", False)
        assert not a.battlefield.background.options.get("debug_controls", False)
        a.draw()
        assert "preview_toggle" not in a.buttons
        a.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F6))
        assert a.preview is None
        a.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F1))
        assert not a.battlefield.camera.debug
    finally:
        pygame.quit()
