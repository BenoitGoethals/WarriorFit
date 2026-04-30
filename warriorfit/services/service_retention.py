"""Retention policy enforcement (GDPR Art. 5(1)(e) storage limitation)."""

from datetime import datetime, timedelta
from typing import Dict

from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError

from warriorfit.data.model.db_model import (
    AuditLog,
    FitnessTest,
    HrMessage,
    March,
    Reservation,
)
from warriorfit.services.service import Service


class RetentionService(Service):
    """Purges records older than their configured retention window."""

    def __init__(self, user_repository=None, config=None):
        super().__init__(user_repository=user_repository, config=config)
        self._retention = self._config().gdpr_retention

    def _config(self):
        from warriorfit.config.application_config import ApplicationConfig

        return ApplicationConfig()

    async def purge_all(self) -> Dict[str, int]:
        """Run every purge. Returns rows deleted per category."""
        report = {
            "fitness_tests": await self._purge_fitness(),
            "marches": await self._purge_marches(),
            "reservations": await self._purge_reservations(),
            "audit_logs": await self._purge_audit_logs(),
            "hr_messages": await self._purge_hr_messages(),
        }
        await self.add_audit_log(action="gdpr_retention_purge", details=str(report))
        return report

    async def _purge_fitness(self) -> int:
        # FitnessTest carries no own timestamp; it's dated through TestSession.
        # Purge by joining on test_sessions.datetime_start < cutoff.
        from sqlalchemy import select

        from warriorfit.data.model.db_model import SessionFitnessTests, TestSession

        cutoff = datetime.now() - timedelta(
            days=self._retention["fitness_retention_days"]
        )
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    stmt = (
                        select(SessionFitnessTests.fitness_test_id)
                        .join(
                            TestSession,
                            TestSession.id == SessionFitnessTests.session_id,
                        )
                        .where(TestSession.datetime_start < cutoff)
                    )
                    ids = [row[0] for row in (await session.execute(stmt)).all()]
                    if not ids:
                        return 0
                    result = await session.execute(
                        delete(FitnessTest).where(FitnessTest.id.in_(ids))
                    )
                    return result.rowcount or 0
        except SQLAlchemyError as e:
            self._logger.error("purge fitness failed: %s", e)
            return 0

    async def _purge_marches(self) -> int:
        cutoff = datetime.now() - timedelta(
            days=self._retention["fitness_retention_days"]
        )
        return await self._delete_older_than(March, March.datetime_executed, cutoff)

    async def _purge_reservations(self) -> int:
        cutoff = datetime.now() - timedelta(
            days=self._retention["fitness_retention_days"]
        )
        return await self._delete_older_than(
            Reservation, Reservation.created_at, cutoff
        )

    async def _purge_audit_logs(self) -> int:
        cutoff = datetime.now() - timedelta(
            days=self._retention["audit_retention_days"]
        )
        return await self._delete_older_than(AuditLog, AuditLog.created_at, cutoff)

    async def _purge_hr_messages(self) -> int:
        cutoff = datetime.now() - timedelta(
            days=self._retention["hr_message_retention_days"]
        )
        return await self._delete_older_than(
            HrMessage, HrMessage.datetime_created, cutoff
        )

    async def _delete_older_than(self, model, date_column, cutoff) -> int:
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    result = await session.execute(
                        delete(model).where(date_column < cutoff)
                    )
                    return result.rowcount or 0
        except SQLAlchemyError as e:
            self._logger.error("purge %s failed: %s", model.__tablename__, e)
            return 0
