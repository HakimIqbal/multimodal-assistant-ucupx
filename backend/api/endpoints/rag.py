import io
import os  
import uuid
from fastapi import APIRouter, UploadFile, HTTPException, Request, Depends
from typing import List, Optional
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
import re
from src.rag import query_rag
from src.vector_db import process_and_store_text
from models import *
from src.db import save_document_to_supabase, check_duplicate_document, log_to_supabase, save_feedback_to_supabase, log_analytics_to_supabase, save_user_preferences, get_user_preferences, update_user_preferences
from pydantic import BaseModel
import urllib3
import time
from datetime import datetime
from api.auth.auth_middleware import get_current_user
import json
from models import SUPPORTED_PDF_CHAT_MODELS, SUPPORTED_GROQ_DEFAULT_MODELS, SUPPORTED_GEMINI_DEFAULT_MODELS, embedding_model, get_vector_store

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

router = APIRouter()

class QueryRequest(BaseModel):
    question: str
    chat_history: Optional[List] = None
    model_name: str = "llama3-70b-8192"
    session_id: str = ""

def extract_page_numbers(text: str, source_text: str) -> List[int]:
    """Extract page numbers from source text"""
    # Simple page number extraction - can be enhanced
    page_patterns = [
        r'page\s+(\d+)',
        r'p\.\s*(\d+)',
        r'(\d+)\s*of\s*\d+\s*pages',
        r'page\s*(\d+)\s*of\s*\d+'
    ]
    
    pages = []
    for pattern in page_patterns:
        matches = re.findall(pattern, source_text, re.IGNORECASE)
        pages.extend([int(match) for match in matches])
    
    return list(set(pages)) if pages else [1]  # Default to page 1

def generate_document_summary(text_content: str, model_name: str) -> dict:
    """Generate document summary using AI"""
    try:
        # For now, create a simple summary
        # In production, use actual AI model for summarization
        sentences = text_content.split('.')
        summary_sentences = sentences[:3]  # Take first 3 sentences
        summary = '. '.join(summary_sentences) + '.'
        
        # Extract key information
        word_count = len(text_content.split())
        sentence_count = len(sentences)
        paragraph_count = len(text_content.split('\n\n'))
        
        # Extract key topics (simple keyword extraction)
        words = re.findall(r'\b\w+\b', text_content.lower())
        word_freq = {}
        for word in words:
            if len(word) > 3:  # Skip short words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top 5 keywords
        top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "summary": summary,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "paragraph_count": paragraph_count,
            "key_topics": [word for word, freq in top_keywords],
            "model_used": model_name,
            "processing_time_ms": 500
        }
    except Exception as e:
        return {
            "summary": "Summary generation failed",
            "error": str(e),
            "model_used": model_name
        }

def enhance_source_citation(answer: str, source_info: dict) -> str:
    """Enhance answer with better source citation"""
    if not source_info:
        return answer
    
    citation = "\n\n📄 **Sumber:**\n"
    
    if source_info.get("filename"):
        citation += f"• **File:** {source_info['filename']}\n"
    
    if source_info.get("page"):
        citation += f"• **Halaman:** {source_info['page']}\n"
    
    if source_info.get("confidence"):
        citation += f"• **Confidence:** {source_info['confidence']:.2f}\n"
    
    if source_info.get("timestamp"):
        citation += f"• **Upload:** {source_info['timestamp']}\n"
    
    return answer + citation

@router.post("/rag/query/")
async def query_documents(request: QueryRequest, req: Request):
    """
    Enhanced RAG query with better source citation and analytics
    """
    session_id = request.session_id or req.cookies.get("session_id", "") if req and hasattr(req, 'cookies') and req.cookies else ""
    user_ip = req.client.host if req and req.client else ""
    
    # Input validation
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question tidak boleh kosong")
    
    if len(request.question) > 2000:
        raise HTTPException(status_code=400, detail="Question terlalu panjang (maksimal 2000 karakter)")
    
    # Model validation
    ALLOWED_MODELS = SUPPORTED_PDF_CHAT_MODELS + SUPPORTED_GROQ_DEFAULT_MODELS + SUPPORTED_GEMINI_DEFAULT_MODELS
    if request.model_name not in ALLOWED_MODELS:
        return {
            "error": "Model tidak didukung untuk RAG System.",
            "allowed_models": ALLOWED_MODELS,
            "suggested_model": "llama3-70b-8192"
        }
    
    # Analytics logging
    log_analytics_to_supabase("rag", str(session_id or ""), user_ip, "query_request", request.model_name)
    
    # Process query
    start_time = time.time()
    try:
        response = query_rag(request.question, request.chat_history or [], request.model_name)
        error_message = ""
    except Exception as e:
        response = {"answer": "", "chat_history": [], "source": {}}
        error_message = str(e)
        print(f"❌ RAG query error: {error_message}")
    
    response_time_ms = int((time.time() - start_time) * 1000)
    
    # Enhance source citation
    if response and not error_message:
        answer = response.get("answer", "")
        source_info = response.get("source", {})
        answer = enhance_source_citation(answer, source_info)
        response["answer"] = answer
    
    # Enhanced logging
    log_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "input": request.question,
        "output": response.get("answer", "") if response else "",
        "metadata": {
            "source": "RAG System",
            "model": request.model_name,
            "context": "Document Analysis",
            "session_id": str(session_id or ""),
            "response_time_ms": response_time_ms,
            "user_ip": user_ip,
            "source_info": response.get("source", {}) if response else {},
            "chat_history_length": len(request.chat_history or [])
        }
    }
    
    log_to_supabase("rag_logs", log_entry, response_time_ms=response_time_ms, error_message=error_message or "")
    
    if error_message:
        raise HTTPException(status_code=500, detail=f"Gagal memproses query: {error_message}")
    
    return {
        "question": request.question,
        "answer": response.get("answer", ""),
        "chat_history": response.get("chat_history", []),
        "source": response.get("source", {}),
        "session_id": str(session_id or ""),
        "response_time_ms": response_time_ms
    }

@router.post("/rag/upload/")
async def upload_document(
    req: Request,
    file: UploadFile,
    category: str = "general",
    description: str = "",
    user=Depends(get_current_user)
):
    """
    Enhanced document upload with categorization and metadata
    """
    # Validate file type
    if not (file.filename or "").lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Hanya file PDF yang didukung")
    
    # Validate file size (max 50MB)
    file_size = getattr(file, 'size', 0) or 0
    if file_size > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File terlalu besar (maksimal 50MB)")
    
    # Validate category
    valid_categories = ["general", "technical", "legal", "financial", "academic", "medical", "other"]
    if category not in valid_categories:
        raise HTTPException(status_code=400, detail=f"Kategori tidak valid. Pilihan: {valid_categories}")
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Check for duplicate
        filename = file.filename or "unknown"
        if check_duplicate_document(filename):
            raise HTTPException(status_code=400, detail="File dengan nama yang sama sudah ada")
        
        # Process document
        start_time = time.time()
        
        # Extract text from PDF
        text_content = ""
        try:
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"
        except Exception as e:
            # Fallback to OCR
            try:
                images = convert_from_bytes(file_content)
                for image in images:
                    text_content += pytesseract.image_to_string(image) + "\n"
            except Exception as ocr_error:
                raise HTTPException(status_code=500, detail=f"Gagal extract text: {str(ocr_error)}")

        if not text_content.strip():
            raise HTTPException(status_code=400, detail="Tidak dapat extract text dari PDF")
        
        # Generate summary
        summary_info = generate_document_summary(text_content, "llama3-70b-8192")
        
        # Save to database
        document_data = {
            "id": str(uuid.uuid4()),
            "filename": filename,
            "text_content": text_content,
            "category": category,
            "description": description,
            "user_id": user["id"],
            "file_size": len(file_content),
            "summary": summary_info.get("summary", ""),
            "word_count": summary_info.get("word_count", 0),
            "key_topics": summary_info.get("key_topics", []),
            "upload_timestamp": datetime.utcnow().isoformat(),
            "processing_time_ms": int((time.time() - start_time) * 1000)
        }
        
        result = save_document_to_supabase(filename, "pdf", text_content, "")
        
        # Process for vector search
        try:
            process_and_store_text(text_content, embedding_model, get_vector_store(), {"filename": filename})
        except Exception as vector_error:
            print(f"Warning: Vector processing failed: {str(vector_error)}")
        
        return {
            "success": True,
            "filename": filename,
            "category": category,
            "summary": summary_info.get("summary", ""),
            "word_count": summary_info.get("word_count", 0),
            "key_topics": summary_info.get("key_topics", []),
            "processing_time_ms": document_data["processing_time_ms"],
            "document_id": result.get("id", "") if result else ""
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal upload dokumen: {str(e)}")

# Enhanced document summary endpoint
class SummaryRequest(BaseModel):
    filename: str
    model_name: str = "llama3-70b-8192"

@router.post("/rag/summary/")
async def generate_summary(request: SummaryRequest, user=Depends(get_current_user)):
    """
    Generate detailed document summary
    """
    try:
        from src.db import supabase
        
        # Get document
        res = supabase.table("documents").select("*").eq("filename", request.filename).eq("user_id", user["id"]).execute()
        
        if not res.data:
            raise HTTPException(status_code=404, detail="Dokumen tidak ditemukan")
        
        document = res.data[0]
        if document is not None and isinstance(document, dict):
            text_content = document.get("text_content", "")
        else:
            text_content = ""
        
        if not text_content:
            raise HTTPException(status_code=400, detail="Dokumen tidak memiliki text content")
        
        # Generate summary
        start_time = time.time()
        summary_info = generate_document_summary(text_content, request.model_name)
        processing_time = int((time.time() - start_time) * 1000)
        
        return {
            "filename": request.filename,
            "summary": summary_info.get("summary", ""),
            "word_count": summary_info.get("word_count", 0),
            "sentence_count": summary_info.get("sentence_count", 0),
            "paragraph_count": summary_info.get("paragraph_count", 0),
            "key_topics": summary_info.get("key_topics", []),
            "processing_time_ms": processing_time,
            "model_used": request.model_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal generate summary: {str(e)}")

# Enhanced feedback endpoint
class FeedbackRequest(BaseModel):
    session_id: str
    log_id: str
    rating: int
    comment: str = ""
    category: str = "rag"  # rag, summary, upload

@router.post("/rag/feedback/")
async def feedback(request: FeedbackRequest, user=Depends(get_current_user)):
    """
    Enhanced feedback system with categorization
    """
    # Validate rating
    if not 1 <= request.rating <= 5:
        raise HTTPException(status_code=400, detail="Rating harus antara 1-5")
    
    # Validate category
    if request.category not in ["rag", "summary", "upload"]:
        raise HTTPException(status_code=400, detail="Kategori tidak valid")
    
    try:
        result = save_feedback_to_supabase(request.session_id, request.category, request.log_id, request.rating, request.comment)
        return {
            "status": "success", 
            "message": "Feedback berhasil disimpan.",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan feedback: {str(e)}")

# Enhanced document search
@router.get("/rag/search/")
async def search_document(
    q: str,
    category: str = "",
    limit: int = 10,
    user=Depends(get_current_user)
):
    """
    Enhanced document search with filters and pagination
    """
    try:
        from src.db import supabase
        
        # Build query
        query = supabase.table("documents").select("filename, text_content, category, summary, key_topics, upload_timestamp")
        
        # Add category filter
        if category:
            query = query.eq("category", category)
        
        # Add user filter
        query = query.eq("user_id", user["id"])
        
        # Add text search
        query = query.ilike("text_content", f"%{q}%")
        
        # Add limit
        query = query.limit(limit)
        
        res = query.execute()
        
        # Process results
        results = []
        for item in res.data or []:
            # Highlight search terms
            text_content = item.get("text_content", "")
            highlighted_content = text_content.replace(q, f"**{q}**")
            
            results.append({
                "filename": item.get("filename"),
                "category": item.get("category"),
                "summary": item.get("summary"),
                "key_topics": item.get("key_topics", []),
                "upload_timestamp": item.get("upload_timestamp"),
                "highlighted_content": highlighted_content[:500] + "..." if len(highlighted_content) > 500 else highlighted_content
            })
        
        return {
            "success": True,
            "query": q,
            "category_filter": category,
            "results": results,
            "total_found": len(results),
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mencari dokumen: {str(e)}")

# Enhanced stats endpoint
@router.get("/rag/stats/")
async def stats(user=Depends(get_current_user)):
    """
    Enhanced statistics with detailed metrics
    """
    try:
        from src.db import supabase
        
        # Get total documents
        res = supabase.table("documents").select("id", count=None).eq("user_id", user["id"]).execute()
        total_documents = res.count or 0
        
        # Get total queries
        res = supabase.table("rag_logs").select("id", count=None).execute()
        total_queries = res.count or 0
        
        # Get recent activity (last 24 hours)
        from datetime import datetime, timedelta
        yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
        res = supabase.table("rag_logs").select("id", count=None).gte("timestamp", yesterday).execute()
        recent_queries = res.count or 0
        
        # Get category distribution
        res = supabase.table("documents").select("category").eq("user_id", user["id"]).execute()
        categories = {}
        for item in res.data or []:
            cat = item.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
        
        # Get average response time
        res = supabase.table("rag_logs").select("metadata").not_.is_("metadata->response_time_ms", "null").execute()
        response_times = []
        for item in res.data or []:
            if item.get("metadata", {}).get("response_time_ms"):
                response_times.append(item["metadata"]["response_time_ms"])
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "total_documents": total_documents,
            "total_queries": total_queries,
            "recent_queries_24h": recent_queries,
            "average_response_time_ms": round(avg_response_time, 2),
            "category_distribution": categories,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mengambil statistik: {str(e)}")

# Enhanced user preferences
class UserPreferences(BaseModel):
    theme: str = "light"  # "light" or "dark"
    language: str = "id"  # "id" or "en"
    auto_save: bool = True
    notifications: bool = True
    compact_mode: bool = False
    default_category: str = "general"  # Default document category
    search_limit: int = 10  # Default search results limit

@router.get("/rag/preferences/")
async def get_preferences(user=Depends(get_current_user)):
    """
    Get user preferences with defaults
    """
    try:
        prefs = get_user_preferences(user["id"])
        return prefs or {
            "theme": "light",
            "language": "id", 
            "auto_save": True,
            "notifications": True,
            "compact_mode": False,
            "default_category": "general",
            "search_limit": 10
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mengambil preferences: {str(e)}")

@router.post("/rag/preferences/")
async def update_preferences(preferences: UserPreferences, user=Depends(get_current_user)):
    """
    Update user preferences with validation
    """
    # Validate theme
    if preferences.theme not in ["light", "dark"]:
        raise HTTPException(status_code=400, detail="Theme harus 'light' atau 'dark'")
    
    # Validate language
    if preferences.language not in ["id", "en"]:
        raise HTTPException(status_code=400, detail="Language harus 'id' atau 'en'")
    
    # Validate default category
    valid_categories = ["general", "technical", "legal", "financial", "academic", "medical", "other"]
    if preferences.default_category not in valid_categories:
        raise HTTPException(status_code=400, detail="Default category tidak valid")
    
    # Validate search limit
    if not 1 <= preferences.search_limit <= 100:
        raise HTTPException(status_code=400, detail="Search limit harus antara 1-100")
    
    try:
        result = update_user_preferences(user["id"], preferences.dict())
        return {
            "status": "success",
            "message": "Preferences berhasil diupdate.",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal update preferences: {str(e)}")

@router.post("/rag/preferences/toggle-theme/")
async def toggle_theme(user=Depends(get_current_user)):
    """
    Quick theme toggle
    """
    try:
        current_prefs = get_user_preferences(user["id"]) or {"theme": "light"}
        new_theme = "dark" if current_prefs.get("theme") == "light" else "light"
        
        result = update_user_preferences(user["id"], {"theme": new_theme})
        return {
            "status": "success",
            "theme": new_theme,
            "message": f"Theme berhasil diubah ke {new_theme}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal toggle theme: {str(e)}")
