import asyncio
import logging
import threading
import time

from data.db.db_model import PhefTest
from mom.message import Message
from mom.message_container import MessageContainer
import httpx
from utils.Os import Os

class Broker:

    def __init__(self, url: str):
        self._msg_queue = MessageContainer()
        self._url = url
        self._running = True
        self._logger = logging.getLogger(__name__)
        self._thread: threading.Thread | None = None

    def send_message(self, message):
        if not isinstance(message, Message):
            raise TypeError("message must be an instance of Message")
        self._msg_queue.push_message(message)

    async def _send_message_to_hr(self, message: Message) -> dict | None:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self._url, json=message.content)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            self._logger.error(f"Error sending message to HR: {e}")

    async def _run_loop(self):
        while self._running:
            check_a_live = Os.is_alive(self._url)
            time.sleep(1)
            if check_a_live:
                message = self._msg_queue.get_message()
                if message:
                    response = await self._send_message_to_hr(message)
                    if response and response.get("success"):
                        self._logger.info("Message sent successfully to HR")
                        self._msg_queue.delete_message(message)
                    else:
                        self._logger.error("Message failed to send to HR")

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._running = True

        def runner():
            try:
                asyncio.run(self._run_loop())
            except Exception as e:
                self._logger.exception(f"Broker thread crashed: {e}")

        self._thread = threading.Thread(target=runner, name="BrokerThread", daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None


if __name__ == "__main__":
    b = Broker("http://localhost:8000/api/v1/phef/test/")
    b.start()
    for i in range(10):
        b.send_message(Message(content=PhefTest(serial_number="BE-20250001",
            running_time=2.0,
            sideBridge_r=2.0,
            sideBridge_l=20.0,
        )))
    time.sleep(10)
    b.stop()
