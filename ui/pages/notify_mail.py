import logging

from config.appliccation_config import ApplicationConfig
from logic.singleton import Singleton

from services.mail_service import MailService
from services.military_service import MilitaryService


class NotifyMail(metaclass=Singleton):

    def __init__(self, ):
        self.be_mil_service = MilitaryService()
        self.logger = logging.getLogger(__name__)

    async def send_mail(self, *, body: str, subject: str,to:str):
        if to:
            mail_sessions_add = {
                "subject": subject,
                "html_body": body
                ,
                "from_email": ApplicationConfig().mail_server.sender_email,
                "to": to
            }
            try:
                MailService().send_html(**mail_sessions_add)
            except Exception as e:
                self.logger.error(f"Error sending email: {str(e)}")
                return

