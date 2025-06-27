from fastapi import APIRouter, Depends, HTTPException
from api.auth.auth_middleware import get_current_user
from backup import backup_database
router = APIRouter()
@router.post("/backup")
async def trigger_backup(user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    result = backup_database()
    if result:
        return {"success": True, "message": "Backup triggered successfully"}
    else:
        return {"success": False, "message": "Backup failed"} 