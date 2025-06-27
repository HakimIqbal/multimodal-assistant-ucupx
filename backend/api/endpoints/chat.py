from fastapi import APIRouter, Request, HTTPException, Query, Body
from pydantic import BaseModel
from src.chat import chat_general
from models import SUPPORTED_GENERAL_CHAT_MODELS, SUPPORTED_GROQ_DEFAULT_MODELS, SUPPORTED_GEMINI_DEFAULT_MODELS
from src.db import log_to_supabase, save_feedback_to_supabase, check_rate_limit, log_analytics_to_supabase, save_user_preferences, get_user_preferences, update_user_preferences, supabase
import time
import uuid
from datetime import datetime
from api.auth.auth_middleware import get_current_user
from fastapi import Depends
import re
from typing import List, Dict, Any, Optional

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    model_name: str = "llama3-70b-8192"
    session_id: str = ""

def detect_intent(query: str) -> dict:
    """Enhanced intent detection for better user experience"""
    query_lower = query.lower()
    
    # Coding intent detection
    coding_keywords = [
        "code", "python", "function", "bug", "error", "debug", "class", "variable", 
        "loop", "array", "list", "dict", "compile", "syntax", "logic", "algoritma", 
        "algoritme", "programming", "pemrograman", "coding", "developer", "script",
        "api", "database", "sql", "javascript", "html", "css", "react", "node",
        "git", "deploy", "server", "client", "frontend", "backend"
    ]
    
    # Document/RAG intent detection
    doc_keywords = [
        "pdf", "dokumen", "document", "file", "rag", "extract", "ringkas", 
        "summary", "upload", "read", "analyze", "content", "text", "page",
        "chapter", "section", "paragraph", "sentence", "word"
    ]
    
    coding_score = sum(1 for keyword in coding_keywords if keyword in query_lower)
    doc_score = sum(1 for keyword in doc_keywords if keyword in query_lower)
    
    intent = "general"
    confidence = 0.5
    
    if coding_score > doc_score and coding_score >= 2:
        intent = "coding"
        confidence = min(0.9, coding_score / len(coding_keywords))
    elif doc_score > coding_score and doc_score >= 2:
        intent = "document"
        confidence = min(0.9, doc_score / len(doc_keywords))
    
    return {
        "intent": intent,
        "confidence": confidence,
        "coding_score": coding_score,
        "doc_score": doc_score
    }

def format_response(response: str, intent: dict) -> str:
    """Format response with intent-based suggestions"""
    if intent["intent"] == "coding" and intent["confidence"] > 0.7:
        suggestion = "\n\n💡 **Saran:** Pertanyaan Anda terdeteksi sebagai coding. Untuk jawaban yang lebih spesifik dan detail, gunakan fitur **Coder Chat**."
        return response + suggestion
    elif intent["intent"] == "document" and intent["confidence"] > 0.7:
        suggestion = "\n\n💡 **Saran:** Pertanyaan Anda terdeteksi terkait dokumen. Untuk analisis dokumen yang lebih mendalam, gunakan fitur **RAG System**."
        return response + suggestion
    
    return response

@router.post("/general/")
async def chat(request: ChatRequest, req: Request):
    """
    Enhanced General Chat with intent detection and better error handling
    """
    session_id = request.session_id or req.cookies.get("session_id", "") if req and hasattr(req, 'cookies') and req.cookies else ""
    user_ip = req.client.host if req and req.client else ""
    session_id_str = str(session_id or "")
    
    # Input validation
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query tidak boleh kosong")
    
    if len(request.query) > 2000:
        raise HTTPException(status_code=400, detail="Query terlalu panjang (maksimal 2000 karakter)")
    
    # Rate limiting
    if not check_rate_limit("general", session_id_str, user_ip, max_per_minute=10):
        raise HTTPException(status_code=429, detail="Terlalu banyak request. Silakan tunggu sebentar sebelum mencoba lagi.")
    
    # Intent detection
    intent = detect_intent(request.query)
    
    # Model validation with detailed error message
    ALLOWED_MODELS = SUPPORTED_GENERAL_CHAT_MODELS + SUPPORTED_GROQ_DEFAULT_MODELS + SUPPORTED_GEMINI_DEFAULT_MODELS
    if request.model_name not in ALLOWED_MODELS:
        return {
            "error": "Model tidak didukung untuk General Chat.",
            "allowed_models": ALLOWED_MODELS,
            "suggested_model": "llama3-70b-8192"
        }
    
    # Analytics logging
    log_analytics_to_supabase("general", session_id_str, user_ip, "chat_request", request.model_name)
    
    # Contextual memory per session
    start_time = time.time()
    try:
        response = chat_general(request.query, request.model_name, session_id=session_id_str)
        error_message = ""
    except Exception as e:
        response = ""
        error_message = str(e)
        print(f"❌ Chat error: {error_message}")
    
    response_time_ms = int((time.time() - start_time) * 1000)
    
    # Format response with intent-based suggestions
    if response and not error_message:
        response = format_response(response, intent)
    
    # Enhanced logging
    log_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "input": request.query,
        "output": response or "",
        "metadata": {
            "source": "General Chatbot",
            "model": request.model_name,
            "context": "General",
            "language": "id" if any(word in request.query.lower() for word in ["apa", "bagaimana", "siapa", "dimana", "kapan", "mengapa"]) else "en",
            "session_id": session_id_str,
            "intent": intent,
            "response_time_ms": response_time_ms,
            "user_ip": user_ip
        }
    }
    
    log_to_supabase("general_logs", log_entry, response_time_ms=response_time_ms, error_message=error_message or "")
    
    if error_message:
        raise HTTPException(status_code=500, detail=f"Gagal memproses chat: {error_message}")
    
    return {
        "query": request.query, 
        "response": response, 
        "model": request.model_name, 
        "session_id": session_id_str,
        "intent": intent,
        "response_time_ms": response_time_ms
    }

# Enhanced feedback endpoint
class FeedbackRequest(BaseModel):
    session_id: str
    log_id: str
    rating: int
    comment: str = ""
    category: str = "general"  # general, coding, document

@router.post("/general/feedback/")
async def feedback(request: FeedbackRequest, user=Depends(get_current_user)):
    """
    Enhanced feedback system with categorization
    """
    # Validate rating
    if not 1 <= request.rating <= 5:
        raise HTTPException(status_code=400, detail="Rating harus antara 1-5")
    
    # Validate category
    if request.category not in ["general", "coding", "document"]:
        raise HTTPException(status_code=400, detail="Kategori tidak valid")
    
    try:
        result = save_feedback_to_supabase(
            request.session_id, 
            "general", 
            request.log_id, 
            request.rating, 
            request.comment
        )
        return {
            "status": "success", 
            "message": "Feedback berhasil disimpan.",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan feedback: {str(e)}")

# Enhanced stats endpoint
@router.get("/general/stats/")
async def stats():
    """
    Enhanced statistics with detailed metrics
    """
    try:
        # Get total chats
        res = supabase.table("general_logs").select("id").execute()
        total_chats = len(res.data) if res.data else 0
        
        # Get recent activity (last 24 hours)
        from datetime import datetime, timedelta
        yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
        res = supabase.table("general_logs").select("id").gte("timestamp", yesterday).execute()
        recent_chats = len(res.data) if res.data else 0
        
        # Get average response time
        res = supabase.table("general_logs").select("metadata").not_.is_("metadata->response_time_ms", "null").execute()
        response_times = []
        for item in res.data or []:
            if item.get("metadata", {}).get("response_time_ms"):
                response_times.append(item["metadata"]["response_time_ms"])
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "total_general_chat": total_chats,
            "recent_chats_24h": recent_chats,
            "average_response_time_ms": round(avg_response_time, 2),
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
    preferred_model: str = "llama3-70b-8192"

@router.get("/general/preferences/")
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
            "preferred_model": "llama3-70b-8192"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mengambil preferences: {str(e)}")

@router.post("/general/preferences/")
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
    
    # Validate preferred model
    ALLOWED_MODELS = SUPPORTED_GENERAL_CHAT_MODELS + SUPPORTED_GROQ_DEFAULT_MODELS + SUPPORTED_GEMINI_DEFAULT_MODELS
    if preferences.preferred_model not in ALLOWED_MODELS:
        raise HTTPException(status_code=400, detail="Model tidak didukung")
    
    try:
        result = update_user_preferences(user["id"], preferences.dict())
        return {
            "status": "success",
            "message": "Preferences berhasil diupdate.",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal update preferences: {str(e)}")

@router.post("/general/preferences/toggle-theme/")
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

@router.post("/compare/")
async def compare_models(query: str = Body(...), model_names: list = Body(...)):
    results = {}
    for model in model_names:
        try:
            results[model] = chat_general(query, model)
        except Exception as e:
            results[model] = f"Error: {str(e)}"
    return {"success": True, "results": results}

@router.post("/prompts/save")
async def save_prompt(prompt_name: str = Body(...), prompt_text: str = Body(...), user=Depends(get_current_user)):
    try:
        supabase.table("custom_prompts").insert({"user_id": user["id"], "name": prompt_name, "text": prompt_text}).execute()
        return {"success": True, "message": "Prompt saved"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.get("/prompts/list")
async def list_prompts(user=Depends(get_current_user)):
    try:
        res = supabase.table("custom_prompts").select("name", "text").eq("user_id", user["id"]).execute()
        return {"success": True, "prompts": res.data or []}
    except Exception as e:
        return {"success": False, "message": str(e), "prompts": []}

@router.delete("/prompts/delete")
async def delete_prompt(prompt_name: str = Body(...), user=Depends(get_current_user)):
    try:
        supabase.table("custom_prompts").delete().eq("user_id", user["id"]).eq("name", prompt_name).execute()
        return {"success": True, "message": "Prompt deleted"}
    except Exception as e:
        return {"success": False, "message": str(e)}