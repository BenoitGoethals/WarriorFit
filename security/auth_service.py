import bcrypt
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from starlette import status

from core.role import Role
from services.db_service import DBService

# Configuration constants
SECRET_KEY = "your-secret-key-here"  # In production, use a secure secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Auth:
    @staticmethod
    async def authenticate_user(username: str, password: str):
        db_service = DBService("../ui/config/config.yml")
        user = await db_service.get_user_by_username(username)
        if not user:
            return None
        if not Auth.verify_password(password, user.password_hash):
            return None
        return user

    @staticmethod
    def hash_password(password: str) -> str:
        # Ensure the password is in bytes format before hashing
        if isinstance(password, str):
            password = password.encode()
        # Generate a bcrypt hash of the password
        hashed = bcrypt.hashpw(password, bcrypt.gensalt())
        # Return the hash as a string
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        try:
            # If the hash is already in bytes format, use it directly
            if isinstance(hashed_password, bytes):
                hash_bytes = hashed_password
            # If it starts with $2b$ it's already in bcrypt format
            elif hashed_password.startswith('$2b$'):
                hash_bytes = hashed_password.encode()
            # Try to convert from hex format if it appears to be hex
            elif all(c in '0123456789abcdefABCDEF' for c in hashed_password.replace('\\x', '')):
                hash_bytes = bytes.fromhex(hashed_password.replace('\\x', ''))
            else:
                # If none of the above, assume it's a bcrypt hash string
                hash_bytes = hashed_password.encode()
            
            return bcrypt.checkpw(plain_password.encode(), hash_bytes)
        except Exception:
            # If any conversion fails, return False to indicate invalid password
            return False



    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        # Convert UserRole enum to string for JSON serialization
        if 'roles' in to_encode and isinstance(to_encode['roles'], Role):
            to_encode['roles'] = to_encode['roles'].name
            
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    async def get_current_user(token: str = Depends(oauth2_scheme)):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
            # Convert role string back to enum if needed
            role = payload.get("roles")
            if isinstance(role, str):
                try:
                    role = [role]
                except KeyError:
                    role = None
            return {"username": username, "roles": role}
        except JWTError:
            raise credentials_exception

    @staticmethod
    def require_roles(required_roles: List[Role]):
        async def role_checker(current_user: dict = Depends(Auth.get_current_user)):
            user_roles = current_user.get("roles", [])
            if not user_roles:
                raise HTTPException(
                    status_code=403,
                    detail="No role assigned to user"
                )

            # Convert single role to list for consistent handling
            if not isinstance(required_roles, list):
                required_role_list = [required_roles]
            else:
                required_role_list = required_roles

            # Check if any of user's roles match the required roles
            if not any(user_role in [role.name for role in required_role_list] for user_role in user_roles):
                raise HTTPException(
                    status_code=403,
                    detail="Operation not permitted"
                )
            return current_user

        return role_checker