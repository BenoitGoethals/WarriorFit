from enum import Enum


class MfftLevel(Enum):
    """Achievement tier on an MFFT Eval event or overall evaluation.

    Ordering (high -> low): GOLD > SILVER > BRONZE > FIT > UNFIT.
    FIT is the lowest COMBAT-passing threshold; UNFIT means the value did
    not even reach the FIT threshold.
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
