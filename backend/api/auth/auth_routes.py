from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict
import uuid
from datetime import datetime, timedelta
from src.auth.firebase_client import firebase_client
from api.auth.auth_middleware import auth_middleware
from src.db import supabase

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Pydantic models
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    username: Optional[str] = None
    confirm_password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

class ProfileUpdateRequest(BaseModel):
    username: Optional[str] = None
    avatar_url: Optional[str] = None

class TwoFactorEnableRequest(BaseModel):
    code: str

class TwoFactorVerifyRequest(BaseModel):
    code: str

# =====================================================
# REGISTRATION & LOGIN
# =====================================================

@router.post("/register")
async def register(request: RegisterRequest, req: Request):
    """Register new user"""
    try:
        # Rate limiting
        await auth_middleware.check_rate_limit(req, "/auth/register")
        
        # Validate password confirmation
        if request.password != request.confirm_password:
            await auth_middleware.log_auth_action(
                None, "register", False, req, "Password confirmation mismatch"
            )
            raise HTTPException(status_code=400, detail="Passwords do not match")
        
        # Validate password strength
        if not validate_password(request.password):
            await auth_middleware.log_auth_action(
                None, "register", False, req, "Weak password"
            )
            raise HTTPException(status_code=400, detail="Password does not meet requirements")
        
        # Check if user already exists
        existing_user = firebase_client.get_user_by_email(request.email)
        if existing_user:
            await auth_middleware.log_auth_action(
                None, "register", False, req, "Email already exists"
            )
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user in Firebase
        display_name = request.username or request.email.split('@')[0]
        user_record = firebase_client.create_user(
            email=request.email,
            password=request.password,
            display_name=display_name
        )
        
        if not user_record:
            await auth_middleware.log_auth_action(
                None, "register", False, req, "Firebase user creation failed"
            )
            raise HTTPException(status_code=500, detail="Failed to create user")
        
        # Log successful registration
        await auth_middleware.log_auth_action(
            user_record['uid'], "register", True, req
        )
        
        return {
            "success": True,
            "message": "User registered successfully",
            "user": {
                "uid": user_record['uid'],
                "email": user_record['email'],
                "username": display_name,
                "email_verified": user_record['email_verified']
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        await auth_middleware.log_auth_action(
            None, "register", False, req, str(e)
        )
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/login")
async def login(request: LoginRequest, req: Request):
    """User login"""
    try:
        # Rate limiting
        await auth_middleware.check_rate_limit(req, "/auth/login")
        
        # Note: Firebase Admin SDK doesn't support email/password authentication
        # This would typically be handled by Firebase Auth UI on the client side
        # For now, we'll return a message indicating client-side authentication is required
        
        return {
            "success": True,
            "message": "Please use Firebase Auth UI for login",
            "note": "Email/password authentication should be handled on the client side using Firebase Auth UI"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        await auth_middleware.log_auth_action(
            None, "login", False, req, str(e)
        )
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/logout")
async def logout(req: Request, user: Dict = Depends(auth_middleware.get_current_user)):
    """User logout"""
    try:
        # Revoke refresh tokens
        firebase_client.revoke_refresh_tokens(user['uid'])
        
        # Log logout action
        await auth_middleware.log_auth_action(
            user['uid'], "logout", True, req
        )
        
        return {
            "success": True,
            "message": "Logged out successfully"
        }
        
    except Exception as e:
        print(f"❌ Logout error: {str(e)}")
        await auth_middleware.log_auth_action(
            user['uid'], "logout", False, req, str(e)
        )
        raise HTTPException(status_code=500, detail="Logout failed")

# =====================================================
# PASSWORD MANAGEMENT
# =====================================================

@router.post("/reset-password")
async def reset_password(request: PasswordResetRequest, req: Request):
    """Send password reset email"""
    try:
        # Rate limiting
        await auth_middleware.check_rate_limit(req, "/auth/reset-password")
        
        # Check if user exists
        user_record = firebase_client.get_user_by_email(request.email)
        if not user_record:
            # Don't reveal if email exists or not
            return {
                "success": True,
                "message": "If the email exists, a password reset link has been sent"
            }
        
        # Send password reset email
        # Note: This would typically be done from the client side
        success = firebase_client.send_password_reset_email(request.email)
        
        if success:
            await auth_middleware.log_auth_action(
                user_record['uid'], "reset_password_sent", True, req
            )
            return {
                "success": True,
                "message": "Password reset email sent"
            }
        else:
            await auth_middleware.log_auth_action(
                user_record['uid'], "reset_password_sent", False, req, "Failed to send email"
            )
            raise HTTPException(status_code=500, detail="Failed to send reset email")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Password reset error: {str(e)}")
        await auth_middleware.log_auth_action(
            None, "reset_password_sent", False, req, str(e)
        )
        raise HTTPException(status_code=500, detail="Password reset failed")

@router.post("/change-password")
async def change_password(request: PasswordChangeRequest, req: Request, user: Dict = Depends(auth_middleware.get_current_user)):
    """Change user password"""
    try:
        # Validate password confirmation
        if request.new_password != request.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")
        
        # Validate password strength
        if not validate_password(request.new_password):
            raise HTTPException(status_code=400, detail="Password does not meet requirements")
        
        # Note: Firebase Admin SDK doesn't support password changes with current password verification
        # This would typically be handled by Firebase Auth UI on the client side
        
        await auth_middleware.log_auth_action(
            user['uid'], "password_change", True, req
        )
        
        return {
            "success": True,
            "message": "Please use Firebase Auth UI to change password",
            "note": "Password changes should be handled on the client side using Firebase Auth UI"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Password change error: {str(e)}")
        await auth_middleware.log_auth_action(
            user['uid'], "password_change", False, req, str(e)
        )
        raise HTTPException(status_code=500, detail="Password change failed")

# =====================================================
# PROFILE MANAGEMENT
# =====================================================

@router.get("/profile")
async def get_profile(user: Dict = Depends(auth_middleware.get_current_user)):
    """Get user profile"""
    try:
        # Get user data from database
        user_data = await auth_middleware.get_user_from_db(user['uid'])
        
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "success": True,
            "profile": {
                "uid": user['uid'],
                "email": user['email'],
                "username": user_data.get('username', ''),
                "role": user_data.get('role', 'user'),
                "avatar_url": user_data.get('avatar_url'),
                "email_verified": user['email_verified'],
                "two_factor_enabled": user_data.get('two_factor_enabled', False),
                "last_login": user_data.get('last_login'),
                "login_count": user_data.get('login_count', 0),
                "created_at": user_data.get('created_at')
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Get profile error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get profile")

@router.put("/profile")
async def update_profile(request: ProfileUpdateRequest, req: Request, user: Dict = Depends(auth_middleware.get_current_user)):
    """Update user profile"""
    try:
        update_data = {}
        
        if request.username is not None:
            # Check if username is already taken
            if request.username != user.get('username', ''):
                existing = supabase.table('users').select('username').eq('username', request.username).execute()
                if existing.data and len(existing.data) > 0:
                    raise HTTPException(status_code=400, detail="Username already taken")
            update_data['username'] = request.username
        
        if request.avatar_url is not None:
            update_data['avatar_url'] = request.avatar_url
        
        if update_data:
            # Update in database
            res = supabase.table('users').update(update_data).eq('id', user['uid']).execute()
            if getattr(res, 'error', None):
                raise HTTPException(status_code=500, detail="Failed to update profile")
            
            # Update in Firebase if display name changed
            if 'username' in update_data:
                firebase_client.update_user(user['uid'], display_name=update_data['username'])
        
        await auth_middleware.log_auth_action(
            user['uid'], "profile_update", True, req
        )
        
        return {
            "success": True,
            "message": "Profile updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Update profile error: {str(e)}")
        await auth_middleware.log_auth_action(
            user['uid'], "profile_update", False, req, str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to update profile")

# =====================================================
# TWO-FACTOR AUTHENTICATION
# =====================================================

@router.post("/2fa/setup")
async def setup_2fa(req: Request, user: Dict = Depends(auth_middleware.get_current_user)):
    """Setup 2FA for user"""
    try:
        # Generate 2FA secret
        import pyotp
        secret = pyotp.random_base32()
        
        # Generate QR code
        import qrcode
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user['email'],
            issuer_name="Multimodal Assistant"
        )
        
        # Store secret temporarily (should be encrypted in production)
        # For now, we'll store it in the database
        res = supabase.table('users').update({
            'two_factor_secret': secret
        }).eq('id', user['uid']).execute()
        
        if getattr(res, 'error', None):
            raise HTTPException(status_code=500, detail="Failed to setup 2FA")
        
        await auth_middleware.log_auth_action(
            user['uid'], "2fa_setup", True, req
        )
        
        return {
            "success": True,
            "message": "2FA setup initiated",
            "secret": secret,
            "qr_code_uri": provisioning_uri,
            "note": "Use Google Authenticator or similar app to scan the QR code"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 2FA setup error: {str(e)}")
        await auth_middleware.log_auth_action(
            user['uid'], "2fa_setup", False, req, str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to setup 2FA")

@router.post("/2fa/enable")
async def enable_2fa(request: TwoFactorEnableRequest, req: Request, user: Dict = Depends(auth_middleware.get_current_user)):
    """Enable 2FA after verification"""
    try:
        # Get stored secret
        user_data = await auth_middleware.get_user_from_db(user['uid'])
        if not user_data or not user_data.get('two_factor_secret'):
            raise HTTPException(status_code=400, detail="2FA not setup")
        
        # Verify code
        import pyotp
        totp = pyotp.TOTP(user_data['two_factor_secret'])
        if not totp.verify(request.code):
            await auth_middleware.log_auth_action(
                user['uid'], "2fa_enable", False, req, "Invalid 2FA code"
            )
            raise HTTPException(status_code=400, detail="Invalid 2FA code")
        
        # Enable 2FA
        res = supabase.table('users').update({
            'two_factor_enabled': True
        }).eq('id', user['uid']).execute()
        
        if getattr(res, 'error', None):
            raise HTTPException(status_code=500, detail="Failed to enable 2FA")
        
        await auth_middleware.log_auth_action(
            user['uid'], "2fa_enable", True, req
        )
        
        return {
            "success": True,
            "message": "2FA enabled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 2FA enable error: {str(e)}")
        await auth_middleware.log_auth_action(
            user['uid'], "2fa_enable", False, req, str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to enable 2FA")

@router.post("/2fa/disable")
async def disable_2fa(request: TwoFactorVerifyRequest, req: Request, user: Dict = Depends(auth_middleware.get_current_user)):
    """Disable 2FA"""
    try:
        # Get stored secret
        user_data = await auth_middleware.get_user_from_db(user['uid'])
        if not user_data or not user_data.get('two_factor_secret'):
            raise HTTPException(status_code=400, detail="2FA not enabled")
        
        # Verify code
        import pyotp
        totp = pyotp.TOTP(user_data['two_factor_secret'])
        if not totp.verify(request.code):
            await auth_middleware.log_auth_action(
                user['uid'], "2fa_disable", False, req, "Invalid 2FA code")
            raise HTTPException(status_code=400, detail="Invalid 2FA code")
        
        # Disable 2FA
        res = supabase.table('users').update({
            'two_factor_enabled': False,
            'two_factor_secret': None
        }).eq('id', user['uid']).execute()
        
        if getattr(res, 'error', None):
            raise HTTPException(status_code=500, detail="Failed to disable 2FA")
        
        await auth_middleware.log_auth_action(
            user['uid'], "2fa_disable", True, req
        )
        
        return {
            "success": True,
            "message": "2FA disabled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 2FA disable error: {str(e)}")
        await auth_middleware.log_auth_action(
            user['uid'], "2fa_disable", False, req, str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to disable 2FA")

# =====================================================
# UTILITY FUNCTIONS
# =====================================================

def validate_password(password: str) -> bool:
    """Validate password strength"""
    from config.firebase_config import PASSWORD_REQUIREMENTS
    
    if len(password) < PASSWORD_REQUIREMENTS['min_length']:
        return False
    
    if len(password) > PASSWORD_REQUIREMENTS['max_length']:
        return False
    
    if PASSWORD_REQUIREMENTS['require_uppercase'] and not any(c.isupper() for c in password):
        return False
    
    if PASSWORD_REQUIREMENTS['require_lowercase'] and not any(c.islower() for c in password):
        return False
    
    if PASSWORD_REQUIREMENTS['require_numbers'] and not any(c.isdigit() for c in password):
        return False
    
    if PASSWORD_REQUIREMENTS['require_special_chars'] and not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
        return False
    
    return True 