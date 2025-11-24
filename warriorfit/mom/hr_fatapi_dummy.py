from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware  # NEW
from warriorfit.mom.message import Message


class MessageContent(BaseModel):
    """
    PHEF test result message content (transport schema)
    """
    serial_number: Optional[str] = None
    running_time: Optional[float] = None
    sideBridge_r: Optional[float] = None
    sideBridge_l: Optional[float] = None

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
    timestamp: Optional[str] = None


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

# CORS configuration (adjust origins to your frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8005",
        "http://127.0.0.1:8005",

    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post(
    "/api/v1/phef/test",
    response_model=AckResponse,
    description="Receive and process PHEF test results",
    responses={
        200: {"description": "Message successfully processed"},
        400: {"description": "Invalid message format or missing serial number"},
    },
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
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid message: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8005)