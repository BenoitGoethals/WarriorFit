from enum import Enum


class Gender(Enum):
    M = "M"
    F = "F"

    @classmethod
    def literals(cls) -> list[str]:
        return [member.value for member in cls]

    def to_literal(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.value
