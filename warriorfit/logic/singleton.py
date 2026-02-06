# Python
# logic/singleton.py
import threading
from abc import ABCMeta


class Singleton(ABCMeta):
    """
    Ensures that a class has only one instance and provides a global point of access to it.
    Compatible with ABC classes by inheriting from ABCMeta.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
