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


class ThreadSafeSingleton:
    """
    A thread-safe singleton implementation.
    Only one instance of this class can exist.
    """
    # Class-level variable to store the single instance
    _instance = None

    # Class-level lock to ensure thread safety
    _lock = threading.Lock()

    def __new__(cls):
        """
        Override __new__ method for thread-safe singleton implementation.
        """
        # Acquire the lock to ensure thread safety
        with cls._lock:
            # Check if instance has been created yet
            if not cls._instance:
                # Create the single instance of the class
                cls._instance = super().__new__(cls)
            # Return the single instance
            return cls._instance

    def __init__(self):
        """
        Initialize the singleton instance.
        Note: This will be called every time the class is instantiated,
        but __new__ ensures only one instance exists.
        """
        pass

