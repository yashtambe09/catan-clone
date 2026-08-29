import pytest

from app.rooms import RoomError, RoomManager


@pytest.fixture
def manager():
    return RoomManager()


def test_create_room_makes_the_creator_host(manager):
    room = manager.create_room("sid-1", "Alice", 4)
    assert room.max_players == 4
    assert len(room.players) == 1
    assert room.players[0].name == "Alice"
    assert room.players[0].is_host is True
    assert room.phase == "lobby"
    assert room.code in manager.rooms


@pytest.mark.parametrize("player_count", [0, 1, 7, -1, None, "4"])
def test_create_room_rejects_invalid_player_count(manager, player_count):
    with pytest.raises(RoomError) as exc:
        manager.create_room("sid-1", "Alice", player_count)
    assert exc.value.code == "invalid_player_count"


@pytest.mark.parametrize("name", ["", "   ", None])
def test_create_room_rejects_invalid_names(manager, name):
    with pytest.raises(RoomError) as exc:
        manager.create_room("sid-1", name, 4)
    assert exc.value.code == "invalid_name"


def test_create_room_rejects_a_sid_already_in_a_room(manager):
    manager.create_room("sid-1", "Alice", 4)
    with pytest.raises(RoomError) as exc:
        manager.create_room("sid-1", "AliceAgain", 4)
    assert exc.value.code == "already_in_room"


def test_join_room_adds_a_non_host_player(manager):
    room = manager.create_room("sid-1", "Alice", 4)
    joined = manager.join_room("sid-2", room.code, "Bob")
    assert joined.code == room.code
    assert [p.name for p in joined.players] == ["Alice", "Bob"]
    assert joined.players[1].is_host is False


def test_join_room_is_case_insensitive_on_code(manager):
    room = manager.create_room("sid-1", "Alice", 4)
    joined = manager.join_room("sid-2", room.code.lower(), "Bob")
    assert joined.code == room.code


def test_join_room_rejects_unknown_code(manager):
    with pytest.raises(RoomError) as exc:
        manager.join_room("sid-2", "NOPE99", "Bob")
    assert exc.value.code == "not_found"


def test_join_room_rejects_when_full(manager):
    room = manager.create_room("sid-1", "Alice", 2)
    manager.join_room("sid-2", room.code, "Bob")
    with pytest.raises(RoomError) as exc:
        manager.join_room("sid-3", room.code, "Carol")
    assert exc.value.code == "room_full"


def test_join_room_rejects_after_start(manager):
    room = manager.create_room("sid-1", "Alice", 4)
    manager.join_room("sid-2", room.code, "Bob")
    manager.start_game("sid-1")
    with pytest.raises(RoomError) as exc:
        manager.join_room("sid-3", room.code, "Carol")
    assert exc.value.code == "already_started"


def test_join_room_rejects_case_insensitive_duplicate_name(manager):
    room = manager.create_room("sid-1", "Alice", 4)
    with pytest.raises(RoomError) as exc:
        manager.join_room("sid-2", room.code, "alice")
    assert exc.value.code == "name_taken"


def test_join_room_rejects_a_sid_already_in_a_room(manager):
    room = manager.create_room("sid-1", "Alice", 4)
    manager.join_room("sid-2", room.code, "Bob")
    with pytest.raises(RoomError) as exc:
        manager.join_room("sid-2", room.code, "BobAgain")
    assert exc.value.code == "already_in_room"


def test_start_game_uses_actual_joined_count_not_declared_max(manager):
    room = manager.create_room("sid-1", "Alice", 6)
    manager.join_room("sid-2", room.code, "Bob")
    manager.join_room("sid-3", room.code, "Carol")
    started = manager.start_game("sid-1")
    assert started.board.player_count == 3
    assert len(started.board.hexes) == 19
    assert started.phase == "in_game"


def test_start_game_rejects_non_host(manager):
    room = manager.create_room("sid-1", "Alice", 4)
    manager.join_room("sid-2", room.code, "Bob")
    with pytest.raises(RoomError) as exc:
        manager.start_game("sid-2")
    assert exc.value.code == "not_host"


def test_start_game_rejects_fewer_than_two_players(manager):
    manager.create_room("sid-1", "Alice", 4)
    with pytest.raises(RoomError) as exc:
        manager.start_game("sid-1")
    assert exc.value.code == "not_enough_players"


def test_start_game_rejects_sid_not_in_any_room(manager):
    with pytest.raises(RoomError) as exc:
        manager.start_game("ghost-sid")
    assert exc.value.code == "not_found"


def test_start_game_rejects_already_started(manager):
    room = manager.create_room("sid-1", "Alice", 4)
    manager.join_room("sid-2", room.code, "Bob")
    manager.start_game("sid-1")
    with pytest.raises(RoomError) as exc:
        manager.start_game("sid-1")
    assert exc.value.code == "already_started"


def test_remove_player_promotes_next_player_to_host_on_host_disconnect(manager):
    room = manager.create_room("sid-1", "Alice", 4)
    manager.join_room("sid-2", room.code, "Bob")
    updated = manager.remove_player("sid-1")
    assert [p.name for p in updated.players] == ["Bob"]
    assert updated.players[0].is_host is True


def test_remove_player_leaves_host_unchanged_when_non_host_leaves(manager):
    room = manager.create_room("sid-1", "Alice", 4)
    manager.join_room("sid-2", room.code, "Bob")
    updated = manager.remove_player("sid-2")
    assert [p.name for p in updated.players] == ["Alice"]
    assert updated.players[0].is_host is True


def test_remove_player_deletes_an_emptied_room(manager):
    room = manager.create_room("sid-1", "Alice", 4)
    result = manager.remove_player("sid-1")
    assert result is None
    assert room.code not in manager.rooms
    assert "sid-1" not in manager.sid_to_code


def test_remove_player_is_a_no_op_for_an_unknown_sid(manager):
    assert manager.remove_player("ghost-sid") is None


def test_remove_player_frees_the_sid_to_join_a_new_room(manager):
    room = manager.create_room("sid-1", "Alice", 4)
    manager.remove_player("sid-1")
    new_room = manager.create_room("sid-1", "Alice", 2)
    assert new_room.code != room.code


def test_room_to_dict_has_no_board_before_start(manager):
    room = manager.create_room("sid-1", "Alice", 4)
    assert room.to_dict()["board"] is None
    assert room.to_dict()["phase"] == "lobby"


def test_room_to_dict_includes_serialized_board_after_start(manager):
    room = manager.create_room("sid-1", "Alice", 4)
    manager.join_room("sid-2", room.code, "Bob")
    manager.start_game("sid-1")
    payload = room.to_dict()
    assert payload["phase"] == "in_game"
    assert payload["board"]["player_count"] == 2
    assert len(payload["board"]["hexes"]) == 19


def _start_two_player_game(manager):
    from app.game.state import Phase

    room = manager.create_room("sid-1", "Alice", 2)
    manager.join_room("sid-2", room.code, "Bob")
    room = manager.start_game("sid-1")
    room.game.phase = Phase.BUILD
    room.game.current_index = room.game.order.index("Alice")
    return room


def test_to_dict_hides_other_players_dev_cards(manager):
    room = _start_two_player_game(manager)
    room.game.players["Alice"].dev_cards["knight"] = 1

    alice_view = room.to_dict(viewer="Alice")
    bob_view = room.to_dict(viewer="Bob")

    assert "dev_cards" in alice_view["game"]["players"]["Alice"]
    assert "dev_cards" not in bob_view["game"]["players"]["Alice"]
    assert bob_view["game"]["players"]["Alice"]["dev_card_count"] == 1


def test_trade_cleared_when_proposer_disconnects(manager):
    room = _start_two_player_game(manager)
    room.game.players["Alice"].resources["wood"] = 1

    from app.game import engine

    engine.trade_propose(room.game, "Alice", {"wood": 1}, {"brick": 1})
    assert room.game.trade is not None

    manager.remove_player("sid-1")
    assert room.game.trade is None
    assert room.players[0].connected is False


def test_bank_trade_dispatches_through_game_action(manager):
    room = _start_two_player_game(manager)
    room.game.players["Alice"].resources["wood"] = 4

    updated = manager.game_action("sid-1", "bank_trade", {"give": "wood", "want": "brick"})
    assert updated.game.players["Alice"].resources["wood"] == 0
    assert updated.game.players["Alice"].resources["brick"] == 1


def test_buy_dev_card_dispatches_through_game_action(manager):
    room = _start_two_player_game(manager)
    room.game.players["Alice"].resources.update({"wheat": 1, "sheep": 1, "ore": 1})

    updated = manager.game_action("sid-1", "buy_dev_card", {})
    assert updated.game.players["Alice"].dev_card_count() == 1
