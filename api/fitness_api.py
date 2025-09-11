# Security configuration

from fastapi_cache import FastAPICache
from fastapi_cache.backends.memcached import MemcachedBackend

from api import users, testsession
from api.auth_service import Auth
from core.role import Role
from ui.services.db_service import DBService
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from starlette import status
from starlette.responses import RedirectResponse



import memcache

SECRET_KEY = "ranger1401"  # Move to configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class FitnessApi:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
    db_service = DBService("../ui/config/config.yml")
    def __init__(self):
        self.__logger = logging.getLogger(__name__)
        self.app = FastAPI(
            title="Fitness API",
            description="An API for managing fitness-related operations",
            version="1.0.0",
            docs_url="/swagger",
            redoc_url="/redoc",
            openapi_url="/openapi.json",
        )

        self._configure_cors()
        self.db_service = DBService()
        self._add_routes()
        self._add_events()

    def _configure_cors(self):
        origins = [
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:5175",
            "http://localhost:8001",
        ]

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _add_routes(self):
        @self.app.get("/", include_in_schema=False)
        async def redirect_to_swagger():
            return RedirectResponse(url="http://localhost:8001/swagger")

        # Replace the authentication methods with the Auth class methods
        @self.app.post("/token")
        async def login_for_access_token(
                form_data: OAuth2PasswordRequestForm = Depends()
        ):
            user = await Auth.authenticate_user(form_data.username, form_data.password)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = Auth.create_access_token(
                data={"sub": user.username, "roles": user.role},
                expires_delta=access_token_expires
            )
            return {"access_token": access_token, "token_type": "bearer"}

        # Include all routers
        self.app.include_router(users.router, )
        self.app.include_router(testsession.router, dependencies=[Depends(lambda: self.db_service)])


    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str):
        return cls.pwd_context.verify(plain_password, hashed_password)

    @classmethod
    def get_password_hash(cls, password: str):
        return cls.pwd_context.hash(password)

    @classmethod
    def create_access_token(cls, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    async def authenticate_user(self, username: str, password: str):
        user = await self.db_service.get_user_by_username(username)
        if not user:
            return False
        if not self.verify_password(password, user["hashed_password"]):
            return False
        return user

    @classmethod
    async def get_current_user(cls, token: str = Depends(oauth2_scheme)):
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
        except JWTError:
            raise credentials_exception

        user = await cls.db_service.get_user_by_username(username)
        if user is None:
            raise credentials_exception
        return user

    @classmethod
    def require_roles(cls, required_roles: List[Role]):
        async def role_checker(user: dict = Depends(cls.get_current_user)):
            if not any(role in user["roles"] for role in required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access forbidden"
                )
            return user

        return role_checker

    def _add_events(self):
        @self.app.on_event("startup")
        async def startup_event():
            if not await self.db_service.check_if_db_is_operational():
                raise Exception("Failed to initialize DBService")

            # Initialize FastAPI Cache with Memcached
            memcached_client = memcache.Client(['localhost:11211'])
            FastAPICache.init(
                backend=MemcachedBackend(memcached_client),
                prefix="fastapi-cache"
            )

        @self.app.on_event("shutdown")
        async def shutdown_event():
            await self.db_service.cleanup()

# Create an instance of the API
api = FitnessApi()
# Export the FastAPI application instance
app = api.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")
