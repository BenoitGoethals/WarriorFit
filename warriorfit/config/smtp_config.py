from dataclasses import dataclass


@dataclass(frozen=True)
class SmtpConfig:
    host: str
    port: int = 587
    username: str | None = None
    password: str | None = None
    use_tls: bool = False
    use_ssl: bool = False
    sender_email: str | None = None  # fallback From address
    sender: str | None = None
