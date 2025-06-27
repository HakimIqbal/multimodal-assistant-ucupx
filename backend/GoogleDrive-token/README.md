# ☁️ Google Drive Token Management (Stable)

## 🇮🇩 Bahasa Indonesia

### Deskripsi
Folder ini berisi logic dan credential untuk integrasi Google Drive (upload, token, dsb).

### Struktur File
- `drive_token_manager.py`: Manajemen token Google Drive
- `get_drive_token.py`: Script untuk mendapatkan token baru
- `client_secret_...json`: Credential OAuth Google

### Alur Utama
1. Jalankan `get_drive_token.py` untuk generate token
2. Token dikelola oleh `drive_token_manager.py`
3. File credential harus aman, jangan di-publish

### Contoh Penggunaan
- Generate token: `python get_drive_token.py`
- Manajemen token: Import `DriveTokenManager` di backend

### Catatan Khusus
- Jangan commit credential ke repo publik
- Token harus di-refresh secara berkala

---

## 🇬🇧 English

### Description
This folder contains logic and credentials for Google Drive integration (upload, token, etc).

### File Structure
- `drive_token_manager.py`: Google Drive token management
- `get_drive_token.py`: Script to obtain new token
- `client_secret_...json`: Google OAuth credentials

### Main Flow
1. Run `get_drive_token.py` to generate token
2. Token managed by `drive_token_manager.py`
3. Credentials file must be kept secure, never publish

### Usage Example
- Generate token: `python get_drive_token.py`
- Token management: Import `DriveTokenManager` in backend

### Special Notes
- Never commit credentials to public repo
- Token must be refreshed regularly 