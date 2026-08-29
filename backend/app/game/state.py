import random
from dataclasses import dataclass, field
from enum import Enum

RESOURCES = ("wood", "brick", "sheep", "wheat", "ore")
DEV_CARDS = ("knight", "victory_point", "monopoly", "road_building", "year_of_plenty")


class Phase(str, Enum):
    SETUP_SETTLEMENT = "setup_settlement"
    SETUP_ROAD = "setup_road"
    ROLL = "roll"
    DISCARD = "discard"
    MOVE_ROBBER = "move_robber"
    BUILD = "build"
    GAME_OVER = "game_over"


def _empty_dev_counts() -> dict:
    return {c: 0 for c in DEV_CARDS}


@dataclass
class PlayerState:
    name: str
    resources: dict = field(default_factory=lambda: {r: 0 for r in RESOURCES})
    settlements: set = field(default_factory=set)
    cities: set = field(default_factory=set)
    roads: set = field(default_factory=set)
    settlements_left: int = 5
    cities_left: int = 4
    roads_left: int = 15
    connected: bool = True
    dev_cards: dict = field(default_factory=_empty_dev_counts)
    dev_new: dict = field(default_factory=_empty_dev_counts)
    dev_played: dict = field(default_factory=_empty_dev_counts)
    knights_played: int = 0
    longest_road: int = 0

    def hand_size(self) -> int:
        return sum(self.resources.values())

    def dev_card_count(self) -> int:
        return sum(self.dev_cards.values()) + sum(self.dev_new.values())

    def base_victory_points(self) -> int:
        return len(self.settlements) + 2 * len(self.cities)

    def to_dict(self, private: bool = False) -> dict:
        d = {
            "name": self.name,
            "resources": dict(self.resources),
            "settlements": sorted(self.settlements),
            "cities": sorted(self.cities),
            "roads": sorted(self.roads),
            "victory_points": self.base_victory_points(),
            "connected": self.connected,
            "dev_card_count": self.dev_card_count(),
            "dev_played": dict(self.dev_played),
            "knights_played": self.knights_played,
            "longest_road": self.longest_road,
        }
        if private:
            d["dev_cards"] = dict(self.dev_cards)
            d["dev_new"] = dict(self.dev_new)
        return d


@dataclass
class TradeOffer:
    offer_id: int
    proposer: str
    give: dict
    want: dict
    target: str | None = None
    rejected_by: set = field(default_factory=set)

    def to_dict(self) -> dict:
        return {
            "offer_id": self.offer_id,
            "proposer": self.proposer,
            "give": dict(self.give),
            "want": dict(self.want),
            "target": self.target,
            "rejected_by": sorted(self.rejected_by),
        }


@dataclass
class GameState:
    order: list
    players: dict
    rng: random.Random
    phase: Phase = Phase.SETUP_SETTLEMENT
    current_index: int = 0
    setup_index: int = 0
    setup_last_vertex: str | None = None
    last_roll: tuple | None = None
    pending_discards: dict = field(default_factory=dict)
    turn_number: int = 1
    dev_deck: list = field(default_factory=list)
    trade: TradeOffer | None = None
    next_offer_id: int = 1
    longest_road_holder: str | None = None
    largest_army_holder: str | None = None
    winner: str | None = None

    def bonus_victory_points(self, name: str) -> int:
        return (2 if self.longest_road_holder == name else 0) + (
            2 if self.largest_army_holder == name else 0
        )

    def public_victory_points(self, name: str) -> int:
        return self.players[name].base_victory_points() + self.bonus_victory_points(name)

    def true_victory_points(self, name: str) -> int:
        player = self.players[name]
        return (
            player.base_victory_points()
            + self.bonus_victory_points(name)
            + player.dev_cards["victory_point"]
            + player.dev_new["victory_point"]
        )

    def current_player(self) -> str:
        n = len(self.order)
        if self.phase in (Phase.SETUP_SETTLEMENT, Phase.SETUP_ROAD):
            if self.setup_index < n:
                return self.order[self.setup_index]
            return self.order[2 * n - 1 - self.setup_index]
        return self.order[self.current_index]

    def to_dict(self, legal: dict | None = None, viewer: str | None = None) -> dict:
        players = {name: p.to_dict(private=(name == viewer)) for name, p in self.players.items()}
        for name, payload in players.items():
            payload["victory_points"] = (
                self.true_victory_points(name) if name == viewer else self.public_victory_points(name)
            )

        return {
            "order": list(self.order),
            "players": players,
            "phase": self.phase.value,
            "current_player": self.current_player(),
            "last_roll": list(self.last_roll) if self.last_roll else None,
            "pending_discards": dict(self.pending_discards),
            "turn_number": self.turn_number,
            "dev_cards_remaining": len(self.dev_deck),
            "trade": self.trade.to_dict() if self.trade else None,
            "longest_road_holder": self.longest_road_holder,
            "largest_army_holder": self.largest_army_holder,
            "winner": self.winner,
            "legal": legal or {"vertices": [], "edges": [], "bank_ratios": {}},
        }
