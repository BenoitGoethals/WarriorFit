from mom.message import Message
import threading
import queue


class MessageStack(object):
    """A class representing a stack of messages in MOM."""
    def __init__(self):
        self._messages = queue.Queue()
        self._lock = threading.Lock()

    def push_message(self, message):
        if not isinstance(message, Message):
            raise TypeError("message must be an instance of Message")
        with self._lock:
            self._messages.put(message)

    def get_message(self):
        with self._lock:
            if not self._messages:
                raise IndexError("message stack is empty")
            return self._messages.get()

    def pop_message(self):
        with self._lock:
            if not self._messages:
                raise IndexError("message stack is empty")
            return self._messages.get()

    def delete_message(self, message):
        pass


