import os
import firebase_admin
from firebase_admin import credentials, auth
from dotenv import load_dotenv
from src.db import supabase

load_dotenv()

# Firebase configuration
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")
FIREBASE_PRIVATE_KEY_ID = os.getenv("FIREBASE_PRIVATE_KEY_ID", "")
FIREBASE_PRIVATE_KEY = os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n")
FIREBASE_CLIENT_EMAIL = os.getenv("FIREBASE_CLIENT_EMAIL", "")
FIREBASE_CLIENT_ID = os.getenv("FIREBASE_CLIENT_ID", "")
FIREBASE_AUTH_URI = os.getenv("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth")
FIREBASE_TOKEN_URI = os.getenv("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token")
FIREBASE_AUTH_PROVIDER_X509_CERT_URL = os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs")
FIREBASE_CLIENT_X509_CERT_URL = os.getenv("FIREBASE_CLIENT_X509_CERT_URL", "")

# Rate limiting configuration
RATE_LIMITS = {
    "/auth/register": {"requests": 5, "window": 3600},      # 5/hour
    "/auth/login": {"requests": 10, "window": 300},         # 10/5min
    "/auth/reset-password": {"requests": 3, "window": 3600}, # 3/hour
    "/auth/2fa/verify": {"requests": 5, "window": 300},     # 5/5min
    "/chat/general": {"requests": 100, "window": 3600},     # 100/hour (authenticated)
    "/chat/general/guest": {"requests": 10, "window": 3600}, # 10/hour (anonymous)
    "default": {"requests": 100, "window": 3600}            # 100/hour
}

# Password requirements
PASSWORD_REQUIREMENTS = {
    "min_length": 8,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_numbers": True,
    "require_special_chars": True,
    "max_length": 128
}

# Session configuration
SESSION_CONFIG = {
    "default_duration": 3600,  # 1 hour in seconds
    "refresh_threshold": 300,  # 5 minutes before expiry
    "max_sessions_per_user": 5
}

# Security configuration
SECURITY_CONFIG = {
    "max_failed_attempts": 10,
    "lockout_duration": 3600,  # 1 hour
    "max_2fa_attempts": 5,
    "2fa_lockout_duration": 900,  # 15 minutes
    "ip_block_duration": 86400,  # 24 hours
}

# Analytics retention policy
RETENTION_POLICY = {
    "auth_logs": "90 days",
    "user_activity": "1 year", 
    "chat_history": "2 years",
    "analytics_data": "3 years",
    "security_logs": "1 year"
}

def get_admin_email():
    """Get admin email from database"""
    try:
        res = supabase.table('admin_settings').select('setting_value').eq('setting_key', 'admin_email').execute()
        if res.data and len(res.data) > 0:
            return res.data[0]['setting_value']
        return None
    except Exception as e:
        print(f"❌ Failed to get admin email from database: {str(e)}")
        return None

def is_admin_email(email: str) -> bool:
    """Check if email is admin email"""
    try:
        admin_email = get_admin_email()
        return bool(admin_email and email == admin_email)
    except Exception:
        return False

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        # Check if Firebase is already initialized
        if not firebase_admin._apps:
            # Create credentials dictionary
            cred_dict = {
                "type": "service_account",
                "project_id": FIREBASE_PROJECT_ID,
                "private_key_id": FIREBASE_PRIVATE_KEY_ID,
                "private_key": FIREBASE_PRIVATE_KEY,
                "client_email": FIREBASE_CLIENT_EMAIL,
                "client_id": FIREBASE_CLIENT_ID,
                "auth_uri": FIREBASE_AUTH_URI,
                "token_uri": FIREBASE_TOKEN_URI,
                "auth_provider_x509_cert_url": FIREBASE_AUTH_PROVIDER_X509_CERT_URL,
                "client_x509_cert_url": FIREBASE_CLIENT_X509_CERT_URL
            }
            
            # Initialize Firebase Admin SDK
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            
            print("✅ Firebase Admin SDK initialized successfully")
            return True
        else:
            print("ℹ️ Firebase Admin SDK already initialized")
            return True
            
    except Exception as e:
        print(f"❌ Failed to initialize Firebase Admin SDK: {str(e)}")
        return False

def verify_firebase_config() -> bool:
    """Verify Firebase configuration"""
    required_vars = [
        "FIREBASE_PROJECT_ID",
        "FIREBASE_PRIVATE_KEY_ID", 
        "FIREBASE_PRIVATE_KEY",
        "FIREBASE_CLIENT_EMAIL",
        "FIREBASE_CLIENT_ID",
        "FIREBASE_CLIENT_X509_CERT_URL"
    ]
    
    missing_vars = []
    for var in required_vars:
        var_value = globals().get(var)
        if var_value is None or str(var_value).strip() == "":
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing Firebase environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ Firebase configuration verified")
    return True

# Initialize Firebase on import
if verify_firebase_config():
    initialize_firebase() 