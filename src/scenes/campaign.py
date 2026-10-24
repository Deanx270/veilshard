from src.cards.models import Card
from src.combat.battle import Battle
from src.core.resources import read_data

GLACIAL_PERCENT = (180, 200, 220, 235, 250)

SHOP_CATALOG = {
    "hp": {
        "name": "Vital Infusion",
        "desc": "+5 Max HP",
        "base_cost": 40,
        "cost_inc": 15,
        "max_level": 8,
    },
    "attack": {
        "name": "Frost Focus",
        "desc": "+2 Magic for both ice spells",
        "base_cost": 45,
        "cost_inc": 20,
        "max_level": 5,
    },
    "shield": {
        "name": "Crystal Aegis",
        "desc": "Shield gives +2 Block",
        "base_cost": 45,
        "cost_inc": 20,
        "max_level": 5,
    },
    "heavy": {
        "name": "Moonshard Surge",
        "desc": "Increase Glacial Bolt Magic multiplier",
        "base_cost": 55,
        "cost_inc": 25,
        "max_level": 4,
    },
    "heal": {
        "name": "Lunar Renewal",
        "desc": "Heal restores +2 HP",
        "base_cost": 40,
        "cost_inc": 15,
        "max_level": 4,
    },
    "energy": {
        "name": "Resonance Conduit",
        "desc": "+1 Energy on Turn 1",
        "base_cost": 75,
        "cost_inc": 0,
        "max_level": 1,
    },
}

class Campaign:
    def __init__(self):
        self.stages = read_data("stages")
        self.cards = [Card(**entry) for entry in read_data("cards")]
        self.story = read_data("story")
        self.scene = "menu"
        self.index = 0
        self.battle: Battle | None = None
        self.shards = 0
        self.cleared_stages = set()
        self.upgrades = {k: 0 for k in SHOP_CATALOG}
        self.last_battle_result: dict | None = None

    @property
    def stage(self):
        return self.stages[self.index]

    def start(self):
        self.index = 0
        self.battle = None
        self.shards = 0
        self.cleared_stages = set()
        self.upgrades = {k: 0 for k in SHOP_CATALOG}
        self.last_battle_result = None
        self.scene = "intro"

    def player_magic(self) -> int:
        """Shared ice-spell power, derived from editable base Frost Bolt damage."""
        base = next(card.amount for card in self.cards if card.id == "attack")
        return base + self.upgrades.get("attack", 0) * 2

    def glacial_multiplier(self, level: int | None = None) -> float:
        level = self.upgrades.get("heavy", 0) if level is None else level
        return GLACIAL_PERCENT[max(0, min(level, len(GLACIAL_PERCENT) - 1))] / 100

    def glacial_damage(self, level: int | None = None) -> int:
        level = self.upgrades.get("heavy", 0) if level is None else level
        percent = GLACIAL_PERCENT[max(0, min(level, len(GLACIAL_PERCENT) - 1))]
        # Nearest whole damage; exact halves round up, without float drift.
        return (self.player_magic() * percent + 50) // 100

    def active_cards(self) -> list[Card]:
        upgraded = []
        for c in self.cards:
            level = self.upgrades.get(c.id, 0)
            if c.id == "attack": amount = self.player_magic()
            elif c.id == "heavy": amount = self.glacial_damage()
            elif c.id in ("shield", "heal"): amount = c.amount + level * 2
            else: amount = c.amount
            desc = c.description
            if c.category == "attack": desc = f"Deal {amount} damage."
            elif c.category == "block": desc = f"Gain {amount} Block."
            elif c.category == "heal": desc = f"Recover up to {amount} HP."
            upgraded.append(Card(c.id, c.name + "+" * level, c.cost, c.category, amount, desc, c.count))
        return upgraded

    def player_max_hp(self) -> int:
        return 30 + self.upgrades.get("hp", 0) * 5

    def enter_battle(self, seed=None):
        cards = self.active_cards()
        max_hp = self.player_max_hp()
        turn1_energy = self.upgrades.get("energy", 0)
        self.battle = Battle(self.stage, cards, seed, player_max_hp=max_hp, turn1_bonus_energy=turn1_energy)
        self.scene = "battle"

    def calculate_reward(self, won: bool, damage_dealt: int, enemy_max_hp: int) -> int:
        base_win = 60 + self.index * 35
        max_loss = 25 + self.index * 15
        if won:
            reward = base_win
        else:
            ratio = min(1.0, max(0.0, damage_dealt / max(1, enemy_max_hp)))
            reward = round(ratio * max_loss)
        if self.index in self.cleared_stages:
            reward = max(1, reward // 2) if reward > 0 else 0
        return reward

    def resolve(self):
        if self.scene == "battle" and self.battle and self.battle.status in ("won", "lost"):
            enemy_max_hp = self.battle.enemy.max_hp
            damage_dealt = max(0, enemy_max_hp - self.battle.enemy.hp)
            won = (self.battle.status == "won")
            earned = self.calculate_reward(won, damage_dealt, enemy_max_hp)
            self.shards += earned
            is_repeat = self.index in self.cleared_stages
            if won:
                self.cleared_stages.add(self.index)
            self.last_battle_result = {
                "won": won,
                "earned": earned,
                "damage_dealt": damage_dealt,
                "enemy_max_hp": enemy_max_hp,
                "enemy_name": self.stage["enemy"]["name"],
                "stage_name": self.stage["name"],
                "half_reward": is_repeat,
            }
            if won:
                self.scene = "victory" if self.index == len(self.stages) - 1 else "shop"
            else:
                self.scene = "shop"

    def advance(self):
        if self.scene in ("clear", "shop"):
            self.index += 1
            self.scene = "intro"

    def retry(self):
        if self.scene in ("over", "shop"):
            self.scene = "intro"

    def retry_previous(self):
        if self.scene in ("over", "shop") and self.index > 0:
            self.index -= 1
            self.scene = "intro"

    def item_cost(self, item_id: str) -> int:
        cat = SHOP_CATALOG.get(item_id)
        if not cat: return 999999
        level = self.upgrades.get(item_id, 0)
        return cat["base_cost"] + level * cat["cost_inc"]

    def can_buy(self, item_id: str) -> bool:
        cat = SHOP_CATALOG.get(item_id)
        if not cat: return False
        level = self.upgrades.get(item_id, 0)
        if level >= cat["max_level"]: return False
        return self.shards >= self.item_cost(item_id)

    def buy(self, item_id: str) -> bool:
        if not self.can_buy(item_id):
            return False
        cost = self.item_cost(item_id)
        self.shards -= cost
        self.upgrades[item_id] = self.upgrades.get(item_id, 0) + 1
        return True
