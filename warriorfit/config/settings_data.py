from dataclasses import dataclass

from warriorfit.config.smtp_config import SmtpConfig


@dataclass
class SettingsData:
    db_host: str = ""
    db_port: int = 5432
    db_database: str = ""
    db_username: str = ""
    db_password: str = ""
    pdf_path: str = ""
    own_unit: str = ""
    mail_server: SmtpConfig=None
    hr_url: str = ""

