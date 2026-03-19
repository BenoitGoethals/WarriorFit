import asyncio

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

from warriorfit.services.service_user import UserService

_ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)


class Auth:
    """
    Handles user authentication using Argon2id one-way hashing.
    """

    @staticmethod
    async def authenticate_user(username: str, password: str):
        db_service = UserService()
        user = await db_service.get_user_by_username(username)
        if not user:
            return None
        if not await Auth.verify_password(password, user.password_hash):
            return None
        return user

    @staticmethod
    async def hash_password(password: str) -> str:
        """Hash a plain-text password with Argon2id (offloaded to thread pool)."""
        return await asyncio.to_thread(_ph.hash, password)

    @staticmethod
    async def verify_password(plain_password: str, stored: str) -> bool:
        """Verify a plain password against a stored Argon2id hash (offloaded to thread pool)."""
        def _verify() -> bool:
            try:
                return _ph.verify(stored, plain_password)
            except (VerifyMismatchError, VerificationError, InvalidHashError):
                return False
        return await asyncio.to_thread(_verify)
