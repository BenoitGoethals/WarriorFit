import asyncio
from typing import Any

from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from warriorfit.data.model.db_model import HrMessage
from warriorfit.data.repositories.abc_repository import ABCRepository


class MomRepository(ABCRepository):
    """
    Manages storage and retrieval of HR messages in the database.

    This repository class is responsible for adding, retrieving, deleting,
    and fetching the latest HR messages from the database. As part of a data
    access layer, it ensures that database interactions are abstracted and
    properly handled, including logging potential database errors and other
    runtime exceptions.

    The repository operates asynchronously, leveraging SQLAlchemy for database
    interactions. It provides methods for managing HR messages in a consistent
    and reliable manner.

    :ivar SessionLocal: Database session creator for managing database interactions.
    :type SessionLocal: Callable[..., AsyncSession]
    :ivar _logger: Logger instance used for logging errors or important runtime details.
    :type _logger: logging.Logger
    """

    def __init__(self, config=None):
        super().__init__(config=config)

    async def add_hr_message(self, msg: HrMessage) -> HrMessage | None:
        """
        Adds an HR message to the database session and refreshes it to reflect
        the most recent state. If an integrity error or other database error
        occurs during the operation, the error is logged and the method returns
        None.

        :param msg: The HR message instance to be added to the database.
        :type msg: HrMessage
        :return: The saved HR message with updated state after being refreshed,
            or None if an exception occurred.
        :rtype: HrMessage | None
        """
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    session.add(msg)
                await session.refresh(msg)
            return msg
        except IntegrityError as e:
            self._logger.error(
                "Integrity error adding cross %s: %s",
                getattr(msg, "id", "unknown"),
                str(e),
            )
            return None
        except SQLAlchemyError as e:
            self._logger.error(
                "Database error adding cross %s: %s",
                getattr(msg, "id", "unknown"),
                str(e),
            )
            return None

    async def get_all_hr_messages(self) -> list[Any] | None | Any:
        """
        Retrieve all HR messages from the database.

        This asynchronous method executes a query to fetch all records from the
        `HrMessage` table. In case of a database error or any unexpected error,
        the errors are logged, and an empty list is returned.

        :raises SQLAlchemyError: If there is an error while executing the SQL query.
        :raises Exception: If any unexpected error occurs during execution.

        :return: A list containing all HR messages if the query is successful, `None`
            or an empty list if there is an error during the process.
        :rtype: list[Any] | None | Any
        """
        try:
            query = select(HrMessage)
            results = await self.fetch_and_log(query, "HrMessage")
            return results
        except SQLAlchemyError as e:
            self._logger.error("Database error fetching cross: %s", str(e))
            return []

    async def delete_hr_message(self, id_msg: int) -> bool | None:
        """
        Deletes a human resource (HR) message from the database based on the provided ID. If the
        message is found, it will be removed and the operation will be committed to the database.

        :param id_msg: The ID of the HR message to be deleted.
        :type id_msg: int
        :return: Returns True if the message was successfully deleted, False if a database
            error occurred, or None if the message wasn't found.
        :rtype: bool | None
        """
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    query = delete(HrMessage).where(HrMessage.id == id_msg)
                    result = await session.execute(query)

                    if result.rowcount == 0:
                        self._logger.error(
                            "No HR message found with ID %s to delete.", id_msg
                        )
                        return False
                    return True
        except SQLAlchemyError as e:
            self._logger.error("Database error deleting cross %s: %s", id_msg, str(e))
            return False

    async def get_last_added_hr_message_by_send_date(self) -> HrMessage | None:
        """
        Fetches the last added HR message based on the send date.

        This method queries the database for the latest `HrMessage` record,
        sorted by the datetime the message was created in descending order.
        If there is an error during the database query or another unexpected
        error occurs, the method logs the error and returns `None`.

        :raises SQLAlchemyError: Raised in case of database operation issues.
        :raises Exception: Raised for any unexpected errors.
        :return: The latest `HrMessage` instance based on send date or `None`
                 in case of an error or if no messages are found.
        :rtype: HrMessage | None
        """
        try:
            async with self.SessionLocal() as session:
                query = select(HrMessage).order_by(HrMessage.datetime_created.desc())
                result = await session.execute(query)
                return result.scalars().first()
        except SQLAlchemyError as e:
            self._logger.error("Database error fetching cross: %s", str(e))
            return None


async def main():
    repo = MomRepository()

    # one = await repo.add_hr_message(HrMessage(message="test", datetime_created=datetime.now()))
    # print(await repo.get_all_hr_messages())
    # two = await repo.add_hr_message(HrMessage(message="test2", datetime_created=datetime.now()))
    # print(await repo.get_all_hr_messages())
    # three = await repo.add_hr_message(HrMessage(message="test3", datetime_created=datetime.now()))
    # print(await repo.get_all_hr_messages())
    # # if one:
    # #     await repo.delete_hr_message(one.id)
    # print(await repo.get_all_hr_messages())
    last_one = await repo.get_last_added_hr_message_by_send_date()

    if last_one:
        print(last_one.message, last_one.datetime_created, last_one.id)
    else:
        print("No messages found.")


if __name__ == "__main__":
    asyncio.run(main())
