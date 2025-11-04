import time
from http.server import HTTPServer

from pydantic.config import JsonDict

from data.db.db_model import PhefTest
from mom.message import Message
from mom.message_container import MessageContainer
import httpx  # added

from utils.Os import Os


class Broker:

    def __init__(self,url:str):
        self._msg_queue = MessageContainer()
        self._url=url
        self._running=True

    def send_message(self, message):
        if not isinstance(message, Message):
            raise TypeError("message must be an instance of Message")
        self._msg_queue.push_message(message)




    async def _send_message_to_hr(self, message:Message)->dict|None:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self._url, json=message.content)
                response.raise_for_status()
                return response.json()

        except Exception as e:
            print(f"Error sending message to HR: {e}")


    async def start(self):
        while self._running:
            check_a_live=Os.is_alive(self._url)
            time.sleep(1)
            if check_a_live:
                message = self._msg_queue.get_message()
                if message:
                    response=await self._send_message_to_hr(message)
                    if response["success"]:
                        print("Message sent successfully to HR")
                        self._msg_queue.delete_message(message)
                    else:
                        print("Message failed to send to HR")


    def stop(self):
        self._running=False


if __name__ == "__main__":
    import asyncio

    broker = Broker("http://localhost:8000/api/v1/hr/message")
    asyncio.run(broker.start())
    broker.send_message(Message(content=PhefTest(
        serial_number="BE-20250001",
        running_time=0.0,
        sideBridge_r=0.0,
        sideBridge_l=0.0,

    )))
