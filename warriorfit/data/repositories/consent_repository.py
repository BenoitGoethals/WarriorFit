from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from warriorfit.data.model.db_model import UserConsent
from warriorfit.data.repositories.abc_repository import ABCRepository


class ConsentRepository(ABCRepository):
    """
    Manages user consent information within the system.

    This class provides functionality to record, withdraw, and retrieve user consent
    data. It acts as a repository to handle interactions with the underlying database
    for consent-related operations.

    :ivar SessionLocal: SQLAlchemy session factory for database interactions.
    :type SessionLocal: Callable[..., AsyncSession]
    :ivar _logger: Logger instance for capturing and reporting errors during database operations.
    :type _logger: logging.Logger
    """

    def __init__(self, config=None):
        super().__init__(config=config)

    async def record_consent(
        self,
        service_number: str,
        consent_type: str,
        version: str,
        ip_address: str | None = None,
    ) -> UserConsent | None:
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
            self._logger.error("record_consent failed for serviceman %s: %s", service_number, e)
            return None

    async def withdraw_consent(self, service_number: str, consent_type: str, version: str) -> bool:
        """
        Withdraws consent for a specified service number and consent type version. Updates the
        withdrawal timestamp if the consent exists and has not been previously withdrawn. Logs
        any database errors encountered during the operation.

        :param service_number: The unique identifier for the service member.
        :type service_number: str
        :param consent_type: The type of consent to withdraw.
        :type consent_type: str
        :param version: The version of the consent to withdraw.
        :type version: str
        :return: A boolean indicating whether the withdrawal was successful. Returns False if
            the consent does not exist, has already been withdrawn, or an error occurred.
        :rtype: bool
        """
        try:
            async with self.SessionLocal() as session, session.begin():
                stmt = select(UserConsent).where(
                    UserConsent.service_number == service_number,
                    UserConsent.consent_type == consent_type,
                    UserConsent.version == version,
                    UserConsent.withdrawn_at.is_(None),
                )
                row = (await session.execute(stmt)).scalar_one_or_none()
                if row is None:
                    return False
                row.withdrawn_at = datetime.now()
                return True
        except SQLAlchemyError as e:
            self._logger.error("withdraw_consent failed for serviceman %s: %s", service_number, e)
            return False

    async def get_active_consent(
        self, service_number: str, consent_type: str, version: str
    ) -> UserConsent | None:
        """
        Retrieve the active consent record for a given user service number, consent type,
        and version. The method filters results by withdrawing status to ensure only
        valid consents are returned.

        :param service_number: The unique service number identifying the user.
        :type service_number: str
        :param consent_type: The type of consent to fetch (e.g., marketing consent).
        :type consent_type: str
        :param version: The version of the consent to consider.
        :type version: str
        :return: An instance of UserConsent if an active consent record is found;
            otherwise, None.
        :rtype: Optional[UserConsent]
        """
        stmt = select(UserConsent).where(
            UserConsent.service_number == service_number,
            UserConsent.consent_type == consent_type,
            UserConsent.version == version,
            UserConsent.withdrawn_at.is_(None),
        )
        results = await self.fetch_and_log(stmt, "user_consent")
        return results[0] if results else None

    async def list_for_serviceman(self, service_number: str) -> list[UserConsent]:
        """
        Retrieve a list of user consents for a specific service number.

        This asynchronous method queries the database for records of user consents
        associated with the given service number and returns them in a list. If no
        records are found, an empty list is returned.

        :param service_number: The service number for which the user consents are to
            be retrieved.
        :return: A list of UserConsent objects associated with the provided service
            number, or an empty list if no records are found.
        """
        stmt = select(UserConsent).where(UserConsent.service_number == service_number)
        results = await self.fetch_and_log(stmt, "user_consents")
        return list(results) if results else []

    async def list_all_active(self) -> list[UserConsent]:
        """
        Lists all active user consents.

        This method retrieves all user consents that have not been withdrawn by
        filtering records where the `withdrawn_at` attribute is null.

        :param self: An instance of the class containing this method.
        :return: A list of active UserConsent objects if present, or an empty
            list otherwise.
        :rtype: List[UserConsent]
        """
        stmt = select(UserConsent).where(UserConsent.withdrawn_at.is_(None))
        results = await self.fetch_and_log(stmt, "user_consents")
        return list(results) if results else []
