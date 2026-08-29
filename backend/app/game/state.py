import random
from dataclasses import dataclass, field
from enum import Enum

RESOURCES = ("wood", "brick", "sheep", "wheat", "ore")


class Phase(str, Enum):
    SETUP_SETTLEMENT = "setup_settlement"
    SETUP_ROAD = "setup_road"
    ROLL = "roll"
    DISCARD = "discard"
    MOVE_ROBBER = "move_robber"
    BUILD = "build"


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

    def hand_size(self) -> int:
        return sum(self.resources.values())

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "resources": dict(self.resources),
            "settlements": sorted(self.settlements),
            "cities": sorted(self.cities),
            "roads": sorted(self.roads),
            "victory_points": len(self.settlements) + 2 * len(self.cities),
            "connected": self.connected,
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

    def current_player(self) -> str:
        n = len(self.order)
        if self.phase in (Phase.SETUP_SETTLEMENT, Phase.SETUP_ROAD):
            if self.setup_index < n:
                return self.order[self.setup_index]
            return self.order[2 * n - 1 - self.setup_index]
        return self.order[self.current_index]

    def to_dict(self, legal: dict | None = None) -> dict:
        return {
            "order": list(self.order),
            "players": {name: p.to_dict() for name, p in self.players.items()},
            "phase": self.phase.value,
            "current_player": self.current_player(),
            "last_roll": list(self.last_roll) if self.last_roll else None,
            "pending_discards": dict(self.pending_discards),
            "turn_number": self.turn_number,
            "legal": legal or {"vertices": [], "edges": []},
        }
