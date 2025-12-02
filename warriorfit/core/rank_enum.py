from enum import IntEnum

from warriorfit.data.model.enum_mapped_user_model import IntEnumType


class Rank(IntEnum):
    """
    Represents military ranks in an enumeration, categorized by Volunteers, NCOs,
    Officers, and General Officers.

    The class provides an integer representation of each rank and includes a string
    representation method for displaying the ranks in a human-readable format.

    """
    # Volunteers
    SOLDIER = 1
    FIRST_SOLDIER = 2
    CORPORAL = 3
    CHIEF_CORPORAL = 4
    FIRST_CHIEF_CORPORAL = 5

    # NCOs
    SERGEANT = 6
    FIRST_SERGEANT = 7
    FIRST_SERGEANT_CHIEF = 8
    FIRST_SERGEANT_MAJOR = 9
    ADJUTANT = 10
    CHIEF_ADJUTANT = 11
    MAJOR_ADJUTANT = 12

    # Officers
    SECOND_LIEUTENANT = 13
    LIEUTENANT = 14
    CAPTAIN = 15
    CAPTAIN_COMMANDANT = 16
    MAJOR = 17
    LIEUTENANT_COLONEL = 18
    COLONEL = 19

    # General Officers
    BRIGADIER_GENERAL = 20
    MAJOR_GENERAL = 21
    LIEUTENANT_GENERAL = 22
    GENERAL = 23

    def __str__(self):
        return self.name.replace("_", " ").title()


if __name__ == "__main__":
    print(Rank.CAPTAIN)
    print(Rank.CAPTAIN.value)
    print(Rank(15))
    print(IntEnumType(Rank))
    r=Rank.CAPTAIN
    print(r)