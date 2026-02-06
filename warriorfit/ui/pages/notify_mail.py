import logging

from warriorfit.config.appliccation_config import ApplicationConfig
from warriorfit.logic.singleton import Singleton

from warriorfit.services.mail_service import MailService
from warriorfit.services.military_service import MilitaryService


class NotifyMail(metaclass=Singleton):
    """
    Singleton class for handling email notifications.

    This class provides functionality for sending email notifications. It uses a
    singleton pattern to ensure only one instance of the NotifyMail class exists
    throughout the application lifecycle. It also includes logging capabilities
    to record events or errors during the email sending process.

    :ivar be_mil_service: Handles operations related to the military service.
    :type be_mil_service: MilitaryService
    :ivar logger: Logger object used to log events and errors within the class.
    :type logger: logging.Logger
    """

    def __init__(
        self,
    ):
        self.be_mil_service = MilitaryService()
        self.logger = logging.getLogger(__name__)

    async def send_mail(self, *, body: str, subject: str, to: str):
        if to:
            mail_sessions_add = {
                "subject": subject,
                "html_body": body,
                "from_email": ApplicationConfig().mail_server.sender_email,
                "to": to,
            }
            try:
                MailService().send_html(**mail_sessions_add)
            except Exception as e:
                self.logger.error(f"Error sending email: {str(e)}")
                return
