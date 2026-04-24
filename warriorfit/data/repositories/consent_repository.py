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
        user_id: int,
        consent_type: str,
        version: str,
        ip_address: Optional[str] = None,
    ) -> Optional[UserConsent]:
        consent = UserConsent(
            user_id=user_id,
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
            existing = await self.get_active_consent(user_id, consent_type, version)
            return existing
        except SQLAlchemyError as e:
            self._logger.error("record_consent failed for user %d: %s", user_id, e)
            return None

    async def withdraw_consent(
        self, user_id: int, consent_type: str, version: str
    ) -> bool:
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    stmt = select(UserConsent).where(
                        UserConsent.user_id == user_id,
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
            self._logger.error("withdraw_consent failed for user %d: %s", user_id, e)
            return False

    async def get_active_consent(
        self, user_id: int, consent_type: str, version: str
    ) -> Optional[UserConsent]:
        stmt = select(UserConsent).where(
            UserConsent.user_id == user_id,
            UserConsent.consent_type == consent_type,
            UserConsent.version == version,
            UserConsent.withdrawn_at.is_(None),
        )
        results = await self.fetch_and_log(stmt, "user_consent")
        return results[0] if results else None

    async def list_for_user(self, user_id: int) -> List[UserConsent]:
        stmt = select(UserConsent).where(UserConsent.user_id == user_id)
        results = await self.fetch_and_log(stmt, "user_consents")
        return list(results) if results else []
