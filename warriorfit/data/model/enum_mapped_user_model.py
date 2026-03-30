from sqlalchemy import Integer, TypeDecorator


class IntEnumType(TypeDecorator):
    """
    Custom SQLAlchemy TypeDecorator that maps an Enum to an integer database
    column. This class is designed to handle bidirectional conversion between
    an Enum type and its underlying integer representation.

    This class primarily aims to facilitate the seamless storage and retrieval
    of Enum values in a database by converting Enum instances to integers
    during binding and mapping integers back to Enum instances during result
    retrieval.

    :ivar impl: The implementation of the database column type, specified as
        Integer.
    :type impl: Type
    :ivar cache_ok: Indicates whether the type is cache-safe in SQLAlchemy.
    :type cache_ok: bool
    """

    impl = Integer
    cache_ok = True

    def __init__(self, enumtype, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._enumtype = enumtype

    def process_bind_param(self, value, dialect):
        """
        Converts an enumerated value or integer into a format suitable for database storage during
        binding. If the provided value matches the enumerated type associated with this instance, it
        extracts and returns the value attribute of the enum. For integer inputs, it returns the
        integer directly. Unsupported inputs result in a return value of None.

        :param value: The enumerated value or integer to be processed.
        :type value: Enum or int
        :param dialect: The SQL dialect in use when processing the value.
        :type dialect: Any
        :return: The processed value ready for database storage or None if input is invalid.
        :rtype: int or None
        """
        if isinstance(value, self._enumtype):
            return value.value
        if isinstance(value, int):
            return value
        return None

    def process_result_value(self, value, dialect):
        """
        Processes the incoming database value and converts it into an enumerated type
        defined by the `_enumtype` callable. If the input `value` is ``None``,
        it will return ``None``. Otherwise, the `value` will be transformed using
        the `_enumtype` function.

        :param value: The raw value retrieved from the database.
        :type value: Any
        :param dialect: The SQL dialect currently in use.
        :type dialect: sqlalchemy.engine.interfaces.Dialect
        :return: The processed enumerated type corresponding to the input `value`
                 or ``None`` if `value` is ``None``.
        :rtype: Any
        """
        if value is None:
            return None
        return self._enumtype(value)
