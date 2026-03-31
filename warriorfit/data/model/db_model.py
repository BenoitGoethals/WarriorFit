from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    Float,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import JSON, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from warriorfit.core.Gender import Gender
from warriorfit.core.rank_enum import Rank
from warriorfit.core.role import Role
from warriorfit.core.type_fitness_test import TypeFitnessTest
from warriorfit.data.model.enum_mapped_user_model import IntEnumType


class Base(DeclarativeBase):
    pass


class AuditLog(Base):
    """
    Represents an audit log for tracking user actions on various entities.
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    created_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP, server_default=func.current_timestamp(), nullable=False
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP, server_default=func.current_timestamp(), nullable=False
    )
    role: Mapped[Role] = mapped_column(SAEnum(Role), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    serial_number: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True)

    # Optional 1:1 link User <-> ServiceMen (via ServiceMen.user_id)
    serviceman: Mapped[Optional["ServiceMen"]] = relationship(
        "ServiceMen",
        back_populates="user",
        uselist=False,
    )


# ----------------------------
# Tests (polymorphic)
# ----------------------------


class FitnessTest(Base):
    __tablename__ = "fitness_tests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)

    # Link FitnessTest -> ServiceMen via service_number (enforced by FK)
    serial_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        ForeignKey("service_men.service_number"),
        nullable=True,
        index=True,
    )

    # discriminator
    type: Mapped[Optional[str]] = mapped_column(String(50))

    service_men: Mapped[Optional["ServiceMen"]] = relationship(
        "ServiceMen",
        back_populates="fitness_tests",
        foreign_keys=[serial_number],
    )

    __mapper_args__ = {
        "polymorphic_identity": "fitness_test",
        "polymorphic_on": type,
    }

    def __repr__(self) -> str:
        return f"<FitnessTest(id={self.id}, serial_number={self.serial_number})>"

    def __str__(self) -> str:
        return f"FitnessTest(id={self.id}, serial_number={self.serial_number})"


class PhefTest(FitnessTest):
    __tablename__ = "phef_tests"

    id: Mapped[int] = mapped_column(ForeignKey("fitness_tests.id"), primary_key=True)
    running_time: Mapped[float] = mapped_column(Float, nullable=False)
    sideBridge_r: Mapped[float] = mapped_column(Float, nullable=False)
    sideBridge_l: Mapped[float] = mapped_column(Float, nullable=False)

    __mapper_args__ = {"polymorphic_identity": "phef_test"}

    def __repr__(self) -> str:
        return (
            f"<PhefTest(id={self.id}, running_time={self.running_time}, "
            f"sideBridge_r={self.sideBridge_r}, sideBridge_l={self.sideBridge_l})>"
        )

    def __str__(self) -> str:
        return (
            f"PhefTest(id={self.id}, running_time={self.running_time}, "
            f"sideBridge_r={self.sideBridge_r}, sideBridge_l={self.sideBridge_l})"
        )


class FunctionalTest(FitnessTest):
    __tablename__ = "functional_tests"

    id: Mapped[int] = mapped_column(ForeignKey("fitness_tests.id"), primary_key=True)
    push_ups: Mapped[int] = mapped_column(nullable=False)
    sit_ups: Mapped[int] = mapped_column(nullable=False)
    pull_ups: Mapped[int] = mapped_column(nullable=False)

    __mapper_args__ = {"polymorphic_identity": "functional_test"}

    def __repr__(self) -> str:
        return (
            f"<FunctionalTest(id={self.id}, push_ups={self.push_ups}, "
            f"sit_ups={self.sit_ups}, pull_ups={self.pull_ups})>"
        )

    def __str__(self) -> str:
        return (
            f"FunctionalTest(id={self.id}, push_ups={self.push_ups}, "
            f"sit_ups={self.sit_ups}, pull_ups={self.pull_ups})"
        )


class CombatTestParatrooper(FitnessTest):
    __tablename__ = "combat_tests"

    id: Mapped[int] = mapped_column(ForeignKey("fitness_tests.id"), primary_key=True)
    running_time: Mapped[float] = mapped_column(Float, nullable=False)
    obstacle_passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rope_passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __mapper_args__ = {"polymorphic_identity": "combat_test"}

    def __repr__(self) -> str:
        return (
            f"<CombatTestParatrooper(id={self.id}, running_time={self.running_time}, "
            f"obstacle_passed={self.obstacle_passed}, rope_passed={self.rope_passed})>"
        )

    def __str__(self) -> str:
        return (
            f"CombatTestParatrooper(id={self.id}, running_time={self.running_time}, "
            f"obstacle_passed={self.obstacle_passed}, rope_passed={self.rope_passed})"
        )


class CombatSwimmingTest(FitnessTest):
    __tablename__ = "combat_swimming_tests"

    id: Mapped[int] = mapped_column(ForeignKey("fitness_tests.id"), primary_key=True)
    swim_paased: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __mapper_args__ = {"polymorphic_identity": "combat_swimming_test"}

    def __repr__(self) -> str:
        return f"<CombatSwimmingTest(id={self.id}, swim_paased={self.swim_paased})>"

    def __str__(self) -> str:
        return f"CombatSwimmingTest(id={self.id}, swim_paased={self.swim_paased})"


class TestSession(Base):
    __tablename__ = "test_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    serial_number_pti: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    datetime_start: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, nullable=False)
    canceled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    type_test: Mapped[TypeFitnessTest] = mapped_column(
        SAEnum(TypeFitnessTest),
        default=TypeFitnessTest.PHEF,
        nullable=False,
    )

    fitness_tests: Mapped[List[FitnessTest]] = relationship(
        "FitnessTest",
        secondary="session_fitness_tests",
        backref="test_sessions",
    )

    def __repr__(self) -> str:
        return (
            f"<TestSession(id={self.id}, serial_number_pti={self.serial_number_pti}, "
            f"datetime_start={self.datetime_start}, executed={self.canceled})>"
        )

    def __str__(self) -> str:
        return (
            f"TestSession(id={self.id}, serial_number_pti={self.serial_number_pti}, "
            f"datetime_start={self.datetime_start}, executed={self.canceled})"
        )


class SessionFitnessTests(Base):
    __tablename__ = "session_fitness_tests"

    session_id: Mapped[int] = mapped_column(ForeignKey("test_sessions.id"), primary_key=True)
    fitness_test_id: Mapped[int] = mapped_column(ForeignKey("fitness_tests.id"), primary_key=True)


# ----------------------------
# CROSS
# ----------------------------


class Cross(Base):
    __tablename__ = "cross"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    datetime_start: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, nullable=False)
    distance: Mapped[float] = mapped_column(Float, nullable=False)
    executed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    runners: Mapped[List["Runner"]] = relationship(
        "Runner",
        secondary="cross_runners",
        back_populates="crosses",
    )

    def __repr__(self) -> str:
        return (
            f"Cross(id={self.id}, datetime_start='{self.datetime_start}', "
            f"distance={self.distance}, executed={self.executed})"
        )

    def __str__(self) -> str:
        return (
            f"Cross(id={self.id}, datetime_start='{self.datetime_start}', "
            f"distance={self.distance}, executed={self.executed})"
        )


class Runner(Base):
    __tablename__ = "runners"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    serial_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    running_time: Mapped[float] = mapped_column(Float, nullable=False)

    crosses: Mapped[List[Cross]] = relationship(
        "Cross",
        secondary="cross_runners",
        back_populates="runners",
    )


class CrossRunners(Base):
    __tablename__ = "cross_runners"

    cross_id: Mapped[int] = mapped_column(ForeignKey("cross.id"), primary_key=True)
    runner_id: Mapped[int] = mapped_column(ForeignKey("runners.id"), primary_key=True)


# ----------------------------
# Core domain
# ----------------------------


class Unit(Base):
    __tablename__ = "units"
    __table_args__ = (UniqueConstraint("name", name="uq_units_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    base_location: Mapped[str] = mapped_column(String(150), nullable=False)

    def __repr__(self) -> str:
        return f"Unit(id={self.id}, name='{self.name}', base_location='{self.base_location}')"

    def __str__(self) -> str:
        return f"{self.name} ({self.base_location})"


class ServiceMen(Base):
    __tablename__ = "service_men"
    __table_args__ = (UniqueConstraint("service_number", name="uq_service_men_service_number"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    mail: Mapped[str] = mapped_column(String(120), nullable=False)
    rank: Mapped[Rank] = mapped_column(IntEnumType(Rank), nullable=False)
    service_number: Mapped[str] = mapped_column(String(50), nullable=False)
    birthdate: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[Gender] = mapped_column(Enum(Gender), nullable=False)
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"), nullable=False, index=True)
    unit: Mapped["Unit"] = relationship("Unit", backref="servicemen")
    para: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ops_test: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Link to users.id (optional 1:1)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        unique=True,
        index=True,
    )
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="serviceman",
        foreign_keys=[user_id],
    )

    # Backrefs for FK-by-service_number links
    fitness_tests: Mapped[List["FitnessTest"]] = relationship(
        "FitnessTest",
        back_populates="service_men",
        primaryjoin="ServiceMen.service_number==FitnessTest.serial_number",
        foreign_keys="FitnessTest.serial_number",
    )

    marches: Mapped[List["March"]] = relationship(
        "March",
        back_populates="service_men",
        primaryjoin="ServiceMen.service_number==March.service_number",
        foreign_keys="March.service_number",
    )

    @property
    def rank_service_men(self) -> Rank:
        return Rank(self.rank)

    @property
    def age(self) -> int:
        return self.age_from_birthdate()

    def age_from_birthdate(self) -> int:
        if isinstance(self.birthdate, str):
            d = datetime.strptime(self.birthdate, "%Y-%m-%d").date()
        elif isinstance(self.birthdate, datetime):
            d = self.birthdate.date()
        else:
            d = self.birthdate
        today = date.today()
        return today.year - d.year - ((today.month, today.day) < (d.month, d.day))

    def age_from_birthdate_and_session_date(self, date_session: date | TIMESTAMP) -> int:
        if isinstance(self.birthdate, str):
            b = datetime.strptime(self.birthdate, "%Y-%m-%d").date()
        elif isinstance(self.birthdate, datetime):
            b = self.birthdate.date()
        else:
            b = self.birthdate
        return (
            date_session.year - b.year - ((date_session.month, date_session.day) < (b.month, b.day))  # type: ignore[union-attr]
        )

    def __repr__(self) -> str:
        return (
            f"ServiceMen(id={self.id}, first_name='{self.first_name}', last_name='{self.last_name}', "
            f"mail='{self.mail}', rank={self.rank}, service_number='{self.service_number}', "
            f"birthdate='{self.birthdate}', gender={self.gender}, unit_id={self.unit_id})"
        )

    def __str__(self) -> str:
        return (
            f"ServiceMen(id={self.id}, first_name='{self.first_name}', last_name='{self.last_name}', "
            f"mail='{self.mail}', rank={self.rank}, service_number='{self.service_number}', "
            f"birthdate='{self.birthdate}', gender={self.gender}, unit_id={self.unit_id})"
        )


class March(Base):
    __tablename__ = "march"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)

    # Link March -> ServiceMen via service_number (enforced by FK)
    service_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        ForeignKey("service_men.service_number"),
        nullable=True,
        index=True,
    )
    distance: Mapped[float] = mapped_column(Float, nullable=True, default=30)
    succeeded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    datetime_executed: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, nullable=False)

    service_men: Mapped[Optional["ServiceMen"]] = relationship(
        "ServiceMen",
        back_populates="marches",
        foreign_keys=[service_number],
    )


class HrMessage(Base):
    __tablename__ = "hr_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    message: Mapped[str] = mapped_column(String(255), nullable=False)
    datetime_created: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, nullable=False)


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    capacity: Mapped[int] = mapped_column(nullable=False)
    location: Mapped[str] = mapped_column(String(100), nullable=False)

    reservations: Mapped[List["Reservation"]] = relationship(
        "Reservation",
        back_populates="room",
    )


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), nullable=False)
    date: Mapped[datetime] = mapped_column(server_default=func.current_timestamp())
    start_time: Mapped[datetime] = mapped_column(server_default=func.current_timestamp())
    end_time: Mapped[datetime] = mapped_column(server_default=func.current_timestamp())
    serial_number: Mapped[str] = mapped_column(String(50), nullable=False)
    activity: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.current_timestamp())

    room: Mapped["Room"] = relationship(
        "Room",
        back_populates="reservations",
    )
