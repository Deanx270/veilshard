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

@pytest.mark.parametrize("card,cost,damage",[("attack",1,6),("heavy",2,11)])
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
    assert enemy_def["hp"] == 40
    assert enemy_def.get("heavy_chance") == 0.5
    assert enemy_def.get("heavy_multiplier") == 2.0
    plan = EnemyPlan(enemy_def, random.Random(42))
    intents = [plan.next(40, 40) for _ in range(200)]
    kinds = [it.kind for it in intents]
    assert "attack" in kinds and "heavy" in kinds
    assert 70 <= kinds.count("heavy") <= 130
    heavy_amounts = {it.amount for it in intents if it.kind == "heavy"}
    assert heavy_amounts == {10, 14}
    assert Intent("heavy", 14).label == "Heavy Attack  14"

def test_stage_two_enemy_buffs_and_passives(campaign):
    enemy_def = campaign.stages[1]["enemy"]
    assert enemy_def["hp"] == 60
    assert enemy_def.get("defend_after_attack_chance") == 0.5
    assert enemy_def.get("defend_amount") == 7
    assert enemy_def.get("bonus_attack_interval") == 2
    assert enemy_def.get("bonus_attack_amount") == 1
    assert all(a[0] == "attack" for a in enemy_def["pattern"])

    plan = EnemyPlan(enemy_def, random.Random(42))
    intents = [plan.next(60, 60) for _ in range(8)]
    assert all(it.kind == "attack" for it in intents)
    assert intents[0].amount == 6
    assert intents[1].amount == 8
    assert intents[2].amount == 7
    assert intents[3].amount == 9
    assert intents[4].amount == 8
    assert intents[5].amount == 10
    assert intents[6].amount == 9
    assert intents[7].amount == 11

    plan2 = EnemyPlan(enemy_def, random.Random(123))
    sample = [plan2.next(60, 60) for _ in range(200)]
    defends = [it.defend_amount for it in sample]
    assert all(d in (0, 7) for d in defends)
    assert 70 <= defends.count(7) <= 130

    assert Intent("attack", 7, defend_amount=7).label == "Attack  7 + Defend  7"
    assert Intent("attack", 6).label == "Attack  6"

    campaign.index = 1
    campaign.enter_battle()
    b = campaign.battle
    b.intent = Intent("attack", 8, defend_amount=7)
    effects = b.end_turn()
    assert b.player.hp == 22
    assert b.enemy.block == 7
    assert len(effects) == 2
    assert effects[0].kind == "damage" and effects[0].amount == 8 and effects[0].target == "player"
    assert effects[1].kind == "block" and effects[1].amount == 7 and effects[1].target == "enemy"

def test_kill_prevents_enemy_action(campaign):
    b=campaign.battle; b.enemy.hp=1; give(campaign,"attack"); b.play(0)
    assert b.status=="won" and b.end_turn()==[] and b.player.hp==30
    assert b.play(0)==[]

def test_defeat_retry(campaign):
    b=campaign.battle; b.player.hp=1; b.end_turn(); campaign.resolve()
    assert b.status=="lost" and campaign.scene in ("shop", "over")
    campaign.retry(); assert campaign.scene=="intro"
    campaign.enter_battle(); assert campaign.battle.player.hp>=30

def test_stage_progression_and_final_victory(campaign):
    for i in range(5):
        b=campaign.battle; b.player.hp=2; b.enemy.hp=1
        give(campaign,"attack"); b.play(0); campaign.resolve()
        if i<4:
            assert campaign.scene in ("shop", "clear")
            campaign.advance(); assert campaign.index==i+1 and campaign.scene=="intro"
            campaign.enter_battle()
            b=campaign.battle
            assert b.player.hp>=30 and len(b.deck.draw_pile)+len(b.deck.hand)==12
        else: assert campaign.scene=="victory"

def test_rage_intent_is_locked(campaign):
    campaign.index=4; campaign.enter_battle()
    b=campaign.battle; original=b.intent; b.enemy.hp=21
    assert b.intent==original
    b.end_turn()
    assert b.plan.enraged and b.intent.kind=="charge"
    b.end_turn(); assert b.intent.kind=="special"

def test_stormcaller_mechanics_and_desperation_vortex(campaign):
    campaign.index = 2
    campaign.enter_battle()
    b = campaign.battle
    enemy_def = campaign.stages[2]["enemy"]
    assert enemy_def["hp"] == 100
    assert enemy_def.get("desperation_vortex") is True
    assert enemy_def.get("excess_block_empower") is True
    assert b.enemy.hp == 100

    # Turn 1: Arcane Barrage (attack 12)
    assert b.intent.kind == "attack" and b.intent.amount == 12
    assert b.intent.label == "Attack  12"
    b.end_turn()
    assert b.player.hp == 18

    # Turn 2: Storm Surge (defend 12)
    assert b.intent.kind == "defend" and b.intent.amount == 12
    assert b.intent.label == "Gain Block  12"
    b.end_turn()
    assert b.enemy.block == 12

    # Turn 3: Thunderfall (heavy 24 base + 12 excess block = 36)
    assert b.intent.kind == "heavy" and b.intent.amount == 36
    assert b.intent.label == "Heavy Attack  36"

    # Attacking enemy block reduces excess block and updates displayed intent in real time
    b.enemy.damage(5) # Enemy block is now 7
    if getattr(b.plan, "excess_block_active", False):
        b.intent = b.plan.refresh_intent(b.enemy.block)
    assert b.intent.amount == 31
    assert b.intent.label == "Heavy Attack  31"

    b.enemy.damage(7) # Enemy block is now 0
    if getattr(b.plan, "excess_block_active", False):
        b.intent = b.plan.refresh_intent(b.enemy.block)
    assert b.intent.amount == 24
    assert b.intent.label == "Heavy Attack  24"

    # Player shields up to survive Thunderfall
    b.player.hp = 50
    b.player.max_hp = 50

    # End turn 3: Thunderfall strikes for 24
    b.end_turn()
    assert b.player.hp == 26

    # Turn 4: Shard Volley (special 10)
    assert b.intent.kind == "special" and b.intent.amount == 10
    assert b.intent.label == "Special Attack  10"

    # Damage enemy down to 50 HP during turn 4 to trigger Desperation Vortex
    b.enemy.hp = 50
    b.end_turn()
    assert b.plan.enraged is True

    # Cycle in rage: Arcane Barrage -> Storm Surge (15 block) -> Thunderfall (+2 bonus). No Shard Volley.
    # Step 0: Arcane Barrage (12)
    assert b.intent.kind == "attack" and b.intent.amount == 12
    b.player.hp = 50
    b.end_turn()

    # Step 1: Storm Surge (15 block)
    assert b.intent.kind == "defend" and b.intent.amount == 15
    b.end_turn()
    assert b.enemy.block == 15

    # Step 2: Thunderfall with 15 excess block
    assert b.intent.kind == "heavy" and b.intent.amount == 24 + 15
    b.player.hp = 50
    b.end_turn()

    # Thunderfall executed while enraged grants permanent +2 attack
    assert b.plan.thunderfall_bonus == 2
    # Next attack has +2 bonus (12 + 2 = 14)
    assert b.intent.kind == "attack" and b.intent.amount == 14

def test_stormcaller_thunderfall_always_follows_storm_surge(campaign):
    campaign.index = 2
    campaign.enter_battle()
    b = campaign.battle

    # Turn 1: Arcane Barrage (attack 12)
    assert b.intent.kind == "attack"
    b.end_turn()

    # Turn 2: Storm Surge (defend 12)
    assert b.intent.kind == "defend"
    # While Storm Surge is active, damage enemy to 50 HP (activating Desperation Vortex)
    b.enemy.hp = 50
    b.end_turn()

    # Desperation Vortex is active, and Thunderfall MUST immediately follow Storm Surge
    assert b.plan.enraged is True
    assert b.intent.kind == "heavy"

    # Survive Thunderfall
    b.player.hp = 50
    b.end_turn()

    # After Thunderfall while enraged, Shard Volley is omitted and next is Arcane Barrage (attack)
    assert b.intent.kind == "attack"
    b.player.hp = 50
    b.end_turn()

    # Then Storm Surge (defend 15)
    assert b.intent.kind == "defend"
    assert b.intent.amount == 15
    b.end_turn()

    # And immediately Thunderfall again!
    assert b.intent.kind == "heavy"


def auto_play(b):
    """Simple public-action policy: evaluate valid turn plays to maximize net HP difference."""
    from itertools import permutations
    import copy
    for _ in range(100):
        if b.status != "active": break
        hand_indices = list(range(len(b.deck.hand)))
        valid_combos = [()]
        for r in range(1, len(hand_indices) + 1):
            for seq in permutations(hand_indices, r):
                if sum(b.deck.hand[i].cost for i in seq) <= b.energy:
                    valid_combos.append(seq)

        best_combo = ()
        best_score = -999999
        for seq in valid_combos:
            b_test = copy.deepcopy(b)
            cards_to_play = [b.deck.hand[i] for i in seq]
            for card in cards_to_play:
                c_idx = next(i for i, c in enumerate(b_test.deck.hand) if c.id == card.id)
                b_test.play(c_idx)
            if b_test.status == "won":
                score = 100000
            elif b_test.player.hp == 0:
                score = -100000
            else:
                damage = b_test.intent.amount if b_test.intent.kind in ("attack", "heavy", "special") else 0
                net_loss = max(0, damage - b_test.player.block)
                hp_after = b_test.player.hp - net_loss
                if hp_after <= 0:
                    score = -50000 + hp_after
                else:
                    score = hp_after * 2 - b_test.enemy.hp
            if score > best_score:
                best_score = score
                best_combo = seq

        cards_to_play = [b.deck.hand[i] for i in best_combo]
        for card in cards_to_play:
            c_idx = next(i for i, c in enumerate(b.deck.hand) if c.id == card.id)
            b.play(c_idx)
        b.end_turn()
    return b.status

@pytest.mark.parametrize("seed",[2])
def test_full_campaign_winnable_without_state_cheats(seed):
    c=Campaign(); c.start()
    for index in range(5):
        for attempt in range(25):
            c.enter_battle(seed if attempt == 0 else (seed + attempt * 17))
            res = auto_play(c.battle)
            c.resolve()
            if c.scene == "shop":
                for item in ("hp", "energy", "shield", "attack", "heavy", "heal"):
                    while c.buy(item):
                        pass
            if res == "won":
                if index < 4:
                    c.advance()
                break
            else:
                c.retry()
        else:
            pytest.fail(f"Could not defeat stage {index}")
    assert c.scene=="victory"

def test_shop_currency_and_progression(campaign):
    c = campaign
    assert c.shards == 0

    assert c.calculate_reward(won=True, damage_dealt=40, enemy_max_hp=40) == 60
    c.index = 1
    assert c.calculate_reward(won=True, damage_dealt=60, enemy_max_hp=60) == 95
    c.index = 2
    assert c.calculate_reward(won=True, damage_dealt=35, enemy_max_hp=35) == 130

    c.index = 1
    assert c.calculate_reward(won=False, damage_dealt=0, enemy_max_hp=60) == 0
    assert c.calculate_reward(won=False, damage_dealt=30, enemy_max_hp=60) == 20
    near_win_loss = c.calculate_reward(won=False, damage_dealt=59, enemy_max_hp=60)
    win_reward = c.calculate_reward(won=True, damage_dealt=60, enemy_max_hp=60)
    assert near_win_loss == 39
    assert win_reward == 95
    assert win_reward >= near_win_loss * 2

    c.index = 1
    c.enter_battle()
    c.battle.player.hp = 0
    c.battle.status = 'lost'
    c.resolve()
    assert c.scene == 'shop'
    assert c.index == 1
    c.retry()
    assert c.scene == 'intro'
    assert c.index == 1

    c.shards = 200
    assert c.buy('hp') is True
    assert c.player_max_hp() == 35
    assert c.shards == 160

    assert c.buy('attack') is True
    assert c.shards == 115
    cards = c.active_cards()
    attack_card = next(cd for cd in cards if cd.id == 'attack')
    assert attack_card.amount == 8
    assert attack_card.name == 'Frost Bolt+'

    assert c.buy('energy') is True
    assert c.shards == 40

    c.enter_battle()
    assert c.battle.player.max_hp == 35
    assert c.battle.player.hp == 35
    assert c.battle.energy == 3

    # Active battle frames must NEVER grant shards or resolve
    pre_shards = c.shards
    for _ in range(60):
        c.resolve()
    assert c.shards == pre_shards
    assert c.scene == 'battle'

    # Once won, resolve grants fixed stage 2 win shards (95) exactly once
    c.battle.enemy.hp = 0
    c.battle.status = 'won'
    c.resolve()
    assert c.shards == pre_shards + 95
    assert c.scene == 'shop'
    # Subsequent frame updates after scene changed do not add more
    for _ in range(60):
        c.resolve()
    assert c.shards == pre_shards + 95

def test_retry_previous_stage_half_rewards():
    c = Campaign()
    c.start()
    # Win Stage 1
    c.enter_battle()
    c.battle.enemy.hp = 0
    c.battle.status = "won"
    c.resolve()
    assert c.scene == "shop"
    assert c.shards == 60 # Stage 1 full win reward
    assert 0 in c.cleared_stages

    # Advance to Stage 2
    c.advance()
    assert c.index == 1

    # Lose Stage 2
    c.enter_battle()
    c.battle.player.hp = 0
    c.battle.status = "lost"
    c.resolve()
    assert c.scene == "shop"
    assert c.index == 1

    # Call retry_previous
    c.retry_previous()
    assert c.index == 0
    assert c.scene == "intro"

    # Play Stage 1 again (previously cleared) - victory grants half reward (30 shards)
    c.enter_battle()
    shards_before = c.shards
    c.battle.enemy.hp = 0
    c.battle.status = "won"
    c.resolve()
    assert c.shards == shards_before + 30 # 60 // 2 = 30
    assert c.last_battle_result["half_reward"] is True

    # Play Stage 1 again - loss with partial damage grants half reward
    c.retry()
    c.enter_battle()
    shards_before = c.shards
    c.battle.enemy.hp = c.battle.enemy.max_hp // 2
    c.battle.player.hp = 0
    c.battle.status = "lost"
    c.resolve()
    full_loss_reward = round(0.5 * 25) # 13
    assert c.shards == shards_before + (full_loss_reward // 2)
    assert c.last_battle_result["half_reward"] is True
