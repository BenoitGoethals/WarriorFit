"""Consent service for GDPR Art. 7 / Art. 9 explicit consent tracking."""

from typing import List, Optional

from warriorfit.data.model.db_model import UserConsent
from warriorfit.data.repositories.consent_repository import ConsentRepository
from warriorfit.services.service import Service


class ConsentType:
    TERMS_OF_SERVICE = "terms_of_service"
    PRIVACY_POLICY = "privacy_policy"
    HEALTH_DATA_PROCESSING = "health_data_processing"


CURRENT_CONSENT_VERSIONS = {
    ConsentType.TERMS_OF_SERVICE: "1.0",
    ConsentType.PRIVACY_POLICY: "1.0",
    ConsentType.HEALTH_DATA_PROCESSING: "1.0",
}


class ConsentService(Service):
    def __init__(
        self,
        consent_repository: ConsentRepository | None = None,
        user_repository=None,
        config=None,
    ):
        super().__init__(user_repository=user_repository, config=config)
        self._consent_repo = (
            consent_repository
            if consent_repository is not None
            else ConsentRepository()
        )

    async def grant(
        self,
        service_number: str,
        consent_type: str,
        ip_address: Optional[str] = None,
    ) -> Optional[UserConsent]:
        version = CURRENT_CONSENT_VERSIONS[consent_type]
        record = await self._consent_repo.record_consent(
            service_number=service_number,
            consent_type=consent_type,
            version=version,
            ip_address=ip_address,
        )
        if record:
            await self.add_audit_log(
                action="consent_grant",
                details=f"{consent_type} v{version} serial={service_number}",
                ip_address=ip_address,
            )
        return record

    async def withdraw(
        self, service_number: str, consent_type: str, ip_address: Optional[str] = None
    ) -> bool:
        version = CURRENT_CONSENT_VERSIONS[consent_type]
        ok = await self._consent_repo.withdraw_consent(
            service_number=service_number, consent_type=consent_type, version=version
        )
        if ok:
            await self.add_audit_log(
                action="consent_withdraw",
                details=f"{consent_type} v{version} serial={service_number}",
                ip_address=ip_address,
            )
        return ok

    async def has_valid_consent(self, service_number: str, consent_type: str) -> bool:
        version = CURRENT_CONSENT_VERSIONS[consent_type]
        record = await self._consent_repo.get_active_consent(
            service_number=service_number, consent_type=consent_type, version=version
        )
        return record is not None

    async def list_for_serviceman(self, service_number: str) -> List[UserConsent]:
        return await self._consent_repo.list_for_serviceman(service_number)
