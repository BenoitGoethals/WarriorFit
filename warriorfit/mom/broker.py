import asyncio
import json
import logging
from sqlalchemy import TIMESTAMP, func
from warriorfit.config.appliccation_config import ApplicationConfig
from warriorfit.data.model.db_model import (
    PhefTest,
    HrMessage,
    TestSession,
    FitnessTest,
    CombatTestParatrooper,
    CombatSwimmingTest,
    March,
    FunctionalTest,
)
from warriorfit.data.repositories.mom_repositor import MomRepository
from warriorfit.logic.singleton import Singleton
from warriorfit.mom.message import Message
from warriorfit.services.be_mil_service import BEMILService


class Broker(metaclass=Singleton):
    """
    Manages message queue services, including background tasks for processing,
    storing, and sending messages to an external HR service.

    This class is designed as a singleton, ensuring that only one instance of the
    message queue service is running within the application. It integrates with
    the asynchronous event loop, providing background functionality for managing
    and dispatching messages efficiently.

    :ivar running: Indicates whether the worker service is running.
    :type running: bool
    :ivar _worker_task: Represents the asyncio task for the worker process.
    :type _worker_task: asyncio.Task or None
    :ivar _msg_queue: Internal asynchronous queue for storing messages to process.
    :type _msg_queue: asyncio.Queue
    """

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
        """
        Processes a single cycle of operations asynchronously.

        This coroutine performs the following tasks:
        1. Drains the message queue to the database by fetching messages from the
           queue and saving them using an external repository.
        2. Checks and sends any pending messages.

        This method ensures queued messages are persisted in the database before
        continuing with further processing.

        :raises asyncio.QueueEmpty: If the message queue is unexpectedly empty while attempting
            to fetch a message.
        :raises Exception: If an error occurs while saving messages to the database.
        """

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

    async def send_message(self, test: FitnessTest):
        """
        Send a message to the message queue.

        This asynchronous method takes a test object, converts it into a DTO (Data
        Transfer Object), serializes it to JSON, and wraps it in a message object
        that includes the creation timestamp. The constructed message object is
        then added to the internal message queue for further processing.

        :param pf: A test object that can be an instance of either `PhefTest`
                   or `FitnessTest`. The test data is processed and added to
                   the message queue.
        :type pf: PhefTest | FitnessTest
        :return: None
        :rtype: None
        """
        dto = None
        if isinstance(test, PhefTest):
            dto = PhefTestDto(test)
        elif isinstance(test, CombatTestParatrooper):
            dto = CombatTestDto(test)
        elif isinstance(test, CombatSwimmingTest):
            dto = CombatSwimTestDto(test)
        elif isinstance(test, March):
            dto = MarchTestDto(test)
        elif isinstance(test, FunctionalTest):
            dto = FunctionalTestDto(test)
        if dto is None:
            return

        hr_m = HrMessage(message=json.dumps(dto.to_dict()), datetime_created=func.now())
        await self._msg_queue.put(hr_m)

    async def _send_message_to_hr(self, message_hr: HrMessage) -> dict | None:
        """
        Sends a message to the HR service asynchronously.

        This method attempts to send a formatted message to the HR service using the
        _be_mil_service. If an error occurs during this process, it will log the error
        message and return None.

        :param message_hr: The HrMessage object containing the message details to
            be sent to the HR service.
        :type message_hr: HrMessage

        :return: A dictionary containing the result of the HR service response, or
            None if an error occurs.
        :rtype: dict | None
        """
        try:
            message = Message(content=message_hr.message)
            return await self._be_mil_service.sent_hr_message_to_hr(message)
        except Exception as e:
            self._logger.error(f"Error sending message to HR: {e}")
            return None

    async def check_and_send_messages(self):
        """
        Checks for messages to send to HR, sends the message if available, and deletes it
        from the repository if sending is successful.

        This asynchronous method retrieves the last HR message from the repository,
        sends it to HR, and subsequently removes the message from the repository if the
        sending operation is successful.

        :return: None
        """
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
                print(
                    "⚠️ Warning: Could not start Broker worker. No running event loop found."
                )
                self._logger.warning(
                    "Could not start Broker worker. No running event loop found."
                )

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


class CombatTestDto:
    def __init__(self, test: CombatTestParatrooper):
        self.serial_number = test.serial_number
        self.running_time = test.running_time
        self.obstacle_passed = test.obstacle_passed
        self.rope_passed = test.rope_passed

    def to_dict(self) -> dict:
        return {
            "serial_number": self.serial_number,
            "running_time": self.running_time,
            "obstacle_passed": self.obstacle_passed,
            "rope_passed": self.rope_passed,
        }


class CombatSwimTestDto:
    def __init__(self, test: CombatSwimmingTest):
        self.serial_number = test.serial_number
        self.swim_passed = test.swim_paased

    def to_dict(self) -> dict:
        return {
            "serial_number": self.serial_number,
            "swim_passed": self.swim_passed,
        }


class MarchTestDto:
    def __init__(self, test: March):
        self.service_number = test.service_number
        self.distance = test.distance
        self.succeeded = test.succeeded
        self.datetime_executed = (
            test.datetime_executed.isoformat() if test.datetime_executed else None
        )

    def to_dict(self) -> dict:
        return {
            "service_number": self.service_number,
            "distance": self.distance,
            "succeeded": self.succeeded,
            "datetime_executed": self.datetime_executed,
        }


class FunctionalTestDto:
    def __init__(self, test: FunctionalTest):
        self.serial_number = test.serial_number
        self.push_ups = test.push_ups
        self.sit_ups = test.sit_ups
        self.pull_ups = test.pull_ups

    def to_dict(self) -> dict:
        return {
            "serial_number": self.serial_number,
            "push_ups": self.push_ups,
            "sit_ups": self.sit_ups,
            "pull_ups": self.pull_ups,
        }


if __name__ == "__main__":

    async def main():
        b = Broker()
        b.start()

        # Example test messages
        await b.send_message(
            PhefTest(
                running_time=120,
                sideBridge_l=50,
                sideBridge_r=50,
                id=1,
                serial_number="TEST001",
            )
        )
        await b.send_message(
            PhefTest(
                running_time=120,
                sideBridge_l=50,
                sideBridge_r=50,
                id=2,
                serial_number="TEST002",
            )
        )

        print("Running broker for 15 seconds...")
        await asyncio.sleep(15)
        b.stop()

    asyncio.run(main())
