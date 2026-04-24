"""GDPR data-subject-rights service: export (Art. 15/20) and erasure (Art. 17)."""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError

from warriorfit.data.model.db_model import (
    CombatSwimmingTest,
    CombatTestParatrooper,
    FitnessTest,
    FunctionalTest,
    March,
    PhefTest,
    Reservation,
    ServiceMen,
    User,
    UserConsent,
)
from warriorfit.data.repositories.consent_repository import ConsentRepository
from warriorfit.data.repositories.fitness_test_repository import FitnessTestRepository
from warriorfit.data.repositories.march_repository import MarchRepository
from warriorfit.data.repositories.servicemen_repository import ServicemenRepository
from warriorfit.services.service import Service


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    return value


def _row_to_dict(row: Any, columns: List[str]) -> Dict[str, Any]:
    return {col: _to_jsonable(getattr(row, col, None)) for col in columns}


class GdprService(Service):
    """Exports and erases personal data for a given user."""

    def __init__(
        self,
        user_repository=None,
        servicemen_repository: ServicemenRepository = None,  # type: ignore[assignment]
        fitness_test_repository: FitnessTestRepository = None,  # type: ignore[assignment]
        march_repository: MarchRepository = None,  # type: ignore[assignment]
        consent_repository: ConsentRepository = None,  # type: ignore[assignment]
        config=None,
    ):
        super().__init__(user_repository=user_repository, config=config)
        self._servicemen_repo = servicemen_repository or ServicemenRepository()
        self._fitness_repo = fitness_test_repository or FitnessTestRepository()
        self._march_repo = march_repository or MarchRepository()
        self._consent_repo = consent_repository or ConsentRepository()

    async def export_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        user = await self._user_repo.get_user_by_id(user_id)
        if user is None:
            return None

        out: Dict[str, Any] = {
            "export_generated_at": datetime.now().isoformat(),
            "user": _row_to_dict(
                user,
                ["id", "username", "email", "role", "is_active", "serial_number", "created_at"],
            ),
            "serviceman": None,
            "fitness_tests": [],
            "marches": [],
            "reservations": [],
            "consents": [],
        }

        serviceman = None
        if user.serial_number:
            try:
                async with self.SessionLocal() as session:
                    stmt = select(ServiceMen).where(ServiceMen.user_id == user.id)
                    serviceman = (await session.execute(stmt)).scalar_one_or_none()
            except SQLAlchemyError as e:
                self._logger.error("export: serviceman fetch failed: %s", e)

        if serviceman:
            out["serviceman"] = _row_to_dict(
                serviceman,
                [
                    "id", "first_name", "last_name", "mail", "rank",
                    "service_number", "birthdate", "gender", "unit_id",
                    "para", "ops_test",
                ],
            )

            out["fitness_tests"] = await self._export_fitness(serviceman.service_number)
            out["marches"] = await self._export_marches(serviceman.service_number)
            out["reservations"] = await self._export_reservations(serviceman.service_number)

        consents = await self._consent_repo.list_for_user(user.id)
        out["consents"] = [
            _row_to_dict(
                c,
                ["id", "consent_type", "version", "consent_given_at", "withdrawn_at", "ip_address"],
            )
            for c in consents
        ]

        await self.add_audit_log(
            action="gdpr_export",
            details=f"user_id={user_id}",
        )
        return out

    async def _export_fitness(self, service_number: str) -> List[Dict[str, Any]]:
        tests: List[Dict[str, Any]] = []
        try:
            async with self.SessionLocal() as session:
                phef = (
                    await session.execute(
                        select(PhefTest).where(PhefTest.serial_number == service_number)
                    )
                ).scalars().all()
                combat = (
                    await session.execute(
                        select(CombatTestParatrooper).where(
                            CombatTestParatrooper.serial_number == service_number
                        )
                    )
                ).scalars().all()
                swim = (
                    await session.execute(
                        select(CombatSwimmingTest).where(
                            CombatSwimmingTest.serial_number == service_number
                        )
                    )
                ).scalars().all()
                func = (
                    await session.execute(
                        select(FunctionalTest).where(
                            FunctionalTest.serial_number == service_number
                        )
                    )
                ).scalars().all()

            for t in phef:
                tests.append({"type": "phef", "id": t.id, "running_time": t.running_time,
                              "sideBridge_r": t.sideBridge_r, "sideBridge_l": t.sideBridge_l})
            for t in combat:
                tests.append({"type": "combat", "id": t.id, "running_time": t.running_time,
                              "obstacle_passed": t.obstacle_passed, "rope_passed": t.rope_passed})
            for t in swim:
                tests.append({"type": "swim", "id": t.id, "swim_passed": t.swim_paased})
            for t in func:
                tests.append({"type": "functional", "id": t.id, "push_ups": t.push_ups,
                              "sit_ups": t.sit_ups, "pull_ups": t.pull_ups})
        except SQLAlchemyError as e:
            self._logger.error("export: fitness fetch failed: %s", e)
        return tests

    async def _export_marches(self, service_number: str) -> List[Dict[str, Any]]:
        try:
            async with self.SessionLocal() as session:
                rows = (
                    await session.execute(
                        select(March).where(March.service_number == service_number)
                    )
                ).scalars().all()
            return [
                _row_to_dict(
                    r, ["id", "distance", "succeeded", "datetime_executed", "service_number"]
                )
                for r in rows
            ]
        except SQLAlchemyError as e:
            self._logger.error("export: march fetch failed: %s", e)
            return []

    async def _export_reservations(self, service_number: str) -> List[Dict[str, Any]]:
        try:
            async with self.SessionLocal() as session:
                rows = (
                    await session.execute(
                        select(Reservation).where(Reservation.serial_number == service_number)
                    )
                ).scalars().all()
            return [
                _row_to_dict(
                    r,
                    [
                        "id", "room_id", "date", "start_time", "end_time",
                        "activity", "serial_number", "created_at",
                    ],
                )
                for r in rows
            ]
        except SQLAlchemyError as e:
            self._logger.error("export: reservation fetch failed: %s", e)
            return []

    async def erase_user(self, user_id: int) -> bool:
        """Full GDPR Art. 17 erasure: user + serviceman + tied fitness data."""
        user = await self._user_repo.get_user_by_id(user_id)
        if user is None:
            return False
        service_number = user.serial_number

        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    if service_number:
                        await session.execute(
                            delete(FitnessTest).where(
                                FitnessTest.serial_number == service_number
                            )
                        )
                        await session.execute(
                            delete(March).where(March.service_number == service_number)
                        )
                        await session.execute(
                            delete(Reservation).where(
                                Reservation.serial_number == service_number
                            )
                        )
                        await session.execute(
                            delete(ServiceMen).where(
                                ServiceMen.service_number == service_number
                            )
                        )
                    await session.execute(
                        delete(UserConsent).where(UserConsent.user_id == user.id)
                    )
                    await session.execute(delete(User).where(User.id == user.id))
        except SQLAlchemyError as e:
            self._logger.error("erase_user failed for %d: %s", user_id, e)
            return False

        await self.add_audit_log(
            action="gdpr_erase",
            details=f"user_id={user_id} serial={service_number}",
        )
        return True
