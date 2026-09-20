from gmail_client.auth import get_gmail_credentials
from googleapiclient.discovery import build

creds = get_gmail_credentials()
print("Fetched Credentials. Valid token state: ", creds.token_state)

service = build("gmail", "v1", credentials=creds)
profile = service.users().getProfile(userId="me").execute()
print(profile)