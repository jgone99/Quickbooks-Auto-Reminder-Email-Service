from google.auth.transport.requests import Request
from google.auth.credentials import TokenState
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path


SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def get_gmail_credentials():
    creds = None
    token_path = Path("token.json")
    cred_path = Path("credentials.json")

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if creds is not None and not creds.token_state == TokenState.FRESH:
        creds.refresh(Request())
    elif creds is None or creds.token_state != TokenState.FRESH:
        creds = InstalledAppFlow.from_client_secrets_file(cred_path, SCOPES).run_local_server(port=0)

    token_path.write_text(creds.to_json())
    return creds