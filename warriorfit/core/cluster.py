from enum import Enum


class Cluster(Enum):
    """Land Component personnel cluster used to pick the MFFT Eval scoring scale."""

    COMBAT = "COMBAT"
    ENABLER = "ENABLER"
    OPS_SP = "OPS_SP"
    TER_SP = "TER_SP"
    NON_DEP = "NON_DEP"

    @classmethod
    def literals(cls) -> list[str]:
        return [member.value for member in cls]

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.value
