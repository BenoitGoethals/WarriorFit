# Message Broker — Unit Test Coverage

**File tested:** `warriorfit/mom/broker.py`
**Test file:** `tests/test_broker_unit.py`

---

## What is the Message Broker?

The Message Broker is the component that automatically forwards fitness test results from WarriorFit to the Belgian Military HR system (BEMIL). Every time a soldier completes a physical test, the broker packages the result and delivers it reliably — retrying on failure, and logging permanently failed deliveries.

No database or network connection is needed to run these tests; all external systems are simulated.

---

## What Is Being Tested

### 1. Data Formatting (DTO Field Mapping)

Before a test result is sent to the HR system, it must be converted into a standardised data format (JSON). These tests verify that each test type produces the correct fields and values.

| Test Type | Verified Fields |
|---|---|
| Physical Fitness Test (PHEF) | serial number, running time, side-bridge scores |
| Combat Test (Paratrooper) | serial number, running time, obstacle and rope passage |
| Combat Swimming Test | serial number, swim passed/failed |
| March Test | service number, distance, succeeded, date and time |
| Functional Test | serial number, push-ups, sit-ups, pull-ups |

**Why it matters:** If the format is wrong, the HR system rejects the message or stores incorrect data against a soldier's record.

---

### 2. Message Queuing

When a test is saved in WarriorFit, it is first placed in an internal queue before being written to the database and forwarded. These tests confirm that:

- All five recognised test types are accepted and queued.
- Unrecognised data types are silently discarded (no crash, no corrupt queue entry).
- Every queued message carries a creation timestamp for audit purposes.

**Why it matters:** A corrupted queue means test results are lost before they ever reach the HR system.

---

### 3. Processing Cycle

The broker runs a background loop that periodically wakes up and does two things: it flushes the in-memory queue to the database, and it attempts to send pending messages to the HR system. These tests confirm that:

- All queued messages (including multiple at once) are written to the database and removed from the in-memory queue.
- An empty queue does not cause unnecessary database writes.
- Both steps (flush + send) always run each cycle.

**Why it matters:** Missed or duplicate writes would create inconsistencies between the WarriorFit database and the HR system.

---

### 4. Delivery to HR System

Once messages are in the database, the broker retrieves them in configurable batches and attempts delivery. These tests verify the delivery decision logic:

| Scenario | Expected behaviour |
|---|---|
| Delivery succeeds | Message is deleted from the queue |
| Delivery fails (e.g. timeout) | Message is kept and marked for retry with a delay |
| Max retries exceeded | Message is moved to "dead-letter" and an error is logged |
| No messages due | Nothing happens (no unnecessary calls) |
| Batch size set to 7 | Repository is asked for exactly 7 messages |

**Why it matters:** Without reliable retry logic, transient network problems would cause permanent data loss. Dead-letter logging ensures nothing silently disappears.

---

### 5. HR System Communication

These tests cover the low-level HTTP call to the BEMIL HR endpoint:

| Scenario | Expected behaviour |
|---|---|
| Successful HTTP response | Result is returned to the caller |
| HTTP timeout | Returns gracefully (no crash); message will be retried |
| Connection refused | Returns gracefully; message will be retried |
| Bad data / malformed response | Returns gracefully; message will be retried |
| Network OS error | Returns gracefully; message will be retried |
| Unexpected exception | Error is wrapped and reported; message will be retried |
| Task cancellation signal | Re-raised immediately (allows clean shutdown) |

**Why it matters:** The HR system may be temporarily unavailable. The broker must never crash and must never abandon a message without recording the failure.

---

### 6. Broker Lifecycle (Start / Stop)

The broker runs as a background service within the application. These tests verify the start and stop behaviour:

| Scenario | Expected behaviour |
|---|---|
| `start()` called with a running loop | Background worker is launched; `running = True`; returns `True` |
| `start()` called twice on a healthy worker | Second call is ignored; a warning is logged; returns `True` |
| `start()` called with no running loop | Warning logged, `running` stays `False`, `_worker_task` stays `None`, returns `False` (so a later call can succeed) |
| **First `send_message()` after a failed eager start** | Lazy-starts the worker via `self.start()` and then queues the message — no message is lost |
| `stop()` called | Worker is cancelled; `running = False` |
| `stop()` called when not running | Warning is logged; no error |

**Why it matters:** Incorrect lifecycle management can leave orphaned background workers consuming resources, **or — as in the pre-2026-06-17 bug — leave the broker in a half-up state (`running=True` but `_worker_task=None`) where every later `start()` is rejected and the queue silently grows forever**. The self-healing `start()` + lazy-start in `send_message()` close that gap.

---

### 7. Configuration

The broker's behaviour is controlled by five tunable parameters read from the application config file. These tests confirm that each parameter is correctly picked up, and that safe default values are used if the config does not supply them.

| Parameter | Default | Purpose |
|---|---|---|
| `broker_poll_interval_s` | 5 s | How often the broker wakes up |
| `broker_batch_size` | 5 | Messages processed per cycle |
| `broker_max_attempts` | 10 | Retries before dead-lettering |
| `broker_base_backoff_s` | 5 s | Initial retry delay |
| `broker_max_backoff_s` | 600 s | Maximum retry delay |

**Why it matters:** Misconfigured values can overload the HR system or cause messages to be dead-lettered prematurely.

---

## Test Count Summary

| Area | Tests |
|---|---|
| Data formatting | 6 |
| Message queuing | 7 |
| Processing cycle | 4 |
| Delivery to HR | 5 |
| HR communication | 7 |
| Lifecycle | 5 |
| Configuration | 2 |
| **Total** | **36** |

---

## Key Quality Guarantees

- No test result is lost silently — every failure is either retried or logged as a dead-letter.
- The broker shuts down cleanly without losing in-flight messages.
- Network and infrastructure problems never crash the application.
- Configuration mistakes result in safe fallback behaviour, not a broken startup.
