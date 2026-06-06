import hmac
import os

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from warriorfit.mom.message import Message

_API_KEY_HEADER = "X-API-Key"
_api_key_scheme = APIKeyHeader(name=_API_KEY_HEADER, auto_error=False)


def require_api_key(api_key: str | None = Depends(_api_key_scheme)) -> None:
    """Reject requests that don't carry a valid MOM API key.

    The expected key is read from the WF_MOM_API_KEY environment variable at
    request time. If the env var is unset or empty the API is locked down
    (fail-closed) so that a misconfigured deployment cannot accidentally
    expose the endpoint without authentication.
    """
    expected = os.getenv("WF_MOM_API_KEY", "")
    if not expected or api_key is None or not hmac.compare_digest(api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": _API_KEY_HEADER},
        )


class MessageContent(BaseModel):
    """
    PHEF test result message content (transport schema)
    """

    serial_number: str | None = None
    running_time: float | None = None
    sideBridge_r: float | None = None
    sideBridge_l: float | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "serial_number": "MIL123",
                "running_time": 12.5,
                "sideBridge_r": 45.0,
                "sideBridge_l": 42.0,
            }
        }
    }


class MessageIn(BaseModel):
    content: MessageContent
    timestamp: str | None = None


class AckResponse(BaseModel):
    success: bool
    ack: str


app = FastAPI(
    title="WarriorFit MOM API",
    description="REST API for WarriorFit Message Oriented Middleware",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
)

# CORS configuration. Origins are configurable through WF_MOM_CORS_ORIGINS
# (comma-separated). Methods/headers are restricted to what this API actually
# uses to avoid an overly permissive policy.
_cors_origins_env = os.getenv("WF_MOM_CORS_ORIGINS", "").strip()
_cors_origins = (
    [o.strip() for o in _cors_origins_env.split(",") if o.strip()]
    if _cors_origins_env
    else ["http://localhost:8005", "http://127.0.0.1:8005"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["Content-Type", _API_KEY_HEADER],
)


@app.post(
    "/api/v1/phef/test",
    response_model=AckResponse,
    description="Receive and process PHEF test results",
    responses={
        200: {"description": "Message successfully processed"},
        400: {"description": "Invalid message format or missing serial number"},
        401: {"description": "Missing or invalid API key"},
    },
    dependencies=[Depends(require_api_key)],
)
def receive_message(payload: MessageIn):
    try:
        if payload.content.serial_number is None:
            raise HTTPException(status_code=400, detail="Serial number is required")
        msg = Message(content=payload.content)  # Message should accept DTO or dict
        print(f"Received message: {msg.content.model_dump()}")

        return AckResponse(success=True, ack="Message enqueued")
    except HTTPException:
        raise
    except (ValueError, TypeError, KeyError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid message: {e}") from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8005)
