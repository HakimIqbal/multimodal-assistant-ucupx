from cryptography.fernet import Fernet

# Kunci harus disimpan secara aman di environment variable atau config
FERNET_KEY = b'your-fernet-key-here'  # Ganti dengan kunci asli dari environment
fernet = Fernet(FERNET_KEY)

def encrypt_data(data: str) -> str:
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(data: str) -> str:
    return fernet.decrypt(data.encode()).decode() 