from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import time
from datetime import datetime, timedelta, timezone
import hashlib
import json
from src.auth.firebase_client import firebase_client
from src.db import supabase
from config.firebase_config import RATE_LIMITS, SECURITY_CONFIG, is_admin_email

security = HTTPBearer()

class AuthMiddleware:
    """Authentication and Security Middleware"""
    
    def __init__(self):
        self.rate_limit_cache = {}
        self.ip_block_cache = {}
    
    async def verify_token(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """Verify Firebase JWT token"""
        try:
            token = credentials.credentials
            decoded_token = firebase_client.verify_id_token(token)
            
            if not decoded_token:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            # Check if user is disabled
            user_record = firebase_client.get_user(decoded_token['uid'])
            if user_record and user_record.get('disabled'):
                raise HTTPException(status_code=401, detail="Account disabled")
            
            # Check if user is locked
            user_data = await self.get_user_from_db(decoded_token['uid'])
            if user_data and user_data.get('locked_until'):
                if datetime.fromisoformat(user_data['locked_until'].replace('Z', '+00:00')) > datetime.now(timezone.utc):
                    raise HTTPException(status_code=401, detail="Account temporarily locked")
            
            return decoded_token
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"❌ Token verification error: {str(e)}")
            raise HTTPException(status_code=401, detail="Authentication failed")
    
    async def get_current_user(self, token: Dict[str, Any] = Depends(verify_token)) -> Dict[str, Any]:
        """Get current authenticated user"""
        try:
            uid = token['uid']
            user_data = await self.get_user_from_db(uid)
            
            if not user_data:
                # Create user in database if not exists
                user_data = await self.create_user_in_db(token)
            
            # Update last login
            await self.update_last_login(uid)
            
            return {
                'uid': uid,
                'email': token.get('email', ''),
                'username': user_data.get('username', '') if user_data else '',
                'role': user_data.get('role', 'user') if user_data else 'user',
                'email_verified': token.get('email_verified', False),
                'custom_claims': token.get('custom_claims', {})
            }
            
        except Exception as e:
            print(f"❌ Get current user error: {str(e)}")
            raise HTTPException(status_code=401, detail="User not found")
    
    async def require_admin(self, user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        """Require admin privileges"""
        if user.get('role') != 'admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        return user
    
    async def require_role(self, required_role: str):
        """Require specific role"""
        async def role_checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
            if user.get('role') != required_role:
                raise HTTPException(status_code=403, detail=f"{required_role.title()} access required")
            return user
        return role_checker
    
    async def check_rate_limit(self, request: Request, endpoint: Optional[str] = None) -> bool:
        """Check rate limiting for IP address"""
        try:
            ip_address = request.client.host if request.client else 'unknown'
            endpoint_str = str(endpoint) if endpoint is not None else request.url.path
            
            # Check if IP is blocked
            if await self.is_ip_blocked(ip_address):
                raise HTTPException(status_code=429, detail="IP address blocked")
            
            # Get rate limit config
            rate_limit = RATE_LIMITS.get(endpoint_str, RATE_LIMITS['default'])
            max_requests = rate_limit['requests']
            window = rate_limit['window']
            
            # Check current window
            window_start = datetime.now() - timedelta(seconds=window)
            
            # Get current request count
            current_count = await self.get_rate_limit_count(ip_address, endpoint_str, window_start)
            
            if current_count >= max_requests:
                # Block IP if too many requests
                await self.block_ip(ip_address, "rate_limit_exceeded")
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            
            # Increment request count
            await self.increment_rate_limit(ip_address, endpoint_str)
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"❌ Rate limit check error: {str(e)}")
            return True  # Allow request if rate limiting fails
    
    async def log_auth_action(self, user_id: Optional[str], action: str, success: bool, 
                            request: Request, error_message: Optional[str] = None) -> None:
        """Log authentication action"""
        try:
            data = {
                'user_id': user_id,
                'session_type': 'user',
                'action': action,
                'ip_address': request.client.host if request.client else 'unknown',
                'user_agent': request.headers.get('user-agent', ''),
                'success': success,
                'error_message': error_message,
                'metadata': {
                    'endpoint': request.url.path,
                    'method': request.method,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
            
            supabase.table('auth_logs').insert(data).execute()
                
        except Exception as e:
            print(f"❌ Auth logging error: {str(e)}")
    
    async def get_user_from_db(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get user from database"""
        try:
            res = supabase.table('users').select('*').eq('id', uid).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
            return None
        except Exception as e:
            print(f"❌ Get user from DB error: {str(e)}")
            return None
    
    async def create_user_in_db(self, token: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create user in database"""
        try:
            uid = token['uid']
            email = token.get('email', '')
            
            # Generate username from email
            username = email.split('@')[0] if email else f"user_{uid[:8]}"
            
            # Check if username exists
            existing = supabase.table('users').select('username').eq('username', username).execute()
            if existing.data and len(existing.data) > 0:
                username = f"{username}_{uid[:4]}"
            
            # Check if user is admin
            role = 'admin' if is_admin_email(email) else 'user'
            
            data = {
                'id': uid,
                'username': username,
                'email': email,
                'role': role,
                'email_verified': token.get('email_verified', False),
                'providers': token.get('firebase', {}).get('sign_in_provider', 'email'),
                'last_login': datetime.utcnow().isoformat(),
                'login_count': 1,
                'ip_addresses': [token.get('firebase', {}).get('sign_in_provider', '')]
            }
            
            supabase.table('users').insert(data).execute()
            return data
            
        except Exception as e:
            print(f"❌ Create user in DB error: {str(e)}")
            return None
    
    async def update_last_login(self, uid: str) -> None:
        """Update user's last login"""
        try:
            # Simple increment approach since RPC might not be available
            res = supabase.table('users').select('login_count').eq('id', uid).execute()
            if res.data and len(res.data) > 0:
                current_count = res.data[0].get('login_count', 0)
                data = {
                    'last_login': datetime.utcnow().isoformat(),
                    'login_count': current_count + 1
                }
                
                supabase.table('users').update(data).eq('id', uid).execute()
                
        except Exception as e:
            print(f"❌ Update last login error: {str(e)}")
    
    async def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP address is blocked"""
        try:
            res = supabase.table('ip_blocklist').select('*').eq('ip_address', ip_address).execute()
            if res.data and len(res.data) > 0:
                block_data = res.data[0]
                blocked_until = datetime.fromisoformat(block_data['blocked_until'].replace('Z', '+00:00'))
                if blocked_until > datetime.now(timezone.utc):
                    return True
                else:
                    # Remove expired block
                    supabase.table('ip_blocklist').delete().eq('ip_address', ip_address).execute()
            return False
        except Exception as e:
            print(f"❌ IP block check error: {str(e)}")
            return False
    
    async def block_ip(self, ip_address: str, reason: str) -> None:
        """Block IP address"""
        try:
            block_duration = SECURITY_CONFIG['ip_block_duration']
            blocked_until = datetime.now(timezone.utc) + timedelta(seconds=block_duration)
            
            data = {
                'ip_address': ip_address,
                'reason': reason,
                'blocked_until': blocked_until.isoformat(),
                'created_at': datetime.utcnow().isoformat()
            }
            
            supabase.table('ip_blocklist').upsert(data).execute()
                
        except Exception as e:
            print(f"❌ Block IP error: {str(e)}")
    
    async def get_rate_limit_count(self, ip_address: str, endpoint: str, window_start: datetime) -> int:
        """Get current rate limit count for IP and endpoint"""
        try:
            res = supabase.table('rate_limits').select('count').eq('ip_address', ip_address).eq('endpoint', endpoint).gte('created_at', window_start.isoformat()).execute()
            if res.data:
                return sum(item['count'] for item in res.data)
            return 0
        except Exception as e:
            print(f"❌ Get rate limit count error: {str(e)}")
            return 0
    
    async def increment_rate_limit(self, ip_address: str, endpoint: str) -> None:
        """Increment rate limit counter"""
        try:
            data = {
                'ip_address': ip_address,
                'endpoint': endpoint,
                'count': 1,
                'created_at': datetime.utcnow().isoformat()
            }
            
            supabase.table('rate_limits').insert(data).execute()
                
        except Exception as e:
            print(f"❌ Increment rate limit error: {str(e)}")

# Create middleware instance
auth_middleware = AuthMiddleware()

# Export commonly used functions
get_current_user = auth_middleware.get_current_user
require_admin = auth_middleware.require_admin
require_role = auth_middleware.require_role 