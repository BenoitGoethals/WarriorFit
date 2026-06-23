"""Consent service for GDPR Art. 7 / Art. 9 explicit consent tracking."""

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
    """
    Handles operations related to managing user consents.

    The ConsentService class provides methods for granting, withdrawing,
    verifying, and listing consents associated with a specific service number.
    This service interacts with a consent repository to persist and retrieve
    consent records. Additionally, it logs audit information when consent-related
    actions occur.

    :ivar _consent_repo: The repository used to manage consent records.
    :type _consent_repo: ConsentRepository
    """
    def __init__(
        self,
        consent_repository: ConsentRepository | None = None,
        user_repository=None,
        config=None,
    ):
        super().__init__(user_repository=user_repository, config=config)
        self._consent_repo = (
            consent_repository if consent_repository is not None else ConsentRepository()
        )

    async def grant(
        self,
        service_number: str,
        consent_type: str,
        ip_address: str | None = None,
    ) -> UserConsent | None:
        """
        Grant consent for a user to a specified service and consent type.

        This function records the user's consent for a given service and consent type,
        optionally including the IP address from which the consent was granted. The
        consent version is determined based on the current consent configurations.
        An audit log is also created for the consent grant action.

        :param service_number: The unique identifier for the service to which the
            consent is being granted.
        :param consent_type: The type of consent being granted (e.g., terms of service,
            privacy policy).
        :param ip_address: The IP address from which the consent is granted. Defaults
            to None if not provided.
        :return: A `UserConsent` object representing the granted consent if the record
            is successfully created, or None if the consent could not be recorded.
        """
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
        self, service_number: str, consent_type: str, ip_address: str | None = None
    ) -> bool:
        """
        Withdraws a specific consent type for a given service number, logs the action through
        audit logging, and returns the status of the operation. The function handles audit
        logging to track user actions if the withdrawal is successful.

        :param service_number: The unique identifier for the service associated with the consent.
        :param consent_type: The type of consent being withdrawn.
        :param ip_address: The IP address of the user initiating the request. It is optional.
        :return: A boolean indicating whether the consent withdrawal was successful.
        """
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
        """
        Checks if a valid consent exists for the given service number and consent type.

        This method verifies if there is an active consent record in the repository
        that matches the provided service number, consent type, and the latest consent
        version.

        :param service_number: The identifier for the service number associated with the consent.
        :type service_number: str
        :param consent_type: The type of consent to verify.
        :type consent_type: str
        :return: True if a valid consent record exists, False otherwise.
        :rtype: bool
        """
        version = CURRENT_CONSENT_VERSIONS[consent_type]
        record = await self._consent_repo.get_active_consent(
            service_number=service_number, consent_type=consent_type, version=version
        )
        return record is not None

    async def list_for_serviceman(self, service_number: str) -> list[UserConsent]:
        """
        Retrieve the list of user consents associated with a given serviceman.

        This asynchronous method interacts with the consent repository to fetch all
        user consents related to the provided serviceman's service number.

        :param service_number: The unique identifier of the serviceman.
        :type service_number: str
        :return: A list containing `UserConsent` objects associated with the
                 serviceman.
        :rtype: list[UserConsent]
        """
        return await self._consent_repo.list_for_serviceman(service_number)
