import time
from collections import defaultdict

MAX_ATTEMPTS = 5
WINDOW_SECONDS = 900  # 15 minutes


class LoginRateLimiter:
    """
    In-memory rate limiter for login attempts.
    Blocks a username after MAX_ATTEMPTS failed attempts within WINDOW_SECONDS.
    """

    def __init__(self):
        self._failures: dict[str, list[float]] = defaultdict(list)

    def _prune(self, username: str) -> None:
        cutoff = time.monotonic() - WINDOW_SECONDS
        self._failures[username] = [t for t in self._failures[username] if t > cutoff]

    def is_locked(self, username: str) -> tuple[bool, int]:
        """Return (locked, seconds_remaining). seconds_remaining is 0 when not locked."""
        self._prune(username)
        attempts = self._failures[username]
        if len(attempts) >= MAX_ATTEMPTS:
            oldest = attempts[0]
            remaining = int(WINDOW_SECONDS - (time.monotonic() - oldest))
            return True, max(remaining, 0)
        return False, 0

    def record_failure(self, username: str) -> None:
        self._prune(username)
        self._failures[username].append(time.monotonic())

    def reset(self, username: str) -> None:
        self._failures.pop(username, None)

    def attempts_remaining(self, username: str) -> int:
        self._prune(username)
        return max(MAX_ATTEMPTS - len(self._failures[username]), 0)


# Single shared instance for the lifetime of the process
login_rate_limiter = LoginRateLimiter()
