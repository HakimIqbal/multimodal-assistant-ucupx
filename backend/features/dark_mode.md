# 🌙 Dark Mode Feature

## Overview
Fitur Dark Mode memungkinkan user memilih tampilan terang (light) atau gelap (dark). Preferensi tema disimpan di database dan dapat diakses oleh backend.

## API Endpoints
- `GET /api/chat/preferences/` — Mendapatkan preferensi user (termasuk theme)
- `POST /api/chat/preferences/` — Update preferensi user (theme, dsb)
- `POST /api/chat/preferences/toggle-theme/` — Toggle dark/light mode

### Contoh Request/Response
**Get Preferences**
```http
GET /api/chat/preferences/
```
**Response:**
```json
{
    "user_id": "username",
  "theme": "dark"
}
```

**Toggle Theme**
```http
POST /api/chat/preferences/toggle-theme/
```
**Response:**
```json
{
    "status": "success",
  "theme": "dark"
}
```

> **Catatan:**
> Detail implementasi backend & database dapat dilihat di `docs/backend.md` dan kode sumber terkait.