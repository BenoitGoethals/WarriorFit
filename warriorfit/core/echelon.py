from enum import Enum


class Echelon(str, Enum):
    BATTALION = "BATTALION"
    COMPANY = "COMPANY"
    PLATOON = "PLATOON"
    SECTION = "SECTION"
    STAFF = "STAFF"
