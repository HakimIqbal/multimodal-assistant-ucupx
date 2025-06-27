from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import json
import uuid
import asyncio
from api.auth.auth_middleware import get_current_user
import requests
import os
from src.document_processor import extract_text
import tempfile

router = APIRouter()

class DocumentVersion(BaseModel):
    id: Optional[str] = None
    document_id: str
    version_number: int
    content_hash: str
    changes_summary: Optional[str] = None
    created_by: str
    created_at: Optional[str] = None

class BulkUploadRequest(BaseModel):
    files: List[str]  # List of file IDs
    category: Optional[str] = None
    workspace_id: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class DocumentSearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    workspace_id: Optional[str] = None
    search_type: str = "full_text"  # full_text, metadata, tags
    limit: int = 20
    offset: int = 0

class DocumentMetadata(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    author: Optional[str] = None
    language: Optional[str] = None
    keywords: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None

@router.post("/documents/upload/bulk")
async def bulk_upload_documents(
    request: BulkUploadRequest,
    user=Depends(get_current_user)
):
    """
    Upload multiple documents at once
    """
    try:
        from src.db import supabase
        
        results = []
        
        # Process files in parallel
        async def process_file(file_id: str):
            try:
                # Get file info
                file_res = supabase.storage.from_("documents").list(path=f"{user['id']}/{file_id}")
                
                if not file_res:
                    return {
                        "file_id": file_id,
                        "status": "error",
                        "error": "File not found"
                    }
                
                # Download and process file
                file_data = supabase.storage.from_("documents").download(f"{user['id']}/{file_id}")
                # Simpan file sementara ke disk
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(file_data)
                    tmp_file_path = tmp_file.name
                # Ekstrak teks
                content = extract_text(tmp_file_path)
                doc_info = {
                    "content": content,
                    "summary": "",  # Bisa tambahkan ringkasan otomatis jika ada
                    "key_topics": [],
                    "word_count": len(content.split()),
                    "content_type": "pdf",
                    "metadata": {},
                    "category": request.category or "general",
                    "tags": request.tags or []
                }
                
                # Upload ke Google Drive (jika file belum di Drive)
                GOOGLE_DRIVE_TOKEN = os.getenv("GOOGLE_DRIVE_TOKEN")
                drive_file_id = None
                if GOOGLE_DRIVE_TOKEN:
                    headers = {"Authorization": f"Bearer {GOOGLE_DRIVE_TOKEN}"}
                    metadata = {"name": file_id}
                    files = {
                        "data": (None, json.dumps(metadata), "application/json; charset=UTF-8"),
                        "file": (file_id, file_data)
                    }
                    response = requests.post(
                        "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
                        headers=headers,
                        files=files
                    )
                    if response.status_code in [200, 201]:
                        drive_file = response.json()
                        drive_file_id = drive_file.get("id")
                
                # Save to database
                document_data = {
                    "id": str(uuid.uuid4()),
                    "user_id": user["id"],
                    "filename": file_id,
                    "category": request.category or doc_info.get("category", "general"),
                    "tags": request.tags or doc_info.get("tags", []),
                    "metadata": {
                        **(request.metadata or {}),
                        **doc_info.get("metadata", {}),
                        "workspace_id": request.workspace_id,
                        "upload_timestamp": datetime.utcnow().isoformat(),
                        "file_size": len(file_data),
                        "content_type": doc_info.get("content_type", "unknown"),
                        "drive_file_id": drive_file_id
                    },
                    "content": doc_info.get("content", ""),
                    "summary": doc_info.get("summary", ""),
                    "key_topics": doc_info.get("key_topics", []),
                    "word_count": doc_info.get("word_count", 0),
                    "upload_timestamp": datetime.utcnow().isoformat()
                }
                
                supabase.table("documents").insert(document_data).execute()
                
                return {
                    "file_id": file_id,
                    "status": "success",
                    "document_id": document_data["id"],
                    "filename": file_id,
                    "word_count": document_data["word_count"]
                }
                
            except Exception as e:
                return {
                    "file_id": file_id,
                    "status": "error",
                    "error": str(e)
                }
        
        # Process all files concurrently
        tasks = [process_file(file_id) for file_id in request.files]
        results = await asyncio.gather(*tasks)
        
        # Count successes and failures
        successful = [r for r in results if r["status"] == "success"]
        failed = [r for r in results if r["status"] == "error"]
        
        return {
            "success": True,
            "total_files": len(request.files),
            "successful_uploads": len(successful),
            "failed_uploads": len(failed),
            "results": results,
            "summary": {
                "total_word_count": sum(int(r.get("word_count", 0)) for r in successful if isinstance(r.get("word_count", 0), int)),
                "average_word_count": sum(int(r.get("word_count", 0)) for r in successful if isinstance(r.get("word_count", 0), int)) / len(successful) if successful else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk upload failed: {str(e)}")

@router.get("/documents/search")
async def search_documents(
    query: str = Query(..., description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    workspace_id: Optional[str] = Query(None, description="Filter by workspace"),
    search_type: str = Query("full_text", description="Search type: full_text, metadata, tags"),
    limit: int = Query(20, description="Number of results"),
    offset: int = Query(0, description="Offset for pagination"),
    user=Depends(get_current_user)
):
    """
    Advanced document search with multiple filters
    """
    try:
        from src.db import supabase
        
        # Build search query
        search_query = supabase.table("documents").select("*").eq("user_id", user["id"])
        
        # Apply filters
        if category:
            search_query = search_query.eq("category", category)
        
        if workspace_id:
            search_query = search_query.eq("metadata->workspace_id", workspace_id)
        
        if date_from:
            search_query = search_query.gte("upload_timestamp", f"{date_from}T00:00:00")
        
        if date_to:
            search_query = search_query.lte("upload_timestamp", f"{date_to}T23:59:59")
        
        # Apply search based on type
        if search_type == "full_text":
            # Full-text search in content
            search_query = search_query.text_search("content", query)
        elif search_type == "metadata":
            # Search in metadata fields
            search_query = search_query.or_(f"metadata->title.ilike.%{query}%,metadata->description.ilike.%{query}%")
        elif search_type == "tags":
            # Search in tags
            if tags:
                tag_list = [tag.strip() for tag in tags.split(",")]
                for tag in tag_list:
                    search_query = search_query.contains("tags", [tag])
        
        # Execute search with pagination
        res = search_query.execute()
        # Sorting manual by upload_timestamp desc
        sorted_data = sorted(res.data, key=lambda d: d.get("upload_timestamp", ""), reverse=True)
        paged_data = sorted_data[offset:offset+limit]
        
        # Format results
        documents = []
        for doc in paged_data:
            documents.append({
                "id": doc["id"],
                "filename": doc["filename"],
                "category": doc["category"],
                "tags": doc.get("tags", []),
                "summary": doc.get("summary", ""),
                "word_count": doc.get("word_count", 0),
                "upload_timestamp": doc["upload_timestamp"],
                "metadata": doc.get("metadata", {}),
                "relevance_score": 0.8  # Placeholder relevance score
            })
        
        total_count = len(sorted_data)
        
        return {
            "success": True,
            "query": query,
            "search_type": search_type,
            "documents": documents,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": total_count,
                "has_more": offset + limit < total_count
            },
            "filters_applied": {
                "category": category,
                "tags": tags.split(",") if tags else None,
                "date_from": date_from,
                "date_to": date_to,
                "workspace_id": workspace_id
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document search failed: {str(e)}")

@router.post("/documents/{document_id}/versions")
async def create_document_version(
    document_id: str,
    version: DocumentVersion,
    user=Depends(get_current_user)
):
    """
    Create a new version of a document
    """
    try:
        from src.db import supabase
        
        # Check if document exists and user has access
        doc_res = supabase.table("documents").select("*").eq("id", document_id).eq("user_id", user["id"]).execute()
        
        if not doc_res.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document = doc_res.data[0]
        
        # Get current version number
        version_res = supabase.table("document_versions").select("version_number").eq("document_id", document_id).order("version_number", desc=True).limit(1).execute()
        
        current_version = 1
        if version_res.data:
            current_version = version_res.data[0]["version_number"] + 1
        
        # Create version record
        version_data = {
            "id": str(uuid.uuid4()),
            "document_id": document_id,
            "version_number": current_version,
            "content_hash": version.content_hash,
            "changes_summary": version.changes_summary,
            "created_by": user["id"],
            "created_at": datetime.utcnow().isoformat(),
            "content_snapshot": document.get("content", ""),
            "metadata_snapshot": document.get("metadata", {})
        }
        
        supabase.table("document_versions").insert(version_data).execute()
        
        return {
            "success": True,
            "version_id": version_data["id"],
            "version_number": current_version,
            "message": f"Version {current_version} created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create version: {str(e)}")

@router.get("/documents/{document_id}/versions")
async def get_document_versions(
    document_id: str,
    user=Depends(get_current_user)
):
    """
    Get all versions of a document
    """
    try:
        from src.db import supabase
        
        # Check if document exists and user has access
        doc_res = supabase.table("documents").select("*").eq("id", document_id).eq("user_id", user["id"]).execute()
        
        if not doc_res.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get all versions
        versions_res = supabase.table("document_versions").select("*").eq("document_id", document_id).order("version_number", desc=True).execute()
        
        versions = []
        for version in versions_res.data:
            versions.append({
                "id": version["id"],
                "version_number": version["version_number"],
                "changes_summary": version["changes_summary"],
                "created_by": version["created_by"],
                "created_at": version["created_at"],
                "content_hash": version["content_hash"]
            })
        
        return {
            "success": True,
            "document_id": document_id,
            "total_versions": len(versions),
            "versions": versions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get versions: {str(e)}")

@router.put("/documents/{document_id}/metadata")
async def update_document_metadata(
    document_id: str,
    metadata: DocumentMetadata,
    user=Depends(get_current_user)
):
    """
    Update document metadata
    """
    try:
        from src.db import supabase
        
        # Check if document exists and user has access
        doc_res = supabase.table("documents").select("*").eq("id", document_id).eq("user_id", user["id"]).execute()
        
        if not doc_res.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Update metadata
        update_data = {}
        
        if metadata.title is not None:
            update_data["metadata->title"] = metadata.title
        
        if metadata.description is not None:
            update_data["metadata->description"] = metadata.description
        
        if metadata.tags is not None:
            update_data["tags"] = metadata.tags
        
        if metadata.category is not None:
            update_data["category"] = metadata.category
        
        if metadata.author is not None:
            update_data["metadata->author"] = metadata.author
        
        if metadata.language is not None:
            update_data["metadata->language"] = metadata.language
        
        if metadata.keywords is not None:
            update_data["metadata->keywords"] = metadata.keywords
        
        if metadata.custom_fields is not None:
            update_data["metadata->custom_fields"] = metadata.custom_fields
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        supabase.table("documents").update(update_data).eq("id", document_id).execute()
        
        return {
            "success": True,
            "message": "Document metadata updated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update metadata: {str(e)}")

@router.get("/documents/statistics")
async def get_document_statistics(user=Depends(get_current_user)):
    """
    Get document statistics for user
    """
    try:
        from src.db import supabase
        
        # Get all user documents
        docs_res = supabase.table("documents").select("*").eq("user_id", user["id"]).execute()
        
        documents = docs_res.data
        
        # Calculate statistics
        total_documents = len(documents)
        total_word_count = sum([doc.get("word_count", 0) for doc in documents if isinstance(doc.get("word_count", 0), int)])
        
        # Category distribution
        categories = {}
        for doc in documents:
            category = doc.get("category", "uncategorized")
            categories[category] = categories.get(category, 0) + 1
        
        # Tag distribution
        all_tags = []
        for doc in documents:
            all_tags.extend(doc.get("tags", []))
        
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Recent activity
        recent_docs = sorted(documents, key=lambda x: x["upload_timestamp"], reverse=True)[:5]
        
        # Storage usage
        total_size = sum([doc.get("metadata", {}).get("file_size", 0) for doc in documents if isinstance(doc.get("metadata", {}).get("file_size", 0), int)])
        
        return {
            "success": True,
            "statistics": {
                "total_documents": total_documents,
                "total_word_count": total_word_count,
                "average_word_count": total_word_count / total_documents if total_documents > 0 else 0,
                "total_storage_bytes": total_size,
                "categories": categories,
                "top_tags": sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10],
                "recent_uploads": len(recent_docs)
            },
            "recent_documents": [
                {
                    "id": doc["id"],
                    "filename": doc["filename"],
                    "category": doc.get("category"),
                    "upload_timestamp": doc["upload_timestamp"]
                }
                for doc in recent_docs
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    user=Depends(get_current_user)
):
    """
    Delete a document and all its versions
    """
    try:
        from src.db import supabase
        
        # Check if document exists and user has access
        doc_res = supabase.table("documents").select("*").eq("id", document_id).eq("user_id", user["id"]).execute()
        
        if not doc_res.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document = doc_res.data[0]
        drive_file_id = document.get("drive_file_id")
        
        # Hapus file di Google Drive jika ada
        if drive_file_id:
            GOOGLE_DRIVE_TOKEN = os.getenv("GOOGLE_DRIVE_TOKEN")
            if GOOGLE_DRIVE_TOKEN:
                headers = {"Authorization": f"Bearer {GOOGLE_DRIVE_TOKEN}"}
                requests.delete(f"https://www.googleapis.com/drive/v3/files/{drive_file_id}", headers=headers)
        
        # Delete document versions first
        supabase.table("document_versions").delete().eq("document_id", document_id).execute()
        
        # Delete document
        supabase.table("documents").delete().eq("id", document_id).execute()
        
        return {
            "success": True,
            "message": "Document and all versions deleted successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@router.post("/documents/{document_id}/duplicate")
async def duplicate_document(
    document_id: str,
    new_filename: Optional[str] = None,
    user=Depends(get_current_user)
):
    """
    Duplicate a document
    """
    try:
        from src.db import supabase
        
        # Get original document
        doc_res = supabase.table("documents").select("*").eq("id", document_id).eq("user_id", user["id"]).execute()
        
        if not doc_res.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        original_doc = doc_res.data[0]
        
        # Create duplicate
        new_doc_id = str(uuid.uuid4())
        duplicate_data = {
            "id": new_doc_id,
            "user_id": user["id"],
            "filename": new_filename or f"{original_doc['filename']}_copy",
            "category": original_doc["category"],
            "tags": original_doc.get("tags", []),
            "metadata": {
                **(original_doc.get("metadata", {})),
                "duplicated_from": document_id,
                "duplicated_at": datetime.utcnow().isoformat()
            },
            "content": original_doc.get("content", ""),
            "summary": original_doc.get("summary", ""),
            "key_topics": original_doc.get("key_topics", []),
            "word_count": original_doc.get("word_count", 0),
            "upload_timestamp": datetime.utcnow().isoformat()
        }
        
        supabase.table("documents").insert(duplicate_data).execute()
        
        return {
            "success": True,
            "original_document_id": document_id,
            "new_document_id": new_doc_id,
            "new_filename": duplicate_data["filename"],
            "message": "Document duplicated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to duplicate document: {str(e)}")

@router.put("/documents/{document_id}/file")
async def update_document_file(
    document_id: str,
    file: UploadFile = File(...),
    user=Depends(get_current_user)
):
    """
    Update/replace the file in Google Drive and update document metadata in the database
    """
    try:
        from src.db import supabase
        # Cek dokumen
        doc_res = supabase.table("documents").select("*").eq("id", document_id).eq("user_id", user["id"]).execute()
        if not doc_res.data:
            raise HTTPException(status_code=404, detail="Document not found")
        document = doc_res.data[0]
        old_drive_file_id = document.get("metadata", {}).get("drive_file_id")
        # Hapus file lama di Google Drive jika ada
        GOOGLE_DRIVE_TOKEN = os.getenv("GOOGLE_DRIVE_TOKEN")
        if old_drive_file_id and GOOGLE_DRIVE_TOKEN:
            headers = {"Authorization": f"Bearer {GOOGLE_DRIVE_TOKEN}"}
            requests.delete(f"https://www.googleapis.com/drive/v3/files/{old_drive_file_id}", headers=headers)
        # Upload file baru ke Google Drive
        if not GOOGLE_DRIVE_TOKEN:
            raise HTTPException(status_code=400, detail="GOOGLE_DRIVE_TOKEN not set")
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
            raise HTTPException(status_code=500, detail=f"Failed to upload new file to Google Drive: {response.text}")
        drive_file = response.json()
        new_drive_file_id = drive_file.get("id")
        # Update metadata dokumen di database
        update_data = {
            "filename": file.filename,
            "metadata": {
                **(document.get("metadata", {})),
                "drive_file_id": new_drive_file_id,
                "updated_at": datetime.utcnow().isoformat(),
                "file_size": getattr(file, 'size', 0) or 0,
                "content_type": file.content_type
            },
            "upload_timestamp": datetime.utcnow().isoformat()
        }
        supabase.table("documents").update(update_data).eq("id", document_id).execute()
        return {
            "success": True,
            "message": "File updated successfully in Google Drive and database.",
            "document_id": document_id,
            "drive_file_id": new_drive_file_id,
            "filename": file.filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update document file: {str(e)}") 