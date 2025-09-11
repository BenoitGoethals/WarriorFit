class Unit:
    """
    Represents a military unit with a name and base location.
    """

    def __init__(self, id: int, name: str, base_location: str):
        self.id = id
        self.name = name
        self.base_location = base_location

    def __repr__(self):
        return f"Unit(id={self.id}, name='{self.name}', base_location='{self.base_location}')"

    def __eq__(self, other):
        if not isinstance(other, Unit):
            return NotImplemented
        return (
            self.id == other.id
            and self.name == other.name
            and self.base_location == other.base_location
        )