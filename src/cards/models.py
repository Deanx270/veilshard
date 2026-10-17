from dataclasses import dataclass, field
import random

@dataclass(frozen=True)
class Card:
    id: str
    name: str
    cost: int
    category: str
    amount: int
    description: str
    count: int

@dataclass
class Deck:
    draw_pile: list[Card]
    rng: random.Random = field(default_factory=random.Random)
    discard: list[Card] = field(default_factory=list)
    hand: list[Card] = field(default_factory=list)

    @classmethod
    def starting(cls, cards: list[Card], rng: random.Random):
        deck = cls([card for card in cards for _ in range(card.count)], rng)
        rng.shuffle(deck.draw_pile)
        return deck

    def draw(self, count: int):
        for _ in range(count):
            if not self.draw_pile:
                self.draw_pile, self.discard = self.discard, []
                self.rng.shuffle(self.draw_pile)
            if not self.draw_pile:
                break
            self.hand.append(self.draw_pile.pop())

    def discard_hand(self):
        self.discard.extend(self.hand)
        self.hand.clear()
