import asyncio
import json
import logging
import threading
import time

from warriorfit.data.db.db_model import PhefTest
from warriorfit.logic.singleton import Singleton
from warriorfit.mom.message import Message

from warriorfit.mom.message_container import MessageContainer
import httpx


class Broker(metaclass=Singleton):

    def __init__(self, url: str="http://127.0.0.1:8005/api/v1/phef/test"):

        self._url = url

        self._logger = logging.getLogger(__name__)




    def send_message(self, message:Message):
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

    for i in range(10):
        time.sleep(1)
        b.send_message(Message(content=PhefTestDto(dt)))