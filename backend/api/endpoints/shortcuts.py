from fastapi import APIRouter
from src.db import supabase
router = APIRouter()
@router.get("/list")
async def list_shortcuts():
    try:
        res = supabase.table("shortcuts").select("*").execute()
        shortcuts = [s.get("shortcut") for s in res.data] if res and res.data else []
        return {"success": True, "shortcuts": shortcuts}
    except Exception as e:
        return {"success": False, "shortcuts": [], "error": str(e)} 