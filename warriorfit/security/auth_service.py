import os

import bcrypt
from fastapi.security import OAuth2PasswordBearer

from warriorfit.services.service_user import UserService

# Configuration constants
SECRET_KEY = os.environ["WF_SECRET_KEY"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Auth:
    """
    Handles user authentication using bcrypt one-way hashing.
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
        """Hash a plain-text password with bcrypt."""
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, stored: str) -> bool:
        """Verify a plain password against a stored bcrypt hash."""
        stored_bytes = stored.strip().encode("utf-8") if isinstance(stored, str) else bytes(stored).strip()
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), stored_bytes)
        except Exception:
            return False
