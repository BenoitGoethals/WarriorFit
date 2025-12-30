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


class ThreadSafeSingleton(metaclass=ABCMeta):
    """
       Metaclass for creating thread-safe Singleton classes.
       Any class using this metaclass will automatically be a singleton.
       """
    # Dictionary to store instances of different classes
    _instances = {}

    # Lock to ensure thread-safe singleton instantiation
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        """
        Override __call__ to control instance creation.
        This method is called when a class is instantiated.
        """
        # Acquire the lock to ensure thread safety
        with cls._lock:
            print(f'<SingletonMeta> in the __call__...')
            # Check if an instance of this class already exists
            if cls not in cls._instances:
                # Create a new instance and store it in the dictionary
                cls._instances[cls] = super().__call__(*args, **kwargs)
            # Return the singleton instance
            return cls._instances[cls]

