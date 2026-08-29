import random
from dataclasses import dataclass, field
from typing import Literal

from app.game.board import Board, generate_board

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 6
MAX_CODE_ATTEMPTS = 50
MAX_NAME_LENGTH = 24


class RoomError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class Player:
    sid: str
    name: str
    is_host: bool = False

    def to_dict(self) -> dict:
        return {"name": self.name, "is_host": self.is_host}


@dataclass
class Room:
    code: str
    max_players: int
    players: list[Player] = field(default_factory=list)
    phase: Literal["lobby", "in_game"] = "lobby"
    board: Board | None = None

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "max_players": self.max_players,
            "players": [p.to_dict() for p in self.players],
            "phase": self.phase,
            "board": self.board.model_dump(mode="json") if self.board else None,
        }


def _validate_name(name: str) -> str:
    name = (name or "").strip()
    if not name:
        raise RoomError("invalid_name", "name cannot be empty")
    if len(name) > MAX_NAME_LENGTH:
        raise RoomError("invalid_name", f"name must be {MAX_NAME_LENGTH} characters or fewer")
    return name


class RoomManager:
    def __init__(self):
        self.rooms: dict[str, Room] = {}
        self.sid_to_code: dict[str, str] = {}

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

    def create_room(self, sid: str, name: str, player_count: int) -> Room:
        name = _validate_name(name)
        if sid in self.sid_to_code:
            raise RoomError("already_in_room", "you are already in a room")
        if not isinstance(player_count, int) or not 2 <= player_count <= 6:
            raise RoomError("invalid_player_count", "player_count must be between 2 and 6")

        code = self._generate_code()
        room = Room(code=code, max_players=player_count)
        room.players.append(Player(sid=sid, name=name, is_host=True))
        self.rooms[code] = room
        self.sid_to_code[sid] = code
        return room

    def join_room(self, sid: str, code: str, name: str) -> Room:
        name = _validate_name(name)
        if sid in self.sid_to_code:
            raise RoomError("already_in_room", "you are already in a room")

        room = self.rooms.get((code or "").strip().upper())
        if room is None:
            raise RoomError("not_found", "no room with that code")
        if room.phase != "lobby":
            raise RoomError("already_started", "that game has already started")
        if len(room.players) >= room.max_players:
            raise RoomError("room_full", "that room is full")
        if name.lower() in {p.name.lower() for p in room.players}:
            raise RoomError("name_taken", "that name is already taken in this room")

        room.players.append(Player(sid=sid, name=name))
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
        room.phase = "in_game"
        return room

    def remove_player(self, sid: str) -> Room | None:
        code = self.sid_to_code.pop(sid, None)
        if code is None:
            return None
        room = self.rooms.get(code)
        if room is None:
            return None

        was_host = any(p.sid == sid and p.is_host for p in room.players)
        room.players = [p for p in room.players if p.sid != sid]

        if not room.players:
            del self.rooms[code]
            return None

        if was_host:
            room.players[0].is_host = True

        return room
