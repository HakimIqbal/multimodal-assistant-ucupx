from fastapi import APIRouter, Request, Query, Body, Depends, HTTPException
from pydantic import BaseModel
from src.coder import chat_coder
from models import *
from src.db import log_to_supabase, save_feedback_to_supabase, save_snippet_to_supabase, search_snippet_in_supabase, log_analytics_to_supabase, save_user_preferences, get_user_preferences, update_user_preferences
import time
import uuid
from datetime import datetime
import subprocess
import re
from api.auth.auth_middleware import get_current_user, require_role
from typing import List, Dict, Any, Optional
import tempfile
import logging
from models import SUPPORTED_CODER_CHAT_MODELS, SUPPORTED_GROQ_DEFAULT_MODELS, SUPPORTED_GEMINI_DEFAULT_MODELS, get_groq_model

router = APIRouter()

class CoderRequest(BaseModel):
    query: str
    model_name: str = "llama3-70b-8192"
    session_id: str = ""

def detect_programming_language(query: str) -> dict:
    """Detect programming language from query"""
    query_lower = query.lower()
    
    language_keywords = {
        "python": ["python", "py", "pip", "django", "flask", "pandas", "numpy", "matplotlib"],
        "javascript": ["javascript", "js", "node", "react", "vue", "angular", "npm", "yarn"],
        "java": ["java", "spring", "maven", "gradle", "jvm"],
        "cpp": ["c++", "cpp", "stl", "boost", "cmake"],
        "csharp": ["c#", "csharp", "dotnet", "asp.net", "linq"],
        "php": ["php", "laravel", "composer", "wordpress"],
        "go": ["golang", "go", "goroutine", "gin"],
        "rust": ["rust", "cargo", "crate"],
        "swift": ["swift", "ios", "xcode", "cocoa"],
        "kotlin": ["kotlin", "android", "gradle"],
        "typescript": ["typescript", "ts", "interface", "type"],
        "sql": ["sql", "mysql", "postgresql", "database", "query"],
        "html": ["html", "css", "web", "frontend"],
        "bash": ["bash", "shell", "script", "linux", "unix"]
    }
    
    detected_languages = {}
    for lang, keywords in language_keywords.items():
        score = sum(1 for keyword in keywords if keyword in query_lower)
        if score > 0:
            detected_languages[lang] = score
    
    # Sort by score
    sorted_languages = sorted(detected_languages.items(), key=lambda x: x[1], reverse=True)
    
    return {
        "primary_language": sorted_languages[0][0] if sorted_languages else "general",
        "confidence": sorted_languages[0][1] / max(len(keywords) for keywords in language_keywords.values()) if sorted_languages else 0,
        "all_detected": detected_languages
    }

def detect_error_log(query: str) -> dict:
    """Detect if query contains error logs"""
    error_patterns = [
        r"error:", r"exception:", r"traceback:", r"stack trace:",
        r"failed:", r"failure:", r"crash:", r"segmentation fault",
        r"typeerror:", r"valueerror:", r"keyerror:", r"indexerror:",
        r"filenotfounderror:", r"permissionerror:", r"timeouterror:",
        r"connectionerror:", r"httperror:", r"jsondecodeerror:",
        r"error \d+:", r"exception \d+:", r"fatal error",
        r"panic:", r"assertion failed", r"null pointer exception"
    ]
    
    query_lower = query.lower()
    detected_errors = []
    
    for pattern in error_patterns:
        if re.search(pattern, query_lower):
            detected_errors.append(pattern.replace(":", "").replace("_", " ").title())
    
    return {
        "is_error_log": len(detected_errors) > 0,
        "error_types": detected_errors,
        "confidence": min(0.9, len(detected_errors) * 0.3)
    }

def format_code_response(response: str, language: str) -> str:
    """Format code response with proper markdown"""
    # Ensure code blocks are properly formatted
    if "```" not in response and ("def " in response or "function " in response or "class " in response):
        # Add code block if missing
        response = f"```{language}\n{response}\n```"
    
    # Add language hints if missing
    response = re.sub(r'```\n', f'```{language}\n', response)
    
    # Add explanation header if it's a code solution
    if "```" in response and not response.startswith("Here's"):
        response = f"Here's the solution:\n\n{response}"
    
    return response

def enhance_coding_prompt(query: str, language: str, is_error: bool) -> str:
    """Enhance prompt for better coding responses"""
    base_prompt = query
    
    if is_error:
        base_prompt = f"Please analyze this error and provide a detailed explanation with solution:\n\n{query}"
    
    if language != "general":
        base_prompt = f"Please provide a {language} solution for the following:\n\n{query}\n\nPlease include:\n1. Clear explanation\n2. Code example\n3. Best practices\n4. Common pitfalls to avoid"
    
    return base_prompt

@router.post("/coder/")
async def coder_chat(request: CoderRequest, req: Request):
    """
    Enhanced Coder Chat with language detection and error analysis
    """
    session_id = request.session_id or req.cookies.get("session_id", "") if req and hasattr(req, 'cookies') and req.cookies else ""
    user_ip = req.client.host if req and req.client else ""
    
    # Input validation
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query tidak boleh kosong")
    
    if len(request.query) > 3000:
        raise HTTPException(status_code=400, detail="Query terlalu panjang (maksimal 3000 karakter)")
    
    # Language detection
    language_info = detect_programming_language(request.query)
    
    # Error detection
    error_info = detect_error_log(request.query)
    
    # Enhanced prompt
    enhanced_query = enhance_coding_prompt(
        request.query, 
        language_info["primary_language"], 
        error_info["is_error_log"]
    )
    
    # Model validation
    ALLOWED_MODELS = SUPPORTED_CODER_CHAT_MODELS + SUPPORTED_GROQ_DEFAULT_MODELS + SUPPORTED_GEMINI_DEFAULT_MODELS
    if request.model_name not in ALLOWED_MODELS:
        return {
            "error": "Model tidak didukung untuk Coder Chat.",
            "allowed_models": ALLOWED_MODELS,
            "suggested_model": "llama3-70b-8192"
        }
    
    # Analytics logging
    log_analytics_to_supabase("coder", str(session_id or ""), user_ip, "chat_request", request.model_name)
    
    # Process request
    start_time = time.time()
    try:
        response = chat_coder(enhanced_query, request.model_name, session_id=str(session_id or ""))
        error_message = ""
    except Exception as e:
        response = ""
        error_message = str(e)
        print(f"❌ Coder chat error: {error_message}")
    
    response_time_ms = int((time.time() - start_time) * 1000)
    
    # Format response
    if isinstance(response, str):
        response = format_code_response(response, language_info["primary_language"])
    
    # Enhanced logging
    log_entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "input": request.query,
        "output": response,
        "metadata": {
            "source": "Coder Chatbot",
            "model": request.model_name,
            "context": "Coding",
            "language": language_info["primary_language"],
            "language_confidence": language_info["confidence"],
            "is_error_log": error_info["is_error_log"],
            "error_types": error_info["error_types"],
            "session_id": str(session_id or ""),
            "response_time_ms": response_time_ms,
            "user_ip": user_ip
        }
    }
    
    log_to_supabase("coder_logs", log_entry, response_time_ms=response_time_ms, error_message=error_message)
    
    if error_message:
        raise HTTPException(status_code=500, detail=f"Gagal memproses chat: {error_message}")
    
    return {
        "query": request.query, 
        "response": response, 
        "model": request.model_name, 
        "session_id": str(session_id or ""),
        "language_detected": language_info,
        "error_analysis": error_info,
        "response_time_ms": response_time_ms
    }

# Enhanced code execution with better sandboxing
class CodeExecutionRequest(BaseModel):
    code: str
    language: str = "python"
    timeout_seconds: int = 5

@router.post("/coder/exec/")
async def execute_code(request: CodeExecutionRequest, user=Depends(get_current_user)):
    """
    Enhanced code execution with better security and error handling (subprocess sandbox)
    """
    # Validate code length
    if len(request.code) > 5000:
        raise HTTPException(status_code=400, detail="Code terlalu panjang (maksimal 5000 karakter)")
    
    # Security checks
    dangerous_patterns = [
        r"import os", r"import sys", r"import subprocess", r"import socket",
        r"__import__", r"eval\(", r"exec\(", r"open\(", r"file\(",
        r"subprocess\.", r"os\.", r"sys\.", r"globals\(", r"locals\(",
        r"del ", r"rm ", r"rmdir", r"format\(", r"compile\("
    ]
    for pattern in dangerous_patterns:
        if re.search(pattern, request.code, re.IGNORECASE):
            raise HTTPException(
                status_code=400, 
                detail=f"Code contains potentially dangerous operations: {pattern}"
            )
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as temp_code:
            temp_code.write(request.code)
            temp_code_path = temp_code.name
        # Run code in subprocess with resource limits
        cmd = ["python3", temp_code_path]
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=lambda: __import__('resource').setrlimit(__import__('resource').RLIMIT_CPU, (request.timeout_seconds, request.timeout_seconds))
        )
        try:
            stdout, stderr = proc.communicate(timeout=request.timeout_seconds)
        except subprocess.TimeoutExpired:
            proc.kill()
            raise HTTPException(status_code=408, detail="Code execution timeout")
        finally:
            import os
            os.remove(temp_code_path)
        # Limit output size
        stdout = stdout.decode()[:2000]
        stderr = stderr.decode()[:2000]
        # Logging
        logging.basicConfig(filename='coder_exec.log', level=logging.INFO)
        logging.info(f"User: {user['uid']} executed code. Output: {stdout}, Error: {stderr}")
        return {
            "stdout": stdout,
            "stderr": stderr,
            "error": None if proc.returncode == 0 else f"Exited with code {proc.returncode}",
            "exec_time_ms": request.timeout_seconds * 1000,
            "language": request.language
        }
    except Exception as e:
        logging.error(f"Code execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Code execution failed: {str(e)}")

# Enhanced feedback endpoint
class FeedbackRequest(BaseModel):
    session_id: str = ""
    log_id: str = ""
    rating: int = 0
    comment: str = ""
    category: str = "coding"  # coding, error, snippet

@router.post("/coder/feedback/")
async def feedback(request: FeedbackRequest, user=Depends(get_current_user)):
    """
    Enhanced feedback system with categorization
    """
    # Validate rating
    if not 1 <= request.rating <= 5:
        raise HTTPException(status_code=400, detail="Rating harus antara 1-5")
    
    # Validate category
    if request.category not in ["coding", "error", "snippet"]:
        raise HTTPException(status_code=400, detail="Kategori tidak valid")
    
    try:
        result = save_feedback_to_supabase(
            request.session_id, 
            "coder", 
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

# Enhanced snippet library
@router.get("/coder/snippet/")
async def search_snippet(q: str = Query(...), language: str = "", user=Depends(get_current_user)):
    """
    Enhanced snippet search with language filtering
    """
    try:
        result = search_snippet_in_supabase(q, language)
        return {
            "success": True,
            "query": q,
            "language_filter": language,
            "results": result,
            "total_found": len(result) if result is not None else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mencari snippet: {str(e)}")

@router.post("/coder/snippet/")
async def save_snippet(
    language: str = Body(...),
    title: str = Body(...),
    code: str = Body(...),
    tags: List[str] = Body(default=[]),
    description: str = Body(default=""),
    user=Depends(get_current_user)
):
    """
    Enhanced snippet saving with better validation
    """
    # Validate inputs
    if not language or not title or not code:
        raise HTTPException(status_code=400, detail="Language, title, dan code wajib diisi")
    
    if len(code) > 10000:
        raise HTTPException(status_code=400, detail="Code terlalu panjang (maksimal 10000 karakter)")
    
    if len(tags) > 10:
        raise HTTPException(status_code=400, detail="Terlalu banyak tags (maksimal 10)")
    
    try:
        result = save_snippet_to_supabase(language, title, code, tags)
        return {
            "status": "success",
            "message": "Snippet berhasil disimpan.",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan snippet: {str(e)}")

# Enhanced stats endpoint
@router.get("/coder/stats/")
async def stats():
    """
    Enhanced statistics with detailed metrics
    """
    try:
        from src.db import supabase
        
        # Get total chats
        res = supabase.table("coder_logs").select("id").execute()
        total_chats = len(res.data) if res.data else 0
        
        # Get recent activity (last 24 hours)
        from datetime import datetime, timedelta
        yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
        res = supabase.table("coder_logs").select("id").gte("timestamp", yesterday).execute()
        recent_chats = len(res.data) if res.data else 0
        
        # Get language distribution
        res = supabase.table("coder_logs").select("metadata->language").execute()
        languages = {}
        for item in res.data or []:
            lang = item.get("metadata", {}).get("language", "unknown")
            languages[lang] = languages.get(lang, 0) + 1
        
        # Get average response time
        res = supabase.table("coder_logs").select("metadata").not_.is_("metadata->response_time_ms", "null").execute()
        response_times = []
        for item in res.data or []:
            if item.get("metadata", {}).get("response_time_ms"):
                response_times.append(item["metadata"]["response_time_ms"])
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "total_coder_chat": total_chats,
            "recent_chats_24h": recent_chats,
            "average_response_time_ms": round(avg_response_time, 2),
            "language_distribution": languages,
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
    preferred_language: str = "python"  # Default programming language
    code_theme: str = "vs-dark"  # Code editor theme

@router.get("/coder/preferences/")
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
            "preferred_language": "python",
            "code_theme": "vs-dark"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mengambil preferences: {str(e)}")

@router.post("/coder/preferences/")
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
    
    # Validate programming language
    valid_languages = ["python", "javascript", "java", "cpp", "csharp", "php", "go", "rust", "swift", "kotlin", "typescript", "sql", "html", "bash"]
    if preferences.preferred_language not in valid_languages:
        raise HTTPException(status_code=400, detail="Programming language tidak valid")
    
    try:
        result = update_user_preferences(user["id"], preferences.dict())
        return {
            "status": "success",
            "message": "Preferences berhasil diupdate.",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal update preferences: {str(e)}")

@router.post("/coder/preferences/toggle-theme/")
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
