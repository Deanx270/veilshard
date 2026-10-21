import os
os.environ["SDL_VIDEODRIVER"]="dummy"
os.environ["SDL_AUDIODRIVER"]="dummy"
import pygame
import pytest
from src.core.app import App
from src.rendering.parallax import ParallaxBackground, ParallaxCamera
from src.core.resources import resource

@pytest.fixture
def app():
    a=App(); a.action("start"); a.action("battle"); a.update(.3); a.fade=0
    yield a
    pygame.quit()


def test_center_crop_master_and_static_idle(app):
    bg=app.background
    assert bg.size==(1920,1080) and bg.inset==(160,90)
    assert [l["name"] for l,_ in bg.layers]==["sky","distant","ground","midground","foreground"]
    bg.compare=True
    app.battlefield.camera.reset()
    expanded=pygame.Surface(bg.size)
    bg.draw(expanded)
    frame=pygame.Surface((1600,900)); app.battlefield.camera.present(expanded,frame)
    expected=bg.master.subsurface((160,90,1600,900))
    assert pygame.image.tobytes(frame,"RGB")==pygame.image.tobytes(expected,"RGB")
    bg.compare=False; bg.draw(expanded); before=pygame.image.tobytes(expanded,"RGB")
    app.update(1); bg.draw(expanded)
    assert app.background.shift==(0,0)
    assert pygame.image.tobytes(expanded,"RGB")==before


def test_depth_camera_and_screen_anchored_hud(app):
    camera=app.battlefield.camera; bg=app.background
    camera.target=[40,25]; camera.update(1)
    ground=next(l for l,_ in bg.layers if l["name"]=="ground")
    assert bg.layer_offset(bg.layers[0][0])[0]<bg.layer_offset(ground)[0]<bg.layer_offset(bg.layers[-1][0])[0]
    assert bg.actor_offset[0]==pytest.approx(bg.inset[0]+bg.shift[0]*.5*bg.scale)
    app.draw()
    pos=app.hud.end.center; hand=[(v.pose.x,v.pose.y) for v in app.hand.views]
    camera.impact(); app.update(.05); app.draw()
    assert app.hud.end.center==pos and [(v.pose.x,v.pose.y) for v in app.hand.views]==hand
    bg.enabled=False
    assert bg.layer_offset(bg.layers[0][0])==bg.layer_offset(ground)


@pytest.mark.parametrize("zoom",[.95,1,1.15])
@pytest.mark.parametrize("pan",[(-40,-25),(-40,25),(40,-25),(40,25)])
def test_extreme_camera_has_opaque_coverage(app,zoom,pan):
    bg=app.background; camera=app.battlefield.camera
    camera.target=list(pan); camera.target_zoom=zoom; camera.update(10)
    # Alpha composite reveals true asset gaps rather than opaque backing fills.
    world=pygame.Surface(bg.size,pygame.SRCALPHA)
    for layer,frame in bg.layers:
        world.blit(frame,tuple(round(v) for v in bg.layer_offset(layer)))
    output=pygame.Surface((1600,900),pygame.SRCALPHA)
    camera.present(world,output)
    assert pygame.mask.from_surface(output,248).count()==1600*900


def test_foreground_occludes_sprite_and_master_skips_overlay(app):
    bg=app.background
    layer,front=bg.layers[-1]
    # Find an opaque foreground pixel inside the original viewport.
    point=next((x,y) for y in range(750,980,8) for x in range(180,1700,8) if front.get_at((x,y)).a>=250)
    world=pygame.Surface(bg.size); world.fill((255,0,255))
    bg.draw(world,foreground=True)
    expected=pygame.Surface((1,1));expected.fill((255,0,255))
    expected.blit(front,(0,0),pygame.Rect(point,(1,1)))
    assert world.get_at(point)==expected.get_at((0,0))
    bg.compare=True; world.fill((255,0,255)); bg.draw(world,foreground=True)
    assert world.get_at(point)[:3]==(255,0,255)


def test_debug_controls_pause_reset_and_stage_scope(app):
    camera=app.battlefield.camera
    def key(k):app.event(pygame.event.Event(pygame.KEYDOWN,key=k))
    # By default, stage 1 has debug_controls disabled
    assert not camera.options.get("debug_controls", False)
    key(pygame.K_F1); assert not camera.debug
    # When enabled, debug controls allow runtime camera manipulation
    camera.options["debug_controls"] = True
    key(pygame.K_RIGHT); assert camera.target==[0,0]
    key(pygame.K_F1); key(pygame.K_RIGHT); key(pygame.K_UP)
    assert camera.target==[40,-25]
    key(pygame.K_F2); assert not app.background.enabled
    key(pygame.K_F3); assert app.background.compare
    key(pygame.K_F5); assert camera.target_zoom==.95
    key(pygame.K_F4); assert camera.remaining>0
    app.paused=True; before=camera.remaining; app.update(1); assert camera.remaining==before
    app.paused=False; key(pygame.K_HOME); assert camera.target==[0,0] and camera.zoom==1
    for index in range(1,5):
        app.campaign.index=index;app.load_stage()
        assert not app.battlefield.parallax


def test_layers_cached_and_missing_falls_back(app,monkeypatch):
    bg=app.background
    frames=[frame for _,frame in bg.layers]
    def fail(*args,**kwargs): raise AssertionError("idle must not load/scale images")
    monkeypatch.setattr(pygame.image,"load",fail)
    monkeypatch.setattr(pygame.transform,"smoothscale",fail)
    for _ in range(3):
        app.battlefield.update(.1)
        app.battlefield.draw(app.canvas,0,app.effects,app.ui.font(34))
    assert frames==[frame for _,frame in bg.layers]
    class Missing:
        def image(self,path,size):return None if path.endswith("sky.png") else bg.master
    with pytest.warns(UserWarning): fallback=ParallaxBackground(Missing(),app.campaign.stage["background"])
    assert not fallback.complete
    surface=pygame.Surface(fallback.size);fallback.draw(surface)
    assert surface.get_at((800,500))==fallback.master.get_at((800,500))


def test_zoomed_opaque_world_replaces_previous_frame(app):
    camera=app.battlefield.camera
    world=pygame.Surface(app.background.size);world.fill((20,90,140))
    target=pygame.Surface((1600,900));target.fill((255,0,255))
    camera.current_zoom=.95;camera.present(world,target)
    assert all(abs(a-b)<=3 for a,b in zip(target.get_at((0,0))[:3],(20,90,140)))
    assert all(abs(a-b)<=3 for a,b in zip(target.get_at((1599,899))[:3],(20,90,140)))
    world.fill((140,90,20));camera.present(world,target)
    # Compare against a fresh reference scale, including backend rounding.
    fresh=pygame.transform.smoothscale(world,camera.buffer.get_size())
    pivot=app.background.pivot;inset=app.background.inset
    offset=tuple(round(pivot[i]*(1-.95)-inset[i]) for i in range(2))
    assert target.get_at((800,450))==fresh.get_at((800-offset[0],450-offset[1]))
