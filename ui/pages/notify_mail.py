from config.appliccation_config import ApplicationConfig
from logic.singleton import Singleton
from services.be_mil_service import BEMILService
from services.mail_service import MailService


class NotifyMail(metaclass=Singleton):

    def __init__(self, ):

        self.be_mil_service = BEMILService()

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
                print(f"Error sending email: {str(e)}")
                return

