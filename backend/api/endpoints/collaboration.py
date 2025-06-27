from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime
import json
import uuid
from api.auth.auth_middleware import get_current_user

router = APIRouter()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, workspace_id: str):
        await websocket.accept()
        if workspace_id not in self.active_connections:
            self.active_connections[workspace_id] = []
        self.active_connections[workspace_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, workspace_id: str):
        if workspace_id in self.active_connections:
            self.active_connections[workspace_id].remove(websocket)
            if not self.active_connections[workspace_id]:
                del self.active_connections[workspace_id]
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast_to_workspace(self, message: str, workspace_id: str):
        if workspace_id in self.active_connections:
            for connection in self.active_connections[workspace_id]:
                try:
                    await connection.send_text(message)
                except:
                    # Remove broken connections
                    self.active_connections[workspace_id].remove(connection)

manager = ConnectionManager()

class Workspace(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    owner_id: str
    is_public: bool = False
    settings: Optional[Dict[str, Any]] = None

class WorkspaceMember(BaseModel):
    id: Optional[str] = None
    workspace_id: str
    user_id: str
    role: str = "member"  # owner, admin, member, viewer
    joined_at: Optional[str] = None

class Comment(BaseModel):
    id: Optional[str] = None
    workspace_id: str
    document_id: Optional[str] = None
    user_id: str
    content: str
    position: Optional[Dict[str, Any]] = None  # For document annotations
    parent_id: Optional[str] = None  # For threaded comments
    created_at: Optional[str] = None

class Annotation(BaseModel):
    id: Optional[str] = None
    workspace_id: str
    document_id: str
    user_id: str
    type: str  # highlight, underline, strikeout, note
    content: Optional[str] = None
    position: Dict[str, Any]  # page, coordinates, text selection
    color: Optional[str] = None
    created_at: Optional[str] = None

@router.post("/workspaces")
async def create_workspace(workspace: Workspace, user=Depends(get_current_user)):
    """
    Create a new collaborative workspace
    """
    try:
        from src.db import supabase
        
        workspace_id = str(uuid.uuid4())
        workspace_data = {
            "id": workspace_id,
            "name": workspace.name,
            "description": workspace.description,
            "owner_id": user["id"],
            "is_public": workspace.is_public,
            "settings": workspace.settings or {},
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Create workspace
        supabase.table("workspaces").insert(workspace_data).execute()
        
        # Add owner as workspace member
        member_data = {
            "id": str(uuid.uuid4()),
            "workspace_id": workspace_id,
            "user_id": user["id"],
            "role": "owner",
            "joined_at": datetime.utcnow().isoformat()
        }
        supabase.table("workspace_members").insert(member_data).execute()
        
        return {
            "success": True,
            "workspace_id": workspace_id,
            "message": "Workspace created successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create workspace: {str(e)}")

@router.get("/workspaces")
async def list_workspaces(user=Depends(get_current_user)):
    """
    List workspaces user has access to
    """
    try:
        from src.db import supabase
        
        # Get workspaces where user is a member
        res = supabase.table("workspace_members").select(
            "workspace_id, role, joined_at, workspaces(*)"
        ).eq("user_id", user["id"]).execute()
        
        workspaces = []
        for member in res.data:
            workspace = member["workspaces"]
            workspaces.append({
                "id": workspace["id"],
                "name": workspace["name"],
                "description": workspace["description"],
                "owner_id": workspace["owner_id"],
                "is_public": workspace["is_public"],
                "user_role": member["role"],
                "joined_at": member["joined_at"],
                "created_at": workspace["created_at"],
                "member_count": 0  # Will be populated separately
            })
        
        # Get member counts
        for workspace in workspaces:
            count_res = supabase.table("workspace_members").select("id", count="exact").eq("workspace_id", workspace["id"]).execute()
            workspace["member_count"] = count_res.count or 0
        
        return {
            "success": True,
            "workspaces": workspaces,
            "total": len(workspaces)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list workspaces: {str(e)}")

@router.get("/workspaces/{workspace_id}")
async def get_workspace(workspace_id: str, user=Depends(get_current_user)):
    """
    Get workspace details and members
    """
    try:
        from src.db import supabase
        
        # Check if user has access to workspace
        member_res = supabase.table("workspace_members").select("*").eq("workspace_id", workspace_id).eq("user_id", user["id"]).execute()
        
        if not member_res.data:
            raise HTTPException(status_code=403, detail="Access denied to workspace")
        
        # Get workspace details
        workspace_res = supabase.table("workspaces").select("*").eq("id", workspace_id).execute()
        
        if not workspace_res.data:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        workspace = workspace_res.data[0]
        
        # Get all members
        members_res = supabase.table("workspace_members").select(
            "*, users(email, display_name)"
        ).eq("workspace_id", workspace_id).execute()
        
        members = []
        for member in members_res.data:
            user_info = member.get("users", {})
            members.append({
                "id": member["id"],
                "user_id": member["user_id"],
                "role": member["role"],
                "joined_at": member["joined_at"],
                "email": user_info.get("email"),
                "display_name": user_info.get("display_name")
            })
        
        # Get workspace documents
        docs_res = supabase.table("documents").select("*").eq("workspace_id", workspace_id).execute()
        
        return {
            "success": True,
            "workspace": {
                "id": workspace["id"],
                "name": workspace["name"],
                "description": workspace["description"],
                "owner_id": workspace["owner_id"],
                "is_public": workspace["is_public"],
                "settings": workspace["settings"],
                "created_at": workspace["created_at"]
            },
            "members": members,
            "documents": docs_res.data,
            "user_role": member_res.data[0]["role"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workspace: {str(e)}")

@router.post("/workspaces/{workspace_id}/members")
async def add_workspace_member(
    workspace_id: str,
    member: WorkspaceMember,
    user=Depends(get_current_user)
):
    """
    Add member to workspace (only owner/admin can do this)
    """
    try:
        from src.db import supabase
        
        # Check if user has admin/owner role
        member_res = supabase.table("workspace_members").select("*").eq("workspace_id", workspace_id).eq("user_id", user["id"]).execute()
        
        if not member_res.data or member_res.data[0]["role"] not in ["owner", "admin"]:
            raise HTTPException(status_code=403, detail="Only owners and admins can add members")
        
        # Check if user is already a member
        existing_res = supabase.table("workspace_members").select("*").eq("workspace_id", workspace_id).eq("user_id", member.user_id).execute()
        
        if existing_res.data:
            raise HTTPException(status_code=400, detail="User is already a member of this workspace")
        
        # Add member
        member_data = {
            "id": str(uuid.uuid4()),
            "workspace_id": workspace_id,
            "user_id": member.user_id,
            "role": member.role,
            "joined_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("workspace_members").insert(member_data).execute()
        
        return {
            "success": True,
            "message": "Member added successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add member: {str(e)}")

@router.delete("/workspaces/{workspace_id}/members/{user_id}")
async def remove_workspace_member(
    workspace_id: str,
    user_id: str,
    user=Depends(get_current_user)
):
    """
    Remove member from workspace
    """
    try:
        from src.db import supabase
        
        # Check if user has admin/owner role
        member_res = supabase.table("workspace_members").select("*").eq("workspace_id", workspace_id).eq("user_id", user["id"]).execute()
        
        if not member_res.data or member_res.data[0]["role"] not in ["owner", "admin"]:
            raise HTTPException(status_code=403, detail="Only owners and admins can remove members")
        
        # Cannot remove owner
        target_member_res = supabase.table("workspace_members").select("*").eq("workspace_id", workspace_id).eq("user_id", user_id).execute()
        
        if target_member_res.data and target_member_res.data[0]["role"] == "owner":
            raise HTTPException(status_code=400, detail="Cannot remove workspace owner")
        
        # Remove member
        supabase.table("workspace_members").delete().eq("workspace_id", workspace_id).eq("user_id", user_id).execute()
        
        return {
            "success": True,
            "message": "Member removed successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove member: {str(e)}")

@router.post("/workspaces/{workspace_id}/comments")
async def add_comment(
    workspace_id: str,
    comment: Comment,
    user=Depends(get_current_user)
):
    """
    Add comment to workspace or document
    """
    try:
        from src.db import supabase
        
        # Check if user has access to workspace
        member_res = supabase.table("workspace_members").select("*").eq("workspace_id", workspace_id).eq("user_id", user["id"]).execute()
        
        if not member_res.data:
            raise HTTPException(status_code=403, detail="Access denied to workspace")
        
        comment_id = str(uuid.uuid4())
        comment_data = {
            "id": comment_id,
            "workspace_id": workspace_id,
            "document_id": comment.document_id,
            "user_id": user["id"],
            "content": comment.content,
            "position": comment.position,
            "parent_id": comment.parent_id,
            "created_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("workspace_comments").insert(comment_data).execute()
        
        # Broadcast to workspace members
        await manager.broadcast_to_workspace(
            json.dumps({
                "type": "new_comment",
                "comment": comment_data
            }),
            workspace_id
        )
        
        return {
            "success": True,
            "comment_id": comment_id,
            "message": "Comment added successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add comment: {str(e)}")

@router.get("/workspaces/{workspace_id}/comments")
async def get_comments(
    workspace_id: str,
    document_id: Optional[str] = None,
    user=Depends(get_current_user)
):
    """
    Get comments for workspace or specific document
    """
    try:
        from src.db import supabase
        
        # Check if user has access to workspace
        member_res = supabase.table("workspace_members").select("*").eq("workspace_id", workspace_id).eq("user_id", user["id"]).execute()
        
        if not member_res.data:
            raise HTTPException(status_code=403, detail="Access denied to workspace")
        
        # Build query
        query = supabase.table("workspace_comments").select(
            "*, users(email, display_name)"
        ).eq("workspace_id", workspace_id)
        
        if document_id:
            query = query.eq("document_id", document_id)
        
        res = query.order("created_at", desc=True).execute()
        
        comments = []
        for comment in res.data:
            user_info = comment.get("users", {})
            comments.append({
                "id": comment["id"],
                "content": comment["content"],
                "position": comment["position"],
                "parent_id": comment["parent_id"],
                "created_at": comment["created_at"],
                "user": {
                    "id": comment["user_id"],
                    "email": user_info.get("email"),
                    "display_name": user_info.get("display_name")
                }
            })
        
        return {
            "success": True,
            "comments": comments,
            "total": len(comments)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get comments: {str(e)}")

@router.post("/workspaces/{workspace_id}/annotations")
async def add_annotation(
    workspace_id: str,
    annotation: Annotation,
    user=Depends(get_current_user)
):
    """
    Add annotation to document
    """
    try:
        from src.db import supabase
        
        # Check if user has access to workspace
        member_res = supabase.table("workspace_members").select("*").eq("workspace_id", workspace_id).eq("user_id", user["id"]).execute()
        
        if not member_res.data:
            raise HTTPException(status_code=403, detail="Access denied to workspace")
        
        annotation_id = str(uuid.uuid4())
        annotation_data = {
            "id": annotation_id,
            "workspace_id": workspace_id,
            "document_id": annotation.document_id,
            "user_id": user["id"],
            "type": annotation.type,
            "content": annotation.content,
            "position": annotation.position,
            "color": annotation.color,
            "created_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("workspace_annotations").insert(annotation_data).execute()
        
        # Broadcast to workspace members
        await manager.broadcast_to_workspace(
            json.dumps({
                "type": "new_annotation",
                "annotation": annotation_data
            }),
            workspace_id
        )
        
        return {
            "success": True,
            "annotation_id": annotation_id,
            "message": "Annotation added successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add annotation: {str(e)}")

@router.get("/workspaces/{workspace_id}/annotations")
async def get_annotations(
    workspace_id: str,
    document_id: Optional[str] = None,
    user=Depends(get_current_user)
):
    """
    Get annotations for workspace or specific document
    """
    try:
        from src.db import supabase
        
        # Check if user has access to workspace
        member_res = supabase.table("workspace_members").select("*").eq("workspace_id", workspace_id).eq("user_id", user["id"]).execute()
        
        if not member_res.data:
            raise HTTPException(status_code=403, detail="Access denied to workspace")
        
        # Build query
        query = supabase.table("workspace_annotations").select(
            "*, users(email, display_name)"
        ).eq("workspace_id", workspace_id)
        
        if document_id:
            query = query.eq("document_id", document_id)
        
        res = query.order("created_at", desc=True).execute()
        
        annotations = []
        for annotation in res.data:
            user_info = annotation.get("users", {})
            annotations.append({
                "id": annotation["id"],
                "type": annotation["type"],
                "content": annotation["content"],
                "position": annotation["position"],
                "color": annotation["color"],
                "created_at": annotation["created_at"],
                "user": {
                    "id": annotation["user_id"],
                    "email": user_info.get("email"),
                    "display_name": user_info.get("display_name")
                }
            })
        
        return {
            "success": True,
            "annotations": annotations,
            "total": len(annotations)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get annotations: {str(e)}")

@router.websocket("/ws/workspace/{workspace_id}")
async def websocket_endpoint(websocket: WebSocket, workspace_id: str):
    """
    WebSocket endpoint for real-time collaboration
    """
    await manager.connect(websocket, workspace_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message["type"] == "user_typing":
                # Broadcast typing indicator
                await manager.broadcast_to_workspace(
                    json.dumps({
                        "type": "user_typing",
                        "user_id": message["user_id"],
                        "document_id": message.get("document_id")
                    }),
                    workspace_id
                )
            
            elif message["type"] == "cursor_position":
                # Broadcast cursor position
                await manager.broadcast_to_workspace(
                    json.dumps({
                        "type": "cursor_position",
                        "user_id": message["user_id"],
                        "position": message["position"],
                        "document_id": message.get("document_id")
                    }),
                    workspace_id
                )
            
            elif message["type"] == "document_update":
                # Broadcast document update
                await manager.broadcast_to_workspace(
                    json.dumps({
                        "type": "document_update",
                        "user_id": message["user_id"],
                        "document_id": message["document_id"],
                        "changes": message["changes"]
                    }),
                    workspace_id
                )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, workspace_id)
        # Notify other users
        await manager.broadcast_to_workspace(
            json.dumps({
                "type": "user_disconnected",
                "workspace_id": workspace_id
            }),
            workspace_id
        )

@router.post("/workspaces/{workspace_id}/share")
async def share_workspace(
    workspace_id: str,
    share_data: Dict[str, Any],
    user=Depends(get_current_user)
):
    """
    Share workspace with external users via email
    """
    try:
        from src.db import supabase
        
        # Check if user has admin/owner role
        member_res = supabase.table("workspace_members").select("*").eq("workspace_id", workspace_id).eq("user_id", user["id"]).execute()
        
        if not member_res.data or member_res.data[0]["role"] not in ["owner", "admin"]:
            raise HTTPException(status_code=403, detail="Only owners and admins can share workspace")
        
        # Get workspace details
        workspace_res = supabase.table("workspaces").select("*").eq("id", workspace_id).execute()
        workspace = workspace_res.data[0]
        
        # Generate share link
        share_token = str(uuid.uuid4())
        share_link = f"/workspace/{workspace_id}/join?token={share_token}"
        
        # Save share token
        share_data = {
            "id": str(uuid.uuid4()),
            "workspace_id": workspace_id,
            "token": share_token,
            "created_by": user["id"],
            "expires_at": share_data.get("expires_at"),
            "max_uses": share_data.get("max_uses"),
            "used_count": 0,
            "created_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("workspace_shares").insert(share_data).execute()
        
        return {
            "success": True,
            "share_link": share_link,
            "expires_at": share_data["expires_at"],
            "max_uses": share_data["max_uses"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to share workspace: {str(e)}")

@router.get("/workspaces/{workspace_id}/activity")
async def get_workspace_activity(
    workspace_id: str,
    limit: int = 50,
    user=Depends(get_current_user)
):
    """
    Get recent activity in workspace
    """
    try:
        from src.db import supabase
        
        # Check if user has access to workspace
        member_res = supabase.table("workspace_members").select("*").eq("workspace_id", workspace_id).eq("user_id", user["id"]).execute()
        
        if not member_res.data:
            raise HTTPException(status_code=403, detail="Access denied to workspace")
        
        # Get recent comments
        comments_res = supabase.table("workspace_comments").select(
            "*, users(email, display_name)"
        ).eq("workspace_id", workspace_id).order("created_at", desc=True).limit(limit).execute()
        
        # Get recent annotations
        annotations_res = supabase.table("workspace_annotations").select(
            "*, users(email, display_name)"
        ).eq("workspace_id", workspace_id).order("created_at", desc=True).limit(limit).execute()
        
        # Combine and sort activities
        activities = []
        
        for comment in comments_res.data:
            user_info = comment.get("users", {})
            activities.append({
                "type": "comment",
                "id": comment["id"],
                "content": comment["content"],
                "created_at": comment["created_at"],
                "user": {
                    "id": comment["user_id"],
                    "email": user_info.get("email"),
                    "display_name": user_info.get("display_name")
                }
            })
        
        for annotation in annotations_res.data:
            user_info = annotation.get("users", {})
            activities.append({
                "type": "annotation",
                "id": annotation["id"],
                "content": f"Added {annotation['type']} annotation",
                "created_at": annotation["created_at"],
                "user": {
                    "id": annotation["user_id"],
                    "email": user_info.get("email"),
                    "display_name": user_info.get("display_name")
                }
            })
        
        # Sort by creation date
        activities.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "success": True,
            "activities": activities[:limit],
            "total": len(activities)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workspace activity: {str(e)}")

@router.websocket("/ws/chat/{room_id}")
async def websocket_chat(websocket: WebSocket, room_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # TODO: Broadcast to all users in room
            await websocket.send_text(f"[Echo] {data}")
    except Exception:
        await websocket.close() 