# Admin Dashboard Skeleton
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from src.db import supabase
from api.auth.auth_middleware import get_current_user, require_admin
import json
import sys

router = APIRouter()

@router.get("/admin/dashboard")
async def admin_dashboard(user=Depends(require_admin)):
    """
    Admin dashboard with comprehensive system overview
    """
    try:
        # Get system statistics
        stats = await get_system_statistics()
        
        # Get recent activity
        recent_activity = await get_recent_activity()
        
        # Get performance metrics
        performance = await get_performance_metrics()
        
        # Get user analytics
        user_analytics = await get_user_analytics()
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "statistics": stats,
            "recent_activity": recent_activity,
            "performance": performance,
            "user_analytics": user_analytics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")

async def get_system_statistics() -> dict:
    """Get comprehensive system statistics"""
    try:
        # User statistics
        user_res = supabase.table("users").select("id").execute()
        total_users = len(user_res.data) if user_res.data else 0
        
        # Get active users (last 7 days)
        week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        active_users_res = supabase.table("users").select("id").gte("last_login", week_ago).execute()
        active_users = len(active_users_res.data) if active_users_res.data else 0
        
        # Chat statistics
        general_chat_res = supabase.table("general_logs").select("id").execute()
        total_general_chats = len(general_chat_res.data) if general_chat_res.data else 0
        
        coder_chat_res = supabase.table("coder_logs").select("id").execute()
        total_coder_chats = len(coder_chat_res.data) if coder_chat_res.data else 0
        
        rag_chat_res = supabase.table("rag_logs").select("id").execute()
        total_rag_chats = len(rag_chat_res.data) if rag_chat_res.data else 0
        
        # Document statistics
        doc_res = supabase.table("documents").select("id").execute()
        total_documents = len(doc_res.data) if doc_res.data else 0
        
        # Feedback statistics
        feedback_res = supabase.table("chat_feedback").select("id").execute()
        total_feedback = len(feedback_res.data) if feedback_res.data else 0
        
        return {
            "users": {
                "total": total_users,
                "active_7d": active_users,
                "active_percentage": round((active_users / total_users * 100) if total_users > 0 else 0, 2)
            },
            "chats": {
                "general": total_general_chats,
                "coder": total_coder_chats,
                "rag": total_rag_chats,
                "total": total_general_chats + total_coder_chats + total_rag_chats
            },
            "documents": {
                "total": total_documents
            },
            "feedback": {
                "total": total_feedback
            }
        }
    except Exception as e:
        print(f"Error getting system statistics: {str(e)}")
        return {}

async def get_recent_activity() -> List[dict]:
    """Get recent system activity"""
    try:
        # Get recent user registrations
        recent_users = supabase.table("users").select("id, email, created_at").order("created_at", desc=True).limit(5).execute()
        
        # Get recent chat activity
        recent_chats = supabase.table("general_logs").select("id, input, timestamp, metadata").order("timestamp", desc=True).limit(5).execute()
        
        # Get recent document uploads
        recent_docs = supabase.table("documents").select("id, filename, upload_timestamp").order("upload_timestamp", desc=True).limit(5).execute()
        
        activity = []
        
        # Add user registrations
        for user in recent_users.data or []:
            activity.append({
                "type": "user_registration",
                "timestamp": user.get("created_at"),
                "description": f"New user registered: {user.get('email', 'Unknown')}",
                "data": user
            })
        
        # Add chat activity
        for chat in recent_chats.data or []:
            activity.append({
                "type": "chat",
                "timestamp": chat.get("timestamp"),
                "description": f"Chat query: {chat.get('input', '')[:50]}...",
                "data": chat
            })
        
        # Add document uploads
        for doc in recent_docs.data or []:
            activity.append({
                "type": "document_upload",
                "timestamp": doc.get("upload_timestamp"),
                "description": f"Document uploaded: {doc.get('filename', 'Unknown')}",
                "data": doc
            })
        
        # Sort by timestamp
        activity.sort(key=lambda x: x["timestamp"], reverse=True)
        return activity[:10]  # Return top 10
        
    except Exception as e:
        print(f"Error getting recent activity: {str(e)}")
        return []

async def get_performance_metrics() -> dict:
    """Get system performance metrics"""
    try:
        # Get average response times
        general_times = supabase.table("general_logs").select("metadata->response_time_ms").not_.is_("metadata->response_time_ms", "null").execute()
        coder_times = supabase.table("coder_logs").select("metadata->response_time_ms").not_.is_("metadata->response_time_ms", "null").execute()
        rag_times = supabase.table("rag_logs").select("metadata->response_time_ms").not_.is_("metadata->response_time_ms", "null").execute()
        
        def calculate_avg_times(data):
            times = []
            for item in data or []:
                if item.get("metadata", {}).get("response_time_ms"):
                    times.append(item["metadata"]["response_time_ms"])
            return sum(times) / len(times) if times else 0
        
        avg_general = calculate_avg_times(general_times.data)
        avg_coder = calculate_avg_times(coder_times.data)
        avg_rag = calculate_avg_times(rag_times.data)
        
        # Get error rates
        general_errors = supabase.table("general_logs").select("id").not_.is_("error_message", "").execute()
        coder_errors = supabase.table("coder_logs").select("id").not_.is_("error_message", "").execute()
        rag_errors = supabase.table("rag_logs").select("id").not_.is_("error_message", "").execute()
        
        total_general = supabase.table("general_logs").select("id").execute()
        total_coder = supabase.table("coder_logs").select("id").execute()
        total_rag = supabase.table("rag_logs").select("id").execute()
        
        def calculate_error_rate(errors, total):
            error_count = len(errors.data) if errors.data else 0
            total_count = len(total.data) if total.data else 1
            return round((error_count / total_count) * 100, 2)
        
        return {
            "response_times": {
                "general_ms": round(avg_general, 2),
                "coder_ms": round(avg_coder, 2),
                "rag_ms": round(avg_rag, 2),
                "overall_ms": round((avg_general + avg_coder + avg_rag) / 3, 2)
            },
            "error_rates": {
                "general_percent": calculate_error_rate(general_errors, total_general),
                "coder_percent": calculate_error_rate(coder_errors, total_coder),
                "rag_percent": calculate_error_rate(rag_errors, total_rag)
            }
        }
    except Exception as e:
        print(f"Error getting performance metrics: {str(e)}")
        return {}

async def get_user_analytics() -> dict:
    """Get user behavior analytics"""
    try:
        # Get user activity by hour
        hour_activity = {}
        for hour in range(24):
            hour_activity[hour] = 0
        
        # Get recent chat activity by hour
        day_ago = (datetime.utcnow() - timedelta(days=1)).isoformat()
        recent_chats = supabase.table("general_logs").select("timestamp").gte("timestamp", day_ago).execute()
        
        for chat in recent_chats.data or []:
            try:
                chat_time = datetime.fromisoformat(chat.get("timestamp", "").replace("Z", "+00:00"))
                hour = chat_time.hour
                hour_activity[hour] = hour_activity.get(hour, 0) + 1
            except:
                continue
        
        # Get user engagement metrics
        engagement_res = supabase.table("users").select("login_count, last_login").execute()
        total_logins = sum(user.get("login_count", 0) for user in engagement_res.data or [])
        avg_logins_per_user = total_logins / len(engagement_res.data) if engagement_res.data else 0
        
        return {
            "hourly_activity": hour_activity,
            "engagement": {
                "total_logins": total_logins,
                "avg_logins_per_user": round(avg_logins_per_user, 2),
                "peak_hour": max(hour_activity.items(), key=lambda x: x[1])[0] if hour_activity else 0
            }
        }
    except Exception as e:
        print(f"Error getting user analytics: {str(e)}")
        return {}

@router.get("/admin/users")
async def get_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str = "",
    user=Depends(require_admin)
):
    """Get paginated list of users with search"""
    try:
        offset = (page - 1) * limit
        
        # Build query
        query = supabase.table("users").select("id, username, email, role, created_at, last_login, login_count, locked_until")
        
        if search:
            query = query.or_(f"username.ilike.%{search}%,email.ilike.%{search}%")
        
        # Get total count
        count_res = supabase.table("users").select("id").execute()
        total_count = len(count_res.data) if count_res.data else 0
        
        # Get paginated results
        users_res = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        
        return {
            "status": "success",
            "users": users_res.data or [],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get users: {str(e)}")

@router.get("/admin/logs")
async def get_logs(
    log_type: str = Query("general", regex="^(general|coder|rag)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    user=Depends(require_admin)
):
    """Get paginated logs by type"""
    try:
        offset = (page - 1) * limit
        table_name = f"{log_type}_logs"
        
        # Get total count
        count_res = supabase.table(table_name).select("id").execute()
        total_count = len(count_res.data) if count_res.data else 0
        
        # Get paginated results
        logs_res = supabase.table(table_name).select("*").order("timestamp", desc=True).range(offset, offset + limit - 1).execute()
        
        return {
            "status": "success",
            "logs": logs_res.data or [],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")

@router.post("/admin/users/{user_id}/toggle-status")
async def toggle_user_status(user_id: str, user=Depends(require_admin)):
    """Toggle user locked status"""
    try:
        # Get current user status
        user_res = supabase.table("users").select("locked_until").eq("id", user_id).execute()
        
        if not user_res.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        current_user = user_res.data[0]
        is_locked = current_user.get("locked_until") is not None
        
        if is_locked:
            # Unlock user
            supabase.table("users").update({"locked_until": None}).eq("id", user_id).execute()
            message = "User unlocked successfully"
        else:
            # Lock user for 24 hours
            lock_until = (datetime.utcnow() + timedelta(hours=24)).isoformat()
            supabase.table("users").update({"locked_until": lock_until}).eq("id", user_id).execute()
            message = "User locked for 24 hours"
        
        return {"status": "success", "message": message}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle user status: {str(e)}")

@router.delete("/admin/users/{user_id}")
async def delete_user(user_id: str, user=Depends(require_admin)):
    """Delete user and all associated data"""
    try:
        # Check if user exists
        user_res = supabase.table("users").select("id").eq("id", user_id).execute()
        if not user_res.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete user data from all tables
        tables_to_clean = [
            "general_logs", "coder_logs", "rag_logs", "documents", 
            "chat_feedback", "user_preferences", "auth_logs"
        ]
        
        for table in tables_to_clean:
            try:
                supabase.table(table).delete().eq("user_id", user_id).execute()
            except Exception as e:
                print(f"Warning: Failed to clean {table} for user {user_id}: {str(e)}")
        
        # Delete user
        supabase.table("users").delete().eq("id", user_id).execute()
        
        return {"status": "success", "message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")

@router.get("/admin/system-info")
async def get_system_info(user=Depends(require_admin)):
    """Get system information and health status"""
    try:
        # Get database connection status
        try:
            test_res = supabase.table("users").select("id").limit(1).execute()
            db_status = "healthy"
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        # Get environment info
        import os
        env_info = {
            "python_version": sys.version,
            "environment": os.getenv("ENVIRONMENT", "development"),
            "database_url": "configured" if os.getenv("SUPABASE_URL") else "not configured",
            "firebase_config": "configured" if os.getenv("FIREBASE_PROJECT_ID") else "not configured"
        }
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "database": db_status,
                "environment": env_info
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system info: {str(e)}") 