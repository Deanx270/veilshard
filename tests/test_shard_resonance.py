import os
os.environ["SDL_VIDEODRIVER"]="dummy"
os.environ["SDL_AUDIODRIVER"]="dummy"
from types import SimpleNamespace
import pygame
import pytest
from src.scenes.campaign import Campaign, SHOP_CATALOG
from src.ui.shard_resonance import ShardResonance
from src.ui.widgets import UI


@pytest.fixture
def screen():
    pygame.init(); pygame.display.set_mode((1,1))
    c=Campaign(); c.scene="shop"; c.shards=140
    c.last_battle_result={"won":True,"earned":60,"stage_name":"Ember Forest"}
    ui=UI(); view=ShardResonance()
    app=SimpleNamespace(campaign=c,canvas=pygame.Surface((1600,900)),ui=ui,buttons={})
    def button(name,label,rect,mouse,enabled=True,accent=None):
        rect=pygame.Rect(rect)
        if enabled: app.buttons[name]=rect
        ui.button(app.canvas,rect,label,mouse,accent or (180,150,240),enabled)
    app.button=button
    app.action=lambda name:view.buy(c,name[4:]) if name.startswith("buy_") else None
    yield view,app
    pygame.quit()


def test_three_choices_stable_until_next_visit(screen):
    view,app=screen; c=app.campaign
    view.enter(c); choices=list(view.choices)
    assert len(set(choices))==3 and set(choices)<=SHOP_CATALOG.keys()
    view.draw(app,(-1,-1));view.update(.1,c)
    assert view.choices==choices
    assert set(k for k in app.buttons if k.startswith("select_"))=={"select_"+k for k in choices}
    c.last_battle_result=dict(c.last_battle_result)
    view.enter(c)
    assert view.visit is c.last_battle_result and view.pulse==0


def test_purchase_release_feedback_and_duplicate_protection(screen):
    view,app=screen;c=app.campaign
    view.draw(app,(-1,-1)); key=view.choices[0]; pos=app.buttons["buy_"+key].center
    old=c.shards;cost=c.item_cost(key)
    down=pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1)
    up=pygame.event.Event(pygame.MOUSEBUTTONUP,button=1)
    view.event(app,down,pos);assert c.shards==old
    view.event(app,up,pos)
    for _ in range(20): view.event(app,up,pos);view.buy(c,key)
    assert c.shards==old-cost and c.upgrades[key]==1
    assert view.balance==old and view.selected==key and view.pulse>0
    view.update(.1,c);assert c.shards<view.balance<old
    for _ in range(30):view.update(.1,c)
    assert view.balance==c.shards


def test_disabled_maxed_and_loss_flow(screen):
    view,app=screen;c=app.campaign
    c.shards=0;c.last_battle_result={"won":False,"earned":0}
    for key,cat in SHOP_CATALOG.items():c.upgrades[key]=cat["max_level"]
    view.draw(app,(-1,-1))
    assert not any(k.startswith("buy_") for k in app.buttons)
    assert "retry" in app.buttons and "next" not in app.buttons
    assert not view.buy(c,view.choices[0])


def test_cancelled_press_and_value_previews(screen):
    view,app=screen;c=app.campaign
    view.draw(app,(-1,-1));key=view.choices[0];pos=app.buttons["buy_"+key].center
    view.event(app,pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1),pos)
    view.event(app,pygame.event.Event(pygame.MOUSEBUTTONUP,button=1),(0,0))
    assert c.upgrades[key]==0
    for key in SHOP_CATALOG:
        before,step=view.values(c,key)
        c.upgrades[key]+=1
        after,_=view.values(c,key)
        assert after==before+step


def test_ice_identity_preserves_ids_and_scaling(screen):
    from src.ui.resonance_icons import icon_surface
    view,app=screen; c=app.campaign
    expected={"attack":("Frost Bolt",1,6),"heavy":("Glacial Bolt",2,11),"shield":("Shield",1,6),"heal":("Heal",1,6)}
    for card in c.cards:
        assert (card.name,card.cost,card.amount)==expected[card.id]
    assert [SHOP_CATALOG[k]["name"] for k in ("hp","attack","shield","heavy","heal","energy")]==["Vital Infusion","Frost Focus","Crystal Aegis","Moonshard Surge","Lunar Renewal","Resonance Conduit"]
    c.upgrades["attack"]=2;c.upgrades["heavy"]=2
    cards={card.id:card for card in c.active_cards()}
    assert cards["attack"].amount==10 and cards["heavy"].amount==22
    assert icon_surface("attack") is icon_surface("attack")
    assert pygame.image.tobytes(icon_surface("attack"),"RGBA")!=pygame.image.tobytes(icon_surface("heavy"),"RGBA")
