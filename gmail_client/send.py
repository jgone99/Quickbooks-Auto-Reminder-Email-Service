import base64
import mimetypes
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.message import EmailMessage
from gmail_client.auth import get_gmail_credentials

_service = None

def _get_service():
    global _service
    if _service is None:
        # create gmail api client
        creds = get_gmail_credentials()
        _service = build("gmail", "v1", credentials=creds)
    return _service

def send_email(to: str, subject: str, body: str) -> dict | None:
    service = _get_service()
    try:
        mime_message = EmailMessage()

        # headers
        mime_message["To"] = to
        mime_message["Subject"] = subject

        # text
        mime_message.set_content(body)

        # attachment

        # encoded message
        encoded_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()

        create_message = {
            'raw': encoded_message
        }

        # send_message = (
        #     service.users()
        #     .messages()
        #     .send(userId="me", body=create_message)
        #     .execute()
        # )

        # print(f'Message Id: {send_message["id"]}')

        print("Would have sent:", create_message)

        return create_message

    except HttpError as error:
        print(f"An error occurred: {error}")
        # send_message = None

        
