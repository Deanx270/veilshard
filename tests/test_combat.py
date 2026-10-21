import random
import pytest
from src.cards.models import Deck
from src.combat.battle import Fighter
from src.enemies.intentions import EnemyPlan, Intent
from src.scenes.campaign import Campaign

@pytest.fixture
def campaign():
    c=Campaign(); c.start(); c.enter_battle(seed=7)
    return c

def give(c,*ids):
    c.battle.deck.hand=[next(card for card in c.cards if card.id==i) for i in ids]

@pytest.mark.parametrize("card,cost,damage",[("attack",1,6),("heavy",2,10)])
def test_damage_energy(campaign,card,cost,damage):
    b=campaign.battle; give(campaign,card)
    hp=b.enemy.hp
    b.play(0)
    assert b.enemy.hp==hp-damage and b.energy==2-cost
    assert b.deck.discard[-1].id==card

def test_affordability(campaign):
    b=campaign.battle; give(campaign,"attack","heavy")
    b.play(0); hp=b.enemy.hp
    assert b.play(0)==[] and b.enemy.hp==hp and len(b.deck.hand)==1
    assert b.play(-1)==[] and b.play(8)==[]

def test_block_absorption_and_nonnegative():
    fighter=Fighter(30,30,6)
    assert fighter.damage(4)==0 and fighter.block==2
    assert fighter.damage(8)==6 and fighter.hp==24 and fighter.block==0
    fighter.damage(100)
    assert fighter.hp==0
    fighter.damage(-2)
    assert fighter.hp==0

def test_heal_cap(campaign):
    b=campaign.battle; b.player.hp=28; give(campaign,"heal")
    assert b.play(0)[0].amount==2 and b.player.hp==30

def test_player_block_expires_on_nonattack(campaign):
    b=campaign.battle; give(campaign,"shield"); b.play(0)
    assert b.player.block==6
    b.intent=Intent("charge",0); b.end_turn()
    assert b.player.block==0 and b.player.hp==30

def test_player_block_absorbs_enemy(campaign):
    b=campaign.battle; give(campaign,"shield"); b.play(0)
    b.intent=Intent("attack",8); b.end_turn()
    assert b.player.hp==28 and b.player.block==0

def test_enemy_block_survives_into_player_turn(campaign):
    b=campaign.battle; b.intent=Intent("defend",9); b.end_turn()
    assert b.enemy.block==9
    give(campaign,"attack"); hp=b.enemy.hp; b.play(0)
    assert b.enemy.block==3 and b.enemy.hp==hp
    b.intent=Intent("charge",0); b.end_turn()
    assert b.enemy.block==0

def test_deck_draw_and_reshuffle(campaign):
    deck=Deck.starting(campaign.cards,random.Random(1))
    assert len(deck.draw_pile)==12
    seen=[]
    for _ in range(4):
        deck.draw(3); seen.extend(c.id for c in deck.hand); deck.discard_hand()
    assert len(seen)==12 and seen.count("attack")==5
    deck.draw(3)
    assert len(deck.hand)==3 and len(deck.draw_pile)==9 and not deck.discard
    empty=Deck([],random.Random(1)); empty.draw(3)
    assert not empty.hand

def test_partial_reshuffle(campaign):
    card=campaign.cards[0]; deck=Deck([card],random.Random(1),[card,card])
    deck.draw(3)
    assert len(deck.hand)==3 and not deck.discard and not deck.draw_pile

def test_end_turn_discards_and_resets(campaign):
    b=campaign.battle; b.energy=0; b.end_turn()
    assert len(b.deck.hand)==3 and len(b.deck.discard)==3 and b.energy==2 and b.turn==2

@pytest.mark.parametrize("kind,amount,expected_hp,block",[("attack",7,23,0),("heavy",7,23,0),("special",11,19,0),("defend",8,30,8),("heal",6,30,0),("charge",0,30,0)])
def test_enemy_actions(campaign,kind,amount,expected_hp,block):
    b=campaign.battle; b.enemy.hp-=2; before=b.enemy.hp
    b.intent=Intent(kind,amount); b.end_turn()
    assert b.player.hp==expected_hp and b.enemy.block==block
    if kind=="heal": assert b.enemy.hp==before+2

def test_stage_one_enemy_heavy_attack_chance(campaign):
    enemy_def = campaign.stages[0]["enemy"]
    assert enemy_def.get("heavy_chance") == 0.5
    assert enemy_def.get("heavy_multiplier") == 2.0
    plan = EnemyPlan(enemy_def, random.Random(42))
    intents = [plan.next(28, 28) for _ in range(200)]
    kinds = [it.kind for it in intents]
    assert "attack" in kinds and "heavy" in kinds
    assert 70 <= kinds.count("heavy") <= 130
    heavy_amounts = {it.amount for it in intents if it.kind == "heavy"}
    assert heavy_amounts == {10, 14}
    assert Intent("heavy", 14).label == "Heavy Attack  14"

def test_kill_prevents_enemy_action(campaign):
    b=campaign.battle; b.enemy.hp=1; give(campaign,"attack"); b.play(0)
    assert b.status=="won" and b.end_turn()==[] and b.player.hp==30
    assert b.play(0)==[]

def test_defeat_retry(campaign):
    b=campaign.battle; b.player.hp=1; b.end_turn(); campaign.resolve()
    assert b.status=="lost" and campaign.scene=="over"
    campaign.retry(); assert campaign.scene=="intro"
    campaign.enter_battle(); assert campaign.battle.player.hp==30

def test_stage_progression_and_final_victory(campaign):
    for i in range(5):
        b=campaign.battle; b.player.hp=2; b.enemy.hp=1
        give(campaign,"attack"); b.play(0); campaign.resolve()
        if i<4:
            assert campaign.scene=="clear"
            campaign.advance(); assert campaign.index==i+1 and campaign.scene=="intro"
            campaign.enter_battle()
            b=campaign.battle
            assert b.player.hp==30 and len(b.deck.draw_pile)+len(b.deck.hand)==12
        else: assert campaign.scene=="victory"

def test_rage_intent_is_locked(campaign):
    campaign.index=4; campaign.enter_battle()
    b=campaign.battle; original=b.intent; b.enemy.hp=21
    assert b.intent==original
    b.end_turn()
    assert b.plan.enraged and b.intent.kind=="charge"
    b.end_turn(); assert b.intent.kind=="special"

def test_storm_charge_precedes_special(campaign):
    campaign.index=2; campaign.enter_battle(); b=campaign.battle
    assert b.intent.kind=="charge"
    b.end_turn(); assert b.player.hp==30 and b.intent.kind=="special"

def auto_play(b):
    """Simple public-action policy: prioritize lethal hits, then sustain."""
    for _ in range(100):
        if b.status!="active": break
        while b.status=="active":
            options=[(i,c) for i,c in enumerate(b.deck.hand) if c.cost<=b.energy]
            if not options: break
            def score(option):
                _,c=option
                if c.category=="attack":
                    if c.amount>=b.enemy.hp+b.enemy.block: return 100
                    return c.amount/c.cost
                if c.category=="heal": return min(c.amount,30-b.player.hp)+1 if b.player.hp<30 else -1
                damage=b.intent.amount if b.intent.kind in ("attack","heavy","special") else 0
                return min(c.amount,max(0,damage-b.player.block))+0.5 if damage else -1
            option=max(options,key=score)
            if score(option)<0: break
            b.play(option[0])
        b.end_turn()
    return b.status

@pytest.mark.parametrize("seed",range(10))
def test_full_campaign_winnable_without_state_cheats(seed):
    c=Campaign(); c.start()
    for index in range(5):
        c.enter_battle(seed)
        assert auto_play(c.battle)=="won", (seed,index,c.battle.player.hp)
        c.resolve()
        if index<4: c.advance()
    assert c.scene=="victory"
