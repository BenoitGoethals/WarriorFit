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
    SessionFitnessTests,
    TestSession,
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

    async def export_serviceman_data(self, service_number: str) -> Optional[Dict[str, Any]]:
        if not service_number:
            return None

        serviceman = None
        try:
            async with self.SessionLocal() as session:
                stmt = select(ServiceMen).where(ServiceMen.service_number == service_number)
                serviceman = (await session.execute(stmt)).scalar_one_or_none()
        except SQLAlchemyError as e:
            self._logger.error("export: serviceman fetch failed: %s", e)
            return None

        if serviceman is None:
            return None

        out: Dict[str, Any] = {
            "export_generated_at": datetime.now().isoformat(),
            "serviceman": _row_to_dict(
                serviceman,
                [
                    "id", "first_name", "last_name", "mail", "rank",
                    "service_number", "birthdate", "gender", "unit_id",
                    "para", "ops_test",
                ],
            ),
            "fitness_tests": await self._export_fitness(service_number),
            "marches": await self._export_marches(service_number),
            "reservations": await self._export_reservations(service_number),
            "consents": [
                _row_to_dict(
                    c,
                    [
                        "id", "consent_type", "version",
                        "consent_given_at", "withdrawn_at", "ip_address",
                    ],
                )
                for c in await self._consent_repo.list_for_serviceman(service_number)
            ],
        }

        await self.add_audit_log(
            action="gdpr_export",
            details=f"service_number={service_number}",
        )
        return out

    async def _export_fitness(self, service_number: str) -> List[Dict[str, Any]]:
        tests: List[Dict[str, Any]] = []

        def _join(model):
            return (
                select(model, TestSession.datetime_start)
                .outerjoin(
                    SessionFitnessTests,
                    SessionFitnessTests.fitness_test_id == model.id,
                )
                .outerjoin(
                    TestSession,
                    TestSession.id == SessionFitnessTests.session_id,
                )
                .where(model.serial_number == service_number)
            )

        try:
            async with self.SessionLocal() as session:
                phef = (await session.execute(_join(PhefTest))).all()
                combat = (await session.execute(_join(CombatTestParatrooper))).all()
                swim = (await session.execute(_join(CombatSwimmingTest))).all()
                func = (await session.execute(_join(FunctionalTest))).all()

            for t, dt in phef:
                tests.append({
                    "type": "phef", "id": t.id, "date": _to_jsonable(dt),
                    "running_time": t.running_time,
                    "sideBridge_r": t.sideBridge_r, "sideBridge_l": t.sideBridge_l,
                })
            for t, dt in combat:
                tests.append({
                    "type": "combat", "id": t.id, "date": _to_jsonable(dt),
                    "running_time": t.running_time,
                    "obstacle_passed": t.obstacle_passed, "rope_passed": t.rope_passed,
                })
            for t, dt in swim:
                tests.append({
                    "type": "swim", "id": t.id, "date": _to_jsonable(dt),
                    "swim_passed": t.swim_paased,
                })
            for t, dt in func:
                tests.append({
                    "type": "functional", "id": t.id, "date": _to_jsonable(dt),
                    "push_ups": t.push_ups, "sit_ups": t.sit_ups, "pull_ups": t.pull_ups,
                })
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
                    if service_number:
                        await session.execute(
                            delete(UserConsent).where(
                                UserConsent.service_number == service_number
                            )
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
