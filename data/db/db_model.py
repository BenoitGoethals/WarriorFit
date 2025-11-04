from numpy import integer
from sqlalchemy.dialects.postgresql import JSON, TIMESTAMP

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Enum,
    Boolean,
    DateTime,
)
from sqlalchemy import Float, Text, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from core.role import Role
from core.type_fitness_test import TypeFitnessTest

Base = declarative_base()

class AuditLog(Base):
    """
    Represents an audit log for tracking user actions on various entities.
    """
    __tablename__ = "audit_logs"
    id = Column(
        Integer, primary_key=True, autoincrement=True, nullable=False
    )
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    action = Column(String(50), nullable=False)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(
        DateTime, default=func.now(), nullable=False
    )


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
    serial_number = Column(String(50), unique=False, nullable=True)

    # Add discriminator column for inheritance
    type = Column(String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'fitness_test',
        'polymorphic_on': type
    }

    def __repr__(self):
        return f"<FitnessTest(id={self.id}, serial_number={self.serial_number}, )>"

    def __str__(self):
        return f"FitnessTest(id={self.id}, serial_number={self.serial_number}, )"

class PhefTest(FitnessTest):
    __tablename__ = "phef_tests"
    id = Column(Integer, ForeignKey('fitness_tests.id'), primary_key=True)
    running_time = Column(Float, nullable=False)
    sideBridge_r = Column(Float, nullable=False)
    sideBridge_l = Column(Float, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'phef_test'
    }

    def __repr__(self):
        return f"<PhefTest(id={self.id}, running_time={self.running_time}, sideBridge_r={self.sideBridge_r}, sideBridge_l={self.sideBridge_l})>"
    def __str__(self):
        return f"PhefTest(id={self.id}, running_time={self.running_time}, sideBridge_r={self.sideBridge_r}, sideBridge_l={self.sideBridge_l})"

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
    serial_number_pti = Column(String(50), unique=False, nullable=True)
    datetime_start = Column(TIMESTAMP, nullable=False)
    canceled = Column(Boolean, default=False, nullable=False)
    description = Column(String(255), nullable=True)
    type_test = Column(Enum(TypeFitnessTest), default=TypeFitnessTest.PHEF , nullable=False)

    # Add relationship to FitnessTest with polymorphic loading
    fitness_tests = relationship(
        "FitnessTest",
        secondary="session_fitness_tests",
        backref="test_sessions"
    )

    def __repr__(self):
        return f"<TestSession(id={self.id}, serial_number_pti={self.serial_number_pti}, datetime_start={self.datetime_start}, executed={self.canceled})>"

    def __str__(self):
        return f"TestSession(id={self.id}, serial_number_pti={self.serial_number_pti}, datetime_start={self.datetime_start}, executed={self.canceled})"


# Create association table for many-to-many relationship
class SessionFitnessTests(Base):
    __tablename__ = "session_fitness_tests"
    session_id = Column(Integer, ForeignKey('test_sessions.id'), primary_key=True)
    fitness_test_id = Column(Integer, ForeignKey('fitness_tests.id'), primary_key=True)

#CROSS
class Cross(Base):
    __tablename__ = "cross"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    datetime_start = Column(TIMESTAMP, nullable=False)
    distance = Column(Float, nullable=False)
    executed = Column(Boolean, default=False, nullable=False)
    description = Column(String(255), nullable=True)

    runners = relationship("Runner", secondary="cross_runners", back_populates="crosses")


class Runner(Base):
    __tablename__ = "runners"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    serial_number = Column(String(50), unique=False, nullable=True)
    running_time = Column(Float, nullable=False)

    crosses = relationship("Cross", secondary="cross_runners", back_populates="runners")


class CrossRunners(Base):
    __tablename__ = "cross_runners"
    cross_id = Column(Integer, ForeignKey('cross.id'), primary_key=True)
    runner_id = Column(Integer, ForeignKey('runners.id'), primary_key=True)
