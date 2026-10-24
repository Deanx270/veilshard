import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
import pygame
from src.core.resources import read_data
from src.rendering.assets import Assets
from src.rendering.characters import CharacterSprite


def test_stage3_enemy_shadow_visible_stable_and_is_cached(monkeypatch):
    pygame.init()
    pygame.display.set_mode((1, 1))
    try:
        stage = next(s for s in read_data("stages") if s["id"] == 3)
        spec = stage["opponent"]
        shadow = spec["shadow"]
        player = stage["player"]["shadow"]
        assert shadow["enabled"] and shadow["mode"] == "frame" and shadow["foot_locked"]
        assert shadow["opacity"] == player["opacity"]
        actor = CharacterSprite(Assets(), spec, stage["accent"], enemy=True)
        target = pygame.Surface((1600,900), pygame.SRCALPHA)
        def fail(*args, **kwargs):
            raise AssertionError("Shadow playback must use cached surfaces")
        monkeypatch.setattr(pygame.transform, "smoothscale", fail)
        monkeypatch.setattr(pygame.transform, "scale", fail)
        monkeypatch.setattr(pygame.transform, "rotate", fail)
        origins_by_size = {}
        for name, (frames, _, _) in actor.clips.items():
            for frame in frames:
                target.fill((0,0,0,0))
                registration = actor.clip_offsets.get(name,(0,0))
                origin = tuple(round(spec["position"][i]-frame.get_size()[i]*spec["anchor"][i])+registration[i] for i in range(2))
                actor.frame_shadows.draw(target, frame, origin)
                bounds = target.get_bounding_rect(min_alpha=1)
                assert bounds.width > 20 and bounds.height > 5, name
                # Check lower silhouette contact across every frame, including
                # differently sized heavy exports and registered charge clips.
                w,h=frame.get_size()
                crop=shadow["crop"]
                region=pygame.Rect(round(crop[0]*w),round((crop[1]+crop[3]*.8)*h),round(crop[2]*w),round(crop[3]*.2*h)).clip(frame.get_rect())
                foot=frame.subsurface(region).get_bounding_rect(min_alpha=128).move(region.topleft)
                assert foot.width > 0, name
                contact=pygame.Rect(origin[0]+foot.x-8,origin[1]+actor.frame_shadows.ground_baselines.get(frame.get_size(),foot.bottom)+shadow["offset"][1]-8,foot.width+16,16).clip(target.get_rect())
                assert target.subsurface(contact).get_bounding_rect(min_alpha=5).width > 0, name
                cached, shadow_origin = actor.frame_shadows.cache[id(frame)]
                previous = origins_by_size.setdefault(frame.get_size(), shadow_origin)
                assert shadow_origin == previous, (name, "shadow baseline drift")
                assert cached.get_alpha() == player["opacity"]
                assert cached.get_width()*cached.get_height() < frame.get_width()*frame.get_height()*.15
    finally:
        pygame.quit()


def test_preview_hides_cards_and_restores_them(monkeypatch):
    from src.core.app import App
    from types import SimpleNamespace
    app=App(start_stage=3)
    try:
        calls=[]
        monkeypatch.setattr(app.hand,"draw",lambda *args: calls.append(True))
        app.preview=SimpleNamespace(panel=lambda *args: None)
        app.draw_battle((-1,-1))
        assert not calls
        app.preview=None
        app.draw_battle((-1,-1))
        assert len(calls)==1
    finally:
        pygame.quit()


def test_continuous_projection_has_no_internal_streaks():
    from src.rendering.frame_shadow import FrameShadows
    pygame.init()
    try:
        frame=pygame.Surface((240,320),pygame.SRCALPHA)
        pygame.draw.rect(frame,(255,255,255,255),(60,30,120,260))
        config={"mode":"frame","foot_locked":True,"local_feet":True,
                "depth":.30,"angle":-105,"width":.75}
        shadow,_=FrameShadows([frame],config).cache[id(frame)]
        checked=0
        for y in range(shadow.get_height()):
            filled=[x for x in range(shadow.get_width()) if shadow.get_at((x,y)).a>100]
            if len(filled)>10:
                assert filled[-1]-filled[0]+1 == len(filled)
                checked+=1
        assert checked>10
    finally:
        pygame.quit()
