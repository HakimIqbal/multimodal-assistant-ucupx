# Webhook/Event Skeleton
from fastapi import APIRouter, Request, HTTPException

router = APIRouter()

@router.post("/event")
async def receive_event(request: Request):
    data = await request.json()
    event_type = data.get("event_type")
    if not event_type:
        raise HTTPException(status_code=400, detail="event_type required")
    # TODO: Simpan event ke Supabase/log
    print(f"[Webhook] Event received: {event_type}")
    return {"status": "received", "event_type": event_type} 