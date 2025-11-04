from mom.message import Message


class MessageStack(object):
    """A class representing a stack of messages in MOM."""
    def __init__(self):
        self.messages = []
    def push_message(self, message):
        if not isinstance(message, Message):
            raise TypeError("message must be an instance of Message")
        self.messages.append(message)

    def pop_message(self):
        if not self.messages:
            raise IndexError("message stack is empty")
        return self.messages.pop()


