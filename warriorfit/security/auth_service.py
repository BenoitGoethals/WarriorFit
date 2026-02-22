import base64
import hashlib
import os

import bcrypt
from cryptography.fernet import Fernet, InvalidToken
from fastapi.security import OAuth2PasswordBearer

from warriorfit.services.service_user import UserService

# Configuration constants
SECRET_KEY = os.environ["WF_SECRET_KEY"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Derive a stable 32-byte Fernet key from SECRET_KEY
_FERNET_KEY = base64.urlsafe_b64encode(hashlib.sha256(SECRET_KEY.encode()).digest())
_fernet = Fernet(_FERNET_KEY)


class Auth:
    """
    Handles user authentication using symmetric (Fernet) encryption so that
    stored passwords can be decrypted back to plain text by administrators.
    """

    @staticmethod
    async def authenticate_user(username: str, password: str):
        db_service = UserService()
        user = await db_service.get_user_by_username(username)
        if not user:
            return None
        if not Auth.verify_password(password, user.password_hash):
            return None
        return user

    @staticmethod
    def hash_password(password: str) -> str:
        """Encrypt a plain-text password with Fernet. Returns a token string."""
        return _fernet.encrypt(password.encode()).decode()

    @staticmethod
    def decrypt_password(stored: str) -> str:
        """Decrypt a Fernet token back to the plain-text password.
        Returns an empty string for legacy bcrypt hashes that cannot be decrypted."""
        try:
            return _fernet.decrypt(stored.encode()).decode()
        except (InvalidToken, Exception):
            return ""

    @staticmethod
    def verify_password(plain_password: str, stored: str) -> bool:
        """Verify a plain password against a stored Fernet token.
        Falls back to bcrypt for legacy hashes already in the database."""
        try:
            decrypted = _fernet.decrypt(stored.encode()).decode()
            return decrypted == plain_password
        except (InvalidToken, Exception):
            pass
        # Legacy bcrypt fallback (for users created before this change)
        try:
            stored_bytes = stored.strip().encode("utf-8") if isinstance(stored, str) else bytes(stored).strip()
            return bcrypt.checkpw(plain_password.encode("utf-8"), stored_bytes)
        except Exception:
            return False
