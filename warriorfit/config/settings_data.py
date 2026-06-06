from dataclasses import dataclass

from warriorfit.config.smtp_config import SmtpConfig


@dataclass
class SettingsData:
    """Configuration data for WarriorFit application settings.

    Attributes:
        db_host: Database host address
        db_port: Database port number (default: 5432)
        db_database: Database name
        db_username: Database username
        db_password: Database password
        pdf_path: Path for PDF file storage
        own_unit: Organization unit identifier
        mail_server: SMTP server configuration
        hr_url: HR system API endpoint URL
        hr_api_key: HR system API authentication key
    """

    # Database configuration
    db_host: str = ""
    db_port: int = 5432
    db_database: str = ""
    db_username: str = ""
    db_password: str = ""
    db_ssl: str = "prefer"
    db_ssl_root_cert: str = ""

    # Application configuration
    pdf_path: str = ""
    own_unit: str = ""

    # External services
    mail_server: SmtpConfig | None = None
    hr_url: str = ""
    hr_api_key: str = ""

    def has_database_config(self) -> bool:
        """Check if all required database configuration is present."""
        return bool(self.db_host and self.db_database and self.db_username and self.db_password)

    def has_hr_config(self) -> bool:
        """Check if HR system configuration is present."""
        return bool(self.hr_url and self.hr_api_key)
