from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional, Dict
import uuid
from datetime import datetime, timedelta
from src.db import supabase
from api.auth.auth_middleware import auth_middleware
from api.endpoints.chat import chat_general

router = APIRouter(prefix="/auth/guest", tags=["Guest Authentication"])

# Pydantic models
class GuestChatRequest(BaseModel):
    message: str
    session_token: str

class GuestSessionResponse(BaseModel):
    session_token: str
    expires_at: str
    chat_limit: int
    remaining_chats: int

# =====================================================
# GUEST SESSION MANAGEMENT
# =====================================================

@router.post("/session")
async def create_guest_session(req: Request):
    """Create guest session for anonymous users"""
    try:
        # Rate limiting for guest session creation
        await auth_middleware.check_rate_limit(req, "/auth/guest/session")
        
        # Generate session token
        session_token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        # Create guest session in database
        data = {
            'id': str(uuid.uuid4()),
            'session_token': session_token,
            'ip_address': req.client.host if req.client else 'unknown',
            'user_agent': req.headers.get('user-agent', ''),
            'chat_count': 0,
            'expires_at': expires_at.isoformat(),
            'is_active': True
        }
        
        res = supabase.table('guest_sessions').insert(data).execute()
        if getattr(res, 'error', None):
            raise HTTPException(status_code=500, detail="Failed to create guest session")
        
        # Log guest session creation
        await auth_middleware.log_auth_action(
            None, "guest_session_created", True, req
        )
        
        return {
            "success": True,
            "session": {
                "session_token": session_token,
                "expires_at": expires_at.isoformat(),
                "chat_limit": 10,
                "remaining_chats": 10
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Guest session creation error: {str(e)}")
        await auth_middleware.log_auth_action(
            None, "guest_session_created", False, req, str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to create guest session")

@router.get("/session/{session_token}")
async def get_guest_session(session_token: str, req: Request):
    """Get guest session information"""
    try:
        # Get session from database
        res = supabase.table('guest_sessions').select('*').eq('session_token', session_token).eq('is_active', True).execute()
        
        if not res.data or len(res.data) == 0:
            raise HTTPException(status_code=404, detail="Guest session not found")
        
        session_data = res.data[0]
        
        # Check if session is expired
        expires_at = datetime.fromisoformat(session_data['expires_at'].replace('Z', '+00:00'))
        if expires_at < datetime.now(expires_at.tzinfo):
            # Mark session as inactive
            supabase.table('guest_sessions').update({'is_active': False}).eq('id', session_data['id']).execute()
            raise HTTPException(status_code=401, detail="Guest session expired")
        
        remaining_chats = 10 - session_data.get('chat_count', 0)
        
        return {
            "success": True,
            "session": {
                "session_token": session_token,
                "expires_at": session_data['expires_at'],
                "chat_limit": 10,
                "remaining_chats": max(0, remaining_chats),
                "created_at": session_data['created_at']
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Get guest session error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get guest session")

@router.delete("/session/{session_token}")
async def delete_guest_session(session_token: str, req: Request):
    """Delete guest session"""
    try:
        # Mark session as inactive
        res = supabase.table('guest_sessions').update({'is_active': False}).eq('session_token', session_token).execute()
        
        if getattr(res, 'error', None):
            raise HTTPException(status_code=500, detail="Failed to delete guest session")
        
        # Log session deletion
        await auth_middleware.log_auth_action(
            None, "guest_session_deleted", True, req
        )
        
        return {
            "success": True,
            "message": "Guest session deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Delete guest session error: {str(e)}")
        await auth_middleware.log_auth_action(
            None, "guest_session_deleted", False, req, str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to delete guest session")

# =====================================================
# GUEST CHAT ACCESS
# =====================================================

@router.post("/chat")
async def guest_chat(request: GuestChatRequest, req: Request):
    """Guest chat endpoint with rate limiting and real chat integration"""
    try:
        await auth_middleware.check_rate_limit(req, "/auth/guest/chat")
        session_data = await validate_guest_session(request.session_token)
        if not session_data:
            raise HTTPException(status_code=401, detail="Invalid guest session")
        if session_data['chat_count'] >= 10:
            raise HTTPException(status_code=429, detail="Guest chat limit reached")
        await increment_guest_chat_count(session_data['id'])
        await auth_middleware.log_auth_action(
            None, "guest_chat", True, req
        )
        # Integrasi ke chat utama
        chat_response = await process_chat(request.message, session_data)
        return {
            "success": True,
            "message": "Guest chat request processed",
            "response": chat_response,
            "remaining_chats": 9 - session_data['chat_count'],
            "note": "Guest users have limited access. Register for full features."
        }
    except HTTPException:
        raise
    except Exception as e:
        await auth_middleware.log_auth_action(
            None, "guest_chat", False, req, str(e)
        )
        raise HTTPException(status_code=500, detail="Guest chat failed")

# =====================================================
# UTILITY FUNCTIONS
# =====================================================

async def validate_guest_session(session_token: str) -> Optional[Dict]:
    """Validate guest session"""
    try:
        res = supabase.table('guest_sessions').select('*').eq('session_token', session_token).eq('is_active', True).execute()
        
        if not res.data or len(res.data) == 0:
            return None
        
        session_data = res.data[0]
        
        # Check if session is expired
        expires_at = datetime.fromisoformat(session_data['expires_at'].replace('Z', '+00:00'))
        if expires_at < datetime.now(expires_at.tzinfo):
            # Mark session as inactive
            supabase.table('guest_sessions').update({'is_active': False}).eq('id', session_data['id']).execute()
            return None
        
        return session_data
        
    except Exception as e:
        print(f"❌ Validate guest session error: {str(e)}")
        return None

async def increment_guest_chat_count(session_id: str) -> None:
    """Increment guest chat count"""
    try:
        res = supabase.table('guest_sessions').select('chat_count').eq('id', session_id).execute()
        if res.data and len(res.data) > 0:
            current_count = res.data[0].get('chat_count', 0)
            supabase.table('guest_sessions').update({'chat_count': current_count + 1}).eq('id', session_id).execute()
    except Exception as e:
        print(f"❌ Increment guest chat count error: {str(e)}")

# =====================================================
# CLEANUP TASK (should be run periodically)
# =====================================================

async def cleanup_expired_guest_sessions():
    """Clean up expired guest sessions"""
    try:
        # Mark expired sessions as inactive
        res = supabase.table('guest_sessions').update({'is_active': False}).lt('expires_at', datetime.utcnow().isoformat()).execute()
        
        if getattr(res, 'error', None):
            print(f"❌ Failed to cleanup expired guest sessions: {getattr(res, 'error', '')}")
        else:
            print(f"✅ Cleaned up expired guest sessions")
            
    except Exception as e:
        print(f"❌ Cleanup guest sessions error: {str(e)}") 

# Tambahkan async wrapper
async def process_chat(message: str, session_data: dict):
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, chat_general, message, "llama3-70b-8192", session_data.get("session_token", "")) 