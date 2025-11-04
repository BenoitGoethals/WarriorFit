from datetime import datetime


class Message:
    """A class representing a message in MOM."""
    def __init__(self, content):
        self.content = content
        self.timestamp = datetime.now()