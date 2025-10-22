import enum
from typing import Optional

class ReportType(enum.Enum):
    PHEF = 1
    FUNCTIONAL = 2
    COMBAT = 3
    SWIMMING = 4

    @staticmethod
    def from_str(test_type: Optional[str]) -> "ReportType":
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