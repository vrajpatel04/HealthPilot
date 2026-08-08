from healthPilot.core.security import hash_password, verify_password


def test_hash_and_verify_password():
    hashed = hash_password("secret-password")
    assert hashed != "secret-password"
    assert verify_password("secret-password", hashed)
    assert not verify_password("wrong-password", hashed)
