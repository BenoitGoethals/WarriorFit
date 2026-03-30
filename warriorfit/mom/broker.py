import asyncio
import json
import logging
from datetime import datetime

from warriorfit.config.appliccation_config import ApplicationConfig
from warriorfit.data.model.db_model import (
    CombatSwimmingTest,
    CombatTestParatrooper,
    FitnessTest,
    FunctionalTest,
    HrMessage,
    March,
    PhefTest,
)
from warriorfit.data.repositories.mom_repositor import MomRepository
from warriorfit.mom.message import Message
from warriorfit.services.be_mil_service import BEMILService


class Broker:
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

    def __init__(
        self,
        mom_repository: MomRepository = None,
        be_mil_service: BEMILService = None,
        config: ApplicationConfig = None,
    ):
        self._mom_repo = mom_repository if mom_repository is not None else MomRepository()
        self._logger = logging.getLogger(__name__)
        self.running = False
        self._worker_task = None
        self._msg_queue = asyncio.Queue()
        self._be_mil_service = be_mil_service if be_mil_service is not None else BEMILService()
        self._config = config if config is not None else ApplicationConfig()

    async def worker(self):
        """Background task running on the main event loop"""
        hr_url = ApplicationConfig().hr_url
        print("🚀 Message Queue Service started")
        print(f"📍 Target URL: {hr_url}")
        print("⏱  Check interval: 5 seconds\n")
        self._logger.info(
            "Message Queue Service started",
            extra={"target_url": hr_url, "check_interval_seconds": 5},
        )

        while self.running:
            try:
                await self._process_cycle()
            except asyncio.CancelledError:
                self._logger.info("Worker task cancelled, shutting down gracefully")
                break
            except (OSError, IOError, ConnectionError) as e:
                self._logger.error(
                    f"Network or I/O error in worker loop: {type(e).__name__}",
                    exc_info=True,
                    extra={"error_type": type(e).__name__, "error_message": str(e)},
                )
            except (AttributeError, TypeError, ValueError) as e:
                self._logger.error(
                    f"Data processing error in worker loop: {type(e).__name__}",
                    exc_info=True,
                    extra={"error_type": type(e).__name__, "error_message": str(e)},
                )
            except asyncio.TimeoutError as e:
                self._logger.error(
                    f"Timeout in worker loop: {type(e).__name__}",
                    exc_info=True,
                    extra={"error_type": "TimeoutError", "error_message": str(e)},
                )

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
            messages_processed = 0
            while not self._msg_queue.empty():
                try:
                    msg = self._msg_queue.get_nowait()
                    await repo.add_hr_message(msg)
                    messages_processed += 1
                    self._logger.debug(
                        "Message saved to database",
                        extra={"message_id": msg.id if hasattr(msg, "id") else None},
                    )
                except asyncio.QueueEmpty:
                    self._logger.debug("Queue empty during drain operation")
                    break
                except AttributeError as e:
                    self._logger.error(
                        f"Invalid message object structure: {type(e).__name__}",
                        exc_info=True,
                        extra={
                            "error_type": "AttributeError",
                            "error_message": str(e),
                            "message_type": type(msg).__name__,
                        },
                    )
                except (OSError, IOError) as e:
                    self._logger.error(
                        f"Database I/O error while saving message: {type(e).__name__}",
                        exc_info=True,
                        extra={
                            "error_type": type(e).__name__,
                            "error_message": str(e),
                            "queue_size": self._msg_queue.qsize(),
                        },
                    )
                except (ValueError, TypeError) as e:
                    self._logger.error(
                        f"Invalid data type or value in message: {type(e).__name__}",
                        exc_info=True,
                        extra={
                            "error_type": type(e).__name__,
                            "error_message": str(e),
                            "queue_size": self._msg_queue.qsize(),
                        },
                    )

            if messages_processed > 0:
                self._logger.info(
                    f"Drained {messages_processed} message(s) from queue to database",
                    extra={"messages_processed": messages_processed},
                )

        # 2. Send pending messages
        await self.check_and_send_messages()

    async def send_message(self, test: FitnessTest):
        """
        Send a message to the message queue.

        This asynchronous method takes a test object, converts it into a DTO (Data
        Transfer Object), serializes it to JSON, and wraps it in a message object
        that includes the creation timestamp. The constructed message object is
        then added to the internal message queue for further processing.

        :param test:
        :param pf: A test object that can be an instance of either `PhefTest`
                   or `FitnessTest`. The test data is processed and added to
                   the message queue.
        :type pf: PhefTest | FitnessTest
        :return: None
        :rtype: None
        """
        test_type = type(test).__name__
        dto = None

        try:
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
                self._logger.warning(
                    f"Unsupported test type received: {test_type}",
                    extra={
                        "test_type": test_type,
                        "test_id": getattr(test, "id", None),
                    },
                )
                return

            hr_m = HrMessage(message=json.dumps(dto.to_dict()), datetime_created=datetime.now())
            await self._msg_queue.put(hr_m)
            self._logger.debug(
                f"Message queued for {test_type}",
                extra={
                    "test_type": test_type,
                    "serial_number": getattr(test, "serial_number", None)
                    or getattr(test, "service_number", None),
                    "queue_size": self._msg_queue.qsize(),
                },
            )
        except AttributeError as e:
            self._logger.error(
                f"Missing required attribute in test object: {type(e).__name__}",
                exc_info=True,
                extra={
                    "error_type": "AttributeError",
                    "error_message": str(e),
                    "test_type": test_type,
                },
            )
        except (TypeError, ValueError, json.JSONDecodeError) as e:
            self._logger.error(
                f"Error serializing test data: {type(e).__name__}",
                exc_info=True,
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "test_type": test_type,
                },
            )
        except (OSError, IOError) as e:
            self._logger.error(
                f"Queue operation error: {type(e).__name__}",
                exc_info=True,
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "test_type": test_type,
                },
            )

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
        message_id = getattr(message_hr, "id", None)
        try:
            message = Message(content=message_hr.message)
            self._logger.debug(
                "Sending message to HR service",
                extra={"message_id": message_id, "hr_url": ApplicationConfig().hr_url},
            )
            result = await self._be_mil_service.sent_hr_message_to_hr(message)
            self._logger.info(
                "Message successfully sent to HR service",
                extra={"message_id": message_id, "response": result},
            )
            return result
        except asyncio.TimeoutError as e:
            self._logger.error(
                "Timeout while sending message to HR service",
                exc_info=True,
                extra={
                    "error_type": "TimeoutError",
                    "error_message": str(e),
                    "message_id": message_id,
                    "hr_url": ApplicationConfig().hr_url,
                },
            )
            return None
        except ConnectionError as e:
            self._logger.error(
                "Connection error while sending message to HR service",
                exc_info=True,
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "message_id": message_id,
                    "hr_url": ApplicationConfig().hr_url,
                },
            )
            return None
        except (ValueError, json.JSONDecodeError) as e:
            self._logger.error(
                f"Invalid message format: {type(e).__name__}",
                exc_info=True,
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "message_id": message_id,
                    "message_content": (
                        message_hr.message[:200] if hasattr(message_hr, "message") else None
                    ),
                },
            )
            return None
        except (OSError, IOError) as e:
            self._logger.error(
                f"Network I/O error sending message to HR: {type(e).__name__}",
                exc_info=True,
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "message_id": message_id,
                },
            )
            return None
        except AttributeError as e:
            self._logger.error(
                f"Invalid message structure or API error: {type(e).__name__}",
                exc_info=True,
                extra={
                    "error_type": "AttributeError",
                    "error_message": str(e),
                    "message_id": message_id,
                },
            )
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
        self._logger.debug("Checking for pending messages to send to HR")
        try:
            repo = MomRepository()
            msg: HrMessage = await repo.get_last_added_hr_message_by_send_date()

            if msg:
                message_id = getattr(msg, "id", None)
                self._logger.info(
                    "Pending message found, attempting to send to HR",
                    extra={"message_id": message_id},
                )
                ret = await self._send_message_to_hr(msg)
                if ret:
                    await repo.delete_hr_message(msg.id)
                    self._logger.info(
                        "Message successfully sent and deleted from repository",
                        extra={"message_id": message_id},
                    )
                else:
                    self._logger.warning(
                        "Failed to send message, will retry in next cycle",
                        extra={"message_id": message_id},
                    )
            else:
                self._logger.debug("No pending messages to send")
        except AttributeError as e:
            self._logger.error(
                f"Repository attribute error: {type(e).__name__}",
                exc_info=True,
                extra={"error_type": "AttributeError", "error_message": str(e)},
            )
        except (OSError, IOError) as e:
            self._logger.error(
                f"Database I/O error in check_and_send_messages: {type(e).__name__}",
                exc_info=True,
                extra={"error_type": type(e).__name__, "error_message": str(e)},
            )
        except (ValueError, TypeError) as e:
            self._logger.error(
                f"Data validation error in check_and_send_messages: {type(e).__name__}",
                exc_info=True,
                extra={"error_type": type(e).__name__, "error_message": str(e)},
            )

    def start(self):
        """Start the service as a background asyncio task"""

        if not self.running:
            self.running = True
            try:
                loop = asyncio.get_running_loop()
                self._worker_task = loop.create_task(self.worker())
                self._logger.info(
                    "Broker worker task created successfully",
                    extra={"task_id": id(self._worker_task)},
                )
            except RuntimeError as e:
                error_msg = "Could not start Broker worker. No running event loop found."
                print(f"⚠️ Warning: {error_msg}")
                self._logger.error(
                    error_msg,
                    exc_info=True,
                    extra={"error_type": "RuntimeError", "error_message": str(e)},
                )
        else:
            self._logger.warning("Broker start() called but worker is already running")

    def stop(self):
        """Stop Service"""
        if not self.running:
            self._logger.warning("Broker stop() called but worker is not running")
            return

        print("\n🛑 Stopping Message Queue Service...")
        self._logger.info("Initiating broker shutdown")
        self.running = False

        if self._worker_task:
            task_id = id(self._worker_task)
            self._worker_task.cancel()
            self._logger.info(
                "Worker task cancelled",
                extra={"task_id": task_id, "queue_size": self._msg_queue.qsize()},
            )

        print("✓ Service stopped")
        self._logger.info("Broker service stopped successfully")


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
