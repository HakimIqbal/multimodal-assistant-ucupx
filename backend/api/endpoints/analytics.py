from fastapi import APIRouter, Depends
from src.db import supabase

router = APIRouter()

@router.get("/user_behavior")
async def user_behavior(user=Depends(lambda: None)):
    """
    Analyze user behavior (simple count from database)
    """
    try:
        users = supabase.table("users").select("id").execute()
        chats = supabase.table("chats").select("id").execute()
        docs = supabase.table("documents").select("id").execute()
        return {
            "success": True,
            "message": "User behavior analysis",
            "data": {
                "total_users": len(users.data) if users.data else 0,
                "total_chats": len(chats.data) if chats.data else 0,
                "total_docs": len(docs.data) if docs.data else 0
            }
        }
    except Exception as e:
        return {"success": False, "message": str(e), "data": {}}

@router.get("/dashboard/summary")
async def dashboard_summary(user=Depends(lambda: None)):
    """
    Custom dashboard summary (simple count from database)
    """
    try:
        users = supabase.table("users").select("id").execute()
        chats = supabase.table("chats").select("id").execute()
        docs = supabase.table("documents").select("id").execute()
        return {
            "success": True,
            "summary": {
                "total_users": len(users.data) if users.data else 0,
                "total_chats": len(chats.data) if chats.data else 0,
                "total_docs": len(docs.data) if docs.data else 0
            }
        }
    except Exception as e:
        return {"success": False, "summary": {"error": str(e)}} 