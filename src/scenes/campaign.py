from src.cards.models import Card
from src.combat.battle import Battle
from src.core.resources import read_data

class Campaign:
    def __init__(self):
        self.stages = read_data("stages")
        self.cards = [Card(**entry) for entry in read_data("cards")]
        self.story = read_data("story")
        self.scene = "menu"
        self.index = 0
        self.battle: Battle | None = None

    @property
    def stage(self):
        return self.stages[self.index]

    def start(self):
        self.index = 0
        self.battle = None
        self.scene = "intro"

    def enter_battle(self, seed=None):
        self.battle = Battle(self.stage, self.cards, seed)
        self.scene = "battle"

    def resolve(self):
        if self.scene == "battle" and self.battle:
            if self.battle.status == "won":
                self.scene = "victory" if self.index == len(self.stages) - 1 else "clear"
            elif self.battle.status == "lost":
                self.scene = "over"

    def advance(self):
        if self.scene == "clear":
            self.index += 1
            self.scene = "intro"

    def retry(self):
        if self.scene == "over":
            self.scene = "intro"
