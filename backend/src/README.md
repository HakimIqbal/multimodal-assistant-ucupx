# 🧠 Core Logic & Integrasi (Stable)

## 🇮🇩 Bahasa Indonesia

### Deskripsi
Folder ini berisi seluruh logic utama backend: chat, RAG, pemrosesan dokumen, integrasi database, dan vektor.

### Struktur File
- `chat.py`: Logic chat general (AI, model selection, dsb)
- `rag.py`: Logic retrieval-augmented generation (RAG)
- `coder.py`: Logic chat khusus coding
- `db.py`: Integrasi ke Supabase, fungsi CRUD, logging, feedback
- `vector_db.py`: Integrasi vektor (Pinecone, embedding, dsb)
- `document_processor.py`: Ekstraksi teks dari dokumen (PDF, OCR)
- `auth/`: Client Firebase, helper autentikasi

### Alur Utama
1. Endpoint API memanggil fungsi di sini untuk proses utama
2. Semua interaksi DB lewat `db.py`
3. Proses dokumen lewat `document_processor.py`
4. Integrasi vektor lewat `vector_db.py`

### Contoh Penggunaan
- Simpan dokumen: `save_document_to_supabase(...)`
- Query RAG: `query_rag(...)`
- Proses chat: `chat_general(...)`

### Catatan Khusus
- Semua logic sudah modular, mudah di-extend
- Integrasi ke Pinecone, Supabase, Firebase sudah siap pakai

---

## 🇬🇧 English

### Description
This folder contains all core backend logic: chat, RAG, document processing, database, and vector integration.

### File Structure
- `chat.py`: General chat logic (AI, model selection, etc)
- `rag.py`: Retrieval-augmented generation logic
- `coder.py`: Coding chat logic
- `db.py`: Supabase integration, CRUD, logging, feedback
- `vector_db.py`: Vector integration (Pinecone, embedding, etc)
- `document_processor.py`: Document text extraction (PDF, OCR)
- `auth/`: Firebase client, auth helpers

### Main Flow
1. API endpoints call functions here for main processing
2. All DB interaction via `db.py`
3. Document processing via `document_processor.py`
4. Vector integration via `vector_db.py`

### Usage Example
- Save document: `save_document_to_supabase(...)`
- Query RAG: `query_rag(...)`
- Process chat: `chat_general(...)`

### Special Notes
- All logic is modular and easy to extend
- Pinecone, Supabase, Firebase integration ready to use 