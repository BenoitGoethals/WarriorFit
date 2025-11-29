from sqlalchemy import TypeDecorator, Integer


class IntEnumType(TypeDecorator):
    """
    Enables using a Python IntEnum as a regular Integer in the database.
    """
    impl = Integer
    cache_ok = True

    def __init__(self, enumtype, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._enumtype = enumtype

    def process_bind_param(self, value, dialect):
        if isinstance(value, self._enumtype):
            return value.value
        if isinstance(value, int):
            return value
        return None

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return self._enumtype(value)
