from enum import Enum


class MfftLevel(Enum):
    """
    Enumeration representing different levels of MFFT (Modified Functional Fitness Test).

    This enumeration defines the levels of MFFT and their relationships, enabling comparison
    of tiers using relational operators. Each level corresponds to a hierarchical fitness rating.

    :ivar GOLD: Represents the highest tier of MFFT level.
    :type GOLD: MfftLevel
    :ivar SILVER: Represents the second highest tier of MFFT level.
    :type SILVER: MfftLevel
    :ivar BRONZE: Represents the third highest tier of MFFT level.
    :type BRONZE: MfftLevel
    :ivar FIT: Represents a moderate tier of MFFT level, indicating general readiness.
    :type FIT: MfftLevel
    :ivar UNFIT: Represents the lowest tier of MFFT level, indicating lack of fitness.
    :type UNFIT: MfftLevel
    """

    GOLD = "GOLD"
    SILVER = "SILVER"
    BRONZE = "BRONZE"
    FIT = "FIT"
    UNFIT = "UNFIT"

    @property
    def rank(self) -> int:
        """Higher number = better tier. UNFIT = 0."""
        return _RANK[self]

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, MfftLevel):
            return NotImplemented
        return self.rank >= other.rank

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, MfftLevel):
            return NotImplemented
        return self.rank > other.rank

    def __le__(self, other: object) -> bool:
        if not isinstance(other, MfftLevel):
            return NotImplemented
        return self.rank <= other.rank

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, MfftLevel):
            return NotImplemented
        return self.rank < other.rank

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.value


_RANK: dict[MfftLevel, int] = {
    MfftLevel.UNFIT: 0,
    MfftLevel.FIT: 1,
    MfftLevel.BRONZE: 2,
    MfftLevel.SILVER: 3,
    MfftLevel.GOLD: 4,
}
