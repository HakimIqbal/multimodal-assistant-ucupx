import os
import io
import uuid
from fastapi import APIRouter, UploadFile, HTTPException, Request, Depends, File
from typing import List, Optional
import base64
from PIL import Image
import requests
from pydantic import BaseModel
import time
from datetime import datetime
from api.auth.auth_middleware import get_current_user
import json
# import from moviepy.editor hanya diperlukan jika fungsi video processing aktif
import tempfile
from src.db import supabase

router = APIRouter()

# Supported file types
SUPPORTED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"]
SUPPORTED_AUDIO_TYPES = ["audio/mpeg", "audio/wav", "audio/mp3", "audio/ogg"]
SUPPORTED_VIDEO_TYPES = ["video/mp4", "video/avi", "video/mov", "video/webm"]

class MultimodalRequest(BaseModel):
    query: str
    model_name: str = "gemini-1.5-pro"  # Default to Gemini for multimodal
    session_id: str = ""

def analyze_image_with_ai(image_data: bytes, query: str, model_name: str) -> dict:
    """
    Analyze image using AI vision models
    """
    try:
        # For now, we'll use a simple approach
        # In production, integrate with actual AI vision APIs
        image = Image.open(io.BytesIO(image_data))
        
        # Basic image analysis
        analysis = {
            "width": image.width,
            "height": image.height,
            "format": image.format,
            "mode": image.mode,
            "size_kb": len(image_data) / 1024,
            "description": f"Image analysis for query: {query}",
            "ai_insights": [
                "Image contains visual content",
                "Ready for AI analysis",
                "Format: " + str(image.format)
            ]
        }
        
        return {
            "success": True,
            "analysis": analysis,
            "model_used": model_name,
            "processing_time_ms": 150
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "model_used": model_name
        }

def transcribe_audio(audio_data: bytes, model_name: str) -> dict:
    """
    Transcribe audio to text (OpenAI removed)
    """
    return {"success": False, "error": "Audio transcription with OpenAI is not available.", "model_used": model_name}

def process_video_content(video_data: bytes, model_name: str) -> dict:
    """
    Extract audio and text from video (OpenAI removed)
    """
    return {"success": False, "error": "Video transcription with OpenAI is not available.", "model_used": model_name}

@router.post("/image/analyze")
async def analyze_image(
    file: UploadFile,
    request: MultimodalRequest,
    req: Request,
    user=Depends(get_current_user)
):
    # Upload file ke Google Drive terlebih dahulu
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
    if response.status_code not in [200, 201]:
        return {"success": False, "message": response.text, "status_code": response.status_code}
    drive_file = response.json()
    drive_file_id = drive_file.get("id")
    # Lanjutkan analisis AI seperti biasa
    # Validate file type
    if file.content_type not in SUPPORTED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"File type not supported. Supported types: {SUPPORTED_IMAGE_TYPES}"
        )
    # Validate file size (max 10MB)
    file_size = getattr(file, 'size', 0) or 0
    if file_size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size: 10MB")
    try:
        # Read file content
        image_data = await file.read()
        # Analyze with AI
        start_time = time.time()
        result = analyze_image_with_ai(image_data, request.query, request.model_name)
        processing_time = int((time.time() - start_time) * 1000)
        # Log to database (tambahkan drive_file_id jika perlu)
        log_entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user["id"],
            "session_id": request.session_id,
            "file_name": file.filename,
            "file_type": file.content_type,
            "file_size": len(image_data),
            "query": request.query,
            "result": result,
            "processing_time_ms": processing_time,
            "model_used": request.model_name,
            "drive_file_id": drive_file_id
        }
        # Save to database (implement this jika perlu)
        # save_multimodal_log("image_analysis", log_entry)
        return {
            "success": True,
            "file_name": file.filename,
            "file_type": file.content_type,
            "file_size_kb": len(image_data) / 1024,
            "query": request.query,
            "analysis": result,
            "processing_time_ms": processing_time,
            "session_id": request.session_id,
            "drive_file_id": drive_file_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze image: {str(e)}")

@router.post("/video/extract")
async def extract_video_content(
    file: UploadFile,
    request: MultimodalRequest,
    req: Request,
    user=Depends(get_current_user)
):
    # Upload file ke Google Drive terlebih dahulu
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
    if response.status_code not in [200, 201]:
        return {"success": False, "message": response.text, "status_code": response.status_code}
    drive_file = response.json()
    drive_file_id = drive_file.get("id")
    # Validate file type
    if file.content_type not in SUPPORTED_VIDEO_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"File type not supported. Supported types: {SUPPORTED_VIDEO_TYPES}"
        )
    # Validate file size (max 100MB)
    file_size = getattr(file, 'size', 0) or 0
    if file_size > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size: 100MB")
    try:
        # Read file content
        video_data = await file.read()
        # Extract content
        start_time = time.time()
        result = process_video_content(video_data, request.model_name)
        processing_time = int((time.time() - start_time) * 1000)
        # Log to database (tambahkan drive_file_id jika perlu)
        log_entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user["id"],
            "session_id": request.session_id,
            "file_name": file.filename,
            "file_type": file.content_type,
            "file_size": len(video_data),
            "result": result,
            "processing_time_ms": processing_time,
            "model_used": request.model_name,
            "drive_file_id": drive_file_id
        }
        # Save to database (implement this jika perlu)
        # save_multimodal_log("video_extraction", log_entry)
        return {
            "success": True,
            "file_name": file.filename,
            "file_type": file.content_type,
            "file_size_kb": len(video_data) / 1024,
            "extraction": result,
            "processing_time_ms": processing_time,
            "session_id": request.session_id,
            "drive_file_id": drive_file_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract video content: {str(e)}")

@router.get("/supported-formats")
async def get_supported_formats():
    """
    Get list of supported file formats for multimodal processing
    """
    return {
        "image": {
            "formats": ["JPEG", "PNG", "GIF", "WebP"],
            "max_size_mb": 10,
            "description": "Image analysis with AI vision"
        },
        "audio": {
            "formats": ["MP3", "WAV", "OGG"],
            "max_size_mb": 50,
            "description": "Audio transcription to text"
        },
        "video": {
            "formats": ["MP4", "AVI", "MOV", "WebM"],
            "max_size_mb": 100,
            "description": "Video content extraction"
        }
    }

@router.get("/multimodal/stats")
async def get_multimodal_stats(user=Depends(get_current_user)):
    """
    Get multimodal processing statistics from database
    """
    try:
        logs = supabase.table("multimodal_logs").select("*").eq("user_id", user["id"]).execute()
        data = logs.data if logs and logs.data else []
        total = len(data)
        images = sum(1 for d in data if d.get("type") == "image")
        audio = sum(1 for d in data if d.get("type") == "audio")
        video = sum(1 for d in data if d.get("type") == "video")
        avg_time = int(sum(d.get("processing_time_ms", 0) for d in data) / total) if total else 0
        success = sum(1 for d in data if d.get("success", True))
        return {
            "total_processed": total,
            "images_analyzed": images,
            "audio_transcribed": audio,
            "videos_extracted": video,
            "average_processing_time_ms": avg_time,
            "success_rate": round(success / total, 2) if total else 0.0,
            "user_id": user["id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}") 