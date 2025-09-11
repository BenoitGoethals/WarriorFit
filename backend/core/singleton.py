class Singleton(type):
    """
    Ensures that a class has only one instance and provides a global point of
    access to it.

    The Singleton metaclass is designed to allow classes to adopt a singleton
    pattern, where only one instance of the class can be created. It achieves
    this by overriding the `__call__` method to ensure that if an instance of
    the class already exists, it is returned instead of creating a new one.

    :ivar _instances: Dictionary to store instances of classes adopting the
        Singleton pattern. The keys are class types, and the values are the
        created instances.
    :type _instances: dict
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
