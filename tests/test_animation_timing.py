import os
os.environ["SDL_VIDEODRIVER"]="dummy"
os.environ["SDL_AUDIODRIVER"]="dummy"
import pygame
import pytest
from src.core.app import App
from src.core.input import viewport
from src.rendering.action_timeline import ActionTimeline

@pytest.fixture
def app():
    a=App(); a.action("start"); a.action("battle"); a.update(.3)
    yield a
    pygame.quit()

def click_card(app):
    app.draw(); pose=app.hand.views[0].pose
    area=viewport(app.window.get_size())
    pos=(round(area.x+pose.x*area.width/1600),round(area.y+pose.y*area.height/900))
    app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=pos))

def set_card(app,kind):
    b=app.campaign.battle
    b.deck.hand=[next(c for c in app.campaign.cards if c.id==kind)]
    app.hand.sync(b.deck.hand)
    return b

@pytest.mark.parametrize("kind,damage,cost",[("attack",6,1),("heavy",10,2)])
def test_rapid_card_clicks_resolve_once_at_impact(app,kind,damage,cost):
    b=set_card(app,kind); hp=b.enemy.hp
    click_card(app)
    for _ in range(20):
        click_card_event=pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=(640,600))
        app.event(click_card_event); app.action("end")
    assert b.enemy.hp==hp and b.energy==2 and b.turn==1
    app.update(app.timeline.impact-.01)
    assert b.enemy.hp==hp and not app.effects.popups
    assert app.battlefield.motion.offset()!=(0,0)
    app.update(.011)
    assert b.enemy.hp==hp-damage and b.energy==2-cost
    assert app.battlefield.camera.remaining>0 and app.effects.popups
    assert app.hud.display_hp["enemy"]>b.enemy.hp
    for _ in range(120): app.update(1/60)
    assert not app.lock and not app.timeline.active
    assert b.enemy.hp==hp-damage and b.turn==1


def test_enemy_attack_pause_and_rapid_end_turn(app):
    b=app.campaign.battle; damage=b.intent.amount; hp=b.player.hp
    for _ in range(30): app.action("end")
    assert b.turn==1 and b.player.hp==hp
    app.update(.1); age=app.timeline.elapsed
    app.action("pause"); app.update(5)
    assert app.timeline.elapsed==age and b.player.hp==hp
    app.action("resume"); app.update(app.timeline.impact-age+.01)
    assert b.turn==2 and b.player.hp==hp-damage
    app.update(3)
    assert b.turn==2 and not app.lock


def test_menu_cancels_pending_action(app):
    b=set_card(app,"heavy"); hp=b.enemy.hp
    click_card(app); app.action("pause"); app.action("menu"); app.update(2)
    assert b.enemy.hp==hp and b.energy==2
    assert not app.timeline.active and app.pending_card is None
    app.action("start"); app.action("battle")
    assert app.campaign.battle.player.hp==30 and not app.lock


def test_lethal_action_never_allows_retaliation(app):
    b=set_card(app,"attack"); b.enemy.hp=1
    click_card(app); app.update(app.timeline.impact+.01)
    assert b.status=="won" and app.campaign.scene=="battle"
    for _ in range(20): app.action("end")
    app.update(1)
    assert app.campaign.scene=="clear" and b.player.hp==30 and b.turn==1


@pytest.mark.parametrize("kind,effect",[("shield","block"),("heal","heal")])
def test_support_effect_timing(app,kind,effect):
    b=set_card(app,kind); b.player.hp=20
    click_card(app); app.update(app.timeline.impact-.05)
    assert b.player.hp==20 and b.player.block==0
    app.update(.06)
    assert app.effects.bursts[-1]["kind"]==effect
    assert b.player.block==6 if kind=="shield" else b.player.hp==26
    assert app.battlefield.camera.remaining==0


def test_long_frame_and_strength(app):
    calls=[]; t=ActionTimeline(); t.start("heavy","player",lambda:calls.append(1))
    assert not t.start("attack","player",lambda:calls.append(2))
    t.update(10); t.update(10)
    assert calls==[1] and not t.active
    b=set_card(app,"heavy"); click_card(app); app.update(app.timeline.impact+.01)
    assert app.battlefield.camera.strength>1
    assert not app.effects.bursts
    from src.combat.battle import Effect
    app.effects.add([Effect("enemy","damage",10)], app.campaign.stages[1], "heavy", "player")
    assert len(app.effects.bursts[-1]["particles"])==14
