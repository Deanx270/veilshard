import pytest
from src.scenes.campaign import Campaign
from src.ui.shard_resonance import ShardResonance


@pytest.mark.parametrize("focus,expected", [(0, [11,12,13,14,15]), (2, [18,20,22,24,25]), (5, [29,32,35,38,40])])
def test_glacial_scaling_and_preview(focus, expected):
    c = Campaign()
    c.upgrades["attack"] = focus
    for level, damage in enumerate(expected):
        c.upgrades["heavy"] = level
        cards = {card.id: card for card in c.active_cards()}
        assert cards["attack"].amount == c.player_magic() == 6 + focus * 2
        assert cards["heavy"].amount == damage
        assert cards["heavy"].description == f"Deal {damage} damage."
        current, step = ShardResonance.values(None, c, "heavy")
        assert current == damage
        assert current + step == expected[min(level + 1, 4)]
        assert cards["heavy"].cost == 2 and cards["heavy"].count == 2


def test_purchase_order_and_actual_battle_damage():
    a, b = Campaign(), Campaign()
    for c, order in ((a, ["attack", "heavy"]), (b, ["heavy", "attack"])):
        c.shards = 100
        for key in order: assert c.buy(key)
        assert c.shards == 0 and c.player_magic() == 8
        assert c.glacial_damage() == 16
        c.enter_battle(seed=7)
        c.battle.deck.hand = [next(card for card in c.active_cards() if card.id == "heavy")]
        c.battle.enemy.block = 3
        hp = c.battle.enemy.hp
        c.battle.play(0)
        assert c.battle.enemy.hp == hp - 13 and c.battle.enemy.block == 0
        assert c.battle.energy == 0
    assert a.active_cards() == b.active_cards()


def test_attack_uses_editable_base_and_upgrades_do_not_mutate_templates():
    from dataclasses import replace
    c = Campaign()
    original = list(c.cards)
    c.cards = [replace(card, amount=7) if card.id == "attack" else card for card in c.cards]
    c.upgrades["heavy"] = 4
    assert c.player_magic() == 7 and c.glacial_damage() == 18
    c.active_cards()
    assert next(card for card in c.cards if card.id == "heavy") == original[1]
