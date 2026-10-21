from dataclasses import dataclass
import random

@dataclass(frozen=True)
class Intent:
    kind: str
    amount: int

    @property
    def label(self) -> str:
        names = {"attack": "Attack", "heavy": "Heavy Attack", "defend": "Gain Block", "charge": "Charge", "heal": "Recover HP", "special": "Special Attack"}
        return names[self.kind] + (f"  {self.amount}" if self.amount else " • next strike empowered")

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
        self.step += 1
        heavy_chance = self.definition.get("heavy_chance", 0.0)
        if action.kind == "attack" and heavy_chance > 0 and self.rng.random() < heavy_chance:
            multiplier = self.definition.get("heavy_multiplier", 1.4)
            amount = self.definition.get("heavy_amount", round(action.amount * multiplier))
            return Intent("heavy", amount)
        return action
