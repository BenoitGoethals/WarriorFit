import datetime
from datetime import date
from typing import Optional, List, Dict, Union, Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class LoginSchema(BaseModel):
    username: str
    password: str


class UnitSchema(BaseModel):
    id: int
    name: str
    base_location: str

    class Config:
        orm_mode = True





class Userschema(BaseModel):
    id: int
    username: str
    email: str

    # Align with ORM attribute names via aliasing.
    is_active: bool = Field(alias="is_active")

    # Timestamps may not always be present; make them optional if not guaranteed
    last_login: Optional[datetime.datetime] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    # Align with ORM 'role' (likely an Enum). Coerce to string at serialization time.
    role: str = Field(alias="role")

    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True,
        populate_by_name=True,  # allow use of field names when exporting
    )


class FitnessTestBase(BaseModel):
    id: int
    serial_number: Optional[str] = None
    passed: bool = False
    # Accept whatever the ORM provides (string or Enum); validator coerces to str
    type: str


class TestSession(BaseModel):
    id: int
    serial_number_pti: Optional[str] = None
    datetime_start: datetime.datetime
    executed: bool = False
    description: Optional[str] = None
    # Accept Enum or str for type_test and coerce to str
    type_test: str

    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True,
    )


# Detailed fitness test models
class FitnessTestBaseModel(BaseModel):
    id: int
    serial_number: Optional[str] = None
    passed: bool = False
    # Keep as string; the validator will normalize enums
    type: str


class PhefTestModel(BaseModel):
    id: int
    serial_number: Optional[str] = None
    passed: bool = False


    running_time: float
    planking_time: float


class FunctionalTestModel(BaseModel):
    id: int
    serial_number: Optional[str] = None
    passed: bool = False
    type: str  # e.g., "FUNCTIONAL"

    push_ups: int
    sit_ups: int
    pull_ups: int


class CombatTestParatrooperModel(BaseModel):
    id: int
    serial_number: Optional[str] = None
    passed: bool = False
    type: str  # e.g., "COMBAT_PARATROOPER"

    running_time: float
    obstacle_passed: bool = False
    rope_passed: bool = False


class CombatSwimmingTestModel(BaseModel):
    id: int
    serial_number: Optional[str] = None
    passed: bool = False
    type: str  # e.g., "COMBAT_SWIMMING"

    # Fix typo to match ORM attribute name
    swim_passed: bool = False




class TestSessionFull(BaseModel):
    id: int
    serial_number_pti: Optional[str] = None
    datetime_start: datetime.datetime
    executed: bool = False
    description: Optional[str] = None
    # Store enum as string for transport; validator will normalize
    type_test: str

    # Related fitness tests (optional)
    fitness_tests: Optional[List[PhefTestModel]] = None

    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True,
    )


class SessionFitnessTestsModel(BaseModel):
    session_id: int
    fitness_test_id: int

    model_config = ConfigDict(from_attributes=True)
