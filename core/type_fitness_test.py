from enum import Enum


class TypeFitnessTest(Enum):
    PHEF = "PHEF",
    COMBAT = "COMBAT",
    FUNCTIONAL = "FUNCTIONAL"
    SWIMMING = "SWIMMING"

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value
