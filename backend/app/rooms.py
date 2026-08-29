import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from app.game import engine
from app.game.board import Board, generate_board, topology_for
from app.game.placement import GameError
from app.game.state import GameState
from app.game.topology import Topology

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 6
MAX_CODE_ATTEMPTS = 50


class RoomError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class Identity:
    user_id: int
    username: str


@dataclass
class Player:
    sid: str
    user_id: int
    name: str
    is_host: bool = False
    connected: bool = True

    def to_dict(self) -> dict:
        return {"name": self.name, "is_host": self.is_host, "connected": self.connected}


@dataclass
class Room:
    code: str
    max_players: int
    players: list[Player] = field(default_factory=list)
    phase: Literal["lobby", "in_game"] = "lobby"
    board: Board | None = None
    topology: Topology | None = None
    game: GameState | None = None
    started_at: datetime | None = None
    persisted: bool = False

    def to_dict(self, viewer: str | None = None) -> dict:
        return {
            "code": self.code,
            "max_players": self.max_players,
            "players": [p.to_dict() for p in self.players],
            "phase": self.phase,
            "board": self.board.model_dump(mode="json") if self.board else None,
            "game": self._game_dict(viewer),
        }

    def _game_dict(self, viewer: str | None) -> dict | None:
        if self.game is None:
            return None
        legal = engine.legal_moves(self.board, self.topology, self.game)
        return self.game.to_dict(legal=legal, viewer=viewer)


def _action_setup_settlement(room: Room, name: str, payload: dict):
    engine.setup_settlement(room.board, room.topology, room.game, name, payload.get("vertex"))


def _action_setup_road(room: Room, name: str, payload: dict):
    engine.setup_road(room.board, room.topology, room.game, name, payload.get("edge"))


def _action_roll(room: Room, name: str, payload: dict):
    engine.roll(room.board, room.topology, room.game, name)


def _action_discard(room: Room, name: str, payload: dict):
    engine.discard(room.game, name, payload.get("resources") or {})


def _action_move_robber(room: Room, name: str, payload: dict):
    from app.game.coords import Axial

    q, r = payload.get("hex", (None, None))
    engine.move_robber(room.board, room.topology, room.game, name, Axial(q, r), payload.get("steal_from"))


def _action_build_settlement(room: Room, name: str, payload: dict):
    engine.build_settlement(room.board, room.topology, room.game, name, payload.get("vertex"))


def _action_build_road(room: Room, name: str, payload: dict):
    engine.build_road(room.board, room.topology, room.game, name, payload.get("edge"))


def _action_build_city(room: Room, name: str, payload: dict):
    engine.build_city(room.board, room.topology, room.game, name, payload.get("vertex"))


def _action_end_turn(room: Room, name: str, payload: dict):
    engine.end_turn(room.board, room.topology, room.game, name)


def _action_bank_trade(room: Room, name: str, payload: dict):
    engine.bank_trade(
        room.board, room.topology, room.game, name,
        payload.get("give"), payload.get("want"), payload.get("count", 1),
    )


def _action_trade_propose(room: Room, name: str, payload: dict):
    engine.trade_propose(
        room.game, name, payload.get("give") or {}, payload.get("want") or {}, payload.get("target")
    )


def _action_trade_counter(room: Room, name: str, payload: dict):
    engine.trade_counter(room.game, name, payload.get("give") or {}, payload.get("want") or {})


def _action_trade_accept(room: Room, name: str, payload: dict):
    engine.trade_accept(room.game, name)


def _action_trade_reject(room: Room, name: str, payload: dict):
    engine.trade_reject(room.game, name)


def _action_trade_cancel(room: Room, name: str, payload: dict):
    engine.trade_cancel(room.game, name)


def _action_buy_dev_card(room: Room, name: str, payload: dict):
    engine.buy_dev_card(room.board, room.topology, room.game, name)


def _action_play_knight(room: Room, name: str, payload: dict):
    from app.game.coords import Axial

    q, r = payload.get("hex", (None, None))
    engine.play_knight(room.board, room.topology, room.game, name, Axial(q, r), payload.get("steal_from"))


def _action_play_monopoly(room: Room, name: str, payload: dict):
    engine.play_monopoly(room.board, room.topology, room.game, name, payload.get("resource"))


def _action_play_year_of_plenty(room: Room, name: str, payload: dict):
    engine.play_year_of_plenty(room.board, room.topology, room.game, name, payload.get("resources") or [])


def _action_play_road_building(room: Room, name: str, payload: dict):
    engine.play_road_building(room.board, room.topology, room.game, name, payload.get("edges") or [])


_GAME_ACTIONS = {
    "setup_settlement": _action_setup_settlement,
    "setup_road": _action_setup_road,
    "roll": _action_roll,
    "discard": _action_discard,
    "move_robber": _action_move_robber,
    "build_settlement": _action_build_settlement,
    "build_road": _action_build_road,
    "build_city": _action_build_city,
    "end_turn": _action_end_turn,
    "bank_trade": _action_bank_trade,
    "trade_propose": _action_trade_propose,
    "trade_counter": _action_trade_counter,
    "trade_accept": _action_trade_accept,
    "trade_reject": _action_trade_reject,
    "trade_cancel": _action_trade_cancel,
    "buy_dev_card": _action_buy_dev_card,
    "play_knight": _action_play_knight,
    "play_monopoly": _action_play_monopoly,
    "play_year_of_plenty": _action_play_year_of_plenty,
    "play_road_building": _action_play_road_building,
}


class RoomManager:
    def __init__(self):
        self.rooms: dict[str, Room] = {}
        self.sid_to_code: dict[str, str] = {}
        self.sid_to_identity: dict[str, Identity] = {}

    def register_identity(self, sid: str, user_id: int, username: str) -> None:
        self.sid_to_identity[sid] = Identity(user_id=user_id, username=username)

    def _identity_for_sid(self, sid: str) -> Identity:
        identity = self.sid_to_identity.get(sid)
        if identity is None:
            raise RoomError("not_authenticated", "no verified identity for this connection")
        return identity

    def _generate_code(self) -> str:
        for _ in range(MAX_CODE_ATTEMPTS):
            code = "".join(random.choices(CODE_ALPHABET, k=CODE_LENGTH))
            if code not in self.rooms:
                return code
        raise RoomError("server_error", "could not allocate a room code")

    def _room_for_sid(self, sid: str) -> Room:
        code = self.sid_to_code.get(sid)
        room = self.rooms.get(code) if code else None
        if room is None:
            raise RoomError("not_found", "you are not in a room")
        return room

    def name_for_sid(self, sid: str) -> str | None:
        code = self.sid_to_code.get(sid)
        room = self.rooms.get(code) if code else None
        if room is None:
            return None
        player = next((p for p in room.players if p.sid == sid), None)
        return player.name if player else None

    def create_room(self, sid: str, player_count: int) -> Room:
        identity = self._identity_for_sid(sid)
        if sid in self.sid_to_code:
            raise RoomError("already_in_room", "you are already in a room")
        if not isinstance(player_count, int) or not 2 <= player_count <= 6:
            raise RoomError("invalid_player_count", "player_count must be between 2 and 6")

        code = self._generate_code()
        room = Room(code=code, max_players=player_count)
        room.players.append(
            Player(sid=sid, user_id=identity.user_id, name=identity.username, is_host=True)
        )
        self.rooms[code] = room
        self.sid_to_code[sid] = code
        return room

    def join_room(self, sid: str, code: str) -> Room:
        identity = self._identity_for_sid(sid)
        if sid in self.sid_to_code:
            raise RoomError("already_in_room", "you are already in a room")

        room = self.rooms.get((code or "").strip().upper())
        if room is None:
            raise RoomError("not_found", "no room with that code")

        existing = next((p for p in room.players if p.user_id == identity.user_id), None)
        if existing is not None and not existing.connected:
            existing.sid = sid
            existing.connected = True
            if room.game is not None and existing.name in room.game.players:
                room.game.players[existing.name].connected = True
            self.sid_to_code[sid] = room.code
            return room
        if existing is not None:
            raise RoomError("already_in_room", "you are already in this room")

        if room.phase != "lobby":
            raise RoomError("already_started", "that game has already started")
        if len(room.players) >= room.max_players:
            raise RoomError("room_full", "that room is full")

        room.players.append(Player(sid=sid, user_id=identity.user_id, name=identity.username))
        self.sid_to_code[sid] = room.code
        return room

    def start_game(self, sid: str) -> Room:
        room = self._room_for_sid(sid)
        player = next((p for p in room.players if p.sid == sid), None)
        if player is None or not player.is_host:
            raise RoomError("not_host", "only the host can start the game")
        if room.phase != "lobby":
            raise RoomError("already_started", "that game has already started")
        if len(room.players) < 2:
            raise RoomError("not_enough_players", "need at least 2 players to start")

        room.board = generate_board(len(room.players))
        room.topology = topology_for(room.board)
        room.game = engine.new_game(room.board, [p.name for p in room.players])
        room.phase = "in_game"
        room.started_at = datetime.now(timezone.utc)
        return room

    def game_action(self, sid: str, action: str, payload: dict) -> Room:
        room = self._room_for_sid(sid)
        if room.game is None:
            raise RoomError("not_in_game", "the game hasn't started yet")
        player = next((p for p in room.players if p.sid == sid), None)
        if player is None:
            raise RoomError("not_found", "you are not in this room")

        handler = _GAME_ACTIONS.get(action)
        if handler is None:
            raise GameError("unknown_action", f"unknown action: {action}")

        handler(room, player.name, payload or {})
        engine.check_win(room.game)
        return room

    def remove_player(self, sid: str) -> Room | None:
        self.sid_to_identity.pop(sid, None)

        code = self.sid_to_code.pop(sid, None)
        if code is None:
            return None
        room = self.rooms.get(code)
        if room is None:
            return None

        if room.phase == "in_game":
            leaver_name = None
            for p in room.players:
                if p.sid == sid:
                    p.connected = False
                    leaver_name = p.name
            if leaver_name and room.game and leaver_name in room.game.players:
                room.game.players[leaver_name].connected = False
            if room.game and room.game.trade and leaver_name in (
                room.game.trade.proposer,
                room.game.trade.target,
            ):
                room.game.trade = None
            return room

        was_host = any(p.sid == sid and p.is_host for p in room.players)
        room.players = [p for p in room.players if p.sid != sid]

        if not room.players:
            del self.rooms[code]
            return None

        if was_host:
            room.players[0].is_host = True

        return room
