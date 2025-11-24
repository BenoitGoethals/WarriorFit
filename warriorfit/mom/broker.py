import asyncio
import json
import logging
import threading
import time
from warriorfit.data.db.db_model import PhefTest, HrMessage
from warriorfit.data.db.mom_repositor import MomRepository
from warriorfit.logic.singleton import Singleton
from warriorfit.mom.message import Message
import httpx


class Broker(metaclass=Singleton):

    def __init__(self, url: str="http://127.0.0.1:8005/api/v1/phef/test"):

        self._url = url
        self._mom_repo=MomRepository()
        self._logger = logging.getLogger(__name__)
        self.running = False
        self.worker_thread = None

    def worker(self):
        """Background thread die om de 5 seconden draait"""
        print(f"🚀 Message Queue Service gestart")
        print(f"📍 Target URL: {self._url}")
       
        print(f"⏱  Check interval: 5 seconden\n")

        while self.running:
            self.check_and_send_messages()
            time.sleep(5)


    async def send_message(self, message:HrMessage):
        if not isinstance(message, HrMessage):
            raise TypeError("message must be an instance of Message")
        await self._mom_repo.add_hr_message(message)

    async def _send_message_to_hr(self, message_hr: HrMessage) -> dict | None:
        try:
            message = Message(content=message_hr.message)
            async with httpx.AsyncClient() as client:
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

    async def check_and_send_messages(self):
        self._logger.info("Checking for messages to send to HR...")
        msg:HrMessage=await self._mom_repo.get_last_added_hr_message_by_send_date()

        if msg:
            self._logger.info("Message sent to HR")
            ret = await self._send_message_to_hr(msg)
            if ret:
                await self._mom_repo.delete_hr_message(msg.id)
        else:
            self._logger.error("Error sending message to HR")

    def start(self):
        """Service starten"""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self.worker, daemon=True)
            self.worker_thread.start()

    def stop(self):
        """Service stoppen"""
        print("\n🛑 Service wordt gestopt...")
        self.running = False
        if self.worker_thread:
            self.worker_thread.join()
        print("✓ Service gestopt")




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

    b = Broker("http://127.0.0.1:8005/api/v1/phef/test")
