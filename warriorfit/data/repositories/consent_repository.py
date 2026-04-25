from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from warriorfit.data.model.db_model import UserConsent
from warriorfit.data.repositories.abc_repository import ABCRepository


class ConsentRepository(ABCRepository):
    """Persistence for GDPR Art. 7 consent records."""

    def __init__(self, config=None):
        super().__init__(config=config)

    async def record_consent(
        self,
        service_number: str,
        consent_type: str,
        version: str,
        ip_address: Optional[str] = None,
    ) -> Optional[UserConsent]:
        consent = UserConsent(
            service_number=service_number,
            consent_type=consent_type,
            version=version,
            ip_address=ip_address,
        )
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    session.add(consent)
                await session.refresh(consent)
                return consent
        except IntegrityError:
            existing = await self.get_active_consent(service_number, consent_type, version)
            return existing
        except SQLAlchemyError as e:
            self._logger.error(
                "record_consent failed for serviceman %s: %s", service_number, e
            )
            return None

    async def withdraw_consent(
        self, service_number: str, consent_type: str, version: str
    ) -> bool:
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    stmt = select(UserConsent).where(
                        UserConsent.service_number == service_number,
                        UserConsent.consent_type == consent_type,
                        UserConsent.version == version,
                        UserConsent.withdrawn_at.is_(None),
                    )
                    row = (await session.execute(stmt)).scalar_one_or_none()
                    if row is None:
                        return False
                    row.withdrawn_at = datetime.now()  # type: ignore[assignment]
                    return True
        except SQLAlchemyError as e:
            self._logger.error(
                "withdraw_consent failed for serviceman %s: %s", service_number, e
            )
            return False

    async def get_active_consent(
        self, service_number: str, consent_type: str, version: str
    ) -> Optional[UserConsent]:
        stmt = select(UserConsent).where(
            UserConsent.service_number == service_number,
            UserConsent.consent_type == consent_type,
            UserConsent.version == version,
            UserConsent.withdrawn_at.is_(None),
        )
        results = await self.fetch_and_log(stmt, "user_consent")
        return results[0] if results else None

    async def list_for_serviceman(self, service_number: str) -> List[UserConsent]:
        stmt = select(UserConsent).where(UserConsent.service_number == service_number)
        results = await self.fetch_and_log(stmt, "user_consents")
        return list(results) if results else []

    async def list_all_active(self) -> List[UserConsent]:
        stmt = select(UserConsent).where(UserConsent.withdrawn_at.is_(None))
        results = await self.fetch_and_log(stmt, "user_consents")
        return list(results) if results else []
