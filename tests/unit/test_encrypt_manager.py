from app.business_logic.encrypte_manager import SymmetricEncode


async def test_encrypt_message_success():
    """Тест: Успешное шифрование сообщения."""
    encoder = SymmetricEncode(app_key=b'XHl3fcj9jbOmGQ3OZuKA-8v4dGP3aH8SYaaSPuk9PH4=')
    message = 'hello world'
    token = encoder.encrypt(message)

    assert token != message
    assert type(token) is bytes


async def test_decrypt_message_success():
    """Тест: Успешное расшифровка сообщения."""
    encoder = SymmetricEncode(app_key=b'XHl3fcj9jbOmGQ3OZuKA-8v4dGP3aH8SYaaSPuk9PH4=')
    message = 'hello world'
    token = encoder.encrypt(message)
    decode_msg = encoder.decrypt(token)

    assert decode_msg == message