# 📊 Monitoring & Logging (Stable)

## 🇮🇩 Bahasa Indonesia

### Deskripsi
Folder ini berisi logic monitoring dan logging backend. Digunakan untuk mencatat aktivitas, error, dan performa aplikasi.

### Struktur File
- `logger.py`: Utility logging custom
- `.gitkeep`: Placeholder agar folder tetap ada di git

### Alur Utama
1. Import logger di modul yang ingin dicatat log-nya
2. Gunakan fungsi logging sesuai kebutuhan

### Contoh Penggunaan
- Import logger: `from monitoring.logger import logger`
- Logging info: `logger.info('Pesan info')`

### Catatan Khusus
- Logging penting untuk debugging dan audit
- Bisa diintegrasi ke monitoring eksternal

---

## 🇬🇧 English

### Description
This folder contains backend monitoring and logging logic. Used to record activity, errors, and app performance.

### File Structure
- `logger.py`: Custom logging utility
- `.gitkeep`: Placeholder to keep folder in git

### Main Flow
1. Import logger in modules to log activity
2. Use logging functions as needed

### Usage Example
- Import logger: `from monitoring.logger import logger`
- Logging info: `logger.info('Info message')`

### Special Notes
- Logging is important for debugging and audit
- Can be integrated with external monitoring

## Sentry (Error Monitoring)
- Daftar di https://sentry.io/
- Install: `pip install sentry-sdk`
- Tambahkan di `main.py` atau `server.py`:
  ```python
  import sentry_sdk
  sentry_sdk.init(dsn="YOUR_SENTRY_DSN")
  ```
- Semua error otomatis dikirim ke dashboard Sentry.

## Prometheus (Metrics)
- Gunakan [prometheus-fastapi-instrumentator](https://github.com/trallard/prometheus-fastapi-instrumentator)
- Install: `pip install prometheus-fastapi-instrumentator`
- Tambahkan di `server.py`:
  ```python
  from prometheus_fastapi_instrumentator import Instrumentator
  Instrumentator().instrument(app).expose(app)
  ```
- Endpoint metrics: `/metrics`

## Health Check Endpoint
- Sudah tersedia: `GET /healthz` (cek status API, DB, dsb)

## TODO
- Integrasi alert ke Slack/email jika error fatal. 