"""Complete OAuth flow using local server — opens browser, handles redirect, saves token."""
import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
BASE = Path(__file__).parent
CLIENT_SECRET = BASE / "youtube" / "client_secret.json"
TOKEN_PATH = BASE / "youtube" / "youtube_token.json"

flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
print("Starting OAuth flow on http://localhost:8090 ...")
print("A browser window should open. If not, open this URL manually:")
print()

# Generate the URL and print it
auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
# Add redirect_uri manually
auth_url += "&redirect_uri=http%3A%2F%2Flocalhost%3A8090%2F"
print(auth_url)
print()

# Run local server on port 8090
creds = flow.run_local_server(port=8090, open_browser=True)

# Save token
with open(TOKEN_PATH, "w") as f:
    f.write(creds.to_json())
print(f"\nToken saved to {TOKEN_PATH}")
print("OAuth complete! You can now run upload_youtube.py")