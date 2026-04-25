"""Controller for the Privacy / GDPR self-service page (serviceman-scoped)."""

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

    @staticmethod
    def serviceman_serial(session_user) -> Optional[str]:
        """Return the service_number of the logged-in user, or None."""
        if session_user is None:
            return None
        serial = getattr(session_user, "serial_number", None)
        return serial or None

    async def export_json(self, service_number: str) -> Optional[str]:
        data = await self._gdpr.export_serviceman_data(service_number)
        if data is None:
            return None
        return json.dumps(data, indent=2, default=str)

    async def consents(self, service_number: str) -> List[Dict[str, Any]]:
        rows = await self._consent.list_for_serviceman(service_number)
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
        self, service_number: str, consent_type: str, ip_address: Optional[str] = None
    ) -> bool:
        result = await self._consent.grant(service_number, consent_type, ip_address=ip_address)
        return result is not None

    async def withdraw(
        self, service_number: str, consent_type: str, ip_address: Optional[str] = None
    ) -> bool:
        return await self._consent.withdraw(
            service_number, consent_type, ip_address=ip_address
        )

    @staticmethod
    def available_consent_types() -> List[str]:
        return list(CURRENT_CONSENT_VERSIONS.keys())
