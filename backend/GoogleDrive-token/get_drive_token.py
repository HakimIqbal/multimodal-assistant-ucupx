from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/drive.file']
CLIENT_SECRET_FILE = 'client_secret_237423433593-54tf0mk8dsi15e54vg6ah6kld5eip0cd.apps.googleusercontent.com.json'

flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
# Set port ke 8080 (atau port lain yang Anda suka)
creds = flow.run_local_server(port=8080)

def main():
    # Set port ke 8080 agar redirect URI selalu http://localhost:8080/
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    creds = flow.run_local_server(port=8080)
    print("\n=== ACCESS TOKEN ===")
    print(creds.token)
    print("\n=== REFRESH TOKEN ===")
    print(creds.refresh_token)
    print("\n=== CREDENTIALS JSON (bisa disimpan untuk backend) ===")
    print(creds.to_json())

if __name__ == '__main__':
    main()