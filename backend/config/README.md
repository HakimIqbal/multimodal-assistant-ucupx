# ⚙️ Konfigurasi & Environment (Stable)

## 🇮🇩 Bahasa Indonesia

### Deskripsi
Folder ini berisi seluruh konfigurasi backend, termasuk integrasi Firebase, environment variable, dan pengaturan global.

### Struktur File
- `firebase_config.py`: Konfigurasi & inisialisasi Firebase Admin SDK
- `__init__.py`: Penanda package Python
- `.gitkeep`: Placeholder agar folder tetap ada di git

### Alur Utama
1. Semua pengaturan environment di-load di sini
2. Inisialisasi Firebase dilakukan otomatis saat import
3. Konfigurasi global bisa di-extend di file ini

### Contoh Penggunaan
- Inisialisasi Firebase: `from config.firebase_config import initialize_firebase`
- Ambil admin email: `get_admin_email()`

### Catatan Khusus
- Jangan commit file .env ke git
- Kunci API dan credential harus aman

---

## 🇬🇧 English

### Description
This folder contains all backend configuration, including Firebase integration, environment variables, and global settings.

### File Structure
- `firebase_config.py`: Firebase Admin SDK config & initialization
- `__init__.py`: Python package marker
- `.gitkeep`: Placeholder to keep folder in git

### Main Flow
1. All environment settings loaded here
2. Firebase initialized automatically on import
3. Global config can be extended in this file

### Usage Example
- Initialize Firebase: `from config.firebase_config import initialize_firebase`
- Get admin email: `get_admin_email()`

### Special Notes
- Never commit .env file to git
- Keep API keys and credentials secure 