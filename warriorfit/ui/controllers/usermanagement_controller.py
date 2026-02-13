# Python
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Tuple, Optional

import pandas as pd

from warriorfit.data.model.db_model import User, Role
from warriorfit.security.auth_service import Auth
from warriorfit.services.military_service import MilitaryService
from warriorfit.services.service_user import UserService


@dataclass
class UserForm:
    serial: str
    username: str
    password: str
    email: str
    role: str
    is_active: str


class UserManagementController:
    """
    Handles user management operations such as creating, updating, validating, and
    deleting users. This controller interacts with underlying services to manage
    user-related data and provides methods to perform specific operations.

    The class includes utilities for validating user input, checking existing
    records, and managing current user sessions, as well as providing role-based
    options for user creation and updates.

    :ivar selected_user: The currently selected user for update or validation operations.
    :type selected_user: Optional[UserForm]
    """

    EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
    USER_REGEX = re.compile(r"^[a-zA-Z0-9_]+$")

    def __init__(
        self,
        mil_service: MilitaryService = None,
        user_service: UserService = None,
    ):
        self.be_mil = mil_service if mil_service is not None else MilitaryService()
        self._service = user_service if user_service is not None else UserService()
        self.selected_user = None

    @staticmethod
    def role_choices() -> List[str]:
        """
        Builds a list of role choices based on the enumerated type `Role`.

        This static method extracts all possible role values from the `Role`
        enumeration. It attempts two approaches: first, by accessing the `value`
        attribute of each role in the `Role` enumeration, and secondly, by
        converting the role objects to their string representation if the `value`
        attribute is not available. If both approaches fail, it raises a runtime
        exception.

        :return: A list of role choices extracted from the `Role` enumeration.
        :rtype: List[str]

        :raises RuntimeError: If the method fails to construct role choices for
            any reason, including unexpected errors during enumeration.
        """
        try:
            return [r.value for r in Role]
        except AttributeError:
            return [str(r) for r in Role]
        except (TypeError, ValueError) as exc:
            raise RuntimeError("Failed to build role choices") from exc

    async def list_users_df(self) -> pd.DataFrame:
        """
        Generate a pandas DataFrame of users.

        This asynchronous method fetches a list of all users and converts it into
        a structured pandas DataFrame. The DataFrame includes details such as
        serial number, ID, username, email, role, active status, password hash,
        and account creation date.

        :return: A pandas DataFrame containing user information.
        :rtype: pd.DataFrame
        """
        users = await self._service.get_all_users()
        return pd.DataFrame(
            [
                {
                    "Serial": u.serial_number,
                    "ID": u.id,
                    "Username": u.username,
                    "Email": u.email,
                    "Role": str(u.role),
                    "Active": bool(u.is_active),
                    "Password": u.password_hash,
                    "Created": getattr(u.created_at, "date", lambda: "")(),
                }
                for u in users
            ]
        )

    async def validate(self, form: UserForm, *, is_update: bool) -> Tuple[bool, str]:
        """
        Validates the user form input to ensure all required fields are correctly filled,
        checks for unique constraints on serial, email, and username, and validates the
        email format against a predefined regex. The validation logic differs based on
        whether it's an update operation or a new record creation.

        :param form: The user form data containing fields such as serial, username,
                     password, email, and role.
        :type form: UserForm
        :param is_update: Indicates whether the operation is an update or a new
                          record creation.
        :type is_update: bool
        :return: A tuple where the first element is a boolean indicating if the
                 validation passed and the second element is a string providing
                 informative feedback on validation failures or success.
        :rtype: Tuple[bool, str]
        """
        req = ["serial", "username", "password", "email", "role"]
        for f in req:
            if not getattr(form, f, "").strip():
                return False, f"Field '{f}' is required."
        if "@" not in form.email or "." not in form.email.split("@")[-1]:
            return False, "Invalid email address."
        if not self.USER_REGEX.match(form.username) or not (
            3 < len(form.username) < 30
        ):
            return (
                False,
                "Username must be valid (a..z,A..Z,0..9,_). Length must be between 3 and 30. ",
            )
        exists = await self._service.serial_exists(form.serial.strip())
        mail_unique = await self._service.user_mail_exist(form.email)
        user_name_exist = await self._service.get_user_by_username(form.username)
        is_email_well_formed = self.EMAIL_REGEX.match(form.email) is not None
        if not is_email_well_formed:
            return False, "Invalid email address."
        if is_update:
            if form.serial.strip() != (self.selected_user.serial or "") and exists:
                return False, f"Serial '{form.serial}' already exists."

            if form.email.strip() != (self.selected_user.email or "") and mail_unique:
                return (False, f"User with email '{form.email}' already exists.")
            if (
                form.username.strip() != (self.selected_user.username or "")
                and user_name_exist
            ):
                return (False, f"User with username '{form.username}' already exists.")
        else:
            if exists:
                return False, f"Serial '{form.serial}' already exists."
            if mail_unique:
                return (False, f"User with email '{form.email}' already exists.")
            if user_name_exist:
                return (False, f"User with username '{form.username}' already exists.")

        return True, "OK"

    def set_selected_user(self, user: UserForm):
        """
        Sets the currently selected user.

        :param user: The user to be set as the selected user.
        :type user: UserForm
        """
        self.selected_user = user

    async def create_user(self, form: UserForm) -> Optional[User]:
        """
        Creates a new user using provided form data and adds it to the user service.

        This method initializes a new user object, populates it with the data from
        the provided form, hashes the password for secure storage, and delegates
        user addition to an underlying service.

        :param form: The form containing user data required to create a new user.
        :type form: UserForm
        :return: The created user object if successful, or None otherwise.
        :rtype: Optional[User]
        """
        user = User()
        user.serial_number = form.serial
        user.username = form.username
        user.password_hash = Auth.hash_password(form.password)
        user.email = form.email
        user.role = form.role
        user.is_active = form.is_active
        return await self._service.add_user(user)

    async def update_user(self, user_id: int | None, form: UserForm) -> bool:
        """
        Updates a user's information asynchronously based on the provided user ID and form data.

        This function modifies user attributes and persists these updates using the
        service's update functionality. It ensures all changes, including sensitive
        fields such as passwords, are properly handled before being saved.

        :param user_id: The ID of the user to be updated. If None, a new user will be created.
        :type user_id: int or None
        :param form: A form instance containing updated user details such as username,
            password, email, role, and active status.
        :type form: UserForm
        :return: A boolean indicating whether the update operation was successful.
        :rtype: bool
        """
        user = User()
        user.id = user_id
        user.serial_number = form.serial
        user.username = form.username
        user.password_hash = Auth.hash_password(form.password)
        user.email = form.email
        user.role = form.role
        user.is_active = form.is_active
        updated = await self._service.update_user(user_id, user)
        return bool(updated)

    async def delete_user_by_serial(self, serial: str | None) -> bool:
        """
        Deletes a user by their serial identifier asynchronously. It interacts with
        the service layer to perform the deletion and returns a boolean indicating
        whether the operation was successful.

        :param serial: The serial identifier of the user to be deleted. It can be
          a string or None.
        :return: A boolean value indicating whether the deletion was successful.
        """
        return await self._service.delete_user_by_serial(serial)
