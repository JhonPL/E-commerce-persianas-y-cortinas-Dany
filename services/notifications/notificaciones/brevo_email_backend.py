import base64
import json
import logging
import smtplib
import urllib.error
from email.mime.base import MIMEBase
from email.utils import parseaddr
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


logger = logging.getLogger(__name__)
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


class BrevoEmailError(smtplib.SMTPException):
    pass


def _format_address(address):
    name, email_address = parseaddr(address or "")
    if not email_address:
        raise BrevoEmailError("A valid email address is required by Brevo.")
    recipient = {"email": email_address}
    if name:
        recipient["name"] = name
    return recipient


def _attachment_payload(attachment):
    if isinstance(attachment, MIMEBase):
        filename = attachment.get_filename() or "attachment"
        content = attachment.get_payload(decode=True)
    elif isinstance(attachment, tuple) and len(attachment) in (2, 3):
        filename, content = attachment[:2]
    else:
        raise BrevoEmailError("Unsupported email attachment format.")

    if not filename or content is None:
        raise BrevoEmailError("Email attachments require a filename and content.")
    if isinstance(content, str):
        content = content.encode("utf-8")
    elif not isinstance(content, bytes):
        content = bytes(content)

    return {
        "name": filename,
        "content": base64.b64encode(content).decode("ascii"),
    }


class BrevoEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        sent_count = 0
        for email_message in email_messages:
            if not email_message.recipients():
                continue
            try:
                self._send_message(email_message)
            except BrevoEmailError:
                if not self.fail_silently:
                    raise
                logger.exception("Brevo transactional email delivery failed.")
            else:
                sent_count += 1
        return sent_count

    def _send_message(self, email_message):
        api_key = getattr(settings, "BREVO_API_KEY", "")
        if not api_key:
            raise BrevoEmailError("BREVO_API_KEY is not configured.")

        payload = {
            "sender": _format_address(
                email_message.from_email or settings.DEFAULT_FROM_EMAIL
            ),
            "to": [_format_address(address) for address in email_message.to],
            "subject": email_message.subject,
        }
        if email_message.cc:
            payload["cc"] = [
                _format_address(address) for address in email_message.cc
            ]
        if email_message.bcc:
            payload["bcc"] = [
                _format_address(address) for address in email_message.bcc
            ]
        if email_message.reply_to:
            payload["replyTo"] = _format_address(email_message.reply_to[0])

        if email_message.content_subtype == "html":
            payload["htmlContent"] = email_message.body
        else:
            payload["textContent"] = email_message.body

        for content, mimetype in getattr(email_message, "alternatives", ()):
            if mimetype == "text/html":
                payload["htmlContent"] = content
            elif mimetype == "text/plain":
                payload["textContent"] = content

        if email_message.attachments:
            payload["attachment"] = [
                _attachment_payload(attachment)
                for attachment in email_message.attachments
            ]

        request = Request(
            BREVO_API_URL,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "api-key": api_key,
                "accept": "application/json",
                "content-type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=15) as response:
                if not 200 <= response.status < 300:
                    raise BrevoEmailError(
                        f"Brevo API returned HTTP {response.status}."
                    )
        except urllib.error.HTTPError as exc:
            raise BrevoEmailError(
                f"Brevo API returned HTTP {exc.code}."
            ) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise BrevoEmailError("Brevo API request failed.") from exc
