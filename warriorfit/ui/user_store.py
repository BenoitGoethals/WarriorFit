from shiny.session import get_current_session

from warriorfit.data.model.db_model import User

_SESSION_USER_ATTR = "user"


class UserStore:
    """Per-session user accessor backed by the active Shiny session.

    The previous implementation stored the user on a process-global Singleton,
    which leaked authentication state between concurrent sessions and was not
    cleared on logout. State now lives on the active Shiny session object,
    so isolation and lifecycle are handled by Shiny itself. See issue #216.
    """

    @classmethod
    def set_user(cls, user: User | None) -> None:
        session = get_current_session()
        if session is None:
            return
        setattr(session, _SESSION_USER_ATTR, user)

    @classmethod
    def get_user(cls) -> User | None:
        session = get_current_session()
        if session is None:
            return None
        return getattr(session, _SESSION_USER_ATTR, None)

    @classmethod
    def logout(cls) -> None:
        session = get_current_session()
        if session is None:
            return
        if hasattr(session, _SESSION_USER_ATTR):
            delattr(session, _SESSION_USER_ATTR)
