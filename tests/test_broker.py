# tests/test_broker.py
import pytest
from mom.broker import Broker
from mom.message import Message


def test_send_message_with_valid_message():
    broker = Broker()
    message = Message(content="Test message")
    try:
        broker.send_message(message)
    except Exception:
        pytest.fail("send_message raised an exception with a valid Message")


def test_send_message_with_invalid_message():
    broker = Broker()
    with pytest.raises(TypeError, match="message must be an instance of Message"):
        broker.send_message("Invalid message")


def test_post_message_with_valid_message():
    broker = Broker()
    message = Message(content="Another test message")
    try:
        broker.post_message(message)
    except Exception:
        pytest.fail("post_message raised an exception with a valid Message")


def test_post_message_with_invalid_message():
    broker = Broker()
    with pytest.raises(TypeError, match="message must be an instance of Message"):
        broker.post_message(12345)
