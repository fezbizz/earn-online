"""Generate the OAuth authorization URL for YouTube upload."""
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
flow = InstalledAppFlow.from_client_secrets_file("youtube/client_secret.json", SCOPES)
auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
print("=" * 60)
print("  YOUTUBE OAUTH — STEP 1")
print("=" * 60)
print()
print("Open this URL in your browser:")
print()
print(auth_url)
print()
print("After authorizing, you'll get a code. Copy it and paste it")
print("back in the chat. I'll use it to complete the upload.")
print("=" * 60)