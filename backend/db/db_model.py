from sqlalchemy.dialects.postgresql import JSON, TIMESTAMP

import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Enum,
    Boolean,
    DateTime,
)
from sqlalchemy import Date, Float, Text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from backend.model.role import Role
from backend.model.type_fitness_test import TypeFitnessTest

Base = declarative_base()

class AuditLog(Base):
    """
    Represents an audit log for tracking user actions on various entities.
    """

    __tablename__ = "audit_logs"

    # Columns
    id = Column(
        Integer, primary_key=True, autoincrement=True, nullable=False
    )  # Change from UUID to Integer
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False
    )  # Change type to Integer to match User.id
    action = Column(String(50), nullable=False)  # e.g., "create", "update", "delete"
    entity_type = Column(String(50), nullable=False)  # e.g., "Mission"
    entity_id = Column(String(50), nullable=False)  # ID of the entity being acted upon
    details = Column(JSON, nullable=True)  # Optional JSON for additional data
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6 format for user's IP
    user_agent = Column(Text, nullable=True)  # Info about browser/device
    created_at = Column(
        DateTime, default=func.now(), nullable=False
    )  # Timestamp of the action
    # Relationship with User



class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(128),  nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    role = Column(Enum(Role), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    serial_number = Column(String(50), unique=True, nullable=True)


#Tests

class FitnessTest(Base):
    __tablename__ = "fitness_tests"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    serial_number = Column(String(50), unique=True, nullable=True)
    passed = Column(Boolean, default=False, nullable=False)


    # Add discriminator column for inheritance
    type = Column(String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'fitness_test',
        'polymorphic_on': type
    }

    def __repr__(self):
        return f"<FitnessTest(id={self.id}, serial_number={self.serial_number}, passed={self.passed})>"

    def __str__(self):
        return f"FitnessTest(id={self.id}, serial_number={self.serial_number}, passed={self.passed})"

class PhefTest(FitnessTest):
    __tablename__ = "phef_tests"
    id = Column(Integer, ForeignKey('fitness_tests.id'), primary_key=True)
    running_time = Column(Float, nullable=False)
    planking_time = Column(Float, nullable=False)
    __mapper_args__ = {
        'polymorphic_identity': 'phef_test'
    }

    def __repr__(self):
        return f"<PhefTest(id={self.id}, running_time={self.running_time}, planking_time={self.planking_time})>"
    def __str__(self):
        return f"PhefTest(id={self.id}, running_time={self.running_time}, planking_time={self.planking_time})"


class FunctionalTest(FitnessTest):
    __tablename__ = "functional_tests"
    id = Column(Integer, ForeignKey('fitness_tests.id'), primary_key=True)
    push_ups = Column(Integer, nullable=False)
    sit_ups = Column(Integer, nullable=False)
    pull_ups = Column(Integer, nullable=False)
    __mapper_args__ = {
        'polymorphic_identity': 'functional_test'
    }
    def __repr__(self):
        return f"<FunctionalTest(id={self.id}, push_ups={self.push_ups}, sit_ups={self.sit_ups}, pull_ups={self.pull_ups})>"
    def __str__(self):
        return f"FunctionalTest(id={self.id}, push_ups={self.push_ups}, sit_ups={self.sit_ups}, pull_ups={self.pull_ups})"

class CombatTestParatrooper(FitnessTest):
    __tablename__ = "combat_tests"
    id = Column(Integer, ForeignKey('fitness_tests.id'), primary_key=True)
    running_time = Column(Float, nullable=False)
    obstacle_passed = Column(Boolean, default=False, nullable=False)
    rope_passed = Column(Boolean, default=False, nullable=False)
    __mapper_args__ = {
        'polymorphic_identity': 'combat_test'
    }
    def __repr__(self):
        return f"<CombatTestParatrooper(id={self.id}, running_time={self.running_time}, obstacle_passed={self.obstacle_passed}, rope_passed={self.rope_passed})>"
    def __str__(self):
        return f"CombatTestParatrooper(id={self.id}, running_time={self.running_time}, obstacle_passed={self.obstacle_passed}, rope_passed={self.rope_passed})"

class CombatSwimmingTest(FitnessTest):
    __tablename__ = "combat_swimming_tests"
    id = Column(Integer, ForeignKey('fitness_tests.id'), primary_key=True)
    swim_paased= Column(Boolean, default=False, nullable=False)
    __mapper_args__ = {
        'polymorphic_identity': 'combat_swimming_test'
    }
    def __repr__(self):
        return f"<CombatSwimmingTest(id={self.id}, swim_paased={self.swim_paased})>"
    def __str__(self):
        return f"CombatSwimmingTest(id={self.id}, swim_paased={self.swim_paased})"



class TestSession(Base):
    __tablename__ = "test_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    serial_number_pti = Column(String(50), unique=True, nullable=True)
    datetime_start = Column(TIMESTAMP, nullable=False)
    executed = Column(Boolean, default=False, nullable=False)
    description = Column(String(255), nullable=True)
    type_test = Column(Enum(TypeFitnessTest), default=TypeFitnessTest.PHEF , nullable=False)

    # Add relationship to FitnessTest with polymorphic loading
    fitness_tests = relationship(
        "FitnessTest",
        secondary="session_fitness_tests",
        backref="test_sessions"
    )

    def __repr__(self):
        return f"<TestSession(id={self.id}, serial_number_pti={self.serial_number_pti}, datetime_start={self.datetime_start}, executed={self.executed})>"

    def __str__(self):
        return f"TestSession(id={self.id}, serial_number_pti={self.serial_number_pti}, datetime_start={self.datetime_start}, executed={self.executed})"


# Create association table for many-to-many relationship
class SessionFitnessTests(Base):
    __tablename__ = "session_fitness_tests"
    session_id = Column(Integer, ForeignKey('test_sessions.id'), primary_key=True)
    fitness_test_id = Column(Integer, ForeignKey('fitness_tests.id'), primary_key=True)






