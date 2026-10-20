from src.core.security import get_password_hash, verify_password


def test_password_hashing_and_verification_work() -> None:
    password = "password123"
    hashed = get_password_hash(password)

    assert hashed
    assert verify_password(password, hashed)
    assert not verify_password("wrong-password", hashed)
