from enum import Enum


class TypeFitnessTest(Enum):
    PHEF = ("PHEF",)
    COMBAT = ("COMBAT",)
    FUNCTIONAL = "FUNCTIONAL"
    SWIMMING = "SWIMMING"
    MFFT_EVAL = "MFFT_EVAL"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.value
