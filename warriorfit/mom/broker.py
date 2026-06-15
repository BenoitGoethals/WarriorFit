import asyncio
import json
import logging
from datetime import datetime

from warriorfit.config.application_config import ApplicationConfig
from warriorfit.data.model.db_model import (
    CombatSwimmingTest,
    CombatTestParatrooper,
    FitnessTest,
    FunctionalTest,
    HrMessage,
    March,
    PhefTest,
)
from warriorfit.data.repositories.mom_repository import MomRepository
from warriorfit.mom.message import Message
from warriorfit.services.be_mil_service import BEMILService
from warriorfit.services.notify_mail import NotifyMail


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
        notify_mail: NotifyMail = None,
    ):
        self._mom_repo = mom_repository if mom_repository is not None else MomRepository()
        self._logger = logging.getLogger(__name__)
        self.running = False
        self._worker_task = None
        self._msg_queue = asyncio.Queue()  # type: ignore[var-annotated]
        self._be_mil_service = be_mil_service if be_mil_service is not None else BEMILService()
        self._config = config if config is not None else ApplicationConfig()
        self._notify_mail = notify_mail
        # Outbox tunables — read from config, fall back to safe defaults.
        # poll_interval: how often the worker wakes up (seconds).
        # batch_size:    how many due messages we attempt to send per cycle.
        # max_attempts:  after this many failures a message becomes dead-letter.
        # base_backoff / max_backoff (seconds): exponential back-off bounds.
        self._poll_interval_s: int = getattr(self._config, "broker_poll_interval_s", 5)
        self._batch_size: int = getattr(self._config, "broker_batch_size", 5)
        self._max_attempts: int = getattr(self._config, "broker_max_attempts", 10)
        self._base_backoff_s: int = getattr(self._config, "broker_base_backoff_s", 5)
        self._max_backoff_s: int = getattr(self._config, "broker_max_backoff_s", 600)

    async def worker(self):
        """Background task running on the main event loop"""
        hr_url = self._config.hr_url
        print("🚀 Message Queue Service started")
        print(f"📍 Target URL: {hr_url}")
        print(
            f"⏱  Poll interval: {self._poll_interval_s}s | batch: {self._batch_size} | "
            f"max attempts: {self._max_attempts} | back-off: {self._base_backoff_s}s..{self._max_backoff_s}s\n"
        )
        self._logger.info(
            "Message Queue Service started",
            extra={
                "target_url": hr_url,
                "poll_interval_seconds": self._poll_interval_s,
                "batch_size": self._batch_size,
                "max_attempts": self._max_attempts,
                "base_backoff_s": self._base_backoff_s,
                "max_backoff_s": self._max_backoff_s,
            },
        )

        while self.running:
            try:
                await self._process_cycle()
            except asyncio.CancelledError:
                self._logger.info("Worker task cancelled, shutting down gracefully")
                break
            except (OSError, ConnectionError) as e:
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
            except TimeoutError as e:
                self._logger.error(
                    f"Timeout in worker loop: {type(e).__name__}",
                    exc_info=True,
                    extra={"error_type": "TimeoutError", "error_message": str(e)},
                )

            # Non-blocking sleep to let other tasks run
            await asyncio.sleep(self._poll_interval_s)

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
            repo = self._mom_repo
            messages_processed = 0
            while not self._msg_queue.empty():
                msg = None
                try:
                    msg = self._msg_queue.get_nowait()
                    saved = await repo.add_hr_message(msg)
                    if saved is None:
                        # Repository swallowed an integrity/DB error — re-queue
                        await self._msg_queue.put(msg)
                        self._logger.warning(
                            "add_hr_message returned None; message re-queued for next cycle",
                            extra={"queue_size": self._msg_queue.qsize()},
                        )
                        break
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
                            "message_type": type(msg).__name__ if msg else "unknown",
                        },
                    )
                except OSError as e:
                    # DB unreachable — put the message back so it survives the cycle
                    if msg is not None:
                        await self._msg_queue.put(msg)
                    self._logger.error(
                        f"Database I/O error while saving message: {type(e).__name__}; message re-queued",
                        exc_info=True,
                        extra={
                            "error_type": type(e).__name__,
                            "error_message": str(e),
                            "queue_size": self._msg_queue.qsize(),
                        },
                    )
                    break  # stop draining; wait for next cycle
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

    async def send_message(self, test: FitnessTest | March):
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
                dto = CombatTestDto(test)  # type: ignore[assignment]
            elif isinstance(test, CombatSwimmingTest):
                dto = CombatSwimTestDto(test)  # type: ignore[assignment]
            elif isinstance(test, March):
                dto = MarchTestDto(test)  # type: ignore[assignment]
            elif isinstance(test, FunctionalTest):
                dto = FunctionalTestDto(test)  # type: ignore[assignment]

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
        except OSError as e:
            self._logger.error(
                f"Queue operation error: {type(e).__name__}",
                exc_info=True,
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "test_type": test_type,
                },
            )

    async def _try_send_to_hr(self, message_hr: HrMessage) -> tuple[dict | None, str | None]:
        """
        Internal wrapper around `_send_message_to_hr` that returns a structured
        (result, error_reason) tuple so the caller can record the failure
        cause on the outbox row.

        result is the HR response dict on success, or None on failure.
        error_reason is None on success, or a short string describing why it
        failed (used for `last_error` in the dead-letter table).
        """
        try:
            result = await self._send_message_to_hr(message_hr)
            if result is None:
                return None, "send returned None (see broker logs for cause)"
            return result, None
        except asyncio.CancelledError:
            raise
        except Exception as e:
            self._logger.error(
                "Unexpected exception during HR send",
                exc_info=True,
                extra={
                    "message_id": getattr(message_hr, "id", None),
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
            )
            return None, f"{type(e).__name__}: {e}"

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
            raw = message_hr.message
            content = json.loads(raw) if isinstance(raw, str) else raw
            message = Message(content=content)
            self._logger.debug(
                "Sending message to HR service",
                extra={"message_id": message_id, "hr_url": self._config.hr_url},
            )
            result = await self._be_mil_service.sent_hr_message_to_hr(message)
            self._logger.info(
                "Message successfully sent to HR service",
                extra={"message_id": message_id, "response": result},
            )
            return result
        except TimeoutError as e:
            self._logger.error(
                "Timeout while sending message to HR service",
                exc_info=True,
                extra={
                    "error_type": "TimeoutError",
                    "error_message": str(e),
                    "message_id": message_id,
                    "hr_url": self._config.hr_url,
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
                    "hr_url": self._config.hr_url,
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
        except OSError as e:
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
        Send a batch of due HR messages. For each message:

            - If HR returns a dict → delete the row from `hr_messages`.
            - If HR fails → record the failure on the row (increments
              `attempt_count`, schedules `next_retry_at` with exponential
              back-off, or flips to `dead_letter` once `max_attempts` is hit).

        Messages already in the dead-letter state are NOT picked up. Per cycle,
        at most `_batch_size` messages are processed; the next batch will be
        picked up on the next worker tick.
        """
        self._logger.debug("Checking for due HR messages to send")
        try:
            repo = self._mom_repo
            due = await repo.get_due_pending_messages(limit=self._batch_size)
            if not due:
                self._logger.debug("No due HR messages")
                return

            self._logger.info(
                "Processing %d due HR message(s)",
                len(due),
                extra={"batch_size": len(due)},
            )
            for msg in due:
                message_id = getattr(msg, "id", None)
                attempt_before = getattr(msg, "attempt_count", 0)
                ret, err = await self._try_send_to_hr(msg)
                if ret is not None:
                    await repo.delete_hr_message(msg.id)
                    self._logger.info(
                        "HR message sent and deleted",
                        extra={
                            "message_id": message_id,
                            "attempts": attempt_before + 1,
                        },
                    )
                else:
                    updated = await repo.mark_failure(
                        msg.id,
                        err or "unknown error",
                        max_attempts=self._max_attempts,
                        base_backoff_seconds=self._base_backoff_s,
                        max_backoff_seconds=self._max_backoff_s,
                    )
                    if updated and attempt_before + 1 >= self._max_attempts:
                        self._logger.error(
                            "HR message moved to dead-letter (max attempts reached)",
                            extra={
                                "message_id": message_id,
                                "attempts": attempt_before + 1,
                                "max_attempts": self._max_attempts,
                                "last_error": err,
                            },
                        )
                        await self._send_dead_letter_alert(msg.id, attempt_before + 1, err)
                    else:
                        self._logger.warning(
                            "HR message send failed, scheduled for retry",
                            extra={
                                "message_id": message_id,
                                "attempts": attempt_before + 1,
                                "last_error": err,
                            },
                        )
        except AttributeError as e:
            self._logger.error(
                f"Repository attribute error: {type(e).__name__}",
                exc_info=True,
                extra={"error_type": "AttributeError", "error_message": str(e)},
            )
        except OSError as e:
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
                self._worker_task = loop.create_task(self.worker())  # type: ignore[assignment]
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

    async def _send_dead_letter_alert(
        self, message_id: int, attempts: int, last_error: str | None
    ) -> None:
        alert_email = getattr(self._config, "broker_alert_email", "")
        if not self._notify_mail or not alert_email:
            return
        subject = f"[WarriorFit] Dead-letter: HR-bericht {message_id} kan niet worden verzonden"
        body = (
            f"<p>Bericht <strong>ID {message_id}</strong> heeft "
            f"<strong>{attempts} pogingen</strong> uitgeput en is naar "
            f"<strong>dead-letter</strong> verplaatst.</p>"
            f"<p><strong>Laatste fout:</strong> {last_error or 'onbekend'}</p>"
            f"<p>Actie vereist:<br>"
            f"&nbsp;&bull; Controleer de verbinding met het HR-systeem.<br>"
            f"&nbsp;&bull; Reset de rij in <code>hr_messages</code> "
            f"(<code>dead_letter = false</code>, <code>attempt_count = 0</code>) "
            f"wanneer het HR-systeem weer beschikbaar is.</p>"
        )
        try:
            await self._notify_mail.send_mail(to=alert_email, subject=subject, body=body)
        except Exception as exc:
            self._logger.error("Failed to send dead-letter alert email: %s", exc)

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
            test.datetime_executed.isoformat() if test.datetime_executed else None  # type: ignore[attr-defined]
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
