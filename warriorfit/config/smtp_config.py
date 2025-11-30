from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SmtpConfig:
    host: str
    port: int = 587
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = False
    use_ssl: bool = False
    sender_email: Optional[str] = None  # fallback From address
    sender: Optional[str] = None