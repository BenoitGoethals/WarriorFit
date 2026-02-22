from datetime import datetime
from typing import Optional, List, Any

from sqlalchemy import select, delete, func, or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from warriorfit.core.role import Role
from warriorfit.data.model.db_model import User
from warriorfit.data.repositories.abc_repository import ABCRepository
from sqlalchemy import or_


class UserRepository(ABCRepository):
    def __init__(self, config=None):
        super().__init__(config=config)

    async def add_user(self, user: User) -> Optional[User]:
        """
        Adds a new user to the database asynchronously.

        The function attempts to add a user to the database using an asynchronous session. Upon
        successful addition, it refreshes the user instance to reflect the changes made in the database.
        If any database-related errors occur, such as integrity constraint violations or other SQLAlchemy
        errors, they are logged, and the function returns None.

        :param user: The `User` instance to be added to the database.
        :type user: User
        :return: The added `User` instance if successful. Otherwise, returns `None` if an error occurs.
        :rtype: Optional[User]
        """
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    user.created_at = datetime.now()
                    session.add(user)
                await session.refresh(user)
                return user
        except IntegrityError as e:
            self._logger.error("Integrity error adding user %s: %s", user.username, str(e))
            return None
        except SQLAlchemyError as e:
            self._logger.error("Database error adding user %s: %s", user.username, str(e))
            return None

    async def user_mail_exist(self, mail: str) -> bool:
        """
        Checks if a user with the specified email exists in the database.

        :param mail: The email address to check for existence.
        :type mail: str
        :return: A boolean indicating whether the email exists (`True`) or not (`False`).
        :rtype: bool
        """
        query = select(User).where(User.email == mail)
        results = await self.fetch_and_log(query, "user")
        return results is not None

    async def get_user_by_id(self, id_unique: int) -> Optional[User]:
        """
        Retrieve a user by their unique identifier.

        This method queries the database to find a single user that matches the
        given unique identifier. If a matching user is found, it is returned;
        otherwise, None is returned.

        :param id_unique: The unique identifier of the user to retrieve.
        :type id_unique: int
        :return: A User instance if found, otherwise None.
        :rtype: Optional[User]
        """
        query = select(User).where(User.id == id_unique)
        results = await self.fetch_and_log(query, "user")
        return results[0] if results else None

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Fetches a user from the database by their username.

        :param username: The username of the user to fetch.
        :type username: str
        :return: User object if found, otherwise None.
        :rtype: Optional[User]
        """
        query = select(User).where(User.username == username)
        results = await self.fetch_and_log(query, "user")
        return results[0] if results else None

    async def get_all_users(self) -> List[User]:
        """
        Fetches all users from the database.

        :return: A list of User objects.
        :rtype: List[User]
        """
        query = select(User)
        results = await self.fetch_and_log(query, "users")
        return results if results else []

    async def update_user(self, id: int, user: User) -> User | None:
        """
        Updates an existing user in the database.

        :param id: The ID of the user to update.
        :type id: int
        :param user: The User object containing updated information.
        :type user: User
        :return: The updated User object if successful, otherwise None.
        :rtype: Optional[User]
        """
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    existing_user = await session.get(User, id)
                    if not existing_user:
                        self._logger.error("User with ID %d not found.", id)
                        return None
                    existing_user.username = user.username
                    existing_user.password_hash = user.password_hash
                    existing_user.email = user.email
                    existing_user.role = user.role
                    existing_user.serial_number = user.serial_number
                    existing_user.is_active = user.is_active
                    await session.flush()
                    await session.refresh(existing_user)
                    return existing_user
        except IntegrityError as e:
            self._logger.error("Integrity error updating user %d: %s", id, str(e))
            return None
        except SQLAlchemyError as e:
            self._logger.error("Database error updating user %d: %s", id, str(e))
            return None

    async def delete_all_users(self):
        """
        Deletes all users from the database.

        :return: None
        """
        query = delete(User)
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    await session.execute(query)
                    await session.commit()
            self._logger.info("All users deleted successfully.")
        except SQLAlchemyError as e:
            self._logger.error("Error deleting all users: %s", e)

    async def check_user(self, user_name: str, plain_password: str) -> bool:
        """
        Checks if the provided username and password match an entry in the database.

        :param user_name: The username to verify.
        :param plain_password: The plain-text password to verify.
        :return: True if the username and password are valid; otherwise, False.
        """
        from warriorfit.security.auth_service import Auth
        try:
            async with self.SessionLocal() as session:
                query = select(User).where(User.username == user_name)
                result = await session.execute(query)
                user = result.scalar_one_or_none()
                if user is None:
                    self._logger.info("User '%s' not found.", user_name)
                    return False
                if not user.password_hash:
                    self._logger.error("User '%s' has no password set.", user_name)
                    return False
                if Auth.verify_password(plain_password, user.password_hash):
                    self._logger.info("User '%s' authenticated successfully.", user_name)
                    return True
                self._logger.info("Password mismatch for user '%s'.", user_name)
                return False
        except SQLAlchemyError as e:
            self._logger.error("Database error in check_user: %s", e)
            return False

    async def delete_user(self, id):
        """
        Deletes a user by ID from the database.

        :param id: The ID of the user to delete.
        :type id: int
        :return: True if the user was deleted successfully, otherwise False.
        :rtype: bool
        """
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    query = delete(User).where(User.id == id)
                    result = await session.execute(query)
                    if result.rowcount == 0:
                        self._logger.error("No user found with ID %d.", id)
                        return False
                    await session.commit()
            self._logger.info("User with ID %d deleted successfully.", id)
            return True
        except SQLAlchemyError as e:
            self._logger.error("Database error deleting user with ID %d: %s", id, str(e))
            return False

    async def serial_exists(self, serial: str) -> bool:
        """
        Check whether a user with a specified serial number exists in the database.

        The function queries the database for a user whose serial number matches
        the given `serial`. If such a user exists, the function returns `True`;
        otherwise, it returns `False`. Any database-related errors or unexpected
        exceptions are logged accordingly, and in such cases, the function
        returns `False`.

        :param serial: The serial number of the user to check.
        :type serial: str
        :return: True if the user exists; otherwise, False.
        :rtype: bool
        """
        try:
            async with self.SessionLocal() as session:
                query = select(User).where(User.serial_number == serial)
                result = await session.execute(query)
                user = result.scalar_one_or_none()
                if user is None:
                    self._logger.info("User '%s' not found.", serial)
                    return False
                return True
        except SQLAlchemyError as e:
            self._logger.error("Database error in check_user: %s", e)
            return False

    async def delete_user_by_serial(self, selected_serial):
        """
        Deletes a user from the database based on a provided serial number. The function
        executes an asynchronous database operation to find and delete the user with
        the given serial number. If no user with the provided serial number is found
        or an error occurs during execution, it logs the relevant error and returns
        False. If the deletion succeeds, it returns True.

        :param selected_serial: Serial number identifying the user to be deleted
        :type selected_serial: Any
        :return: True if the user is successfully deleted, False otherwise
        :rtype: bool
        """
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    query = delete(User).where(User.serial_number == selected_serial)
                    result = await session.execute(query)
                    if result.rowcount == 0:
                        self._logger.error(
                            "No user found with serial %s.", selected_serial
                        )
                        return False
                    return True
        except SQLAlchemyError as e:
            self._logger.error(
                "Database error deleting user with serial %s: %s", selected_serial, str(e)
            )
            return False

    async def update_user_by_serial(self, user):
        """
        Updates an existing user in the database based on the provided user instance. It uses the
        `serial_number` attribute to locate the user record. If the user with the given serial
        number does not exist, an error is logged, and `None` is returned. The user fields provided
        are updated and persisted back to the database. Error handling is included for potential
        database constraint violations as well as general SQLAlchemy-related errors.

        :param user: The user instance containing the updated values to be applied.
        :type user: User
        :return: The updated user instance if update succeeds, `None` if the user is not found or an
            error occurs.
        :rtype: User or None
        :raises IntegrityError: If a database constraint error occurs during the update process.
        :raises SQLAlchemyError: If a generic SQLAlchemy error occurs during the update process.
        """
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    existing_user = (
                        await session.execute(
                            select(User).where(User.serial_number == user.serial_number)
                        )
                    ).scalar_one_or_none()
                    if not existing_user:
                        self._logger.error(
                            "User with serial number %s not found.", user.serial_number
                        )
                        return None
                    existing_user.username = user.username
                    existing_user.password_hash = user.password_hash
                    existing_user.email = user.email
                    existing_user.role = user.role
                    existing_user.serial_number = user.serial_number
                    await session.flush()
                    await session.refresh(existing_user)
                    return existing_user

        except IntegrityError as e:
            self._logger.error("Integrity error updating user %s: %s", id, str(e))
            return None
        except SQLAlchemyError as e:
            self._logger.error("Database error updating user %s: %s", id, str(e))
            return None

    async def get_all_pti(self) -> list[Any] | None:
        try:
            query = select(User).where(
                or_(
                    User.role == Role.PTI,
                    User.role == Role.ADMIN,
                    User.role == Role.APTI,
                    User.role == Role.PLANNER,
                )
            )
            results = await self.fetch_and_log(query, "user")
            return results
        except SQLAlchemyError as e:
            self._logger.error("Database error fetching all pti: %s", str(e))
            return None

    async def get_user_by_serial(self, serial_number) -> User | None:
        query = select(User).where(User.serial_number == serial_number)
        results = await self.fetch_and_log(query, "user")
        return results[0] if results else None
