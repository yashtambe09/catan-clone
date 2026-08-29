import pytest

from app.rooms import RoomError, RoomManager


@pytest.fixture
def manager():
    return RoomManager()


def _auth(manager, sid, user_id, username):
    manager.register_identity(sid, user_id, username)


def test_create_room_makes_the_creator_host(manager):
    _auth(manager, "sid-1", 1, "Alice")
    room = manager.create_room("sid-1", 4)
    assert room.max_players == 4
    assert len(room.players) == 1
    assert room.players[0].name == "Alice"
    assert room.players[0].user_id == 1
    assert room.players[0].is_host is True
    assert room.phase == "lobby"
    assert room.code in manager.rooms


@pytest.mark.parametrize("player_count", [0, 1, 7, -1, None, "4"])
def test_create_room_rejects_invalid_player_count(manager, player_count):
    _auth(manager, "sid-1", 1, "Alice")
    with pytest.raises(RoomError) as exc:
        manager.create_room("sid-1", player_count)
    assert exc.value.code == "invalid_player_count"


def test_create_room_rejects_an_unauthenticated_sid(manager):
    with pytest.raises(RoomError) as exc:
        manager.create_room("ghost-sid", 4)
    assert exc.value.code == "not_authenticated"


def test_create_room_rejects_a_sid_already_in_a_room(manager):
    _auth(manager, "sid-1", 1, "Alice")
    manager.create_room("sid-1", 4)
    with pytest.raises(RoomError) as exc:
        manager.create_room("sid-1", 4)
    assert exc.value.code == "already_in_room"


def test_join_room_adds_a_non_host_player(manager):
    _auth(manager, "sid-1", 1, "Alice")
    _auth(manager, "sid-2", 2, "Bob")
    room = manager.create_room("sid-1", 4)
    joined = manager.join_room("sid-2", room.code)
    assert joined.code == room.code
    assert [p.name for p in joined.players] == ["Alice", "Bob"]
    assert joined.players[1].is_host is False


def test_join_room_is_case_insensitive_on_code(manager):
    _auth(manager, "sid-1", 1, "Alice")
    _auth(manager, "sid-2", 2, "Bob")
    room = manager.create_room("sid-1", 4)
    joined = manager.join_room("sid-2", room.code.lower())
    assert joined.code == room.code


def test_join_room_rejects_unknown_code(manager):
    _auth(manager, "sid-2", 2, "Bob")
    with pytest.raises(RoomError) as exc:
        manager.join_room("sid-2", "NOPE99")
    assert exc.value.code == "not_found"


def test_join_room_rejects_when_full(manager):
    _auth(manager, "sid-1", 1, "Alice")
    _auth(manager, "sid-2", 2, "Bob")
    _auth(manager, "sid-3", 3, "Carol")
    room = manager.create_room("sid-1", 2)
    manager.join_room("sid-2", room.code)
    with pytest.raises(RoomError) as exc:
        manager.join_room("sid-3", room.code)
    assert exc.value.code == "room_full"


def test_join_room_rejects_after_start(manager):
    _auth(manager, "sid-1", 1, "Alice")
    _auth(manager, "sid-2", 2, "Bob")
    _auth(manager, "sid-3", 3, "Carol")
    room = manager.create_room("sid-1", 4)
    manager.join_room("sid-2", room.code)
    manager.start_game("sid-1")
    with pytest.raises(RoomError) as exc:
        manager.join_room("sid-3", room.code)
    assert exc.value.code == "already_started"


def test_join_room_rejects_a_second_connected_seat_for_the_same_user(manager):
    _auth(manager, "sid-1", 1, "Alice")
    _auth(manager, "sid-1b", 1, "Alice")
    room = manager.create_room("sid-1", 4)
    with pytest.raises(RoomError) as exc:
        manager.join_room("sid-1b", room.code)
    assert exc.value.code == "already_in_room"


def test_join_room_rejects_a_sid_already_in_a_room(manager):
    _auth(manager, "sid-1", 1, "Alice")
    _auth(manager, "sid-2", 2, "Bob")
    room = manager.create_room("sid-1", 4)
    manager.join_room("sid-2", room.code)
    with pytest.raises(RoomError) as exc:
        manager.join_room("sid-2", room.code)
    assert exc.value.code == "already_in_room"


def test_join_room_reconnects_a_disconnected_seat_for_the_same_user(manager):
    _auth(manager, "sid-1", 1, "Alice")
    _auth(manager, "sid-2", 2, "Bob")
    room = manager.create_room("sid-1", 2)
    manager.join_room("sid-2", room.code)
    manager.start_game("sid-1")

    manager.remove_player("sid-2")
    assert room.players[1].connected is False

    _auth(manager, "sid-2-new", 2, "Bob")
    rejoined = manager.join_room("sid-2-new", room.code)
    assert rejoined.code == room.code
    bob = next(p for p in rejoined.players if p.user_id == 2)
    assert bob.connected is True
    assert bob.sid == "sid-2-new"
    assert rejoined.game.players["Bob"].connected is True


def test_start_game_uses_actual_joined_count_not_declared_max(manager):
    _auth(manager, "sid-1", 1, "Alice")
    _auth(manager, "sid-2", 2, "Bob")
    _auth(manager, "sid-3", 3, "Carol")
    room = manager.create_room("sid-1", 6)
    manager.join_room("sid-2", room.code)
    manager.join_room("sid-3", room.code)
    started = manager.start_game("sid-1")
    assert started.board.player_count == 3
    assert len(started.board.hexes) == 19
    assert started.phase == "in_game"


def test_start_game_rejects_non_host(manager):
    _auth(manager, "sid-1", 1, "Alice")
    _auth(manager, "sid-2", 2, "Bob")
    room = manager.create_room("sid-1", 4)
    manager.join_room("sid-2", room.code)
    with pytest.raises(RoomError) as exc:
        manager.start_game("sid-2")
    assert exc.value.code == "not_host"


def test_start_game_rejects_fewer_than_two_players(manager):
    _auth(manager, "sid-1", 1, "Alice")
    manager.create_room("sid-1", 4)
    with pytest.raises(RoomError) as exc:
        manager.start_game("sid-1")
    assert exc.value.code == "not_enough_players"


def test_start_game_rejects_sid_not_in_any_room(manager):
    with pytest.raises(RoomError) as exc:
        manager.start_game("ghost-sid")
    assert exc.value.code == "not_found"


def test_start_game_rejects_already_started(manager):
    _auth(manager, "sid-1", 1, "Alice")
    _auth(manager, "sid-2", 2, "Bob")
    room = manager.create_room("sid-1", 4)
    manager.join_room("sid-2", room.code)
    manager.start_game("sid-1")
    with pytest.raises(RoomError) as exc:
        manager.start_game("sid-1")
    assert exc.value.code == "already_started"


def test_remove_player_promotes_next_player_to_host_on_host_disconnect(manager):
    _auth(manager, "sid-1", 1, "Alice")
    _auth(manager, "sid-2", 2, "Bob")
    room = manager.create_room("sid-1", 4)
    manager.join_room("sid-2", room.code)
    updated = manager.remove_player("sid-1")
    assert [p.name for p in updated.players] == ["Bob"]
    assert updated.players[0].is_host is True


def test_remove_player_leaves_host_unchanged_when_non_host_leaves(manager):
    _auth(manager, "sid-1", 1, "Alice")
    _auth(manager, "sid-2", 2, "Bob")
    room = manager.create_room("sid-1", 4)
    manager.join_room("sid-2", room.code)
    updated = manager.remove_player("sid-2")
    assert [p.name for p in updated.players] == ["Alice"]
    assert updated.players[0].is_host is True


def test_remove_player_deletes_an_emptied_room(manager):
    _auth(manager, "sid-1", 1, "Alice")
    room = manager.create_room("sid-1", 4)
    result = manager.remove_player("sid-1")
    assert result is None
    assert room.code not in manager.rooms
    assert "sid-1" not in manager.sid_to_code


def test_remove_player_is_a_no_op_for_an_unknown_sid(manager):
    assert manager.remove_player("ghost-sid") is None


def test_remove_player_also_clears_the_identity_for_a_sid_that_never_joined(manager):
    _auth(manager, "sid-1", 1, "Alice")
    manager.remove_player("sid-1")
    assert "sid-1" not in manager.sid_to_identity


def test_remove_player_frees_the_sid_to_join_a_new_room(manager):
    _auth(manager, "sid-1", 1, "Alice")
    room = manager.create_room("sid-1", 4)
    manager.remove_player("sid-1")
    _auth(manager, "sid-1", 1, "Alice")
    new_room = manager.create_room("sid-1", 2)
    assert new_room.code != room.code


def test_room_to_dict_has_no_board_before_start(manager):
    _auth(manager, "sid-1", 1, "Alice")
    room = manager.create_room("sid-1", 4)
    assert room.to_dict()["board"] is None
    assert room.to_dict()["phase"] == "lobby"


def test_room_to_dict_includes_serialized_board_after_start(manager):
    _auth(manager, "sid-1", 1, "Alice")
    _auth(manager, "sid-2", 2, "Bob")
    room = manager.create_room("sid-1", 4)
    manager.join_room("sid-2", room.code)
    manager.start_game("sid-1")
    payload = room.to_dict()
    assert payload["phase"] == "in_game"
    assert payload["board"]["player_count"] == 2
    assert len(payload["board"]["hexes"]) == 19


def _start_two_player_game(manager):
    from app.game.state import Phase

    _auth(manager, "sid-1", 1, "Alice")
    _auth(manager, "sid-2", 2, "Bob")
    room = manager.create_room("sid-1", 2)
    manager.join_room("sid-2", room.code)
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


def test_game_action_detects_a_win_and_sets_game_over(manager):
    room = _start_two_player_game(manager)
    room.game.players["Alice"].settlements = {f"v{i}" for i in range(10)}

    updated = manager.game_action("sid-1", "end_turn", {})
    assert updated.game.phase.value == "game_over"
    assert updated.game.winner == "Alice"


def test_game_action_does_not_check_win_when_the_action_itself_is_rejected(manager):
    room = _start_two_player_game(manager)
    room.game.players["Alice"].settlements = {f"v{i}" for i in range(10)}

    with pytest.raises(Exception):
        manager.game_action("sid-1", "bank_trade", {"give": "wood", "want": "wood"})
    assert room.game.phase.value != "game_over"
