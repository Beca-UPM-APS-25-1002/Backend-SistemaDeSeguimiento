from django.core.mail.backends.smtp import EmailBackend
from .models import EmailSettings


class DynamicEmailBackend(EmailBackend):
    """
    A Django email backend that loads configuration from singleton settings
    each time an email is sent.
    """

    def __init__(
        self,
        host=None,
        port=None,
        username=None,
        password=None,
        use_tls=None,
        fail_silently=None,
        use_ssl=None,
        timeout=None,
        ssl_keyfile=None,
        ssl_certfile=None,
        **kwargs,
    ):
        # Get the singleton instance of EmailSettings
        settings = EmailSettings.get_solo()

        # Initialize parent EmailBackend with values from settings or passed parameters
        super().__init__(
            host=settings.email_host if host is None else host,
            port=settings.email_port if port is None else port,
            username=settings.email_host_user if username is None else username,
            password=settings.email_host_password if password is None else password,
            use_tls=settings.email_use_tls if use_tls is None else use_tls,
            fail_silently=settings.email_fail_silently
            if fail_silently is None
            else fail_silently,
            use_ssl=settings.email_use_ssl if use_ssl is None else use_ssl,
            timeout=settings.email_timeout if timeout is None else timeout,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile,
            **kwargs,
        )
