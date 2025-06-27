import os
from fastapi import APIRouter, Depends
from src.db import supabase
router = APIRouter()
@router.post("/delete_account")
async def delete_account(user=Depends(lambda: None)):
    try:
        supabase.table("users").delete().eq("id", user["id"]).execute()
        supabase.table("general_logs").delete().eq("user_id", user["id"]).execute()
        supabase.table("custom_prompts").delete().eq("user_id", user["id"]).execute()
        return {"success": True, "message": "Account and related data deleted"}
    except Exception as e:
        return {"success": False, "message": str(e)}
@router.get("/data_retention")
async def data_retention_policy():
    policy = os.getenv("DATA_RETENTION_POLICY", "30 days")
    return {"success": True, "policy": policy} 