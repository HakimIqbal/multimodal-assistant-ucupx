from supabase import create_client, Client
import os
import uuid
from datetime import datetime
from typing import Optional, List, Dict

# Get Supabase credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def save_document_to_supabase(filename: str, file_type: str, text_content: str, file_url: str = ""):
    data = {
        "filename": filename or "",
        "file_format": file_type or "",
        "text_content": text_content or "",
        "file_url": file_url or "",
        "uploaded_at": datetime.utcnow().isoformat()
    }
    res = supabase.table("documents").insert(data).execute()
    if getattr(res, "error", None):
        print(f"\n[Supabase] Gagal menyimpan dokumen:")
        print(f"  Error   : {getattr(res, 'error', '')}")
        print(f"  Data    : {data}\n")
        raise Exception(getattr(res, 'error', ''))
    print(f"\n[Supabase] Dokumen berhasil disimpan:")
    print(f"  Filename: {filename}")
    print(f"  URL     : {file_url}")
    print(f"  Data    : {getattr(res, 'data', '')}\n")
    return getattr(res, 'data', None)

def save_feedback_to_supabase(session_id: str, feature: str, log_id: str, rating: int, comment: str = ""):
    data = {
        "session_id": session_id or "",
        "feature": feature or "",
        "log_id": log_id or "",
        "rating": int(rating or 0),
        "comment": comment or "",
    }
    data["created_at"] = datetime.utcnow().isoformat()
    res = supabase.table("chat_feedback").insert(data).execute()
    if getattr(res, "error", None):
        print(f"\n[Supabase] Gagal menyimpan feedback:")
        print(f"  Error   : {getattr(res, 'error', '')}")
        print(f"  Data    : {data}\n")
        raise Exception(getattr(res, 'error', ''))
    print(f"\n[Supabase] Feedback berhasil disimpan:")
    print(f"  Feature : {feature}")
    print(f"  Log ID  : {log_id}")
    print(f"  Rating  : {rating}")
    print(f"  Data    : {getattr(res, 'data', '')}\n")
    return getattr(res, 'data', None)

def log_to_supabase(table: str, log_entry: dict, response_time_ms: int = 0, error_message: str = ""):
    data = {
        "id": log_entry["id"],
        "timestamp": log_entry["timestamp"],
        "input": log_entry["input"],
        "output": log_entry["output"],
        "metadata": log_entry["metadata"],
        "response_time_ms": response_time_ms or 0,
        "error_message": error_message or ""
    }
    res = supabase.table(table).insert(data).execute()
    if getattr(res, "error", None):
        print(f"\n[Supabase] Gagal menyimpan log:")
        print(f"  Tabel   : {table}")
        print(f"  Error   : {getattr(res, 'error', '')}")
        print(f"  Data    : {data}\n")
        raise Exception(getattr(res, 'error', ''))
    print(f"\n[Supabase] Log berhasil disimpan:")
    print(f"  Tabel   : {table}")
    print(f"  ID      : {log_entry['id']}")
    print(f"  Input   : {log_entry['input']}")
    print(f"  Output  : {log_entry['output'][:60]}{'...' if len(log_entry['output']) > 60 else ''}")
    print(f"  Metadata: {log_entry['metadata']}")
    print(f"  Response: {response_time_ms} ms")
    print(f"  Error   : {error_message}")
    print(f"  Data    : {getattr(res, 'data', '')}\n")
    return getattr(res, 'data', None)

def check_duplicate_document(filename: str):
    res = supabase.table("documents").select("filename").eq("filename", filename).execute()
    if getattr(res, "error", None):
        print(f"\n[Supabase] Gagal cek duplikat dokumen:")
        print(f"  Filename: {filename}")
        print(f"  Error   : {getattr(res, 'error', '')}\n")
        raise Exception(getattr(res, 'error', ''))
    print(f"\n[Supabase] Cek duplikat dokumen:")
    print(f"  Filename: {filename}")
    print(f"  Result  : {res.data}\n")
    return len(res.data) > 0

def save_snippet_to_supabase(language: str, title: str, code: str, tags: Optional[List] = None):
    tags = tags if tags is not None else []
    data = {
        "language": language or "",
        "title": title or "",
        "code": code or "",
        "tags": tags,
    }
    data["created_at"] = datetime.utcnow().isoformat()
    data["updated_at"] = datetime.utcnow().isoformat()
    res = supabase.table("snippet_library").insert(data).execute()
    if getattr(res, "error", None):
        print(f"\n[Supabase] Gagal menyimpan snippet:")
        print(f"  Error   : {getattr(res, 'error', '')}")
        print(f"  Data    : {data}\n")
        raise Exception(getattr(res, 'error', ''))
    print(f"\n[Supabase] Snippet berhasil disimpan:")
    print(f"  Title   : {title}")
    print(f"  Language: {language}")
    print(f"  Data    : {getattr(res, 'data', '')}\n")
    return getattr(res, 'data', None)

def search_snippet_in_supabase(query: str, language: str = "", tags: Optional[List] = None):
    tags = tags if tags is not None else []
    q = supabase.table("snippet_library").select("id, title, code, language, tags, usage_count")
    if language:
        q = q.eq("language", language)
    if tags:
        for tag in tags:
            q = q.contains("tags", [tag])
    q = q.ilike("title", f"%{query}%")
    res = q.execute()
    if getattr(res, "error", None):
        print(f"\n[Supabase] Gagal mencari snippet:")
        print(f"  Error   : {getattr(res, 'error', '')}")
        print(f"  Query   : {query}\n")
        raise Exception(getattr(res, 'error', ''))
    print(f"\n[Supabase] Hasil pencarian snippet:")
    print(f"  Query   : {query}")
    print(f"  Result  : {getattr(res, 'data', '')}\n")
    return getattr(res, 'data', None)

def log_analytics_to_supabase(feature: str, session_id: str, user_ip: str, action: str, model: str = "", extra_data: Optional[Dict] = None):
    extra_data = extra_data if extra_data is not None else {}
    data = {
        "feature": feature or "",
        "session_id": session_id or "",
        "user_ip": user_ip or "",
        "action": action or "",
        "model": model or "",
        "extra_data": extra_data
    }
    data["timestamp"] = datetime.utcnow().isoformat()
    res = supabase.table("analytics_log").insert(data).execute()
    if getattr(res, "error", None):
        print(f"\n[Supabase] Gagal log analytics:")
        print(f"  Error   : {getattr(res, 'error', '')}")
        print(f"  Data    : {data}\n")
        raise Exception(getattr(res, 'error', ''))
    print(f"\n[Supabase] Analytics log berhasil disimpan:")
    print(f"  Feature : {feature}")
    print(f"  Action  : {action}")
    print(f"  Data    : {getattr(res, 'data', '')}\n")
    return getattr(res, 'data', None)

def check_rate_limit(feature: str, session_id: str, user_ip: str, max_per_minute: int = 10):
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    one_minute_ago = (now - timedelta(minutes=1)).isoformat()
    q = supabase.table("analytics_log").select("id").eq("feature", feature)
    if session_id:
        q = q.eq("session_id", session_id)
    if user_ip:
        q = q.eq("user_ip", user_ip)
    q = q.gte("timestamp", one_minute_ago)
    res = q.execute()
    count = len(res.data) if hasattr(res, "data") else 0
    print(f"\n[Supabase] Rate limit check: {count} request(s) in last minute for {feature} by {session_id or user_ip}")
    return count < max_per_minute

# User Preferences Management
def save_user_preferences(user_id: str, preferences: dict):
    """Save or update user preferences"""
    data = {
        "user_id": user_id,
        "theme": preferences.get("theme", "light"),
        "language": preferences.get("language", "id"),
        "auto_save": preferences.get("auto_save", True),
        "notifications": preferences.get("notifications", True),
        "compact_mode": preferences.get("compact_mode", False),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    # Check if preferences exist
    existing = supabase.table("user_preferences").select("id").eq("user_id", user_id).execute()
    
    if existing.data and len(existing.data) > 0:
        # Update existing
        res = supabase.table("user_preferences").update(data).eq("user_id", user_id).execute()
    else:
        # Create new
        data["created_at"] = datetime.utcnow().isoformat()
        res = supabase.table("user_preferences").insert(data).execute()
    
    if getattr(res, "error", None):
        print(f"\n[Supabase] Gagal menyimpan preferences:")
        print(f"  Error   : {getattr(res, 'error', '')}")
        print(f"  Data    : {data}\n")
        raise Exception(getattr(res, 'error', ''))
    
    print(f"\n[Supabase] Preferences berhasil disimpan:")
    print(f"  User ID : {user_id}")
    print(f"  Theme   : {data['theme']}")
    print(f"  Data    : {getattr(res, 'data', '')}\n")
    return getattr(res, 'data', None)

def get_user_preferences(user_id: str):
    """Get user preferences"""
    res = supabase.table("user_preferences").select("*").eq("user_id", user_id).execute()
    if getattr(res, "error", None):
        print(f"\n[Supabase] Gagal mengambil preferences:")
        print(f"  Error   : {getattr(res, 'error', '')}")
        print(f"  User ID : {user_id}\n")
        raise Exception(getattr(res, 'error', ''))
    
    if res.data and len(res.data) > 0:
        print(f"\n[Supabase] Preferences berhasil diambil:")
        print(f"  User ID : {user_id}")
        print(f"  Data    : {res.data[0]}\n")
        return res.data[0]
    else:
        # Return default preferences
        default_prefs = {
            "user_id": user_id,
            "theme": "light",
            "language": "id",
            "auto_save": True,
            "notifications": True,
            "compact_mode": False,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        print(f"\n[Supabase] Menggunakan default preferences untuk user {user_id}")
        return default_prefs

def update_user_preferences(user_id: str, updates: dict):
    """Update specific user preferences"""
    data = {
        "updated_at": datetime.utcnow().isoformat()
    }
    
    # Only update provided fields
    if "theme" in updates:
        data["theme"] = updates["theme"]
    if "language" in updates:
        data["language"] = updates["language"]
    if "auto_save" in updates:
        data["auto_save"] = updates["auto_save"]
    if "notifications" in updates:
        data["notifications"] = updates["notifications"]
    if "compact_mode" in updates:
        data["compact_mode"] = updates["compact_mode"]
    
    res = supabase.table("user_preferences").update(data).eq("user_id", user_id).execute()
    
    if getattr(res, "error", None):
        print(f"\n[Supabase] Gagal update preferences:")
        print(f"  Error   : {getattr(res, 'error', '')}")
        print(f"  Data    : {data}\n")
        raise Exception(getattr(res, 'error', ''))
    
    print(f"\n[Supabase] Preferences berhasil diupdate:")
    print(f"  User ID : {user_id}")
    print(f"  Updates : {data}")
    print(f"  Data    : {getattr(res, 'data', '')}\n")
    return getattr(res, 'data', None)
