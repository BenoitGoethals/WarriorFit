# Python
# logic/singleton.py
from abc import ABCMeta
from typing import ClassVar


class Singleton(ABCMeta):
    """
    Ensures that a class has only one instance and provides a global point of access to it.
    Compatible with ABC classes by inheriting from ABCMeta.
    """

    _instances: ClassVar[dict[type, object]] = {}

    def __call__(cls, *args: object, **kwargs: object) -> object:
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
