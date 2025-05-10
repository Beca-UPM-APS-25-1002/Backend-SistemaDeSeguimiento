from django.test import TestCase
from unittest.mock import patch
from django.core.mail import send_mail

from .models import EmailSettings
from .backend import DynamicEmailBackend


class DynamicEmailBackendTest(TestCase):
    """Tests for the DynamicEmailBackend class."""

    def setUp(self):
        """Set up test environment."""
        # Configure EmailSettings
        settings = EmailSettings.get_solo()
        settings.email_host = "test.example.com"
        settings.email_port = 587
        settings.email_host_user = "testuser"
        settings.email_host_password = "testpassword"
        settings.email_use_tls = True
        settings.email_use_ssl = False
        settings.email_fail_silently = False
        settings.email_timeout = 60
        settings.save()

    def test_backend_initialization(self):
        """Test that the backend initializes with settings from EmailSettings."""
        backend = DynamicEmailBackend()

        # Check backend initialized with values from our singleton
        self.assertEqual(backend.host, "test.example.com")
        self.assertEqual(backend.port, 587)
        self.assertEqual(backend.username, "testuser")
        self.assertEqual(backend.password, "testpassword")
        self.assertTrue(backend.use_tls)
        self.assertFalse(backend.use_ssl)
        self.assertFalse(backend.fail_silently)
        self.assertEqual(backend.timeout, 60)

    def test_backend_override_parameters(self):
        """Test that passed parameters override settings."""
        backend = DynamicEmailBackend(
            host="override.example.com",
            port=465,
            username="override_user",
            password="override_password",
            use_tls=False,
            fail_silently=True,
            use_ssl=True,
            timeout=30,
        )

        # Check that overridden values take precedence
        self.assertEqual(backend.host, "override.example.com")
        self.assertEqual(backend.port, 465)
        self.assertEqual(backend.username, "override_user")
        self.assertEqual(backend.password, "override_password")
        self.assertFalse(backend.use_tls)
        self.assertTrue(backend.use_ssl)
        self.assertTrue(backend.fail_silently)
        self.assertEqual(backend.timeout, 30)

    @patch("django.core.mail.backends.smtp.EmailBackend.send_messages")
    def test_send_mail_uses_settings(self, mock_send_messages):
        """Test that send_mail uses our backend with correct settings."""
        # Mock the send_messages method to avoid actual SMTP connections
        mock_send_messages.return_value = 1

        # Temporarily change EMAIL_BACKEND to use our DynamicEmailBackend
        with self.settings(EMAIL_BACKEND="dynamic_email.backend.DynamicEmailBackend"):
            # Update settings to test they're used correctly
            email_settings = EmailSettings.get_solo()
            email_settings.email_host = "updated.example.com"
            email_settings.save()

            # Send a test email
            send_mail(
                "Test Subject",
                "Test Message",
                "from@example.com",
                ["to@example.com"],
            )

            # Check send_messages was called
            self.assertTrue(mock_send_messages.called)

            # The first argument to send_messages is a list of EmailMessage objects
            # We need to check the connection attribute on the EmailMessage objects
            email_messages = mock_send_messages.call_args[0][0]

            # Check that at least one message was sent
            self.assertTrue(len(email_messages) > 0)

            # Get the connection from the first email message
            connection = email_messages[0].connection

            # Verify it used our updated settings
            self.assertEqual(connection.host, "updated.example.com")


class DynamicConfigurationTest(TestCase):
    """Test that configuration updates affect email sending."""

    @patch("django.core.mail.backends.smtp.EmailBackend.send_messages")
    def test_settings_change_affects_email_sending(self, mock_send_messages):
        """Test that changing settings affects future email sending."""
        # Set up initial settings
        settings = EmailSettings.get_solo()
        settings.email_host = "initial.example.com"
        settings.save()

        # Mock the send_messages method
        mock_send_messages.return_value = 1

        # Use our backend for sending emails
        with self.settings(EMAIL_BACKEND="dynamic_email.backend.DynamicEmailBackend"):
            # Send first email with initial settings
            send_mail(
                "Test Subject 1",
                "Test Message 1",
                "from@example.com",
                ["to@example.com"],
            )

            # Get the email messages sent in the first call
            first_email_messages = mock_send_messages.call_args[0][0]
            self.assertTrue(len(first_email_messages) > 0)

            # Get the connection from the first email message
            first_connection = first_email_messages[0].connection
            self.assertEqual(first_connection.host, "initial.example.com")

            # Change settings
            settings = EmailSettings.get_solo()
            settings.email_host = "updated.example.com"
            settings.save()

            # Send second email with updated settings
            send_mail(
                "Test Subject 2",
                "Test Message 2",
                "from@example.com",
                ["to@example.com"],
            )

            # Get the email messages sent in the second call
            second_email_messages = mock_send_messages.call_args[0][0]
            self.assertTrue(len(second_email_messages) > 0)

            # Get the connection from the second email message
            second_connection = second_email_messages[0].connection
            self.assertEqual(second_connection.host, "updated.example.com")
