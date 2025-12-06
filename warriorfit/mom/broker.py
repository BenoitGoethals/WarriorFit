import asyncio
import json
import logging
from sqlalchemy import TIMESTAMP, func
from warriorfit.config.appliccation_config import ApplicationConfig
from warriorfit.data.model.db_model import PhefTest, HrMessage
from warriorfit.data.repositories.mom_repositor import MomRepository
from warriorfit.logic.singleton import Singleton
from warriorfit.mom.message import Message
from warriorfit.services.be_mil_service import BEMILService

class Broker(metaclass=Singleton):

    def __init__(self):

        self._mom_repo = MomRepository()
        self._logger = logging.getLogger(__name__)
        self.running = False
        self._worker_task = None
        self._msg_queue = asyncio.Queue()
        self._be_mil_service = BEMILService()

    async def worker(self):
        """Background task running on the main event loop"""
        print(f"🚀 Message Queue Service started")
        print(f"📍 Target URL: {ApplicationConfig().hr_url}")
        print(f"⏱  Check interval: 5 seconds\n")
        self._logger.info("Message Queue Service started")
        self._logger.info(f"Target URL: {ApplicationConfig().hr_url}")
        self._logger.info(f"Check interval: 5 seconds")

        while self.running:
            try:
                await self._process_cycle()
            except Exception as e:
                self._logger.error(f"Worker loop error: {e}")

            # Non-blocking sleep to let other tasks run
            await asyncio.sleep(5)

    async def _process_cycle(self):
        """Process queue and then check for sending"""
        # 1. Drain queue to DB
        if not self._msg_queue.empty():
            repo = MomRepository()
            while not self._msg_queue.empty():
                try:
                    msg = self._msg_queue.get_nowait()
                    await repo.add_hr_message(msg)
                except asyncio.QueueEmpty:
                    break
                except Exception as e:
                    self._logger.error(f"Error saving queued message: {e}")

        # 2. Send pending messages
        await self.check_and_send_messages()

    async def send_message(self, pf: PhefTest):
        """Enqueues a message to be sent"""
        if isinstance(pf, PhefTest):
            pf_dto = PhefTestDto(pf)
            hr_m = HrMessage(
                message=json.dumps(pf_dto.to_dict()), 
                datetime_created=func.now()
            )
            await self._msg_queue.put(hr_m)

    async def _send_message_to_hr(self, message_hr: HrMessage) -> dict | None:
        try:
            message = Message(content=message_hr.message)
            return await self._be_mil_service.sent_hr_message_to_hr(message)
        except Exception as e:
            self._logger.error(f"Error sending message to HR: {e}")
            return None

    async def check_and_send_messages(self):
        self._logger.info("Checking for messages to send to HR...")
        repo = MomRepository()
        msg: HrMessage = await repo.get_last_added_hr_message_by_send_date()

        if msg:
            self._logger.info("Message sent to HR")
            ret = await self._send_message_to_hr(msg)
            if ret:
                await repo.delete_hr_message(msg.id)

    def start(self):
        """Start the service as a background asyncio task"""

        if not self.running:
            self.running = True
            try:
                loop = asyncio.get_running_loop()
                self._worker_task = loop.create_task(self.worker())
            except RuntimeError:
                print("⚠️ Warning: Could not start Broker worker. No running event loop found.")
                self._logger.warning("Could not start Broker worker. No running event loop found.")

    def stop(self):
        """Stop Service"""
        print("\n🛑 Service stopped...")
        self._logger.info("Service stopped...")
        self.running = False
        if self._worker_task:
            self._worker_task.cancel()
        print("✓ Service stopped")
        self._logger.info("Service stopped")


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
    async def main():
        b = Broker()
        b.start()
        
        # Example test messages
        await b.send_message(PhefTest(running_time=120, sideBridge_l=50, sideBridge_r=50, id=1, serial_number="TEST001"))
        await b.send_message(PhefTest(running_time=120, sideBridge_l=50, sideBridge_r=50, id=2, serial_number="TEST002"))
        
        print("Running broker for 15 seconds...")
        await asyncio.sleep(15)
        b.stop()

    asyncio.run(main())
