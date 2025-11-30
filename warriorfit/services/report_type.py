import enum
from typing import Optional


class ReportType(enum.Enum):
    """
    Enumeration of report types.

    Defines a set of report types that can be used to categorize tests or
    other entities based on their type. The `ReportType` enumeration ensures
    consistency and eliminates ambiguity when dealing with predefined report
    categories.

    :ivar PHEF: Represents a PHEF report type.
    :type PHEF: int
    :ivar FUNCTIONAL: Represents a functional report type.
    :type FUNCTIONAL: int
    :ivar COMBAT: Represents a combat report type.
    :type COMBAT: int
    :ivar SWIMMING: Represents a swimming report type.
    :type SWIMMING: int
    """
    PHEF = 1
    FUNCTIONAL = 2
    COMBAT = 3
    SWIMMING = 4

    @staticmethod
    def from_str(test_type: Optional[str]) -> "ReportType":
        """
        Parses a given string to determine the corresponding `ReportType` enumeration value.

        This method attempts to match a string representation of a report type
        to a predefined set of report type mappings. The input string is first
        normalized (trimmed and converted to uppercase). If the normalized value
        does not match any of the predefined report types, a `ValueError` is raised.

        :param test_type: A string representation of the report type to be parsed.
                          This string can be any case and may contain surrounding spaces.
        :return: An instance of `ReportType` corresponding to the provided
                 string representation.
        :rtype: ReportType
        :raises ValueError: If the input string does not match any known report type.
        """
        key = (test_type or "").strip().upper()
        mapping = {
            "PHEF": ReportType.PHEF,
            "FUNCTIONAL": ReportType.FUNCTIONAL,
            "COMBAT": ReportType.COMBAT,
            "SWIMMING": ReportType.SWIMMING,
        }
        rt = mapping.get(key)
        if rt is None:
            raise ValueError(f"Unknown report type: {test_type!r}")
        return rt
