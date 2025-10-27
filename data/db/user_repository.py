import logging
from typing import Optional, List

import bcrypt
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from data.db.abc_repository import ABCRepository
from data.db.db_model import User


class UserRepository(ABCRepository):
    def __init__(self):
        super().__init__()
        self.__logger = logging.getLogger(__name__)
    async def add_user(self, user: User) -> Optional[User]:
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    session.add(user)
                await session.refresh(user)
                return user
        except IntegrityError as e:
            self.__logger.error(
                f"Integrity error adding user {user.username}: {str(e)}"
            )
            return None
        except SQLAlchemyError as e:
            self.__logger.error(f"Database error adding user {user.username}: {str(e)}")
            return None

    async def user_mail_exist(self,mail:str)->bool:
        query = select(User).where(User.email==mail)
        results = await self.fetch_and_log(query, "user")
        return results is not None

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
                        self.__logger.error(f"User with ID {id} not found.")
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
            self.__logger.error(f"Integrity error updating user {id}: {str(e)}")
            return None
        except SQLAlchemyError as e:
            self.__logger.error(f"Database error updating user {id}: {str(e)}")
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
            self.__logger.info("All users deleted successfully.")
        except SQLAlchemyError as e:
            self.__logger.error(f"Error deleting all users: {e}")
        except Exception as e:
            self.__logger.error(f"Unexpected error deleting all users: {e}")

    async def check_user(self, user_name: str, plain_password: str) -> bool:
        """
        Securely checks if the provided username and password match an entry in the database.

        :param user_name: The username to verify.
        :param plain_password: The plain-text password to verify.
        :return: True if the username and password are valid; otherwise, False.
        """
        try:
            async with self.SessionLocal() as session:
                query = select(User).where(User.username == user_name)
                result = await session.execute(query)
                user = result.scalar_one_or_none()
                if user is None:
                    self.__logger.info(f"User '{user_name}' not found.")
                    return False
                password_matches = bcrypt.checkpw(
                    plain_password.encode("utf-8"),
                    user.password_hash.encode("utf-8"),
                )
                if not password_matches:
                    self.__logger.info("Password mismatch.")
                    return False
                self.__logger.info(f"User '{user_name}' authenticated successfully.")
                return True
        except SQLAlchemyError as e:
            self.__logger.error(f"Database error in check_user: {e}")
            return False
        except Exception as e:
            self.__logger.error(f"Unexpected error in check_user: {e}")
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
                        self.__logger.error(f"No user found with ID {id}.")
                        return False
                    await session.commit()
            self.__logger.info(f"User with ID {id} deleted successfully.")
            return True
        except SQLAlchemyError as e:
            self.__logger.error(f"Database error deleting user with ID {id}: {str(e)}")
            return False
        except Exception as e:
            self.__logger.error(
                f"Unexpected error deleting user with ID {id}: {str(e)}"
            )
            return False

    async def serial_exists(self, serial: str) -> bool:
        try:
            async with self.SessionLocal() as session:
                query = select(User).where(User.serial_number == serial)
                result = await session.execute(query)
                user = result.scalar_one_or_none()
                if user is None:
                    self.__logger.info(f"User '{serial}' not found.")
                    return False
                return True
        except SQLAlchemyError as e:
            self.__logger.error(f"Database error in check_user: {e}")
            return False
        except Exception as e:
            self.__logger.error(f"Unexpected error in check_user: {e}")
            return False

    async def delete_user_by_serial(self, selected_serial):
        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    query = delete(User).where(User.serial_number == selected_serial)
                    result = await session.execute(query)
                    if result.rowcount == 0:
                        self.__logger.error(f"No user found with serial {selected_serial}.")
                        return False
                    return True
        except SQLAlchemyError as e:
            self.__logger.error(f"Database error deleting user with serial {selected_serial}: {str(e)}")
            return False
        except Exception as e:
            self.__logger.error(f"Unexpected error deleting user with serial {selected_serial}: {str(e)}")
            return False

    async def update_user_by_serial(self, user):

        try:
            async with self.SessionLocal() as session:
                async with session.begin():
                    existing_user = (await session.execute(
                        select(User).where(User.serial_number == user.serial_number)
                    )).scalar_one_or_none()
                    if not existing_user:
                        self.__logger.error(f"User with serial number {user.serial_number} not found.")
                        return None

                    # Update fields

                    existing_user.username = user.username
                    existing_user.password_hash = user.password_hash
                    existing_user.email = user.email
                    existing_user.role = user.role
                    existing_user.serial_number = user.serial_number

                    await session.flush()  # Ensure changes are applied
                    await session.refresh(existing_user)  # Refresh to get updated data
                    return existing_user

        except IntegrityError as e:
            self.__logger.error(f"Integrity error updating user {id}: {str(e)}")
            return None
        except SQLAlchemyError as e:
            self.__logger.error(f"Database error updating user {id}: {str(e)}")
            return None