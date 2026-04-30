"""
Unit tests for warriorfit/mom/broker.py.

All external dependencies (MomRepository, BEMILService, ApplicationConfig) are
mocked. No database or network connection is required.
"""

import asyncio
import json
import logging
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from warriorfit.data.model.db_model import (
    CombatSwimmingTest,
    CombatTestParatrooper,
    FunctionalTest,
    HrMessage,
    March,
    PhefTest,
)
from warriorfit.mom.broker import (
    Broker,
    CombatSwimTestDto,
    CombatTestDto,
    FunctionalTestDto,
    MarchTestDto,
    PhefTestDto,
)


# ── helpers ────────────────────────────────────────────────────────────────────


def _make_broker(
    poll_interval: int = 1,
    batch_size: int = 5,
    max_attempts: int = 3,
    base_backoff: int = 5,
    max_backoff: int = 30,
) -> tuple[Broker, AsyncMock, AsyncMock]:
    """
    Creates and configures a Broker instance for testing with mocked dependencies.

    This utility function sets up a Broker instance by initializing mocked
    dependencies that mimic the behavior of the real ones. Configuration
    parameters can be adjusted to control polling interval, batch size,
    number of attempts, and backoff intervals.

    :param poll_interval: The interval (in seconds) at which the broker polls for new tasks.
    :param batch_size: The maximum number of tasks that the broker will process in a single batch.
    :param max_attempts: The maximum number of retry attempts for a task.
    :param base_backoff: The base value (in seconds) used for exponential backoff during retries.
    :param max_backoff: The maximum backoff time (in seconds) allowed during retries.
    :return: A tuple containing the configured Broker instance, the mocked repository, and
             the mocked service.
    """
    mock_repo = AsyncMock()
    mock_service = AsyncMock()
    mock_config = MagicMock()
    mock_config.broker_poll_interval_s = poll_interval
    mock_config.broker_batch_size = batch_size
    mock_config.broker_max_attempts = max_attempts
    mock_config.broker_base_backoff_s = base_backoff
    mock_config.broker_max_backoff_s = max_backoff
    mock_config.hr_url = "http://test-hr/"
    broker = Broker(
        mom_repository=mock_repo,
        be_mil_service=mock_service,
        config=mock_config,
    )
    return broker, mock_repo, mock_service


def _hr_msg(id_: int = 1, attempt_count: int = 0) -> MagicMock:
    msg = MagicMock(spec=HrMessage)
    msg.id = id_
    msg.attempt_count = attempt_count
    msg.dead_letter = False
    msg.message = json.dumps({"serial_number": "ABC"})
    return msg


# ── DTO field mapping ──────────────────────────────────────────────────────────


class TestPhefTestDto:
    def test_to_dict(self):
        test = PhefTest(
            serial_number="S1", running_time=120.0, sideBridge_r=45.0, sideBridge_l=50.0
        )
        assert PhefTestDto(test).to_dict() == {
            "serial_number": "S1",
            "running_time": 120.0,
            "sideBridge_r": 45.0,
            "sideBridge_l": 50.0,
        }


class TestCombatTestDto:
    def test_to_dict(self):
        test = CombatTestParatrooper(
            serial_number="S2", running_time=300.0, obstacle_passed=True, rope_passed=False
        )
        assert CombatTestDto(test).to_dict() == {
            "serial_number": "S2",
            "running_time": 300.0,
            "obstacle_passed": True,
            "rope_passed": False,
        }


class TestCombatSwimTestDto:
    def test_to_dict(self):
        test = CombatSwimmingTest()
        test.serial_number = "S3"
        test.swim_paased = True  # intentional typo matches the model column name
        dto = CombatSwimTestDto(test)
        assert dto.to_dict() == {"serial_number": "S3", "swim_passed": True}


class TestMarchTestDto:
    def test_to_dict_with_datetime(self):
        dt = datetime(2026, 1, 15, 10, 30)
        test = March()
        test.service_number = "SVC001"
        test.distance = 30.0
        test.succeeded = True
        test.datetime_executed = dt
        assert MarchTestDto(test).to_dict() == {
            "service_number": "SVC001",
            "distance": 30.0,
            "succeeded": True,
            "datetime_executed": dt.isoformat(),
        }

    def test_to_dict_without_datetime(self):
        test = March()
        test.service_number = "SVC002"
        test.distance = 20.0
        test.succeeded = False
        test.datetime_executed = None
        assert MarchTestDto(test).to_dict()["datetime_executed"] is None


class TestFunctionalTestDto:
    def test_to_dict(self):
        test = FunctionalTest(serial_number="S4", push_ups=40, sit_ups=50, pull_ups=10)
        assert FunctionalTestDto(test).to_dict() == {
            "serial_number": "S4",
            "push_ups": 40,
            "sit_ups": 50,
            "pull_ups": 10,
        }


# ── send_message ──────────────────────────────────────────────────────────────


class TestSendMessage:
    """
    Test class for verifying the behavior of message queuing in a broker system.

    This class contains test methods for various scenarios to ensure that specific
    test instances are queued correctly with proper payload and metadata. It also
    verifies that invalid or unrecognized message types are not queued.

    """
    def test_phef_test_queued_with_correct_payload(self):
        async def _test():
            broker, _, _ = _make_broker()
            test = PhefTest(
                serial_number="S1", running_time=90.0, sideBridge_r=40.0, sideBridge_l=42.0
            )
            await broker.send_message(test)
            assert broker._msg_queue.qsize() == 1
            msg = broker._msg_queue.get_nowait()
            payload = json.loads(msg.message)
            assert payload["serial_number"] == "S1"
            assert payload["running_time"] == 90.0

        asyncio.run(_test())

    def test_combat_test_queued(self):
        async def _test():
            broker, _, _ = _make_broker()
            test = CombatTestParatrooper(
                serial_number="S2", running_time=200.0, obstacle_passed=True, rope_passed=True
            )
            await broker.send_message(test)
            assert broker._msg_queue.qsize() == 1

        asyncio.run(_test())

    def test_swim_test_queued(self):
        async def _test():
            broker, _, _ = _make_broker()
            test = CombatSwimmingTest()
            test.serial_number = "S3"
            test.swim_paased = True
            await broker.send_message(test)
            assert broker._msg_queue.qsize() == 1

        asyncio.run(_test())

    def test_march_test_queued(self):
        async def _test():
            broker, _, _ = _make_broker()
            test = March()
            test.service_number = "SVC1"
            test.distance = 30.0
            test.succeeded = True
            test.datetime_executed = datetime(2026, 1, 1)
            await broker.send_message(test)
            assert broker._msg_queue.qsize() == 1

        asyncio.run(_test())

    def test_functional_test_queued(self):
        async def _test():
            broker, _, _ = _make_broker()
            test = FunctionalTest(serial_number="S5", push_ups=30, sit_ups=40, pull_ups=8)
            await broker.send_message(test)
            assert broker._msg_queue.qsize() == 1

        asyncio.run(_test())

    def test_unknown_type_not_queued(self):
        async def _test():
            broker, _, _ = _make_broker()
            await broker.send_message(MagicMock())
            assert broker._msg_queue.empty()

        asyncio.run(_test())

    def test_message_carries_datetime(self):
        async def _test():
            broker, _, _ = _make_broker()
            test = PhefTest(
                serial_number="S6", running_time=100.0, sideBridge_r=30.0, sideBridge_l=30.0
            )
            await broker.send_message(test)
            msg = broker._msg_queue.get_nowait()
            assert isinstance(msg.datetime_created, datetime)

        asyncio.run(_test())


# ── _process_cycle ────────────────────────────────────────────────────────────


class TestProcessCycle:
    """
    Represents a test suite for validating the process cycle functionality
    of the broker, which handles asynchronous messaging and database storage.

    This class contains various test methods designed to verify different
    aspects of the process cycle, including queue message draining, empty
    queue behavior, and multiple message processing.

    :ivar broker: The broker instance used in the test cases.
    :type broker: object
    :ivar mock_repo: A mock instance of the repository to simulate database
        interactions.
    :type mock_repo: AsyncMock
    :ivar hr_msg: Represents a human-readable message object used for testing.
    :type hr_msg: HrMessage
    """
    def test_drains_queue_to_db(self):
        async def _test():
            broker, _, _ = _make_broker()
            hr_msg = HrMessage(message='{"x":1}', datetime_created=datetime.now())
            await broker._msg_queue.put(hr_msg)

            mock_repo = AsyncMock()
            mock_repo.add_hr_message = AsyncMock(return_value=hr_msg)
            broker.check_and_send_messages = AsyncMock()

            with patch("warriorfit.mom.broker.MomRepository", return_value=mock_repo):
                await broker._process_cycle()

            mock_repo.add_hr_message.assert_awaited_once_with(hr_msg)
            assert broker._msg_queue.empty()

        asyncio.run(_test())

    def test_empty_queue_skips_db_write(self):
        async def _test():
            broker, _, _ = _make_broker()
            mock_repo = AsyncMock()
            broker.check_and_send_messages = AsyncMock()

            with patch("warriorfit.mom.broker.MomRepository", return_value=mock_repo):
                await broker._process_cycle()

            mock_repo.add_hr_message.assert_not_awaited()

        asyncio.run(_test())

    def test_always_calls_check_and_send(self):
        async def _test():
            broker, _, _ = _make_broker()
            mock_repo = AsyncMock()
            broker.check_and_send_messages = AsyncMock()

            with patch("warriorfit.mom.broker.MomRepository", return_value=mock_repo):
                await broker._process_cycle()

            broker.check_and_send_messages.assert_awaited_once()

        asyncio.run(_test())

    def test_multiple_messages_all_drained(self):
        async def _test():
            broker, _, _ = _make_broker()
            for i in range(3):
                await broker._msg_queue.put(
                    HrMessage(message=f'{{"i":{i}}}', datetime_created=datetime.now())
                )
            mock_repo = AsyncMock()
            mock_repo.add_hr_message = AsyncMock(return_value=None)
            broker.check_and_send_messages = AsyncMock()

            with patch("warriorfit.mom.broker.MomRepository", return_value=mock_repo):
                await broker._process_cycle()

            assert mock_repo.add_hr_message.await_count == 3
            assert broker._msg_queue.empty()

        asyncio.run(_test())


# ── check_and_send_messages ───────────────────────────────────────────────────


class TestCheckAndSendMessages:
    """
    Collection of unit tests for validating the behavior of the `check_and_send_messages`
    function in various scenarios.

    Tests in this class ensure that the message processing logic behaves correctly
    under different conditions, such as successful deletion, marking messages as failures,
    handling retries, managing dead letters, and processing empty message queues.

    The tests employ asynchronous mocks and patches to verify interactions with external
    dependencies while simulating different outcomes during message processing.
    """
    def test_success_deletes_row(self):
        async def _test():
            broker, _, _ = _make_broker()
            msg = _hr_msg(id_=42)
            mock_repo = AsyncMock()
            mock_repo.get_due_pending_messages = AsyncMock(return_value=[msg])
            mock_repo.delete_hr_message = AsyncMock(return_value=True)
            broker._try_send_to_hr = AsyncMock(return_value=({"ok": True}, None))

            with patch("warriorfit.mom.broker.MomRepository", return_value=mock_repo):
                await broker.check_and_send_messages()

            mock_repo.delete_hr_message.assert_awaited_once_with(42)
            mock_repo.mark_failure.assert_not_awaited()

        asyncio.run(_test())

    def test_failure_calls_mark_failure(self):
        async def _test():
            broker, _, _ = _make_broker(max_attempts=10, base_backoff=5, max_backoff=30)
            msg = _hr_msg(id_=7, attempt_count=2)
            mock_repo = AsyncMock()
            mock_repo.get_due_pending_messages = AsyncMock(return_value=[msg])
            mock_repo.mark_failure = AsyncMock(return_value=True)
            broker._try_send_to_hr = AsyncMock(return_value=(None, "timeout"))

            with patch("warriorfit.mom.broker.MomRepository", return_value=mock_repo):
                await broker.check_and_send_messages()

            mock_repo.mark_failure.assert_awaited_once_with(
                7,
                "timeout",
                max_attempts=10,
                base_backoff_seconds=5,
                max_backoff_seconds=30,
            )
            mock_repo.delete_hr_message.assert_not_awaited()

        asyncio.run(_test())

    def test_dead_letter_logged_at_max_attempts(self, caplog):
        async def _test():
            broker, _, _ = _make_broker(max_attempts=3)
            msg = _hr_msg(id_=9, attempt_count=2)  # next attempt is the 3rd = max
            mock_repo = AsyncMock()
            mock_repo.get_due_pending_messages = AsyncMock(return_value=[msg])
            mock_repo.mark_failure = AsyncMock(return_value=True)
            broker._try_send_to_hr = AsyncMock(return_value=(None, "conn refused"))

            with patch("warriorfit.mom.broker.MomRepository", return_value=mock_repo):
                with caplog.at_level(logging.ERROR):
                    await broker.check_and_send_messages()

            assert any("dead-letter" in r.message for r in caplog.records)

        asyncio.run(_test())

    def test_no_due_messages_does_nothing(self):
        async def _test():
            broker, _, _ = _make_broker()
            mock_repo = AsyncMock()
            mock_repo.get_due_pending_messages = AsyncMock(return_value=[])

            with patch("warriorfit.mom.broker.MomRepository", return_value=mock_repo):
                await broker.check_and_send_messages()

            mock_repo.delete_hr_message.assert_not_awaited()
            mock_repo.mark_failure.assert_not_awaited()

        asyncio.run(_test())

    def test_batch_size_passed_to_repo(self):
        async def _test():
            broker, _, _ = _make_broker(batch_size=7)
            mock_repo = AsyncMock()
            mock_repo.get_due_pending_messages = AsyncMock(return_value=[])

            with patch("warriorfit.mom.broker.MomRepository", return_value=mock_repo):
                await broker.check_and_send_messages()

            mock_repo.get_due_pending_messages.assert_awaited_once_with(limit=7)

        asyncio.run(_test())


# ── _try_send_to_hr ───────────────────────────────────────────────────────────


class TestTrySendToHr:
    def test_returns_result_on_success(self):
        async def _test():
            broker, _, _ = _make_broker()
            broker._send_message_to_hr = AsyncMock(return_value={"status": "ok"})
            result, err = await broker._try_send_to_hr(_hr_msg())
            assert result == {"status": "ok"}
            assert err is None

        asyncio.run(_test())

    def test_returns_none_and_reason_when_send_returns_none(self):
        async def _test():
            broker, _, _ = _make_broker()
            broker._send_message_to_hr = AsyncMock(return_value=None)
            result, err = await broker._try_send_to_hr(_hr_msg())
            assert result is None
            assert err is not None

        asyncio.run(_test())

    def test_wraps_unexpected_exception(self):
        async def _test():
            broker, _, _ = _make_broker()
            broker._send_message_to_hr = AsyncMock(side_effect=RuntimeError("boom"))
            result, err = await broker._try_send_to_hr(_hr_msg())
            assert result is None
            assert "RuntimeError" in err

        asyncio.run(_test())

    def test_reraises_cancelled_error(self):
        async def _test():
            broker, _, _ = _make_broker()
            broker._send_message_to_hr = AsyncMock(side_effect=asyncio.CancelledError())
            with pytest.raises(asyncio.CancelledError):
                await broker._try_send_to_hr(_hr_msg())

        asyncio.run(_test())


# ── _send_message_to_hr ───────────────────────────────────────────────────────


class TestSendMessageToHr:
    _config_patch = patch(
        "warriorfit.mom.broker.ApplicationConfig",
        return_value=MagicMock(hr_url="http://hr/"),
    )

    def test_returns_result_on_success(self):
        async def _test():
            broker, _, mock_service = _make_broker()
            mock_service.sent_hr_message_to_hr = AsyncMock(return_value={"ok": True})
            with self._config_patch:
                result = await broker._send_message_to_hr(_hr_msg())
            assert result == {"ok": True}

        asyncio.run(_test())

    def test_returns_none_on_timeout(self):
        async def _test():
            broker, _, mock_service = _make_broker()
            mock_service.sent_hr_message_to_hr = AsyncMock(side_effect=asyncio.TimeoutError())
            with self._config_patch:
                assert await broker._send_message_to_hr(_hr_msg()) is None

        asyncio.run(_test())

    def test_returns_none_on_connection_error(self):
        async def _test():
            broker, _, mock_service = _make_broker()
            mock_service.sent_hr_message_to_hr = AsyncMock(
                side_effect=ConnectionError("refused")
            )
            with self._config_patch:
                assert await broker._send_message_to_hr(_hr_msg()) is None

        asyncio.run(_test())

    def test_returns_none_on_value_error(self):
        async def _test():
            broker, _, mock_service = _make_broker()
            mock_service.sent_hr_message_to_hr = AsyncMock(
                side_effect=ValueError("bad data")
            )
            with self._config_patch:
                assert await broker._send_message_to_hr(_hr_msg()) is None

        asyncio.run(_test())

    def test_returns_none_on_os_error(self):
        async def _test():
            broker, _, mock_service = _make_broker()
            mock_service.sent_hr_message_to_hr = AsyncMock(side_effect=OSError("network"))
            with self._config_patch:
                assert await broker._send_message_to_hr(_hr_msg()) is None

        asyncio.run(_test())


# ── start / stop lifecycle ────────────────────────────────────────────────────


class TestLifecycle:
    def test_start_sets_running_and_creates_task(self):
        async def _test():
            broker, _, _ = _make_broker()
            broker.worker = AsyncMock()
            broker.start()
            assert broker.running is True
            assert broker._worker_task is not None
            broker._worker_task.cancel()
            with pytest.raises((asyncio.CancelledError, Exception)):
                await broker._worker_task

        asyncio.run(_test())

    def test_start_idempotent(self, caplog):
        async def _test():
            broker, _, _ = _make_broker()
            broker.worker = AsyncMock()
            broker.start()
            first_task = broker._worker_task
            with caplog.at_level(logging.WARNING):
                broker.start()
            assert broker._worker_task is first_task
            assert any("already running" in r.message for r in caplog.records)
            first_task.cancel()
            with pytest.raises((asyncio.CancelledError, Exception)):
                await first_task

        asyncio.run(_test())

    def test_stop_sets_running_false(self):
        async def _test():
            broker, _, _ = _make_broker()
            broker.worker = AsyncMock()
            broker.start()
            broker.stop()
            assert broker.running is False

        asyncio.run(_test())

    def test_stop_cancels_worker_task(self):
        async def _test():
            broker, _, _ = _make_broker()
            broker.worker = AsyncMock()
            broker.start()
            task = broker._worker_task
            broker.stop()
            assert task.cancelled() or task.cancelling() > 0

        asyncio.run(_test())

    def test_stop_when_not_running_logs_warning(self, caplog):
        with caplog.at_level(logging.WARNING):
            broker, _, _ = _make_broker()
            broker.stop()
        assert any("not running" in r.message for r in caplog.records)


# ── configurable tunables ─────────────────────────────────────────────────────


class TestTunables:
    def test_reads_tunables_from_config(self):
        config = MagicMock()
        config.broker_poll_interval_s = 10
        config.broker_batch_size = 20
        config.broker_max_attempts = 5
        config.broker_base_backoff_s = 15
        config.broker_max_backoff_s = 300
        broker = Broker(config=config)
        assert broker._poll_interval_s == 10
        assert broker._batch_size == 20
        assert broker._max_attempts == 5
        assert broker._base_backoff_s == 15
        assert broker._max_backoff_s == 300

    def test_fallback_defaults_when_config_has_no_broker_attrs(self):
        broker = Broker(config=MagicMock(spec=[]))  # no broker_* attrs
        assert broker._poll_interval_s == 5
        assert broker._batch_size == 5
        assert broker._max_attempts == 10
        assert broker._base_backoff_s == 5
        assert broker._max_backoff_s == 600
