import asyncio
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import delete, or_, select
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

    async def get_due_pending_messages(
        self, limit: int = 5, now: datetime | None = None
    ) -> list[HrMessage]:
        """
        Return up to `limit` HR messages that the broker is allowed to send right now.

        A message is "due" when:
            - it is NOT in the dead-letter state, AND
            - its `next_retry_at` is NULL (never tried) OR <= now.

        Results are ordered by `datetime_created` ASC so older messages are sent
        before newer ones — preventing a permanently-failing newest row from
        starving the rest of the outbox.
        """
        now = now or datetime.now()
        try:
            async with self.SessionLocal() as session:
                query = (
                    select(HrMessage)
                    .where(HrMessage.dead_letter.is_(False))
                    .where(
                        or_(
                            HrMessage.next_retry_at.is_(None),
                            HrMessage.next_retry_at <= now,
                        )
                    )
                    .order_by(HrMessage.datetime_created.asc())
                    .limit(limit)
                )
                result = await session.execute(query)
                return list(result.scalars().all())
        except SQLAlchemyError as e:
            self._logger.error("Database error fetching due HR messages: %s", str(e))
            return []

    async def mark_failure(
        self,
        msg_id: int,
        error: str,
        max_attempts: int,
        base_backoff_seconds: int,
        max_backoff_seconds: int,
    ) -> bool:
        """
        Record a failed send attempt against `msg_id`.

        Increments `attempt_count`, stores `last_error` (truncated to fit), and
        schedules `next_retry_at` using exponential back-off:

            delay = min(base * 2 ** (attempt_count - 1), max_backoff)

        Once `attempt_count >= max_attempts`, the row is flipped to
        `dead_letter = True` and will not be picked up by `get_due_pending_messages`
        again.

        Returns True if the row was updated, False otherwise.
        """
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    row = (
                        await session.execute(
                            select(HrMessage).where(HrMessage.id == msg_id)
                        )
                    ).scalar_one_or_none()
                    if row is None:
                        return False
                    row.attempt_count = (row.attempt_count or 0) + 1
                    row.last_error = (error or "")[:500]
                    if row.attempt_count >= max_attempts:
                        row.dead_letter = True
                        row.next_retry_at = None
                    else:
                        delay_s = min(
                            base_backoff_seconds * (2 ** (row.attempt_count - 1)),
                            max_backoff_seconds,
                        )
                        row.next_retry_at = datetime.now() + timedelta(seconds=delay_s)
                    return True
        except SQLAlchemyError as e:
            self._logger.error(
                "Database error marking HR message %s as failed: %s", msg_id, str(e)
            )
            return False

    async def list_dead_letter(self) -> list[HrMessage]:
        """Return all rows currently parked in the dead-letter state, oldest first."""
        try:
            async with self.SessionLocal() as session:
                query = (
                    select(HrMessage)
                    .where(HrMessage.dead_letter.is_(True))
                    .order_by(HrMessage.datetime_created.asc())
                )
                result = await session.execute(query)
                return list(result.scalars().all())
        except SQLAlchemyError as e:
            self._logger.error(
                "Database error listing dead-letter HR messages: %s", str(e)
            )
            return []

    async def outbox_health_summary(self) -> dict:
        """
        Snapshot of the HR outbox for the dashboard health card.

        Returned keys:
            pending          int  — rows still waiting to be sent (dead_letter=False)
            dead_letter      int  — rows that exhausted retries
            oldest_pending   datetime | None — datetime_created of the oldest pending row
            last_error       str | None      — most recent `last_error` text seen
            db_ok            bool — False if the query itself failed (DB unreachable)
        """
        from sqlalchemy import func as sa_func

        try:
            async with self.SessionLocal() as session:
                pending = (
                    await session.execute(
                        select(sa_func.count(HrMessage.id)).where(
                            HrMessage.dead_letter.is_(False)
                        )
                    )
                ).scalar_one()
                dead = (
                    await session.execute(
                        select(sa_func.count(HrMessage.id)).where(
                            HrMessage.dead_letter.is_(True)
                        )
                    )
                ).scalar_one()
                oldest = (
                    await session.execute(
                        select(sa_func.min(HrMessage.datetime_created)).where(
                            HrMessage.dead_letter.is_(False)
                        )
                    )
                ).scalar_one()
                last_err = (
                    await session.execute(
                        select(HrMessage.last_error)
                        .where(HrMessage.last_error.is_not(None))
                        .order_by(HrMessage.id.desc())
                        .limit(1)
                    )
                ).scalar_one_or_none()
            return {
                "pending": int(pending or 0),
                "dead_letter": int(dead or 0),
                "oldest_pending": oldest,
                "last_error": last_err,
                "db_ok": True,
            }
        except SQLAlchemyError as e:
            self._logger.error("Database error reading outbox health: %s", str(e))
            return {
                "pending": 0,
                "dead_letter": 0,
                "oldest_pending": None,
                "last_error": str(e)[:200],
                "db_ok": False,
            }


async def _smoke():
    repo = MomRepository()
    due = await repo.get_due_pending_messages(limit=3)
    if not due:
        print("No due HR messages.")
        return
    for m in due:
        print(m.id, m.attempt_count, m.next_retry_at, m.message[:60])


if __name__ == "__main__":
    asyncio.run(_smoke())
