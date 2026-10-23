from dataclasses import dataclass
import random

@dataclass(frozen=True)
class Intent:
    kind: str
    amount: int
    defend_amount: int = 0

    @property
    def label(self) -> str:
        names = {"attack": "Attack", "heavy": "Heavy Attack", "defend": "Gain Block", "charge": "Charge", "heal": "Recover HP", "special": "Special Attack"}
        base = names[self.kind] + (f"  {self.amount}" if self.amount else " • next strike empowered")
        if self.defend_amount:
            base += f" + Defend  {self.defend_amount}"
        return base

class EnemyPlan:
    """The selected intent is locked until executed, even if HP crosses 50%."""
    def __init__(self, definition: dict, rng: random.Random | None = None):
        self.definition = definition
        self.rng = rng or random.Random()
        self.step = 0
        self.enraged = False

    def next(self, hp: int, max_hp: int) -> Intent:
        if self.definition.get("rage_pattern") and hp * 2 < max_hp and not self.enraged:
            self.enraged = True
            self.step = 0
        pattern = self.definition["rage_pattern"] if self.enraged else self.definition["pattern"]
        action = Intent(*pattern[self.step % len(pattern)])

        bonus_interval = self.definition.get("bonus_attack_interval", 0)
        bonus_amount = self.definition.get("bonus_attack_amount", 1)
        if bonus_interval > 0 and action.kind in ("attack", "heavy", "special"):
            bonus = (self.step // bonus_interval) * bonus_amount
            if bonus > 0:
                action = Intent(action.kind, action.amount + bonus, action.defend_amount)

        self.step += 1

        heavy_chance = self.definition.get("heavy_chance", 0.0)
        if action.kind == "attack" and heavy_chance > 0 and self.rng.random() < heavy_chance:
            multiplier = self.definition.get("heavy_multiplier", 2.0)
            amount = self.definition.get("heavy_amount", round(action.amount * multiplier + 1e-9))
            return Intent("heavy", amount, action.defend_amount)

        defend_chance = self.definition.get("defend_after_attack_chance", self.definition.get("defend_chance", 0.0))
        if action.kind in ("attack", "heavy", "special") and defend_chance > 0 and self.rng.random() < defend_chance:
            defend_amount = self.definition.get("defend_amount", 7)
            return Intent(action.kind, action.amount, defend_amount=defend_amount)

        return action
