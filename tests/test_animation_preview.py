import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
import pytest
from src.core.app import App
from src.rendering.animation_preview import AnimationPreview


@pytest.fixture
def app(tmp_path):
    a = App()
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
    app.update(1)
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
    for kind, damage in (("attack", 6), ("heavy", 10)):
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
        app.update(app.timeline.remaining+.01)
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
