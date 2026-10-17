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
    def __init__(self, stage: dict, cards: list[Card], seed: int | None = None):
        self.stage = stage
        self.player = Fighter(30, 30)
        self.enemy = Fighter(stage["enemy"]["hp"], stage["enemy"]["hp"])
        self.deck = Deck.starting(cards, random.Random(seed))
        self.plan = EnemyPlan(stage["enemy"])
        self.intent = self.plan.next(self.enemy.hp, self.enemy.max_hp)
        self.status = "active"
        self.turn = 0
        self.energy = 0
        self._start_turn()

    def _start_turn(self):
        self.turn += 1
        self.energy = 2
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
        if action.kind in ("attack", "special"):
            effects = [Effect("player", "damage", self.player.damage(action.amount))]
        elif action.kind == "defend":
            self.enemy.block += action.amount
            effects = [Effect("enemy", "block", action.amount)]
        elif action.kind == "heal":
            effects = [Effect("enemy", "heal", self.enemy.heal(action.amount))]
        else:
            effects = [Effect("enemy", "charge", 0)]
        self.player.block = 0
        if self.player.hp == 0:
            self.status = "lost"
        else:
            self.intent = self.plan.next(self.enemy.hp, self.enemy.max_hp)
            self._start_turn()
        return effects
