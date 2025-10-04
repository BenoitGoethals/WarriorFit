import enum


class ReportGeneratorTypeOutput(enum.Enum):
    PDF = 1
    CSV = 2


class ReportType(enum.Enum):
    PHEF = 1
    FUNCTIONAL = 2
    COMBAT = 3
    SWIMMING = 4