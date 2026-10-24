from dataclasses import dataclass
import random
from src.cards.models import Card, Deck
from src.enemies.intentions import EnemyPlan

@dataclass
class Fighter:
    max_hp: int
    hp: int
    block: int = 0

    def damage(self, amount: int) -> int:
        absorbed = min(self.block, max(0, amount))
        self.block -= absorbed
        loss = min(self.hp, max(0, amount - absorbed))
        self.hp -= loss
        return loss

    def heal(self, amount: int) -> int:
        gain = min(max(0, amount), self.max_hp - self.hp)
        self.hp += gain
        return gain

@dataclass(frozen=True)
class Effect:
    target: str
    kind: str
    amount: int

class Battle:
    """Pure combat state. Player Block expires after enemy phase.

    Enemy Block expires at the START of its next phase, after defending
    against one full player turn. Defend creates fresh Block afterward.
    """
    def __init__(self, stage: dict, cards: list[Card], seed: int | None = None, player_max_hp: int = 30, turn1_bonus_energy: int = 0):
        self.stage = stage
        self.player = Fighter(player_max_hp, player_max_hp)
        self.enemy = Fighter(stage["enemy"]["hp"], stage["enemy"]["hp"])
        self.deck = Deck.starting(cards, random.Random(seed))
        self.plan = EnemyPlan(stage["enemy"], random.Random(seed))
        self.intent = self.plan.next(self.enemy.hp, self.enemy.max_hp)
        self.status = "active"
        self.turn = 0
        self.energy = 0
        self.turn1_bonus_energy = turn1_bonus_energy
        self._start_turn()

    def _start_turn(self):
        self.turn += 1
        bonus = self.turn1_bonus_energy if self.turn == 1 else 0
        self.energy = 2 + bonus
        self.deck.draw(3)

    def play(self, index: int) -> list[Effect]:
        if self.status != "active" or not 0 <= index < len(self.deck.hand):
            return []
        card = self.deck.hand[index]
        if card.cost > self.energy:
            return []
        self.energy -= card.cost
        self.deck.discard.append(self.deck.hand.pop(index))
        if card.category == "attack":
            effects = [Effect("enemy", "damage", self.enemy.damage(card.amount))]
            if getattr(self.plan, "excess_block_active", False):
                self.intent = self.plan.refresh_intent(self.enemy.block)
        elif card.category == "heal":
            effects = [Effect("player", "heal", self.player.heal(card.amount))]
        else:
            self.player.block += card.amount
            effects = [Effect("player", "block", card.amount)]
        if self.enemy.hp == 0:
            self.status = "won"
        return effects

    def end_turn(self) -> list[Effect]:
        if self.status != "active":
            return []
        self.deck.discard_hand()
        self.enemy.block = 0
        action = self.intent
        effects = []
        if action.kind in ("attack", "heavy", "special"):
            effects.append(Effect("player", "damage", self.player.damage(action.amount)))
        elif action.kind == "defend":
            self.enemy.block += action.amount
            effects.append(Effect("enemy", "block", action.amount))
        elif action.kind == "heal":
            effects.append(Effect("enemy", "heal", self.enemy.heal(action.amount)))
        else:
            effects.append(Effect("enemy", "charge", 0))
        if getattr(action, "defend_amount", 0) > 0 and action.kind != "defend":
            self.enemy.block += action.defend_amount
            effects.append(Effect("enemy", "block", action.defend_amount))
        if hasattr(self.plan, "on_action_executed"):
            self.plan.on_action_executed(action)
        self.player.block = 0
        if self.player.hp == 0:
            self.status = "lost"
        else:
            self.intent = self.plan.next(self.enemy.hp, self.enemy.max_hp, self.enemy.block)
            self._start_turn()
        return effects
