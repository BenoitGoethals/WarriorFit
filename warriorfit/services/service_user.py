"""
User database service class for managing user-related database operations.
"""

from warriorfit.logic.singleton import Singleton
from warriorfit.services.service import Service


class UserService(Service, metaclass=Singleton):
    """
    User database service class for managing user-related database operations.
    """

    def __init__(self):
        super().__init__()

    async def check_user(self, username_login, password_login):
        """
        Checks if a user exists in the system by username and verifies their active status.

        This asynchronous method retrieves a user based on the provided username and
        returns the user if they are marked as active. If the user is either not active
        or does not exist, the method returns None.

        :param username_login: The username used to identify the user.
        :type username_login: str
        :param password_login: The password associated with the username.
        :type password_login: str
        :return: The user object if the user exists and is active, or None if the user
                 is inactive or does not exist.
        :rtype: User or None
        """
        user = await self._user_repo.get_user_by_username(username_login)
        if user.is_active:
            return user
        return None


    async def get_user_by_username(self, username_login):
        return await self._user_repo.get_user_by_username(username_login)

    async def get_all_users(self):
        return await self._user_repo.get_all_users()

    async def serial_exists(self, param):
        return await self._user_repo.serial_exists(param)

    async def user_mail_exist(self, email):
        return await self._user_repo.user_mail_exist(email)

    async def add_user(self, user):
        """
        Add a new user to the system and log the action.

        This asynchronous method interacts with the repository to add a user
        object to the system and subsequently records an audit log of the
        addition action.

        :param user: The user object containing the details of the user to
            be added.
        :type user: User
        :return: The newly added user object if the operation is successful,
            otherwise None.
        :rtype: User | None
        """
        user = await self._user_repo.add_user(user)
        if user:
            await self.add_audit_log(
                details=f"User {user.username} added", action="add"
            )
        return user

    async def update_user(self, user_id, user):
        """
        Updates an existing user in the system.

        This method interacts with a user repository to update the user
        details for the specified user_id. If the user is successfully
        updated, an audit log entry is created containing information
        about the update operation.

        :param user_id: The unique identifier of the user to update.
        :type user_id: int
        :param user: The user object containing updated information.
        :type user: User
        :return: The updated user object if the operation is successful, otherwise None.
        :rtype: User
        """
        user = await self._user_repo.update_user(user_id, user)
        if user:
            await self.add_audit_log(
                details=f"User {user.username} updated", action="update"
            )
        return user

    async def delete_user_by_serial(self, serial):
        """
        Deletes a user based on the provided serial number and logs the action if successful.

        This asynchronous method removes a user's data by their unique serial number using the
        user repository. If the deletion operation succeeds, it records the event into an audit
        log with relevant details.

        :param serial: Serial number of the user to be deleted.
        :type serial: str
        :return: A boolean indicating whether the deletion was successful.
        :rtype: bool
        """
        is_deleted = await self._user_repo.delete_user_by_serial(serial)
        if is_deleted:
            await self.add_audit_log(details=f"User {serial} deleted", action="delete")
        return is_deleted

    async def get_user_by_id(self, id):
        return await self._user_repo.get_user_by_id(id)
