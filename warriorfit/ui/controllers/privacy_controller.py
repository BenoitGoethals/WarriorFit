"""Controller for the Privacy / GDPR self-service page (serviceman-scoped)."""

import json
from typing import Any

from warriorfit.services.service_consent import CURRENT_CONSENT_VERSIONS, ConsentService
from warriorfit.services.service_gdpr import GdprService


class PrivacyController:
    """
    Facilitates privacy management, including user consent and GDPR-related operations.

    This class provides methods for handling GDPR data exports, user consents, and consent
    actions such as granting or withdrawing. It acts as a controller for privacy-related
    workflows and integrates with underlying GDPR and Consent services.

    :ivar _gdpr: The service responsible for GDPR-related operations.
    :type _gdpr: GdprService
    :ivar _consent: The service responsible for user consent operations.
    :type _consent: ConsentService
    """
    def __init__(
        self,
        gdpr_service: GdprService | None = None,
        consent_service: ConsentService | None = None,
    ):
        self._gdpr = gdpr_service if gdpr_service is not None else GdprService()
        self._consent = consent_service if consent_service is not None else ConsentService()

    @staticmethod
    def serviceman_serial(session_user) -> str | None:
        """
        Retrieve the serial number of a serviceman from the session user object if available.

        :param session_user: The user object from the session, which may or may not have a
            serial_number attribute.
        :type session_user: Any
        :return: Returns the serial number of the serviceman if it exists and is set in the
            session_user object; otherwise, returns None.
        :rtype: str | None
        """
        if session_user is None:
            return None
        serial = getattr(session_user, "serial_number", None)
        return serial or None

    async def export_json(self, service_number: str) -> str | None:
        """
        Exports service data in JSON format for a given service number.

        This asynchronous method retrieves data using the service number provided and
        returns it as a JSON-formatted string. If no data is found, it returns None.

        :param service_number: The unique service number used to query the service data.
        :type service_number: str
        :return: A JSON-formatted string containing the service data, or None if no data
                 is available.
        :rtype: str | None
        """
        data = await self._gdpr.export_serviceman_data(service_number)
        if data is None:
            return None
        return json.dumps(data, indent=2, default=str)

    async def consents(self, service_number: str) -> list[dict[str, Any]]:
        """
        Retrieve a list of consent records for a given service member.

        This asynchronous method fetches consent records associated with the specified
        service member identified by their service number. Each consent record includes
        information about the type of consent, the version, the timestamp when consent
        was given, and when it was withdrawn (if applicable).

        :param service_number: The unique identifier of the service member whose consents
            are to be retrieved.
        :type service_number: str
        :return: A list of dictionaries where each dictionary represents a consent
            record containing details such as type, version, given_at, and withdrawn_at.
        :rtype: list[dict[str, Any]]
        """
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
        self, service_number: str, consent_type: str, ip_address: str | None = None
    ) -> bool:
        """
        Grant consent for a specific service number with a specified consent type.

        This method interacts with the consent management system to grant consent for
        a given service number based on the provided consent type. Optionally, an
        IP address can be provided to log the source of this consent action.

        :param service_number: The unique identifier of the service number for which
            consent is being granted.
        :param consent_type: The type of consent being granted (e.g., marketing,
            transactional).
        :param ip_address: Optional IP address of the requester to provide additional
            metadata about the source of the consent action.
        :return: A boolean value indicating whether the consent was successfully
            granted.
        """
        result = await self._consent.grant(service_number, consent_type, ip_address=ip_address)
        return result is not None

    async def withdraw(
        self, service_number: str, consent_type: str, ip_address: str | None = None
    ) -> bool:
        """
        Withdraw consent for a specified service, identified by the service number.
        This method interacts with the consent management system to process the
        withdrawal request.

        :param service_number: The identifier of the service for which consent is being withdrawn.
        :type service_number: str
        :param consent_type: The type of consent to be withdrawn.
        :type consent_type: str
        :param ip_address: The IP address from which the request is initiated. This parameter is optional.
        :type ip_address: str | None
        :return: A boolean value indicating whether the withdrawal was successful.
        :rtype: bool
        """
        return await self._consent.withdraw(service_number, consent_type, ip_address=ip_address)

    @staticmethod
    def available_consent_types() -> list[str]:
        """
        Provides a list of all available consent types.

        This static method retrieves the current consent types available in the system, as
        defined by the keys in the `CURRENT_CONSENT_VERSIONS` dictionary.

        :return: A list of strings representing all available consent types.
        :rtype: list[str]
        """
        return list(CURRENT_CONSENT_VERSIONS.keys())
