# tests/test_broker.py

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mom.broker import Broker
from mom.message import Message
from mom.message_container import MessageContainer
from utils.Os import Os


@pytest.fixture
def broker():
    url = "https://example.com"
    return Broker(url)


def test_broker_initialization(broker):
    assert broker._url == "https://example.com"
    assert isinstance(broker._msg_queue, MessageContainer)
    assert broker._running is True
    assert broker._thread is None


def test_send_message_valid(broker):
    message = MagicMock(spec=Message)
    with patch.object(broker._msg_queue, "push_message") as mock_push:
        broker.send_message(message)
        mock_push.assert_called_once_with(message)


def test_send_message_invalid_type(broker):
    invalid_message = "Invalid Message"
    with pytest.raises(TypeError, match="message must be an instance of Message"):
        broker.send_message(invalid_message)


@pytest.mark.asyncio
async def test_send_message_to_hr_success():
    url = "https://example.com"
    broker = Broker(url)
    message = MagicMock(spec=Message, content={"key": "value"})

    with patch("httpx.AsyncClient.post",
               return_value=AsyncMock(status_code=200, json=AsyncMock(return_value={"success": True}))) as mock_post:
        response = await broker._send_message_to_hr(message)
        assert response == {"success": True}
        mock_post.assert_called_once_with(url, json=message.content)


@pytest.mark.asyncio
async def test_send_message_to_hr_failure():
    url = "https://example.com"
    broker = Broker(url)
    message = MagicMock(spec=Message, content={"key": "value"})

    with patch("httpx.AsyncClient.post", side_effect=Exception("Connection error")) as mock_post:
        response = await broker._send_message_to_hr(message)
        assert response is None
        mock_post.assert_called_once_with(url, json=message.content)


@pytest.mark.asyncio
async def test_run_loop_sends_message_on_alive():
    broker = Broker("https://example.com")
    broker._msg_queue = MagicMock()
    message = MagicMock(spec=Message)
    broker._msg_queue.get_message.return_value = message
    broker._running = False  # Avoid infinite loop

    with patch("utils.Os.Os.is_alive", return_value=True) as mock_alive, \
            patch("time.sleep"), \
            patch.object(broker, "_send_message_to_hr", new=AsyncMock(return_value={"success": True})) as mock_send:
        await broker._run_loop()

        mock_alive.assert_called_once_with(broker._url)
        broker._msg_queue.get_message.assert_called_once()
        mock_send.assert_awaited_once_with(message)
        broker._msg_queue.delete_message.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_run_loop_no_message_when_not_alive():
    broker = Broker("https://example.com")
    broker._msg_queue = MagicMock()
    broker._msg_queue.get_message.return_value = None
    broker._running = False  # Avoid infinite loop

    with patch("utils.Os.Os.is_alive", return_value=False) as mock_alive, \
            patch("time.sleep"):
        await broker._run_loop()

        mock_alive.assert_called_once_with(broker._url)
        broker._msg_queue.get_message.assert_not_called()


def test_start_starts_thread(broker):
    with patch("threading.Thread", autospec=True) as mock_thread:
        broker.start()
        assert broker._running is True
        mock_thread.assert_called_once()
        assert broker._thread == mock_thread.return_value
        broker._thread.start.assert_called_once()


def test_stop_stops_thread(broker):
    mock_thread = MagicMock()
    broker._thread = mock_thread
    broker._running = True

    broker.stop()

    assert broker._running is False
    mock_thread.join.assert_called_once_with(timeout=5)
    assert broker._thread is None
