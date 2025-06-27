import pytest
from backend.crypto_utils import encrypt_data, decrypt_data

def test_encrypt_decrypt():
    data = "test123"
    encrypted = encrypt_data(data)
    assert encrypted != data
    decrypted = decrypt_data(encrypted)
    assert decrypted == data 