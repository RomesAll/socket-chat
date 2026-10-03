from app.business_logic.psw_manager import PasswordManager


def test_psw_manager():
    psw = b'qwerty'
    hash_psw = PasswordManager.hash_password(psw)
    assert type(hash_psw) is bytes
    assert PasswordManager.check_equal_psw(password=psw, hashed_password=hash_psw)
    assert not PasswordManager.check_equal_psw(password=b'1', hashed_password=hash_psw)

