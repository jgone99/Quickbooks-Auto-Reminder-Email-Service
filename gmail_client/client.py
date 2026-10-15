import base64
import logging
import mimetypes
from email.message import EmailMessage
from pathlib import Path
from gmail_client.auth import get_gmail_service

NUM_RETRIES = 3

# so emailed run logs open as text in Gmail instead of as an unknown binary file
mimetypes.add_type("text/plain", ".log")

def build_message(to: str, subject: str, body: str, attachment_path: Path = None) -> EmailMessage:
    message = EmailMessage()
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    if attachment_path:
        attachment_path = Path(attachment_path)
        # .xlsx isn't in every machine's mimetypes table, so fall back to a generic binary type
        content_type, _ = mimetypes.guess_type(attachment_path.name)
        maintype, subtype = (content_type or "application/octet-stream").split("/")

        message.add_attachment(attachment_path.read_bytes(), maintype=maintype, subtype=subtype, filename=attachment_path.name)

    return message

def send_message(message: EmailMessage) -> dict:
    """
    Send a message from the authorized account. Raises on failure.
    """
    service = get_gmail_service()

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    result = service.users().messages().send(
        userId="me",
        body={"raw": encoded_message}
    ).execute(num_retries=NUM_RETRIES)

    logging.info(f"Sent message {result['id']} to {message['To']}")

    return result
