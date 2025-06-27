# 🗂️ Dokumentasi Backend

## Pilih Bahasa / Choose Language
- [🇮🇩 Bahasa Indonesia](#dokumentasi-backend-indonesia)
- [🇬🇧 English](#backend-documentation-english)

---

# 🇮🇩 Dokumentasi Backend (Indonesia)

## Status: Stable

### Daftar Isi
1. [API Layer](../backend/api/README.md)
2. [Core Logic & Integrasi](../backend/src/README.md)
3. [Konfigurasi & Environment](../backend/config/README.md)
4. [Migrasi & Schema Database](../backend/migrations/README.md)
5. [Monitoring & Logging](../backend/monitoring/README.md)
6. [Worker & Background Jobs](../backend/worker/README.md)
7. [Fitur & Pengembangan](../backend/features/README.md)
8. [Google Drive Token](../backend/GoogleDrive-token/README.md)
9. [Pengujian & Test Otomatis](../backend/tests/README.md)

### Ringkasan
- **API Layer**: Semua endpoint, routing, dan autentikasi API. [Detail](../backend/api/README.md)
- **Core Logic**: Logic utama chat, RAG, database, vektor, dsb. [Detail](../backend/src/README.md)
- **Konfigurasi**: Pengaturan environment, Firebase, dsb. [Detail](../backend/config/README.md)
- **Migrasi**: File schema dan migrasi database. [Detail](../backend/migrations/README.md)
- **Monitoring**: Logging dan monitoring performa/error. [Detail](../backend/monitoring/README.md)
- **Worker**: Template untuk background job/async task. [Detail](../backend/worker/README.md)
- **Fitur**: Dokumentasi fitur khusus & pengembangan. [Detail](../backend/features/README.md)
- **Google Drive Token**: Integrasi & manajemen token Google Drive. [Detail](../backend/GoogleDrive-token/README.md)
- **Pengujian**: Unit test & integration test backend. [Detail](../backend/tests/README.md)

### Navigasi
- Untuk detail tiap fitur/folder, klik link pada daftar isi di atas.
- Setiap folder memiliki README sendiri yang menjelaskan struktur, alur, dan contoh penggunaan.

---

## 🇮🇩 Ringkasan Fitur & Status Implementasi

### Status Implementasi
| Kategori Fitur            | Status         | Persentase |
|--------------------------|----------------|------------|
| Multimodal Input         | 🚧 Coming Soon (Audio/Video) | 90%       |
| AI Lanjutan              | ✅ Selesai      | 100%       |
| Manajemen Dokumen        | ✅ Selesai      | 100%       |
| Kolaborasi               | ✅ Selesai      | 100%       |
| Analitik                 | ✅ Selesai      | 100%       |
| Integrasi & API          | ✅ Selesai      | 100%       |
| Keamanan & Compliance    | ✅ Selesai      | 100%       |
| Pengalaman Pengguna      | ✅ Selesai      | 100%       |
| Advanced RAG             | ✅ Selesai      | 100%       |
| DevOps                   | ✅ Selesai      | 100%       |

**Total Endpoint: 30+**

### Fitur Utama
- Pemrosesan gambar (image) ✅
- Pemrosesan audio & video 🚧 *Coming Soon*
- AI multi-model & prompt engineering
- Manajemen dokumen (versi, kategori, bulk upload, metadata)
- Kolaborasi (workspaces, komentar, anotasi, chat realtime)
- Analitik & pelacakan biaya
- Webhook & integrasi pihak ketiga
- Keamanan (Firebase, audit log, GDPR, rate limit)
- Export chat/dokumen (PDF, DOCX, TXT)
- Advanced RAG (hybrid search, query expansion, confidence, multi-language)
- Monitoring, logging, caching, load balancing

### Daftar Endpoint Utama
- `/api/auth/`, `/api/guest/`, `/api/admin/`
- `/api/chat/`, `/api/coder/`, `/api/rag/`, `/api/models/`
- `/api/multimodal/image/analyze` ✅
- `/api/multimodal/audio/transcribe` 🚧 *Coming Soon*
- `/api/multimodal/video/extract` 🚧 *Coming Soon*
- `/api/documents/upload/bulk`, `/api/documents/search`, `/api/documents/versions`, `/api/documents/metadata`, `/api/documents/statistics`
- `/api/collaboration/workspaces`, `/api/collaboration/comments`, `/api/collaboration/annotations`, `/api/collaboration/activity`, `/ws/workspace/{id}`
- `/api/advanced-rag/hybrid-search`, `/api/advanced-rag/query-expansion`, `/api/advanced-rag/confidence`, `/api/advanced-rag/multilanguage`
- `/api/export/chat`, `/api/export/document`, `/api/webhook/`, `/api/costs/`, `/api/performance/`, `/health`, `/docs`

### Arsitektur Teknis (Ringkasan)
- Autentikasi Firebase, JWT, rate limit, audit log
- Database: users, documents, versions, chat logs, workspaces, comments, webhooks, analytics, cost tracking
- Optimasi: async, caching, load balancing, monitoring

> **Catatan:**
> Penjelasan teknis, struktur file, dan contoh kode ada di README masing-masing folder (lihat TOC di atas).

---

# 🇬🇧 Backend Documentation (English)

## Status: Stable

### Table of Contents
1. [API Layer](../backend/api/README.md)
2. [Core Logic & Integration](../backend/src/README.md)
3. [Configuration & Environment](../backend/config/README.md)
4. [Migration & Database Schema](../backend/migrations/README.md)
5. [Monitoring & Logging](../backend/monitoring/README.md)
6. [Worker & Background Jobs](../backend/worker/README.md)
7. [Features & Development](../backend/features/README.md)
8. [Google Drive Token](../backend/GoogleDrive-token/README.md)
9. [Testing & Automated Tests](../backend/tests/README.md)

### Summary
- **API Layer**: All endpoints, routing, and API authentication. [Detail](../backend/api/README.md)
- **Core Logic**: Main logic for chat, RAG, database, vector, etc. [Detail](../backend/src/README.md)
- **Configuration**: Environment settings, Firebase, etc. [Detail](../backend/config/README.md)
- **Migration**: Database schema and migration files. [Detail](../backend/migrations/README.md)
- **Monitoring**: Logging and performance/error monitoring. [Detail](../backend/monitoring/README.md)
- **Worker**: Template for background jobs/async tasks. [Detail](../backend/worker/README.md)
- **Features**: Special features documentation & development. [Detail](../backend/features/README.md)
- **Google Drive Token**: Google Drive integration & token management. [Detail](../backend/GoogleDrive-token/README.md)
- **Testing**: Backend unit & integration tests. [Detail](../backend/tests/README.md)

### Navigation
- For details of each feature/folder, click the links in the table of contents above.
- Each folder has its own README explaining structure, flow, and usage examples.

### Features & Implementation Status Summary

### Implementation Status
| Feature Category          | Status         | Completion |
|--------------------------|----------------|------------|
| Multimodal Input         | 🚧 Coming Soon (Audio/Video) | 90%       |
| Advanced AI              | ✅ Complete    | 100%       |
| Document Management      | ✅ Complete    | 100%       |
| Collaboration            | ✅ Complete    | 100%       |
| Analytics                | ✅ Complete    | 100%       |
| Integration & API        | ✅ Complete    | 100%       |
| Security & Compliance    | ✅ Complete    | 100%       |
| User Experience          | ✅ Complete    | 100%       |
| Advanced RAG             | ✅ Complete    | 100%       |
| DevOps                   | ✅ Complete    | 100%       |

**Total Endpoints: 30+**

### Main Features
- Image processing ✅
- Audio & video processing 🚧 *Coming Soon*
- Multi-model AI & prompt engineering
- Document management (versioning, categories, bulk upload, metadata)
- Collaboration (workspaces, comments, annotations, real-time chat)
- Analytics & cost tracking
- Webhook & third-party integrations
- Security (Firebase, audit log, GDPR, rate limiting)
- Export chat/documents (PDF, DOCX, TXT)
- Advanced RAG (hybrid search, query expansion, confidence, multi-language)
- Monitoring, logging, caching, load balancing

### Main Endpoints
- `/api/auth/`, `/api/guest/`, `/api/admin/`
- `/api/chat/`, `/api/coder/`, `/api/rag/`, `/api/models/`
- `/api/multimodal/image/analyze` ✅
- `/api/multimodal/audio/transcribe` 🚧 *Coming Soon*
- `/api/multimodal/video/extract` 🚧 *Coming Soon*
- `/api/documents/upload/bulk`, `/api/documents/search`, `/api/documents/versions`, `/api/documents/metadata`, `/api/documents/statistics`
- `/api/collaboration/workspaces`, `/api/collaboration/comments`, `/api/collaboration/annotations`, `/api/collaboration/activity`, `/ws/workspace/{id}`
- `/api/advanced-rag/hybrid-search`, `/api/advanced-rag/query-expansion`, `/api/advanced-rag/confidence`, `/api/advanced-rag/multilanguage`
- `/api/export/chat`, `/api/export/document`, `/api/webhook/`, `/api/costs/`, `/api/performance/`, `/health`, `/docs`

### Technical Architecture (Summary)
- Firebase authentication, JWT, rate limiting, audit logging
- Database: users, documents, versions, chat logs, workspaces, comments, webhooks, analytics, cost tracking
- Optimizations: async, caching, load balancing, monitoring

> **Note:**
> Technical explanations, file structure, and code examples are in each folder's README (see TOC above). 