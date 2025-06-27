# 📦 API Layer (Stable)

## 🇮🇩 Bahasa Indonesia

### Deskripsi
Folder ini berisi seluruh logic API utama, endpoint, dan middleware autentikasi. Semua request dari frontend masuk ke sini.

### Struktur File
- `server.py`: Entry point FastAPI, setup router, middleware, CORS.
- `admin.py`: Endpoint admin (analytics, logs, dsb).
- `webhook.py`: Endpoint webhook sederhana.
- `README_API.md`: Dokumentasi API (legacy, bisa merge ke sini).
- `auth/`: Middleware & route autentikasi (JWT, Firebase, guest, dsb).
- `endpoints/`: Endpoint modular (chat, rag, coder, dsb).

### Alur Utama
1. Semua request masuk ke `server.py` (FastAPI)
2. Routing ke endpoint sesuai fitur (chat, rag, dsb)
3. Middleware autentikasi di-handle di `auth/`
4. Endpoint spesifik di-handle di `endpoints/`

### Contoh Penggunaan
- Jalankan server: `python backend/main.py`
- Endpoint chat: `POST /api/chat/general`
- Endpoint admin: `GET /api/admin/system-info`

### Catatan Khusus
- Semua endpoint sudah terproteksi JWT/Firebase kecuali guest.
- Struktur endpoint mudah di-extend untuk fitur baru.

---

## 🇬🇧 English

### Description
This folder contains the main API logic, endpoints, and authentication middleware. All frontend requests are routed here.

### File Structure
- `server.py`: FastAPI entry point, router setup, middleware, CORS.
- `admin.py`: Admin endpoints (analytics, logs, etc).
- `webhook.py`: Simple webhook endpoint.
- `README_API.md`: API documentation (legacy, can be merged here).
- `auth/`: Authentication middleware & routes (JWT, Firebase, guest, etc).
- `endpoints/`: Modular endpoints (chat, rag, coder, etc).

### Main Flow
1. All requests enter via `server.py` (FastAPI)
2. Routed to feature endpoints (chat, rag, etc)
3. Auth middleware handled in `auth/`
4. Feature endpoints handled in `endpoints/`

### Usage Example
- Run server: `python backend/main.py`
- Chat endpoint: `POST /api/chat/general`
- Admin endpoint: `GET /api/admin/system-info`

### Special Notes
- All endpoints are JWT/Firebase protected except guest.
- Endpoint structure is easy to extend for new features. 