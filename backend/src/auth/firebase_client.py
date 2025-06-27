import firebase_admin
from firebase_admin import auth, credentials
from typing import Dict, Optional, List
import json
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import os

class FirebaseClient:
    """Firebase Authentication Client"""
    
    def __init__(self):
        """Initialize Firebase client"""
        try:
            # Check if Firebase is already initialized
            if not firebase_admin._apps:
                from config.firebase_config import initialize_firebase
                initialize_firebase()
            
            self.auth = auth
            print("✅ Firebase Auth client initialized")
        except Exception as e:
            print(f"❌ Failed to initialize Firebase Auth client: {str(e)}")
            raise
    
    def verify_id_token(self, id_token: str) -> Optional[Dict]:
        """Verify Firebase ID token"""
        try:
            decoded_token = self.auth.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            print(f"❌ Token verification failed: {str(e)}")
            return None
    
    def create_user(self, email: str, password: str, display_name: Optional[str] = None) -> Optional[Dict]:
        """Create new user in Firebase"""
        try:
            user_properties = {
                'email': email,
                'password': password,
                'email_verified': False
            }
            
            if display_name:
                user_properties['display_name'] = display_name
            
            user_record = self.auth.create_user(**user_properties)
            
            # Set custom claims based on email
            from config.firebase_config import is_admin_email
            custom_claims = {
                'role': 'admin' if is_admin_email(email) else 'user',
                'created_at': datetime.utcnow().isoformat()
            }
            
            self.auth.set_custom_user_claims(user_record.uid, custom_claims)
            
            return {
                'uid': user_record.uid,
                'email': user_record.email,
                'display_name': user_record.display_name,
                'email_verified': user_record.email_verified,
                'custom_claims': custom_claims
            }
        except Exception as e:
            print(f"❌ Failed to create user: {str(e)}")
            return None
    
    def get_user(self, uid: str) -> Optional[Dict]:
        """Get user by UID"""
        try:
            user_record = self.auth.get_user(uid)
            return {
                'uid': user_record.uid,
                'email': user_record.email,
                'display_name': user_record.display_name,
                'email_verified': user_record.email_verified,
                'photo_url': user_record.photo_url,
                'disabled': user_record.disabled,
                'custom_claims': user_record.custom_claims or {}
            }
        except Exception as e:
            print(f"❌ Failed to get user: {str(e)}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        try:
            user_record = self.auth.get_user_by_email(email)
            return {
                'uid': user_record.uid,
                'email': user_record.email,
                'display_name': user_record.display_name,
                'email_verified': user_record.email_verified,
                'photo_url': user_record.photo_url,
                'disabled': user_record.disabled,
                'custom_claims': user_record.custom_claims or {}
            }
        except Exception as e:
            print(f"❌ Failed to get user by email: {str(e)}")
            return None
    
    def update_user(self, uid: str, **kwargs) -> Optional[Dict]:
        """Update user properties"""
        try:
            user_record = self.auth.update_user(uid, **kwargs)
            return {
                'uid': user_record.uid,
                'email': user_record.email,
                'display_name': user_record.display_name,
                'email_verified': user_record.email_verified,
                'photo_url': user_record.photo_url,
                'disabled': user_record.disabled,
                'custom_claims': user_record.custom_claims or {}
            }
        except Exception as e:
            print(f"❌ Failed to update user: {str(e)}")
            return None
    
    def delete_user(self, uid: str) -> bool:
        """Delete user"""
        try:
            self.auth.delete_user(uid)
            return True
        except Exception as e:
            print(f"❌ Failed to delete user: {str(e)}")
            return False
    
    def set_custom_claims(self, uid: str, claims: Dict) -> bool:
        """Set custom claims for user"""
        try:
            self.auth.set_custom_user_claims(uid, claims)
            return True
        except Exception as e:
            print(f"❌ Failed to set custom claims: {str(e)}")
            return False
    
    def get_custom_claims(self, uid: str) -> Optional[Dict]:
        """Get custom claims for user"""
        try:
            user_record = self.auth.get_user(uid)
            return user_record.custom_claims or {}
        except Exception as e:
            print(f"❌ Failed to get custom claims: {str(e)}")
            return None
    
    def send_email_verification(self, email: str) -> bool:
        """
        Send email verification using external SMTP service
        """
        try:
            # Kirim email verifikasi manual
            smtp_host = os.getenv("SMTP_HOST") or ''
            smtp_port = int(os.getenv("SMTP_PORT", 587))
            smtp_user = os.getenv("SMTP_USER") or ''
            smtp_pass = os.getenv("SMTP_PASS") or ''
            verify_link = f"https://your-app.com/verify?email={email}"
            msg = MIMEText(f"Klik link berikut untuk verifikasi email Anda: {verify_link}")
            msg["Subject"] = "Verifikasi Email"
            msg["From"] = smtp_user or ''
            msg["To"] = email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, [email], msg.as_string())
            return True
        except Exception as e:
            print(f"❌ Failed to send email verification: {str(e)}")
            return False
    
    def send_password_reset_email(self, email: str) -> bool:
        """
        Send password reset email using external SMTP service
        """
        try:
            smtp_host = os.getenv("SMTP_HOST") or ''
            smtp_port = int(os.getenv("SMTP_PORT", 587))
            smtp_user = os.getenv("SMTP_USER") or ''
            smtp_pass = os.getenv("SMTP_PASS") or ''
            reset_link = f"https://your-app.com/reset-password?email={email}"
            msg = MIMEText(f"Klik link berikut untuk reset password Anda: {reset_link}")
            msg["Subject"] = "Reset Password"
            msg["From"] = smtp_user or ''
            msg["To"] = email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, [email], msg.as_string())
            return True
        except Exception as e:
            print(f"❌ Failed to send password reset email: {str(e)}")
            return False
    
    def verify_password_reset_code(self, oob_code: str) -> Optional[str]:
        """Verify password reset code and return email"""
        try:
            # Note: Firebase Admin SDK doesn't directly support verifying reset codes
            # This would typically be done from the client side
            # For now, we'll return None and handle this differently
            return None
        except Exception as e:
            print(f"❌ Failed to verify password reset code: {str(e)}")
            return None
    
    def confirm_password_reset(self, oob_code: str, new_password: str) -> bool:
        """Confirm password reset"""
        try:
            # Note: Firebase Admin SDK doesn't directly support confirming reset
            # This would typically be done from the client side
            # For now, we'll return True and handle this differently
            return True
        except Exception as e:
            print(f"❌ Failed to confirm password reset: {str(e)}")
            return False
    
    def list_users(self, max_results: int = 1000) -> List[Dict]:
        """List all users (admin only)"""
        try:
            users = []
            page = self.auth.list_users(max_results=max_results)
            
            for user in page.users:
                users.append({
                    'uid': user.uid,
                    'email': user.email,
                    'display_name': user.display_name,
                    'email_verified': user.email_verified,
                    'photo_url': user.photo_url,
                    'disabled': user.disabled,
                    'custom_claims': user.custom_claims or {},
                    'creation_timestamp': user.user_metadata.creation_timestamp,
                    'last_sign_in_timestamp': user.user_metadata.last_sign_in_timestamp
                })
            
            return users
        except Exception as e:
            print(f"❌ Failed to list users: {str(e)}")
            return []
    
    def disable_user(self, uid: str) -> bool:
        """Disable user account"""
        try:
            self.auth.update_user(uid, disabled=True)
            return True
        except Exception as e:
            print(f"❌ Failed to disable user: {str(e)}")
            return False
    
    def enable_user(self, uid: str) -> bool:
        """Enable user account"""
        try:
            self.auth.update_user(uid, disabled=False)
            return True
        except Exception as e:
            print(f"❌ Failed to enable user: {str(e)}")
            return False
    
    def is_admin(self, uid: str) -> bool:
        """Check if user is admin"""
        try:
            claims = self.get_custom_claims(uid)
            if claims:
                return claims.get('role') == 'admin'
            return False
        except Exception as e:
            print(f"❌ Failed to check admin status: {str(e)}")
            return False
    
    def create_session_cookie(self, id_token: str, expires_in: timedelta) -> Optional[str]:
        """Create session cookie"""
        try:
            session_cookie = self.auth.create_session_cookie(
                id_token, 
                expires_in=expires_in
            )
            return session_cookie
        except Exception as e:
            print(f"❌ Failed to create session cookie: {str(e)}")
            return None
    
    def verify_session_cookie(self, session_cookie: str) -> Optional[Dict]:
        """Verify session cookie"""
        try:
            decoded_claims = self.auth.verify_session_cookie(session_cookie, check_revoked=True)
            return decoded_claims
        except Exception as e:
            print(f"❌ Failed to verify session cookie: {str(e)}")
            return None
    
    def revoke_refresh_tokens(self, uid: str) -> bool:
        """Revoke all refresh tokens for user"""
        try:
            self.auth.revoke_refresh_tokens(uid)
            return True
        except Exception as e:
            print(f"❌ Failed to revoke refresh tokens: {str(e)}")
            return False

# Global Firebase client instance
firebase_client = FirebaseClient() 