class User:
    def __init__(self, name, password):
        self.name = name
        self.password = password
        self.email = f"{name}@example.com"
        self.id = None
