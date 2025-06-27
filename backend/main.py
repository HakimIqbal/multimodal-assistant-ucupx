import os
import time
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

start_time = time.time()

# Load .env file
env_loaded = load_dotenv()
if env_loaded:
    print('✅ .env file loaded successfully')
else:
    print('⚠️  .env file not found or not loaded')

# Print environment info
ENV = os.getenv('ENVIRONMENT', 'development')
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 8000))
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
print(f'🌎 Environment: {ENV}')
print(f'🔌 Host: {HOST}')
print(f'🔢 Port: {PORT}')
print(f'🐞 Debug mode: {DEBUG}')

# LangSmith tracing info
LANGSMITH_TRACING = os.getenv('LANGSMITH_TRACING', 'false').lower() == 'true'
LANGSMITH_PROJECT = os.getenv('LANGSMITH_PROJECT', 'multimodal-assistant')
if LANGSMITH_TRACING:
    print(f'System: LangSmith tracing diaktifkan. Project: {LANGSMITH_PROJECT}')
else:
    print('System: LangSmith tracing tidak diaktifkan.')

try:
    from config import firebase_config
    print('✅ Firebase configuration verified')
    print('✅ Firebase Admin SDK initialized successfully')
    print('✅ Firebase Auth client initialized')
except Exception as e:
    print(f'❌ Firebase configuration/init error: {e}')

try:
    from src.db import supabase
    res = supabase.table('users').select('id').limit(1).execute()
    if hasattr(res, 'data'):
        print('✅ Supabase connection successful')
    else:
        print('⚠️  Supabase connection: No data returned')
except Exception as e:
    print(f'❌ Supabase connection failed: {e}')

try:
    from api.endpoints.performance import cache_manager
    if getattr(cache_manager, 'iron_available', False):
        print(f'✅ IronCache connected: {cache_manager.cache_name}')
    else:
        print('⚠️  IronCache not available, using in-memory cache')
except Exception as e:
    print(f'❌ IronCache init error: {e}')

# Pinecone check (if used)
try:
    import pinecone
    pinecone_api_key = os.getenv('PINECONE_API_KEY', '')
    if pinecone_api_key:
        print('✅ Pinecone API key found')
    else:
        print('⚠️  Pinecone API key not set')
except Exception as e:
    print(f'❌ Pinecone import error: {e}')

# AI Model API keys check
groq_key = os.getenv('GROQ_API_KEY', '')
gemini_key = os.getenv('GEMINI_API_KEY', '')
openrouter_key = os.getenv('OPENROUTER_API_KEY', '')
if groq_key:
    print('✅ Groq API key found')
else:
    print('⚠️  Groq API key not set')
if gemini_key:
    print('✅ Gemini API key found')
else:
    print('⚠️  Gemini API key not set')
if openrouter_key:
    print('✅ OpenRouter API key found')
else:
    print('⚠️  OpenRouter API key not set')

gdrive_token = os.getenv('GOOGLE_DRIVE_TOKEN', '')
if gdrive_token:
    print('✅ Google Drive token found and loaded')
else:
    print('⚠️  Google Drive token not set or not found')

from api.server import app
from dotenv import load_dotenv
import uvicorn

startup_time = time.time() - start_time
print(f'🚀 Startup complete in {startup_time:.2f} seconds')

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)