import logging

from warriorfit.config.application_config import ApplicationConfig
from warriorfit.services.mail_service import MailService


class NotifyMail:
    """
    Class for handling email notifications.

    This class provides functionality for sending email notifications.
    It accepts injected dependencies for mail_service and config, with
    fallbacks to default instances for backward compatibility.

    :ivar logger: Logger object used to log events and errors within the class.
    :type logger: logging.Logger
    """

    def __init__(
        self,
        mail_service: MailService = None,
        config: ApplicationConfig = None,
    ):
        self._mail_service = mail_service if mail_service is not None else MailService()
        self._config = config if config is not None else ApplicationConfig()
        self.logger = logging.getLogger(__name__)

    async def send_mail(self, *, body: str, subject: str, to: str):
        if to:
            mail_sessions_add = {
                "subject": subject,
                "html_body": body,
                "from_email": self._config.mail_server.sender_email,
                "to": to,
            }
            try:
                self._mail_service.send_html(**mail_sessions_add)  # type: ignore[arg-type]
            except (OSError, ValueError, TypeError) as e:
                self.logger.error(f"Error sending email: {e!s}")
                return
