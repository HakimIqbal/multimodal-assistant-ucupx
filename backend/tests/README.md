# 🧪 Pengujian & Test Otomatis (Stable)

## 🇮🇩 Bahasa Indonesia

### Deskripsi
Folder ini berisi seluruh script pengujian (unit test, integration test) untuk backend.

### Struktur File
- `test_query_expansion.py`: Test untuk fitur query expansion
- `test_api_integration.py`: Test integrasi API
- `test_backup.py`: Test backup database
- `test_crypto_utils.py`: Test utility enkripsi
- `.gitkeep`: Placeholder agar folder tetap ada di git

### Alur Utama
1. Semua test bisa dijalankan dengan pytest
2. Test terpisah per fitur/utility

### Contoh Penggunaan
- Jalankan semua test: `pytest backend/tests/`
- Jalankan test spesifik: `pytest backend/tests/test_api_integration.py`

### Catatan Khusus
- Tambahkan test baru untuk setiap fitur baru
- Pastikan coverage test selalu tinggi

---

## 🇬🇧 English

### Description
This folder contains all test scripts (unit test, integration test) for the backend.

### File Structure
- `test_query_expansion.py`: Query expansion feature test
- `test_api_integration.py`: API integration test
- `test_backup.py`: Database backup test
- `test_crypto_utils.py`: Encryption utility test
- `.gitkeep`: Placeholder to keep folder in git

### Main Flow
1. All tests can be run with pytest
2. Tests are separated per feature/utility

### Usage Example
- Run all tests: `pytest backend/tests/`
- Run specific test: `pytest backend/tests/test_api_integration.py`

### Special Notes
- Add new tests for every new feature
- Keep test coverage high

## Install
- `pip install pytest httpx`

## Contoh test file: `tests/test_api.py`
```python
import pytest
from httpx import AsyncClient
from api.server import app

@pytest.mark.asyncio
def test_healthz():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/healthz")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
```

## Jalankan test
- `pytest tests/`

## Lihat juga:
- https://docs.pytest.org/
- https://www.python-httpx.org/ 