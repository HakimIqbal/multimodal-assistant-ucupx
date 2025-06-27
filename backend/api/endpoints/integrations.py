from fastapi import APIRouter
import httpx
router = APIRouter()

@router.post("/integrations/test")
async def test_integration(service: str):
    """
    Test third-party integration by making a simple GET request to the service URL.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(service)
            return {"success": True, "service": service, "status_code": response.status_code, "message": "Integration test successful"}
    except Exception as e:
        return {"success": False, "service": service, "error": str(e), "message": "Integration test failed"} 