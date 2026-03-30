from enum import Enum


class Gender(Enum):
    M = "M"
    F = "F"

    @classmethod
    def literals(cls) -> list[str]:
        return [member.value for member in cls]

    def to_literal(self):
        return self.name

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value
