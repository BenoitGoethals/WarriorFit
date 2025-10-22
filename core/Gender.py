from enum import Enum

class Gender(Enum):
    MALE = "M"
    FEMALE = "F"

    def __str__(self):
        return self.value
    def __repr__(self):
        return self.value

