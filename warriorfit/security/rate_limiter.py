import time
from collections import defaultdict

MAX_ATTEMPTS = 5
WINDOW_SECONDS = 900  # 15 minutes


class LoginRateLimiter:
    """
    In-memory rate limiter for login attempts.
    Blocks a username after MAX_ATTEMPTS failed attempts within WINDOW_SECONDS.
    """

    def __init__(self) -> None:
        self._failures: dict[str, list[float]] = defaultdict(list)

    def _prune(self, username: str) -> None:
        """
        Prunes outdated login failure timestamps for a given username.

        The method removes timestamps that are older than a specified cutoff
        defined by the `WINDOW_SECONDS` constant. This ensures that only
        recent login failures are retained in the record for throttling or
        monitoring purposes.

        :param username: The username for which outdated failure timestamps
            should be removed.
        :type username: str
        :return: None
        """
        cutoff = time.monotonic() - WINDOW_SECONDS
        self._failures[username] = [t for t in self._failures[username] if t > cutoff]

    def is_locked(self, username: str) -> tuple[bool, int]:
        """
        Determine if the username is currently locked due to failed attempts.

        This function checks whether the specified username has exceeded the maximum
        number of allowed login attempts within the configured time window. If the
        maximum number of attempts is reached, the username is considered locked, and
        the time remaining until the lock expires is returned.

        :param username: The username to check for locked status.
        :return: A tuple containing a boolean indicating whether the username is
            locked and the remaining lock time in seconds if locked, or 0 if not locked.

        """
        self._prune(username)
        attempts = self._failures[username]
        if len(attempts) >= MAX_ATTEMPTS:
            oldest = attempts[0]
            remaining = int(WINDOW_SECONDS - (time.monotonic() - oldest))
            return True, max(remaining, 0)
        return False, 0

    def record_failure(self, username: str) -> None:
        """
        Records a failure for a specific user by appending the current time to the user's
        failure history. This method only interacts with the user's failure data.

        :param username: The username of the user for whom the failure is being recorded.
        :type username: str
        """
        self._prune(username)
        self._failures[username].append(time.monotonic())

    def reset(self, username: str) -> None:
        """
        Resets the failure count for a specific user.

        Removes the given user's failure entry from the tracking structure, effectively
        resetting their failure count to zero.

        :param username: The username whose failure count is to be reset.
        :type username: str
        :return: None
        """
        self._failures.pop(username, None)

    def attempts_remaining(self, username: str) -> int:
        """
        Calculate the remaining login attempts for the specified username.

        This method determines the remaining number of failed login attempts
        allowed for a given user. It considers the allowed maximum attempts
        (`MAX_ATTEMPTS`) and the number of failures already recorded for the
        user. The method also ensures that outdated failure data is pruned
        before performing the calculation.

        :param username: The username for which to calculate the remaining login
            attempts.
        :type username: str
        :return: The number of remaining allowed login attempts. If no failures
            have been recorded for the user, returns `MAX_ATTEMPTS`. If the
            recorded failures exceed the allowed limit, returns `0`.
        :rtype: int
        """
        self._prune(username)
        return max(MAX_ATTEMPTS - len(self._failures[username]), 0)


# Single shared instance for the lifetime of the process
login_rate_limiter = LoginRateLimiter()
