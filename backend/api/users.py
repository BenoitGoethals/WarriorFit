import json
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.params import Body, Depends
from datetime import datetime

from fastapi_cache.decorator import cache
from starlette.responses import RedirectResponse

from backend.api.auth_service import Auth
from backend.api.json_shema import LoginSchema
from backend.db.db_model import User
from backend.model.role import Role
from backend.services.db_service import DBService

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)

def get_db():
    return DBService()

# Replace DropManagerAPI with Auth in the existing dependencies
@router.get("/protected-endpoint")
async def protected_endpoint(current_user: dict = Depends(Auth.get_current_user)):
    return {"message": "Hello authenticated user!", "user": current_user}


@router.get("/admin-only")
async def admin_only(current_user: dict = Depends(Auth.require_roles([Role.ADMIN]))):
    return {"message": "Hello admin!", "user": current_user}


@router.get("/", include_in_schema=False)
async def redirect_to_swagger():
    # Redirect users to the Swagger documentation
    return RedirectResponse(url="http://localhost:8001/swagger")


@router.get("/all", summary="users")
#@cache(expire=100)
async def get_users(current_user: dict = Depends(Auth.require_roles([Role.ADMIN])),db_service: DBService = Depends(get_db)
):
    try:
        results = await db_service.get_all_users()
        if not results:
            return JSONResponse(
                content={"message": "No users found"}, status_code=404
            )
        return jsonable_encoder(results)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{username}",
    summary="Fetch a user by username",
)
async def get_user_by_username(username: str,db_service: DBService = Depends(get_db)
):
    try:
        result = await db_service.get_user_by_username(username)
        if not result:
            return JSONResponse(
                content={"message": f"No user found with username {username}"},
                status_code=404,
            )
        return result
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login", summary="login")
async def login(credentials: LoginSchema = Body(...),db_service: DBService = Depends(get_db)
):
    """
    Handles user login.
    - Accepts LoginSchema as input.
    - Returns Userschema as the response.
    """
    try:

            # Check the user's credentials (authentication)
            result = await db_service.check_user(
                user_name=credentials.username,
                plain_password=credentials.password,
            )
            if not result:
                logger.info(
                    f"Failed to authenticate user {
                    credentials.username}"
                )
                return JSONResponse(
                    content={"message": "bad credentials"},
                    status_code=404,
                )

            # Fetch user details (authorization and details)
            user = await db_service.get_user_by_username(
                credentials.username
            )
            logger.info(
                f"User {credentials.username} logged in successfully"
            )
            # Return a response conforming to the Userschema model
            return user


    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{id}", summary="Update a user by username")
async def update_user(
        id: int,
        user_data: dict = Body(...),db_service: DBService = Depends(get_db),
        current_user: dict = Depends(Auth.require_roles([Role.ADMIN]),)
):
    """
    Updates a user's information.
    - Requires admin role.
    - Accepts user data as input.
    """
    try:
        # Add updated_at timestamp
        user_data["updated_at"] = datetime.now()

        # Create User instance with data validation
        user = User(
            id=id,
            username=user_data.get("username"),
            password_hash=user_data.get("password_hash"),
            email=user_data.get("email"),
            role=user_data.get("role"),
            is_active=user_data.get("is_active", True),
            serial_number=user_data.get("serial_number")
        )

        updated_user = await db_service.update_user(id, user)
        if not updated_user:
            return JSONResponse(
                content={"message": f"No user found with id {id}"},
                status_code=404,
            )
        return updated_user
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", summary="Add a new user")
async def add_user(user: dict = Body(...),db_service: DBService = Depends(get_db)
):
    """
    Adds a new user to the system.
    - Accepts user data as input.
    - Returns the created user or an error message.
    """
    try:
        # Create User instance with data validation
        new_user = User(
            username=user.get("username"),
            password_hash=Auth.hash_password("password"),  # Default password, should be changed later
            email=user.get("email"),
            role=user.get("role", Role.USER),
            is_active=user.get("is_active", True),
            serial_number=user.get("serial_number")
        )

        created_user = await db_service.add_user(new_user)
        return JSONResponse(
            content=jsonable_encoder(created_user), status_code=201
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{id}", summary="delete a user by username")
async def delete_user(id: int,db_service: DBService = Depends(get_db)
):
    """
    Deletes a user by ID.
    - Requires admin role.
    - Returns a success message or 404 if not found.
    """
    try:
        deleted = await db_service.delete_user(id)
        if not deleted:
            return JSONResponse(
                content={"message": f"No user found with id {id}"},
                status_code=404,
            )
        return JSONResponse(
            content={"message": f"User with id {id} deleted successfully"},
            status_code=200,
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))