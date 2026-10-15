import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from config import GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

_service = None

def get_gmail_service():
    global _service
    if _service is None:
        creds = _get_credentials()
        _service = build("gmail", "v1", credentials=creds)

    return _service

def _get_credentials() -> Credentials:
    creds = None

    if GMAIL_TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_PATH, SCOPES)

    if creds is not None and creds.valid:
        return creds

    if creds is not None and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        # needs someone at the computer to sign in. Logged first so a run that hangs
        # here under Task Scheduler can be traced
        logging.warning("No usable Gmail token, opening the browser to authorize Gmail")
        creds = InstalledAppFlow.from_client_secrets_file(GMAIL_CREDENTIALS_PATH, SCOPES).run_local_server(port=0)

    GMAIL_TOKEN_PATH.write_text(creds.to_json())
    return creds
