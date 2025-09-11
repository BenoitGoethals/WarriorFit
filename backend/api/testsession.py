import datetime
import logging

from fastapi import APIRouter, HTTPException
from fastapi.params import Body, Depends

import backend
from backend.api.auth_service import Auth
from backend.api.json_shema import TestSession, TestSessionFull
from backend.model.role import Role
from backend.services.db_service import DBService

router = APIRouter(prefix="/testsessions", tags=["testsessions"])
logger = logging.getLogger(__name__)


def get_db():
    return DBService()


def _parse_datetime(value) -> datetime.datetime:
    # Accept datetime, ISO 8601 string, or UNIX timestamp
    if isinstance(value, datetime.datetime):
        dt = value
    elif isinstance(value, str):
        # Support trailing 'Z' and general ISO format
        try:
            dt = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as e:
            raise ValueError(f"Invalid datetime format: {value}") from e
    elif isinstance(value, (int, float)):
        # Treat numbers as UNIX timestamps (seconds)
        dt = datetime.datetime.fromtimestamp(value, tz=datetime.timezone.utc)
    else:
        raise ValueError("datetime_start must be an ISO 8601 string, timestamp, or datetime")

    # Normalize to UTC, then strip tzinfo to match TIMESTAMP WITHOUT TIME ZONE
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    else:
        dt = dt.astimezone(datetime.timezone.utc)

    return dt.replace(tzinfo=None)


@router.get("/", response_model=list[TestSession])
async def all_test_sessions(db_service: DBService = Depends(get_db
                                                            ),
                            ):
    # Now you can use db_service here
    return await db_service.get_all_test_sessions()


@router.get("/upcoming", response_model=list[TestSession])
async def upcoming_test_sessions(db_service: DBService = Depends(get_db
                                                                 ),
                                 current_user: dict = Depends(Auth.require_roles([Role.ADMIN, Role.USER]), )):
    return await db_service.get_upcoming_test_sessions()


@router.get("/{id}", response_model=TestSession)
async def test_session_by_id(id: int, db_service: DBService = Depends(get_db), ):
    return await db_service.get_test_session_by_id(id)


@router.get("/full/{id}", response_model=TestSessionFull)
async def test_session_by_id_full(id: int, db_service: DBService = Depends(get_db), ):
    return await db_service.get_test_session_by_id(id)


@router.post("/", summary="Add a test session", response_model=TestSession)
async def add_test_session(session: dict = Body(...), db_service: DBService = Depends(get_db)):
    try:
        new_test_session = backend.services.db_service.TestSession(

            serial_number_pti=session.get('serial_number_pti'),
            datetime_start=_parse_datetime(session.get('datetime_start')),
            executed=session.get('executed', False),
            description=session.get('description'),
            type_test=session.get('type_test')
        )
        result = await db_service.add_test_session(new_test_session)
        if result is None:
            raise HTTPException(status_code=500, detail="Failed to create test session")
        return result
    except ValueError as ve:
        logger.error(f"Validation error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{id}", summary="Update a test session", response_model=TestSession)
async def update_test_session(id: int, session: dict = Body(...), db_service: DBService = Depends(get_db)
                              ):
    existing_session = await db_service.get_test_session_by_id(id)
    if not existing_session:
        raise HTTPException(status_code=404, detail="Test session not found")
    """
       Updates a user's information.
       - Requires admin role.
       - Accepts user data as input.
       """
    try:
        new_test_session = backend.services.db_service.TestSession(
            id=session.get('id'),
            serial_number_pti=session.get('serial_number_pti'),
            datetime_start=_parse_datetime(session.get('datetime_start')),
            executed=session.get('executed', False),
            description=session.get('description'),
            type_test=session.get('type_test')
        )
        new_test_session.id = id
        return await db_service.update_test_session(new_test_session)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{id}", summary="Delete a test session")
async def delete_test_session(id: int, db_service: DBService = Depends(get_db),
                              ):
    return await db_service.delete_test_session(id)
