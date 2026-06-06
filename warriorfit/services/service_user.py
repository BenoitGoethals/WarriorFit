"""
User database service class for managing user-related database operations.
"""

from warriorfit.services.service import Service


class UserService(Service):
    """
    User database service class for managing user-related database operations.
    """

    def __init__(self, user_repository=None, config=None):
        super().__init__(user_repository=user_repository, config=config)

    async def check_user(self, username_login, password_login):
        """
        Checks if the provided username and password match the credentials stored in the repository.

        :param username_login: The username to check.
        :type username_login: str
        :param password_login: The password to check.
        :type password_login: str
        :return: A boolean indicating whether the provided credentials are valid.
        :rtype: bool
        """
        return await self._user_repo.check_user(username_login, password_login)

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
            await self.add_audit_log(details=f"User {user.username} added", action="add")
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
            await self.add_audit_log(details=f"User {user.username} updated", action="update")
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
        """
        Retrieve a user by their unique identifier.

        This asynchronous method retrieves user data by querying the underlying user
        repository using the provided unique identifier. It is commonly used to fetch
        specific user details from the database or storage system.

        :param id: The unique identifier of the user.
        :type id: Any
        :return: The user object corresponding to the given ID.
        :rtype: Any
        """
        return await self._user_repo.get_user_by_id(id)
