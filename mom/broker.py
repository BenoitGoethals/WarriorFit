import asyncio
import json
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
                # send dict, not pre-serialized JSON string
                response = await client.post(
                    self._url,
                    json=message.to_dict(),
                    headers={'accept': 'application/json', 'Content-Type': 'application/json'}
                )
                print(json.dumps(message.to_dict(), indent=2))
                response.raise_for_status()
                return response.json()
        except Exception as e:
            self._logger.error(f"Error sending message to HR: {e}")
            print(e)
            return None

    async def _run_loop(self):
        while self._running:

            await asyncio.sleep(1)

            message = self._msg_queue.get_message()
            if not message:
                continue
            try:
                resp = await self._send_message_to_hr(message)
                if resp and resp.get("success"):
                    self._logger.info("Message sent successfully to HR")
                    self._msg_queue.delete_message(message)
                else:
                    self._logger.error("Message failed to send to HR")
            except Exception as e:
                self._logger.exception(f"send loop error: {e}")

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._running = True

        def runner():
            try:
                asyncio.run(self._run_loop())
            except Exception:
                self._logger.exception("Broker thread crashed")

        # Make it non-daemon so process won’t exit early
        self._thread = threading.Thread(target=runner, name="BrokerThread", daemon=False)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None


class PhefTestDto:
    def __init__(self, pf: PhefTest):
        self.serial_number = pf.serial_number
        self.running_time = pf.running_time
        self.sideBridge_r = pf.sideBridge_r
        self.sideBridge_l = pf.sideBridge_l

    def to_dict(self) -> dict:
        return {
            "serial_number": self.serial_number,
            "running_time": self.running_time,
            "sideBridge_r": self.sideBridge_r,
            "sideBridge_l": self.sideBridge_l,
        }


if __name__ == "__main__":
    dt = PhefTest(
        serial_number="BE-20250001",
        running_time=2.0,
        sideBridge_r=2.0,
        sideBridge_l=20.0,
    )
    b = Broker("http://127.0.0.1:8005/api/v1/phef/test")
    b.start()
    for i in range(10):
        time.sleep(1)
        b.send_message(Message(content=PhefTestDto(dt)))