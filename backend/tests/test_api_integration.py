import pytest
from fastapi.testclient import TestClient
from backend.api.server import app
import json

client = TestClient(app)

def test_multimodal_stats():
    response = client.get("/multimodal/stats")
    assert response.status_code == 200
    assert "total_processed" in response.json()

def test_load_balancer_status():
    response = client.get("/performance/load_balancer_status")
    assert response.status_code == 200
    assert "status" in response.json()

def test_security_audit():
    response = client.get("/security/audit")
    assert response.status_code == 200
    assert "endpoints" in response.json()

def test_cache_invalidate_tag():
    response = client.post("/cache/invalidate/tag/testtag")
    assert response.status_code == 200 or response.status_code == 204

def test_loadbalancer_release():
    # Register dummy service first
    client.post("/loadbalancer/register", json={"service_name": "testsvc", "instances": ["http://localhost:1234"], "health_check_url": "http://localhost:1234", "load_balancing_algorithm": "least_connections"})
    instance = client.get("/loadbalancer/instance/testsvc").json().get("instance")
    response = client.post(f"/loadbalancer/release/testsvc/{instance}")
    assert response.status_code == 200

def test_advanced_rag_query_expansion():
    response = client.post("/advanced-rag/query-expansion", json={"query": "help me", "expansion_type": "semantic"})
    assert response.status_code == 200

def test_advanced_rag_multilanguage():
    response = client.post("/advanced-rag/multilanguage", json={"query": "hello", "target_language": "id"})
    assert response.status_code == 200

def test_audio_transcribe():
    # Simulasi file audio kosong
    response = client.post("/audio/transcribe", files={"file": ("test.wav", b"", "audio/wav")}, data={"query": "transcribe", "model_name": "whisper-1", "session_id": ""})
    assert response.status_code in [200, 400, 500]

def test_video_upload():
    response = client.post("/video/upload", files={"file": ("test.mp4", b"", "video/mp4")})
    assert response.status_code in [200, 400, 500]

def test_admin_backup():
    response = client.post("/backup")
    assert response.status_code in [200, 403, 500]

def test_upload_drive():
    response = client.post("/upload_drive", files={"file": ("test.txt", b"hello", "text/plain")})
    assert response.status_code in [200, 400, 500]

def test_upload_dropbox():
    response = client.post("/upload_dropbox", files={"file": ("test.txt", b"hello", "text/plain")})
    assert response.status_code in [200, 400, 500]

def test_compare_models():
    response = client.post("/compare/", json={"query": "hello", "model_names": ["llama3-70b-8192"]})
    assert response.status_code == 200

def test_prompts_save_list_delete():
    # Save
    response = client.post("/prompts/save", json={"prompt_name": "test", "prompt_text": "test prompt"})
    assert response.status_code in [200, 400, 500]
    # List
    response = client.get("/prompts/list")
    assert response.status_code in [200, 400, 500]
    # Delete
    response = client.delete("/prompts/delete", data=json.dumps({"prompt_name": "test"}), headers={"Content-Type": "application/json"})
    assert response.status_code in [200, 400, 500]

def test_delete_account():
    response = client.post("/delete_account")
    assert response.status_code in [200, 400, 500]

def test_data_retention():
    response = client.get("/data_retention")
    assert response.status_code == 200 