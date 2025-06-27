# 📚 Dokumentasi Lengkap Backend Multimodal Assistant

## 🇮🇩 Bahasa Indonesia

### 📋 Daftar Isi
1. [Gambaran Umum](#gambaran-umum)
2. [Struktur Folder](#struktur-folder)
3. [File Utama](#file-utama)
4. [API Endpoints](#api-endpoints)
5. [Database Schema](#database-schema)
6. [Konfigurasi](#konfigurasi)
7. [Fitur Utama](#fitur-utama)
8. [Testing](#testing)
9. [Monitoring & Logging](#monitoring--logging)
10. [Deployment](#deployment)

---

## 🇺🇸 English

### 📋 Table of Contents
1. [Overview](#overview)
2. [Folder Structure](#folder-structure)
3. [Main Files](#main-files)
4. [API Endpoints](#api-endpoints-1)
5. [Database Schema](#database-schema-1)
6. [Configuration](#configuration)
7. [Core Features](#core-features)
8. [Testing](#testing-1)
9. [Monitoring & Logging](#monitoring--logging-1)
10. [Deployment](#deployment-1)

---

## 🇮🇩 GAMBARAN UMUM

Backend Multimodal Assistant adalah sistem AI yang komprehensif dengan kemampuan multimodal, autentikasi, dan fitur-fitur canggih. Sistem ini dibangun menggunakan FastAPI, Python, dan berbagai teknologi AI modern.

### 🎯 Fitur Utama:
- **Chat AI**: General chat, coding assistant, dan RAG system
- **Multimodal Processing**: Pemrosesan gambar, dokumen, dan teks
- **Authentication**: Firebase Auth dengan middleware keamanan
- **Document Management**: Upload, processing, dan retrieval dokumen
- **Collaboration**: Fitur kolaborasi real-time
- **Cost Tracking**: Pelacakan biaya penggunaan AI
- **Webhooks**: Integrasi dengan sistem eksternal
- **Performance Monitoring**: Caching dan optimasi performa

---

## 🇺🇸 OVERVIEW

The Multimodal Assistant Backend is a comprehensive AI system with multimodal capabilities, authentication, and advanced features. The system is built using FastAPI, Python, and various modern AI technologies.

### 🎯 Core Features:
- **AI Chat**: General chat, coding assistant, and RAG system
- **Multimodal Processing**: Image, document, and text processing
- **Authentication**: Firebase Auth with security middleware
- **Document Management**: Upload, processing, and document retrieval
- **Collaboration**: Real-time collaboration features
- **Cost Tracking**: AI usage cost tracking
- **Webhooks**: External system integration
- **Performance Monitoring**: Caching and performance optimization

---

## 🇮🇩 STRUKTUR FOLDER

```
backend/
├── 📁 api/                          # API endpoints dan server
│   ├── 📁 auth/                     # Autentikasi dan middleware
│   ├── 📁 endpoints/                # Semua endpoint API
│   ├── admin.py                     # Admin panel endpoints
│   ├── server.py                    # FastAPI server utama
│   └── webhook.py                   # Webhook handler
├── 📁 src/                          # Core business logic
│   ├── 📁 auth/                     # Firebase client
│   ├── chat.py                      # Chat functionality
│   ├── coder.py                     # Code assistant logic
│   ├── db.py                        # Database operations
│   ├── document_processor.py        # Document processing
│   ├── rag.py                       # RAG system
│   └── vector_db.py                 # Vector database operations
├── 📁 config/                       # Konfigurasi sistem
│   └── firebase_config.py           # Firebase configuration
├── 📁 migrations/                   # Database schema
│   └── complete_schema.sql          # Complete database schema
├── 📁 monitoring/                   # Monitoring dan logging
│   └── logger.py                    # Logging configuration
├── 📁 worker/                       # Background workers
├── 📁 features/                     # Fitur tambahan
│   └── dark_mode.md                 # Dark mode documentation
├── 📁 GoogleDrive-token/            # Google Drive integration
│   ├── drive_token_manager.py       # Token management
│   └── get_drive_token.py           # Token retrieval
├── 📁 tests/                        # Unit tests
├── 📁 .github/                      # GitHub workflows
├── app.py                           # Streamlit frontend
├── main.py                          # Entry point
├── models.py                        # AI models configuration
├── config.py                        # Environment configuration
├── backup.py                        # Backup utilities
├── crypto_utils.py                  # Cryptographic utilities
├── query_expansion.py               # Query expansion logic
└── requirements.txt                 # Python dependencies
```

---

## 🇺🇸 FOLDER STRUCTURE

```
backend/
├── 📁 api/                          # API endpoints and server
│   ├── 📁 auth/                     # Authentication and middleware
│   ├── 📁 endpoints/                # All API endpoints
│   ├── admin.py                     # Admin panel endpoints
│   ├── server.py                    # Main FastAPI server
│   └── webhook.py                   # Webhook handler
├── 📁 src/                          # Core business logic
│   ├── 📁 auth/                     # Firebase client
│   ├── chat.py                      # Chat functionality
│   ├── coder.py                     # Code assistant logic
│   ├── db.py                        # Database operations
│   ├── document_processor.py        # Document processing
│   ├── rag.py                       # RAG system
│   └── vector_db.py                 # Vector database operations
├── 📁 config/                       # System configuration
│   └── firebase_config.py           # Firebase configuration
├── 📁 migrations/                   # Database schema
│   └── complete_schema.sql          # Complete database schema
├── 📁 monitoring/                   # Monitoring and logging
│   └── logger.py                    # Logging configuration
├── 📁 worker/                       # Background workers
├── 📁 features/                     # Additional features
│   └── dark_mode.md                 # Dark mode documentation
├── 📁 GoogleDrive-token/            # Google Drive integration
│   ├── drive_token_manager.py       # Token management
│   └── get_drive_token.py           # Token retrieval
├── 📁 tests/                        # Unit tests
├── 📁 .github/                      # GitHub workflows
├── app.py                           # Streamlit frontend
├── main.py                          # Entry point
├── models.py                        # AI models configuration
├── config.py                        # Environment configuration
├── backup.py                        # Backup utilities
├── crypto_utils.py                  # Cryptographic utilities
├── query_expansion.py               # Query expansion logic
└── requirements.txt                 # Python dependencies
```

---

## 🇮🇩 FILE UTAMA

### 🚀 Entry Points
- **`main.py`**: Entry point utama dengan health checks dan konfigurasi
- **`app.py`**: Streamlit frontend untuk testing dan demo
- **`api/server.py`**: FastAPI server dengan semua endpoint

### 🧠 AI Models & Configuration
- **`models.py`**: Konfigurasi model AI (Groq, Gemini, OpenRouter)
- **`config.py`**: Environment variables dan konfigurasi sistem
- **`query_expansion.py`**: Logika ekspansi query untuk RAG

### 🔧 Utilities
- **`backup.py`**: Utilitas backup database
- **`crypto_utils.py`**: Fungsi kriptografi untuk keamanan

---

## 🇺🇸 MAIN FILES

### 🚀 Entry Points
- **`main.py`**: Main entry point with health checks and configuration
- **`app.py`**: Streamlit frontend for testing and demo
- **`api/server.py`**: FastAPI server with all endpoints

### 🧠 AI Models & Configuration
- **`models.py`**: AI model configuration (Groq, Gemini, OpenRouter)
- **`config.py`**: Environment variables and system configuration
- **`query_expansion.py`**: Query expansion logic for RAG

### 🔧 Utilities
- **`backup.py`**: Database backup utilities
- **`crypto_utils.py`**: Cryptographic functions for security

---

## 🇮🇩 API ENDPOINTS

### 🔐 Authentication (`/api/auth`)
- **POST** `/register` - Registrasi user baru
- **POST** `/login` - Login user
- **POST** `/logout` - Logout user
- **GET** `/profile` - Ambil profil user
- **PUT** `/profile` - Update profil user
- **POST** `/refresh` - Refresh token
- **POST** `/forgot-password` - Reset password
- **POST** `/verify-email` - Verifikasi email

### 👥 Guest Access (`/api/guest`)
- **POST** `/chat` - Chat untuk guest users
- **POST** `/upload` - Upload dokumen untuk guest
- **GET** `/models` - Daftar model yang tersedia

### 💬 General Chat (`/api/chat`)
- **POST** `/general/` - Chat umum dengan AI
- **POST** `/stream/` - Streaming chat response
- **GET** `/history` - Riwayat chat

### 💻 Code Assistant (`/api/coder`)
- **POST** `/coder/` - Coding assistance
- **POST** `/debug/` - Debug code
- **POST** `/explain/` - Explain code
- **POST** `/optimize/` - Optimize code

### 📄 Document RAG (`/api/rag`)
- **POST** `/upload/` - Upload dokumen
- **POST** `/query/` - Query dokumen
- **GET** `/documents` - List dokumen
- **DELETE** `/documents/{id}` - Hapus dokumen

### 🖼️ Multimodal (`/api/multimodal`)
- **POST** `/process-image/` - Proses gambar
- **POST** `/ocr/` - OCR text dari gambar
- **POST** `/analyze/` - Analisis multimodal

### 📤 Export (`/api/export`)
- **POST** `/chat-history` - Export riwayat chat
- **POST** `/documents` - Export dokumen
- **POST** `/analytics` - Export analytics

### 🔗 Webhooks (`/api/webhook`)
- **POST** `/register` - Register webhook
- **GET** `/list` - List webhooks
- **DELETE** `/delete/{id}` - Delete webhook
- **POST** `/trigger/{id}` - Trigger webhook

### 👥 Collaboration (`/api/collaboration`)
- **POST** `/create-room` - Buat room kolaborasi
- **POST** `/join-room` - Join room
- **POST** `/send-message` - Kirim pesan
- **GET** `/room/{id}/messages` - Ambil pesan room

### 🔍 Advanced RAG (`/api/advanced-rag`)
- **POST** `/hybrid-search` - Hybrid search
- **POST** `/semantic-search` - Semantic search
- **POST** `/query-expansion` - Query expansion

### 📁 Document Management (`/api/documents`)
- **GET** `/list` - List semua dokumen
- **POST** `/upload` - Upload dokumen
- **GET** `/download/{id}` - Download dokumen
- **PUT** `/update/{id}` - Update dokumen
- **DELETE** `/delete/{id}` - Delete dokumen

### 💰 Cost Tracking (`/api/costs`)
- **GET** `/usage` - Usage statistics
- **GET** `/billing` - Billing information
- **POST** `/set-limits` - Set usage limits

### ⚡ Performance (`/api/performance`)
- **GET** `/cache-stats` - Cache statistics
- **POST** `/clear-cache` - Clear cache
- **GET** `/metrics` - Performance metrics

---

## 🇺🇸 API ENDPOINTS

### 🔐 Authentication (`/api/auth`)
- **POST** `/register` - Register new user
- **POST** `/login` - User login
- **POST** `/logout` - User logout
- **GET** `/profile` - Get user profile
- **PUT** `/profile` - Update user profile
- **POST** `/refresh` - Refresh token
- **POST** `/forgot-password` - Reset password
- **POST** `/verify-email` - Verify email

### 👥 Guest Access (`/api/guest`)
- **POST** `/chat` - Chat for guest users
- **POST** `/upload` - Upload documents for guests
- **GET** `/models` - List available models

### 💬 General Chat (`/api/chat`)
- **POST** `/general/` - General AI chat
- **POST** `/stream/` - Streaming chat response
- **GET** `/history` - Chat history

### 💻 Code Assistant (`/api/coder`)
- **POST** `/coder/` - Coding assistance
- **POST** `/debug/` - Debug code
- **POST** `/explain/` - Explain code
- **POST** `/optimize/` - Optimize code

### 📄 Document RAG (`/api/rag`)
- **POST** `/upload/` - Upload documents
- **POST** `/query/` - Query documents
- **GET** `/documents` - List documents
- **DELETE** `/documents/{id}` - Delete document

### 🖼️ Multimodal (`/api/multimodal`)
- **POST** `/process-image/` - Process images
- **POST** `/ocr/` - OCR text from images
- **POST** `/analyze/` - Multimodal analysis

### 📤 Export (`/api/export`)
- **POST** `/chat-history` - Export chat history
- **POST** `/documents` - Export documents
- **POST** `/analytics` - Export analytics

### 🔗 Webhooks (`/api/webhook`)
- **POST** `/register` - Register webhook
- **GET** `/list` - List webhooks
- **DELETE** `/delete/{id}` - Delete webhook
- **POST** `/trigger/{id}` - Trigger webhook

### 👥 Collaboration (`/api/collaboration`)
- **POST** `/create-room` - Create collaboration room
- **POST** `/join-room` - Join room
- **POST** `/send-message` - Send message
- **GET** `/room/{id}/messages` - Get room messages

### 🔍 Advanced RAG (`/api/advanced-rag`)
- **POST** `/hybrid-search` - Hybrid search
- **POST** `/semantic-search` - Semantic search
- **POST** `/query-expansion` - Query expansion

### 📁 Document Management (`/api/documents`)
- **GET** `/list` - List all documents
- **POST** `/upload` - Upload document
- **GET** `/download/{id}` - Download document
- **PUT** `/update/{id}` - Update document
- **DELETE** `/delete/{id}` - Delete document

### 💰 Cost Tracking (`/api/costs`)
- **GET** `/usage` - Usage statistics
- **GET** `/billing` - Billing information
- **POST** `/set-limits` - Set usage limits

### ⚡ Performance (`/api/performance`)
- **GET** `/cache-stats` - Cache statistics
- **POST** `/clear-cache` - Clear cache
- **GET** `/metrics` - Performance metrics

---

## 🇮🇩 DATABASE SCHEMA

### 📊 Tabel Utama:
1. **users** - Data pengguna
2. **chat_logs** - Riwayat chat
3. **documents** - Dokumen yang diupload
4. **feedback** - Feedback pengguna
5. **analytics** - Data analytics
6. **user_preferences** - Preferensi pengguna
7. **snippets** - Code snippets
8. **audit_logs** - Log audit
9. **cost_tracking** - Pelacakan biaya
10. **webhook_events** - Event webhook
11. **webhook_configs** - Konfigurasi webhook
12. **ip_blocklist** - Daftar IP yang diblokir

### 🔗 Relasi:
- Foreign key constraints dengan cascade delete
- Index untuk optimasi query
- Triggers untuk audit logging

---

## 🇺🇸 DATABASE SCHEMA

### 📊 Main Tables:
1. **users** - User data
2. **chat_logs** - Chat history
3. **documents** - Uploaded documents
4. **feedback** - User feedback
5. **analytics** - Analytics data
6. **user_preferences** - User preferences
7. **snippets** - Code snippets
8. **audit_logs** - Audit logs
9. **cost_tracking** - Cost tracking
10. **webhook_events** - Webhook events
11. **webhook_configs** - Webhook configurations
12. **ip_blocklist** - Blocked IP list

### 🔗 Relations:
- Foreign key constraints with cascade delete
- Indexes for query optimization
- Triggers for audit logging

---

## 🇮🇩 KONFIGURASI

### 🔑 Environment Variables:
```bash
# AI Model APIs
GROQ_API_KEY=your_groq_key
GEMINI_API_KEY=your_gemini_key
OPENROUTER_API_KEY=your_openrouter_key

# Database
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Vector Database
PINECONE_API_KEY=your_pinecone_key

# Firebase
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_PRIVATE_KEY_ID=your_private_key_id
FIREBASE_PRIVATE_KEY=your_private_key
FIREBASE_CLIENT_EMAIL=your_client_email
FIREBASE_CLIENT_ID=your_client_id

# Monitoring
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_PROJECT=multimodal-assistant
LANGSMITH_TRACING=true

# Google Drive
GOOGLE_DRIVE_TOKEN=your_drive_token

# Server
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development
DEBUG=true
```

### 🎛️ Model Configuration:
- **Groq Models**: llama3-70b-8192, llama3-8b-8192, gemma2-9b-it
- **Gemini Models**: gemini-1.5-flash, gemini-1.5-pro
- **OpenRouter Models**: Various free and paid models

---

## 🇺🇸 CONFIGURATION

### 🔑 Environment Variables:
```bash
# AI Model APIs
GROQ_API_KEY=your_groq_key
GEMINI_API_KEY=your_gemini_key
OPENROUTER_API_KEY=your_openrouter_key

# Database
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Vector Database
PINECONE_API_KEY=your_pinecone_key

# Firebase
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_PRIVATE_KEY_ID=your_private_key_id
FIREBASE_PRIVATE_KEY=your_private_key
FIREBASE_CLIENT_EMAIL=your_client_email
FIREBASE_CLIENT_ID=your_client_id

# Monitoring
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_PROJECT=multimodal-assistant
LANGSMITH_TRACING=true

# Google Drive
GOOGLE_DRIVE_TOKEN=your_drive_token

# Server
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development
DEBUG=true
```

### 🎛️ Model Configuration:
- **Groq Models**: llama3-70b-8192, llama3-8b-8192, gemma2-9b-it
- **Gemini Models**: gemini-1.5-flash, gemini-1.5-pro
- **OpenRouter Models**: Various free and paid models

---

## 🇮🇩 FITUR UTAMA

### 🤖 AI Chat System
- **General Chat**: Percakapan umum dengan AI
- **Code Assistant**: Bantuan coding dan debugging
- **RAG System**: Retrieval-Augmented Generation untuk dokumen

### 📄 Document Processing
- **PDF Processing**: Upload dan analisis PDF
- **OCR**: Optical Character Recognition
- **Text Extraction**: Ekstraksi teks dari dokumen
- **Vector Storage**: Penyimpanan vektor di Pinecone

### 🔐 Authentication & Security
- **Firebase Auth**: Autentikasi yang aman
- **JWT Tokens**: Token-based authentication
- **Rate Limiting**: Pembatasan request
- **IP Blocking**: Pemblokiran IP berbahaya

### 💰 Cost Management
- **Usage Tracking**: Pelacakan penggunaan AI
- **Cost Calculation**: Perhitungan biaya per request
- **Budget Limits**: Pembatasan anggaran
- **Billing Reports**: Laporan billing

### 🔗 Integrations
- **Google Drive**: Integrasi dengan Google Drive
- **Webhooks**: Integrasi dengan sistem eksternal
- **LangSmith**: Monitoring dan tracing

### ⚡ Performance
- **Caching**: IronCache untuk optimasi
- **Async Processing**: Pemrosesan asynchronous
- **Load Balancing**: Distribusi beban
- **Monitoring**: Monitoring performa real-time

---

## 🇺🇸 CORE FEATURES

### 🤖 AI Chat System
- **General Chat**: General conversations with AI
- **Code Assistant**: Coding help and debugging
- **RAG System**: Retrieval-Augmented Generation for documents

### 📄 Document Processing
- **PDF Processing**: PDF upload and analysis
- **OCR**: Optical Character Recognition
- **Text Extraction**: Text extraction from documents
- **Vector Storage**: Vector storage in Pinecone

### 🔐 Authentication & Security
- **Firebase Auth**: Secure authentication
- **JWT Tokens**: Token-based authentication
- **Rate Limiting**: Request rate limiting
- **IP Blocking**: Blocking malicious IPs

### 💰 Cost Management
- **Usage Tracking**: AI usage tracking
- **Cost Calculation**: Cost calculation per request
- **Budget Limits**: Budget limitations
- **Billing Reports**: Billing reports

### 🔗 Integrations
- **Google Drive**: Google Drive integration
- **Webhooks**: External system integration
- **LangSmith**: Monitoring and tracing

### ⚡ Performance
- **Caching**: IronCache for optimization
- **Async Processing**: Asynchronous processing
- **Load Balancing**: Load distribution
- **Monitoring**: Real-time performance monitoring

---

## 🇮🇩 TESTING

### 🧪 Test Files:
- **`test_api_integration.py`**: Integration tests untuk API
- **`test_backup.py`**: Tests untuk backup functionality
- **`test_crypto_utils.py`**: Tests untuk cryptographic utilities
- **`test_query_expansion.py`**: Tests untuk query expansion

### 🎯 Test Coverage:
- API endpoints
- Database operations
- Authentication flows
- Error handling
- Performance testing

---

## 🇺🇸 TESTING

### 🧪 Test Files:
- **`test_api_integration.py`**: API integration tests
- **`test_backup.py`**: Backup functionality tests
- **`test_crypto_utils.py`**: Cryptographic utilities tests
- **`test_query_expansion.py`**: Query expansion tests

### 🎯 Test Coverage:
- API endpoints
- Database operations
- Authentication flows
- Error handling
- Performance testing

---

## 🇮🇩 MONITORING & LOGGING

### 📊 Monitoring:
- **LangSmith**: AI model tracing dan monitoring
- **Custom Logging**: Logging kustom untuk debugging
- **Performance Metrics**: Metrik performa real-time
- **Error Tracking**: Pelacakan error dan exception

### 📝 Logging:
- **Structured Logging**: Logging terstruktur
- **Log Levels**: Different log levels (INFO, WARNING, ERROR)
- **Log Rotation**: Rotasi log otomatis
- **Centralized Logging**: Logging terpusat

---

## 🇺🇸 MONITORING & LOGGING

### 📊 Monitoring:
- **LangSmith**: AI model tracing and monitoring
- **Custom Logging**: Custom logging for debugging
- **Performance Metrics**: Real-time performance metrics
- **Error Tracking**: Error and exception tracking

### 📝 Logging:
- **Structured Logging**: Structured logging
- **Log Levels**: Different log levels (INFO, WARNING, ERROR)
- **Log Rotation**: Automatic log rotation
- **Centralized Logging**: Centralized logging

---

## 🇮🇩 DEPLOYMENT

### 🚀 Quick Start:
```bash
# Clone repository
git clone <repository-url>
cd backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Run database migrations
# Execute complete_schema.sql in your database

# Start the server
python main.py
```

### 🐳 Docker Deployment:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "main.py"]
```

### ☁️ Cloud Deployment:
- **Heroku**: Ready for Heroku deployment
- **AWS**: Compatible with AWS services
- **Google Cloud**: GCP deployment support
- **Azure**: Azure deployment ready

---

## 🇺🇸 DEPLOYMENT

### 🚀 Quick Start:
```bash
# Clone repository
git clone <repository-url>
cd backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Run database migrations
# Execute complete_schema.sql in your database

# Start the server
python main.py
```

### 🐳 Docker Deployment:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "main.py"]
```

### ☁️ Cloud Deployment:
- **Heroku**: Ready for Heroku deployment
- **AWS**: Compatible with AWS services
- **Google Cloud**: GCP deployment support
- **Azure**: Azure deployment ready

---

## 📞 SUPPORT & CONTRIBUTION

### 🤝 Contributing:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### 📧 Support:
- **Email**: support@multimodal-assistant.com
- **Documentation**: /docs
- **API Docs**: /docs (Swagger UI)
- **Issues**: GitHub Issues

---

## 📄 LICENSE

This project is licensed under the MIT License - see the LICENSE file for details.

---

*Dokumentasi ini dibuat untuk Multimodal Assistant Backend v2.0.0*
*This documentation is created for Multimodal Assistant Backend v2.0.0* 