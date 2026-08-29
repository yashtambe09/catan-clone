import time

import jwt
import pytest

from app.auth import JWT_ALGORITHM, JWT_SECRET, AuthError, create_access_token, decode_access_token


def test_round_trip():
    token = create_access_token(42, "alice")
    assert decode_access_token(token) == {"user_id": 42, "username": "alice"}


@pytest.mark.parametrize("bad_token", [None, ""])
def test_missing_token_rejected(bad_token):
    with pytest.raises(AuthError) as exc:
        decode_access_token(bad_token)
    assert exc.value.code == "missing_token"


def test_tampered_token_rejected():
    token = create_access_token(1, "bob")
    # Flip a character in the middle of the payload segment, not the very last
    # character of the signature - a base64url segment's last character can
    # encode only spare padding bits, so tampering exactly there can coincide
    # with the same decoded bytes and the signature would still verify.
    mid = len(token) // 2
    flipped = "A" if token[mid] != "A" else "B"
    tampered = token[:mid] + flipped + token[mid + 1 :]
    with pytest.raises(AuthError) as exc:
        decode_access_token(tampered)
    assert exc.value.code == "invalid_token"


def test_forged_with_different_secret_rejected():
    forged = jwt.encode({"sub": "1", "username": "eve"}, "wrong-secret", algorithm=JWT_ALGORITHM)
    with pytest.raises(AuthError) as exc:
        decode_access_token(forged)
    assert exc.value.code == "invalid_token"


def test_expired_token_rejected():
    payload = {
        "sub": "1",
        "username": "carol",
        "iat": int(time.time()) - 1000,
        "exp": int(time.time()) - 500,
    }
    expired = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    with pytest.raises(AuthError) as exc:
        decode_access_token(expired)
    assert exc.value.code == "token_expired"


def test_missing_sub_rejected():
    token = jwt.encode({"username": "dave", "exp": int(time.time()) + 1000}, JWT_SECRET, algorithm=JWT_ALGORITHM)
    with pytest.raises(AuthError) as exc:
        decode_access_token(token)
    assert exc.value.code == "invalid_token"


def test_missing_username_rejected():
    token = jwt.encode({"sub": "1", "exp": int(time.time()) + 1000}, JWT_SECRET, algorithm=JWT_ALGORITHM)
    with pytest.raises(AuthError) as exc:
        decode_access_token(token)
    assert exc.value.code == "invalid_token"
