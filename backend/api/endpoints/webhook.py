from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, HttpUrl
from datetime import datetime
import httpx
import json
import uuid
from api.auth.auth_middleware import get_current_user
from src.db import supabase

router = APIRouter()

class WebhookConfig(BaseModel):
    id: Optional[str] = None
    user_id: str
    name: str
    url: HttpUrl
    events: List[str]  # ["chat_completed", "document_uploaded", "error_occurred", "user_registered"]
    secret: Optional[str] = None
    is_active: bool = True
    retry_count: int = 3
    timeout: int = 30

class WebhookEvent(BaseModel):
    id: str
    event_type: str
    timestamp: str
    data: Dict[str, Any]
    webhook_id: str
    status: str = "pending"  # pending, sent, failed
    retry_count: int = 0
    last_attempt: Optional[str] = None
    error_message: Optional[str] = None

class WebhookPayload(BaseModel):
    event_id: str
    event_type: str
    timestamp: str
    data: Dict[str, Any]
    signature: Optional[str] = None

async def send_webhook_notification(webhook_config: Dict[str, Any], event_data: Dict[str, Any]):
    """Send webhook notification to external service"""
    try:
        # Create event record
        event_id = str(uuid.uuid4())
        event = {
            "id": event_id,
            "webhook_id": webhook_config["id"],
            "event_type": event_data["event_type"],
            "timestamp": datetime.utcnow().isoformat(),
            "data": event_data["data"],
            "status": "pending",
            "retry_count": 0
        }
        
        # Save event to database
        supabase.table("webhook_events").insert(event).execute()
        
        # Prepare payload
        payload = {
            "event_id": event_id,
            "event_type": event_data["event_type"],
            "timestamp": event_data["timestamp"],
            "data": event_data["data"]
        }
        
        # Add signature if secret is configured
        if webhook_config.get("secret"):
            import hmac
            import hashlib
            payload_str = json.dumps(payload, sort_keys=True)
            signature = hmac.new(
                webhook_config["secret"].encode(),
                payload_str.encode(),
                hashlib.sha256
            ).hexdigest()
            payload["signature"] = f"sha256={signature}"
        
        # Send webhook
        async with httpx.AsyncClient(timeout=webhook_config.get("timeout", 30)) as client:
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "MultimodalAssistant/1.0"
            }
            
            response = await client.post(
                str(webhook_config["url"]),
                json=payload,
                headers=headers
            )
            
            # Update event status
            if response.status_code in [200, 201, 202]:
                supabase.table("webhook_events").update({
                    "status": "sent",
                    "last_attempt": datetime.utcnow().isoformat()
                }).eq("id", event_id).execute()
            else:
                supabase.table("webhook_events").update({
                    "status": "failed",
                    "last_attempt": datetime.utcnow().isoformat(),
                    "error_message": f"HTTP {response.status_code}: {response.text}"
                }).eq("id", event_id).execute()
                
    except Exception as e:
        # Update event with error
        supabase.table("webhook_events").update({
            "status": "failed",
            "last_attempt": datetime.utcnow().isoformat(),
            "error_message": str(e)
        }).eq("id", event_id).execute()

@router.post("/webhooks")
async def create_webhook(webhook: WebhookConfig, user=Depends(get_current_user)):
    """
    Create a new webhook configuration
    """
    try:
        # Validate events
        valid_events = [
            "chat_completed", "document_uploaded", "error_occurred", 
            "user_registered", "user_login", "document_processed",
            "model_switched", "feedback_submitted", "export_created"
        ]
        
        invalid_events = [event for event in webhook.events if event not in valid_events]
        if invalid_events:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid events: {invalid_events}. Valid events: {valid_events}"
            )
        
        # Generate webhook ID and secret
        webhook_id = str(uuid.uuid4())
        webhook_secret = str(uuid.uuid4()) if not webhook.secret else webhook.secret
        
        webhook_data = {
            "id": webhook_id,
            "user_id": user["id"],
            "name": webhook.name,
            "url": str(webhook.url),
            "events": webhook.events,
            "secret": webhook_secret,
            "is_active": webhook.is_active,
            "retry_count": webhook.retry_count,
            "timeout": webhook.timeout,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Save webhook configuration
        supabase.table("webhook_configs").insert(webhook_data).execute()
        
        return {
            "success": True,
            "webhook_id": webhook_id,
            "secret": webhook_secret,
            "message": "Webhook created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create webhook: {str(e)}")

@router.get("/webhooks")
async def list_webhooks(user=Depends(get_current_user)):
    """
    List all webhooks for the user
    """
    try:
        res = supabase.table("webhook_configs").select("*").eq("user_id", user["id"]).execute()
        
        webhooks = []
        for webhook in res.data:
            webhooks.append({
                "id": webhook["id"],
                "name": webhook["name"],
                "url": webhook["url"],
                "events": webhook["events"],
                "is_active": webhook["is_active"],
                "created_at": webhook["created_at"],
                "last_triggered": webhook.get("last_triggered"),
                "success_count": webhook.get("success_count", 0),
                "failure_count": webhook.get("failure_count", 0)
            })
        
        return {
            "success": True,
            "webhooks": webhooks,
            "total": len(webhooks)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list webhooks: {str(e)}")

@router.get("/webhooks/{webhook_id}")
async def get_webhook(webhook_id: str, user=Depends(get_current_user)):
    """
    Get webhook details
    """
    try:
        res = supabase.table("webhook_configs").select("*").eq("id", webhook_id).eq("user_id", user["id"]).execute()
        
        if not res.data:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        webhook = res.data[0]
        
        # Get recent events
        events_res = supabase.table("webhook_events").select("*").eq("webhook_id", webhook_id).order("timestamp", desc=True).limit(10).execute()
        
        return {
            "success": True,
            "webhook": {
                "id": webhook["id"],
                "name": webhook["name"],
                "url": webhook["url"],
                "events": webhook["events"],
                "is_active": webhook["is_active"],
                "created_at": webhook["created_at"],
                "last_triggered": webhook.get("last_triggered"),
                "success_count": webhook.get("success_count", 0),
                "failure_count": webhook.get("failure_count", 0)
            },
            "recent_events": events_res.data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get webhook: {str(e)}")

@router.put("/webhooks/{webhook_id}")
async def update_webhook(
    webhook_id: str, 
    webhook_update: WebhookConfig, 
    user=Depends(get_current_user)
):
    """
    Update webhook configuration
    """
    try:
        # Check if webhook exists and belongs to user
        res = supabase.table("webhook_configs").select("*").eq("id", webhook_id).eq("user_id", user["id"]).execute()
        
        if not res.data:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        # Validate events
        valid_events = [
            "chat_completed", "document_uploaded", "error_occurred", 
            "user_registered", "user_login", "document_processed",
            "model_switched", "feedback_submitted", "export_created"
        ]
        
        invalid_events = [event for event in webhook_update.events if event not in valid_events]
        if invalid_events:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid events: {invalid_events}. Valid events: {valid_events}"
            )
        
        # Update webhook
        update_data = {
            "name": webhook_update.name,
            "url": str(webhook_update.url),
            "events": webhook_update.events,
            "is_active": webhook_update.is_active,
            "retry_count": webhook_update.retry_count,
            "timeout": webhook_update.timeout,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        if webhook_update.secret:
            update_data["secret"] = webhook_update.secret
        
        supabase.table("webhook_configs").update(update_data).eq("id", webhook_id).execute()
        
        return {
            "success": True,
            "message": "Webhook updated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update webhook: {str(e)}")

@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(webhook_id: str, user=Depends(get_current_user)):
    """
    Delete webhook configuration
    """
    try:
        # Check if webhook exists and belongs to user
        res = supabase.table("webhook_configs").select("*").eq("id", webhook_id).eq("user_id", user["id"]).execute()
        
        if not res.data:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        # Delete webhook and related events
        supabase.table("webhook_events").delete().eq("webhook_id", webhook_id).execute()
        supabase.table("webhook_configs").delete().eq("id", webhook_id).execute()
        
        return {
            "success": True,
            "message": "Webhook deleted successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete webhook: {str(e)}")

@router.post("/webhooks/{webhook_id}/test")
async def test_webhook(webhook_id: str, user=Depends(get_current_user)):
    """
    Test webhook by sending a test event
    """
    try:
        # Get webhook configuration
        res = supabase.table("webhook_configs").select("*").eq("id", webhook_id).eq("user_id", user["id"]).execute()
        
        if not res.data:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        webhook_config = res.data[0]
        
        if not webhook_config["is_active"]:
            raise HTTPException(status_code=400, detail="Webhook is not active")
        
        # Send test event
        test_event = {
            "event_type": "test_event",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "message": "This is a test webhook event",
                "user_id": user["id"],
                "webhook_id": webhook_id
            }
        }
        
        await send_webhook_notification(webhook_config, test_event)
        
        return {
            "success": True,
            "message": "Test webhook sent successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test webhook: {str(e)}")

@router.get("/webhooks/{webhook_id}/events")
async def get_webhook_events(
    webhook_id: str,
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    user=Depends(get_current_user)
):
    """
    Get webhook events with pagination and filtering
    """
    try:
        # Check if webhook belongs to user
        res = supabase.table("webhook_configs").select("id").eq("id", webhook_id).eq("user_id", user["id"]).execute()
        
        if not res.data:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        # Build query
        query = supabase.table("webhook_events").select("*").eq("webhook_id", webhook_id)
        
        if status:
            query = query.eq("status", status)
        
        # Get events with pagination
        events_res = query.order("timestamp", desc=True).range(offset, offset + limit - 1).execute()
        
        # Get total count
        count_res = query.execute()
        total_count = len(count_res.data)
        
        return {
            "success": True,
            "events": events_res.data,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": total_count,
                "has_more": offset + limit < total_count
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get webhook events: {str(e)}")

# Background task to retry failed webhooks
async def retry_failed_webhooks():
    """Retry failed webhook events"""
    try:
        # Get failed events that haven't exceeded retry limit
        res = supabase.table("webhook_events").select("*").eq("status", "failed").execute()
        
        for event in res.data:
            webhook_res = supabase.table("webhook_configs").select("*").eq("id", event["webhook_id"]).execute()
            
            if webhook_res.data:
                webhook_config = webhook_res.data[0]
                
                if event["retry_count"] < webhook_config.get("retry_count", 3):
                    # Retry sending webhook
                    await send_webhook_notification(webhook_config, {
                        "event_type": event["event_type"],
                        "timestamp": event["timestamp"],
                        "data": event["data"]
                    })
                    
    except Exception as e:
        print(f"Error retrying failed webhooks: {e}")

# Event triggers (to be called from other endpoints)
async def trigger_webhook_event(event_type: str, data: Dict[str, Any], user_id: str):
    """Trigger webhook events for all matching webhooks"""
    try:
        # Get all active webhooks for this event type
        res = supabase.table("webhook_configs").select("*").eq("is_active", True).execute()
        
        for webhook in res.data:
            if event_type in webhook["events"]:
                event_data = {
                    "event_type": event_type,
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": data
                }
                
                await send_webhook_notification(webhook, event_data)
                
    except Exception as e:
        print(f"Error triggering webhook event: {e}") 