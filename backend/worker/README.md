# ⚙️ Worker & Background Jobs (Experimental)

## 🇮🇩 Bahasa Indonesia

### Deskripsi
Folder ini disiapkan untuk logic worker/background job (misal: task async, scheduled job, dsb). Saat ini belum ada implementasi, bisa diisi sesuai kebutuhan.

### Struktur File
- `.gitkeep`: Placeholder agar folder tetap ada di git

### Alur Utama
1. Tambahkan worker/job baru di folder ini jika dibutuhkan
2. Ikuti best practice async/background job

### Contoh Penggunaan
- (Belum ada, template siap diisi)

### Catatan Khusus
- Folder ini masih experimental
- Silakan diisi sesuai kebutuhan project

---

## 🇬🇧 English

### Description
This folder is prepared for worker/background job logic (e.g., async tasks, scheduled jobs, etc). Currently no implementation, can be filled as needed.

### File Structure
- `.gitkeep`: Placeholder to keep folder in git

### Main Flow
1. Add new worker/job in this folder as needed
2. Follow async/background job best practices

### Usage Example
- (None yet, template ready to fill)

### Special Notes
- This folder is still experimental
- Please fill as needed for the project

## Celery (Rekomendasi)
- Install: `pip install celery redis`
- Buat file `worker/tasks.py`:
  ```python
  from celery import Celery
  app = Celery('tasks', broker='redis://localhost:6379/0')

  @app.task
def ocr_pdf(file_path):
      # TODO: Implementasi OCR async
      return "Hasil OCR"
  ```
- Jalankan worker: `celery -A worker.tasks worker --loglevel=info`
- Panggil task dari backend:
  ```python
  from worker.tasks import ocr_pdf
o = ocr_pdf.delay("file.pdf")
  ```
- Lihat https://docs.celeryq.dev/en/stable/

## RQ (Alternatif ringan)
- Install: `pip install rq redis`
- Lihat https://python-rq.org/

## TODO
- Integrasi task async untuk OCR, summary, eksekusi kode berat. 