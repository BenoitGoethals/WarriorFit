from mom.message import Message


class Broker:
    """A class representing a message broker for MOM."""
    ...

    def send_message(self, message):
        if not isinstance(message, Message):
            raise TypeError("message must be an instance of Message")


    def post_message(self, message):
        if not isinstance(message, Message):
            raise TypeError("message must be an instance of Message")



