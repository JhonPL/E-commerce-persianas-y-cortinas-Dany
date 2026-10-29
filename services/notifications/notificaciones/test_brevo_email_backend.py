import base64
import json
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIClient

from .brevo_email_backend import BREVO_API_URL, BrevoEmailBackend, BrevoEmailError
from .email_templates import _header


class BrevoEmailBackendTests(SimpleTestCase):
    @override_settings(
        BREVO_API_KEY="test-api-key",
        DEFAULT_FROM_EMAIL="Tienda <store@example.com>",
    )
    def test_sends_plain_email_message_without_alternatives(self):
        message = EmailMessage(
            "Nuevo mensaje de contacto",
            "Consulta de un cliente.",
            "Tienda <store@example.com>",
            ["admin@example.com"],
            reply_to=["customer@example.com"],
        )
        response = MagicMock()
        response.__enter__.return_value = response
        response.status = 201

        with patch(
            "notificaciones.brevo_email_backend.urlopen",
            return_value=response,
        ) as send_request:
            sent_count = BrevoEmailBackend().send_messages([message])

        payload = json.loads(send_request.call_args.args[0].data)

        self.assertEqual(sent_count, 1)
        self.assertEqual(payload["textContent"], "Consulta de un cliente.")
        self.assertEqual(payload["replyTo"], {
            "email": "customer@example.com",
        })

    @override_settings(
        BREVO_API_KEY="test-api-key",
        DEFAULT_FROM_EMAIL="Tienda <store@example.com>",
    )
    def test_sends_html_and_attachments_using_the_transactional_api(self):
        message = EmailMultiAlternatives(
            "Pedido confirmado",
            "El pedido fue confirmado.",
            "Tienda <store@example.com>",
            ["Cliente <customer@example.com>"],
            cc=["copy@example.com"],
            reply_to=["support@example.com"],
        )
        message.attach_alternative("<p>Pedido confirmado</p>", "text/html")
        message.attach("invoice.pdf", b"%PDF-demo", "application/pdf")
        response = MagicMock()
        response.__enter__.return_value = response
        response.status = 201

        with patch(
            "notificaciones.brevo_email_backend.urlopen",
            return_value=response,
        ) as send_request:
            sent_count = BrevoEmailBackend().send_messages([message])

        request = send_request.call_args.args[0]
        payload = json.loads(request.data)
        headers = {
            name.lower(): value
            for name, value in request.header_items()
        }

        self.assertEqual(sent_count, 1)
        self.assertEqual(request.full_url, BREVO_API_URL)
        self.assertEqual(headers["api-key"], "test-api-key")
        self.assertEqual(payload["sender"], {
            "name": "Tienda",
            "email": "store@example.com",
        })
        self.assertEqual(payload["to"], [{"name": "Cliente", "email": "customer@example.com"}])
        self.assertEqual(payload["cc"], [{"email": "copy@example.com"}])
        self.assertEqual(payload["replyTo"], {"email": "support@example.com"})
        self.assertEqual(payload["htmlContent"], "<p>Pedido confirmado</p>")
        self.assertEqual(
            payload["attachment"],
            [{
                "name": "invoice.pdf",
                "content": base64.b64encode(b"%PDF-demo").decode("ascii"),
            }],
        )

    @override_settings(BREVO_API_KEY="test-api-key")
    def test_provider_http_errors_are_reported_without_response_contents(self):
        message = EmailMultiAlternatives(
            "Test",
            "Body",
            "store@example.com",
            ["customer@example.com"],
        )
        response_error = HTTPError(
            BREVO_API_URL,
            429,
            "Too many requests",
            {},
            None,
        )

        with patch(
            "notificaciones.brevo_email_backend.urlopen",
            side_effect=response_error,
        ):
            with self.assertRaisesRegex(BrevoEmailError, "HTTP 429"):
                BrevoEmailBackend().send_messages([message])

    def test_missing_api_key_is_an_explicit_delivery_error(self):
        message = EmailMultiAlternatives(
            "Test",
            "Body",
            "store@example.com",
            ["customer@example.com"],
        )

        with override_settings(BREVO_API_KEY=""):
            with self.assertRaisesRegex(
                BrevoEmailError,
                "BREVO_API_KEY is not configured",
            ):
                BrevoEmailBackend().send_messages([message])

    def test_empty_recipient_list_does_not_make_an_api_request(self):
        message = EmailMultiAlternatives(
            "Test",
            "Body",
            "store@example.com",
            [],
        )

        with patch("notificaciones.brevo_email_backend.urlopen") as send_request:
            self.assertEqual(
                BrevoEmailBackend().send_messages([message]),
                0,
            )

        send_request.assert_not_called()


class BrevoEmailTemplateTests(SimpleTestCase):
    @override_settings(
        EMAIL_BACKEND="notificaciones.brevo_email_backend.BrevoEmailBackend",
        NOTIFICATIONS_PUBLIC_URL="https://notifications.example.com",
    )
    def test_brevo_uses_a_public_logo_url_instead_of_inline_cid(self):
        html = _header()

        self.assertIn(
            "https://notifications.example.com/email-assets/logogreen.png",
            html,
        )
        self.assertNotIn("cid:brand-logo", html)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
    )
    def test_smtp_keeps_the_existing_inline_logo(self):
        self.assertIn("cid:brand-logo", _header())

    @override_settings(
        EMAIL_BACKEND="notificaciones.brevo_email_backend.BrevoEmailBackend",
        NOTIFICATIONS_PUBLIC_URL="",
    )
    def test_brevo_requires_a_public_url_for_the_logo(self):
        from smtplib import SMTPException

        with self.assertRaisesRegex(SMTPException, "NOTIFICATIONS_PUBLIC_URL"):
            _header()


class EmailLogoViewTests(SimpleTestCase):
    def test_public_logo_route_serves_the_png_asset(self):
        response = APIClient().get("/email-assets/logogreen.png")
        image_bytes = b"".join(response.streaming_content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertEqual(response["Cache-Control"], "public, max-age=86400")
        self.assertTrue(image_bytes.startswith(b"\x89PNG\r\n\x1a\n"))
