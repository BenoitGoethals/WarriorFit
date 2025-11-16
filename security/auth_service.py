import bcrypt
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from starlette import status

from core.role import Role
from services.service_user import UserService

# Configuration constants
SECRET_KEY = "your-secret-key-here"  # In production, use a secure secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Auth:
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
        if isinstance(password, str):
            password = password.encode()
        hashed = bcrypt.hashpw(password, bcrypt.gensalt())
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        try:
            if isinstance(hashed_password, bytes):
                hash_bytes = hashed_password
            elif hashed_password.startswith('$2b$'):
                hash_bytes = hashed_password.encode()
            elif all(c in '0123456789abcdefABCDEF' for c in hashed_password.replace('\\x', '')):
                hash_bytes = bytes.fromhex(hashed_password.replace('\\x', ''))
            else:
                hash_bytes = hashed_password.encode()
            return bcrypt.checkpw(plain_password.encode(), hash_bytes)
        except Exception:
            return False


