from datetime import datetime

from data.db.db_model import PhefTest


class Message():
    """A class representing a message in MOM."""
    def __init__(self, content: PhefTest):
        self.content = content
        self.timestamp = datetime.now()