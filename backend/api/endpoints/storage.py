from fastapi import APIRouter, UploadFile, File
import httpx
import os
import json
import requests

router = APIRouter()

@router.post("/upload_drive")
async def upload_drive(file: UploadFile = File(...)):
    try:
        GOOGLE_DRIVE_TOKEN = os.getenv("GOOGLE_DRIVE_TOKEN")
        if not GOOGLE_DRIVE_TOKEN:
            return {"success": False, "message": "GOOGLE_DRIVE_TOKEN not set"}
        headers = {"Authorization": f"Bearer {GOOGLE_DRIVE_TOKEN}"}
        metadata = {"name": file.filename}
        files = {
            "data": (None, json.dumps(metadata), "application/json; charset=UTF-8"),
            "file": (file.filename, await file.read())
        }
        response = requests.post(
            "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
            headers=headers,
            files=files
        )
        if response.status_code in [200, 201]:
            drive_file = response.json()
            drive_file_id = drive_file.get("id")
            # Simpan ke database jika perlu (misal: Supabase)
            # from src.db import supabase
            # supabase.table("drive_uploads").insert({"filename": file.filename, "drive_file_id": drive_file_id, "uploaded_at": datetime.utcnow().isoformat()}).execute()
            return {"success": True, "message": "Uploaded to Google Drive", "filename": file.filename, "drive_file_id": drive_file_id}
        else:
            return {"success": False, "message": response.text, "status_code": response.status_code}
    except Exception as e:
        return {"success": False, "message": str(e)} 