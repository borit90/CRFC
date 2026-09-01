import unittest
from unittest.mock import patch

import app as app_module


class ContactPageTests(unittest.TestCase):
    def test_contact_page_renders_without_error(self):
        client = app_module.app.test_client()

        response = client.get("/contact")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Contact the Club", response.data)
        self.assertIn(b"hero-image.png", response.data)
        self.assertIn(b"Contact", response.data)

    def test_homepage_includes_official_photographer_section(self):
        client = app_module.app.test_client()

        response = client.get("/home")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Official Photographer", response.data)
        self.assertIn(b"Photographs from Colchester Rangers FC matches and events", response.data)
        self.assertIn(b"Visit the official photographer website", response.data)
        self.assertIn(b"https://www.instagram.com/", response.data)


class ContactFormMailTests(unittest.TestCase):
    def test_send_contact_email_returns_false_when_configuration_missing(self):
        with (
            patch.object(app_module, "MAIL_SERVER", None),
            patch.object(app_module, "MAIL_USERNAME", None),
            patch.object(app_module, "MAIL_PASSWORD", None),
            patch.object(app_module, "MAIL_TO", ""),
        ):
            self.assertFalse(app_module.send_contact_email("Test", "test@example.com", "Hello"))

    @patch("app.smtplib.SMTP")
    def test_send_contact_email_uses_localhost_fallback(self, smtp_cls):
        server = smtp_cls.return_value.__enter__.return_value

        with (
            patch.object(app_module, "MAIL_SERVER", "localhost"),
            patch.object(app_module, "MAIL_PORT", 25),
            patch.object(app_module, "MAIL_USE_TLS", False),
            patch.object(app_module, "MAIL_USERNAME", None),
            patch.object(app_module, "MAIL_PASSWORD", None),
            patch.object(app_module, "MAIL_TO", "club@example.com"),
            patch.object(app_module, "MAIL_FROM", "noreply@example.com"),
        ):
            self.assertTrue(app_module.send_contact_email("Test", "test@example.com", "Hello"))
            smtp_cls.assert_called_once_with("localhost", 25)
            server.send_message.assert_called_once()


if __name__ == "__main__":
    unittest.main()
