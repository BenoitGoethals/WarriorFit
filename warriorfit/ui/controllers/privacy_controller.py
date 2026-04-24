"""Controller for the Privacy / GDPR self-service page."""

import json
from typing import Any, Dict, List, Optional

from warriorfit.services.service_consent import CURRENT_CONSENT_VERSIONS, ConsentService
from warriorfit.services.service_gdpr import GdprService


class PrivacyController:
    def __init__(
        self,
        gdpr_service: GdprService = None,  # type: ignore[assignment]
        consent_service: ConsentService = None,  # type: ignore[assignment]
    ):
        self._gdpr = gdpr_service if gdpr_service is not None else GdprService()
        self._consent = consent_service if consent_service is not None else ConsentService()

    async def export_json(self, user_id: int) -> Optional[str]:
        data = await self._gdpr.export_user_data(user_id)
        if data is None:
            return None
        return json.dumps(data, indent=2, default=str)

    async def erase(self, user_id: int) -> bool:
        return await self._gdpr.erase_user(user_id)

    async def consents(self, user_id: int) -> List[Dict[str, Any]]:
        rows = await self._consent.list_for_user(user_id)
        return [
            {
                "type": r.consent_type,
                "version": r.version,
                "given_at": r.consent_given_at,
                "withdrawn_at": r.withdrawn_at,
            }
            for r in rows
        ]

    async def grant(
        self, user_id: int, consent_type: str, ip_address: Optional[str] = None
    ) -> bool:
        result = await self._consent.grant(user_id, consent_type, ip_address=ip_address)
        return result is not None

    async def withdraw(
        self, user_id: int, consent_type: str, ip_address: Optional[str] = None
    ) -> bool:
        return await self._consent.withdraw(user_id, consent_type, ip_address=ip_address)

    @staticmethod
    def available_consent_types() -> List[str]:
        return list(CURRENT_CONSENT_VERSIONS.keys())
