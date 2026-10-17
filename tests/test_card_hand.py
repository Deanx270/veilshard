import math
import pytest
from src.ui.card_layout import FanConfig, Pose, fan_layout, card_contains
from src.ui.card_hand import CardHand
from src.scenes.campaign import Campaign
from src.core.app import App
import pygame

@pytest.mark.parametrize("count",range(7))
def test_fan_geometry(count):
    poses=fan_layout(count)
    assert len(poses)==count
    if not count: return
    assert sum(p.x for p in poses)/count==800
    assert all(abs(p.angle)<=8.75 for p in poses)
    assert max(p.y for p in poses)-min(p.y for p in poses)<=18
    if count==1: assert poses[0].angle==0
    if count==2: assert 0<poses[0].angle<4 and poses[1].angle==-poses[0].angle
    if count==3: assert poses[0].angle==7 and poses[2].angle==-7


def test_inverse_rotation_and_corners():
    pose=Pose(800,700,17,1.06)
    def world(x,y):
        a=math.radians(pose.angle)
        return (pose.x+(x*math.cos(a)+y*math.sin(a))*pose.scale,
                pose.y+(-x*math.sin(a)+y*math.cos(a))*pose.scale)
    assert card_contains(world(70,100),pose)
    assert not card_contains(world(90,0),pose)
    assert not card_contains(world(-85,-124),pose)


def test_reflow_duplicate_instances_and_topmost_hover():
    card=Campaign().cards[0]
    hand=CardHand(None); hand.sync([card]*3)
    first=hand.views[0]; last=hand.views[2]
    hand.remove(1); hand.sync([card]*2)
    assert hand.views==[first,last]
    old=first.pose.x; hand.update(.02,(-1,-1))
    assert old<first.pose.x<fan_layout(2)[0].x
    for _ in range(60): hand.update(1/60,(-1,-1))
    hand.remove(1); hand.sync([card])
    for _ in range(60): hand.update(1/60,(-1,-1))
    assert abs(first.pose.x-800)<.01 and abs(first.pose.angle)<.01
    hand.sync([card]*3)
    # Deliberate overlap proves last drawn gets the click.
    for view in hand.views: view.pose=Pose(800,740)
    assert hand.hit((800,740))==2
    hand.hovered=0
    assert hand.hit((800,740))==0
    hand.update(.05,(800,740))
    assert hand.hovered==0 and hand.views[0].pose.scale>1
    hand.sync([])
    assert hand.hit((800,740)) is None


def test_floating_hud_no_footer_and_resized_card_click():
    from src.core.input import viewport
    app=App()
    try:
        app.action("start"); app.action("battle"); app.update(.3); app.fade=0
        app.draw()
        # Uncovered lower-screen pixels equal the actual world, not a footer.
        assert app.canvas.get_at((1200,870))==app.battlefield.world.get_at((1200,870))
        app.window=pygame.display.set_mode((1000,1000),pygame.RESIZABLE)
        app.draw()
        pose=app.hand.views[0].pose; area=viewport(app.window.get_size())
        pos=(round(area.x+pose.x*area.width/1600),round(area.y+pose.y*area.height/900))
        count=len(app.campaign.battle.deck.hand)
        app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=pos))
        assert len(app.hand.views)==count-1
        app.update(.1)
        assert app.hand.ghost is not None
        # Unaffordable cards do not mutate hand or create activation feedback.
        app.update(1)
        assert len(app.campaign.battle.deck.hand)==count-1
        app.lock=0; app.campaign.battle.energy=0; app.hand.ghost=None; app.draw()
        pose=app.hand.views[0].pose
        pos=(round(area.x+pose.x*area.width/1600),round(area.y+pose.y*area.height/900))
        app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=pos))
        assert len(app.campaign.battle.deck.hand)==count-1 and app.hand.ghost is None
        assert not app.hud.end.collidepoint((1380,716))
    finally: pygame.quit()
