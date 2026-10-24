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
        base = names.get(self.kind, self.kind.title()) + (f"  {self.amount}" if self.amount else " • next strike empowered")
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
        self.thunderfall_bonus = 0
        self.prev_action_kind: str | None = None
        self.excess_block_active = False
        self.base_intent_amount = 0
        self.current_intent: Intent | None = None

    def refresh_intent(self, current_enemy_block: int) -> Intent:
        if self.excess_block_active and self.current_intent:
            bonus = max(0, current_enemy_block)
            self.current_intent = Intent(self.current_intent.kind, self.base_intent_amount + bonus, self.current_intent.defend_amount)
            return self.current_intent
        return self.current_intent

    def on_action_executed(self, action: Intent):
        self.prev_action_kind = action.kind
        self.excess_block_active = False
        if action.kind == "heavy" and self.definition.get("desperation_vortex"):
            if self.enraged or self.definition.get("thunderfall_bonus_always", False):
                self.thunderfall_bonus += self.definition.get("thunderfall_bonus_amount", 2)

    def next(self, hp: int, max_hp: int, current_enemy_block: int = 0) -> Intent:
        if (self.definition.get("rage_pattern") or self.definition.get("desperation_vortex")) and hp * 2 <= max_hp and not self.enraged:
            self.enraged = True
            if self.definition.get("desperation_vortex"):
                if self.prev_action_kind == "defend":
                    self.step = 2
                elif self.prev_action_kind == "heavy":
                    self.step = 0
                elif self.prev_action_kind == "attack":
                    self.step = 1
                else:
                    self.step = 0
            else:
                self.step = 0
        pattern = self.definition["rage_pattern"] if self.enraged and self.definition.get("rage_pattern") else self.definition["pattern"]
        if self.definition.get("desperation_vortex") and self.prev_action_kind == "defend":
            for i, p in enumerate(pattern):
                if p[0] == "heavy":
                    self.step = i
                    break
        action = Intent(*pattern[self.step % len(pattern)])

        bonus_interval = self.definition.get("bonus_attack_interval", 0)
        bonus_amount = self.definition.get("bonus_attack_amount", 1)
        if bonus_interval > 0 and action.kind in ("attack", "heavy", "special"):
            bonus = (self.step // bonus_interval) * bonus_amount
            if bonus > 0:
                action = Intent(action.kind, action.amount + bonus, action.defend_amount)

        if self.thunderfall_bonus > 0 and action.kind in ("attack", "heavy", "special"):
            action = Intent(action.kind, action.amount + self.thunderfall_bonus, action.defend_amount)

        self.step += 1

        heavy_chance = self.definition.get("heavy_chance", 0.0)
        if action.kind == "attack" and heavy_chance > 0 and self.rng.random() < heavy_chance:
            multiplier = self.definition.get("heavy_multiplier", 2.0)
            amount = self.definition.get("heavy_amount", round(action.amount * multiplier + 1e-9))
            action = Intent("heavy", amount, action.defend_amount)

        defend_chance = self.definition.get("defend_after_attack_chance", self.definition.get("defend_chance", 0.0))
        if action.kind in ("attack", "heavy", "special") and defend_chance > 0 and self.rng.random() < defend_chance:
            defend_amount = self.definition.get("defend_amount", 7)
            action = Intent(action.kind, action.amount, defend_amount=defend_amount)

        self.base_intent_amount = action.amount
        if self.definition.get("excess_block_empower") and self.prev_action_kind == "defend" and action.kind == "heavy":
            self.excess_block_active = True
            if current_enemy_block > 0:
                action = Intent(action.kind, action.amount + current_enemy_block, action.defend_amount)
        else:
            self.excess_block_active = False

        self.current_intent = action
        return action
