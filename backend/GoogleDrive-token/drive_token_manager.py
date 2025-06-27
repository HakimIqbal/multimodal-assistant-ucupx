import os
import json
import requests
from datetime import datetime, timedelta

# Path ke client_secret.json dan token.json
CLIENT_SECRET_FILE = 'client_secret_237423433593-54tf0mk8dsi15e54vg6ah6kld5eip0cd.apps.googleusercontent.com.json'
TOKEN_FILE = 'token.json'  # Simpan hasil get_drive_token.py ke sini

class DriveTokenManager:
    def __init__(self):
        self.client_id, self.client_secret = self._load_client_secret()
        self.token_data = self._load_token()
        self.access_token = self.token_data.get('access_token')
        self.refresh_token = self.token_data.get('refresh_token')
        self.expiry = self._parse_expiry(self.token_data.get('expiry'))

    def _load_client_secret(self):
        with open(CLIENT_SECRET_FILE, 'r') as f:
            data = json.load(f)
            web = data['web']
            return web['client_id'], web['client_secret']

    def _load_token(self):
        if not os.path.exists(TOKEN_FILE):
            raise FileNotFoundError(f"{TOKEN_FILE} not found. Jalankan get_drive_token.py dulu!")
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)

    def _parse_expiry(self, expiry_str):
        if not expiry_str:
            return None
        try:
            return datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
        except Exception:
            return None

    def is_expired(self, buffer_seconds=60):
        if not self.expiry:
            return True
        return datetime.utcnow() + timedelta(seconds=buffer_seconds) > self.expiry

    def refresh_access_token(self):
        print('[DriveTokenManager] Refreshing access token...')
        token_url = 'https://oauth2.googleapis.com/token'
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token'
        }
        response = requests.post(token_url, data=payload)
        if response.status_code == 200:
            tokens = response.json()
            self.access_token = tokens['access_token']
            # Google tidak selalu mengembalikan expiry, default 1 jam
            expires_in = tokens.get('expires_in', 3600)
            self.expiry = datetime.utcnow() + timedelta(seconds=expires_in)
            # Update token file
            self.token_data['access_token'] = self.access_token
            self.token_data['expiry'] = self.expiry.isoformat() + 'Z'
            with open(TOKEN_FILE, 'w') as f:
                json.dump(self.token_data, f, indent=2)
            print('[DriveTokenManager] Access token refreshed.')
            return self.access_token
        else:
            raise Exception(f"Failed to refresh token: {response.text}")

    def get_access_token(self):
        if self.is_expired():
            return self.refresh_access_token()
        return self.access_token

if __name__ == '__main__':
    mgr = DriveTokenManager()
    token = mgr.get_access_token()
    print('Current valid access token:', token) 