# Broker Class Documentation

The `Broker` class serves as a background service responsible for reliably transmitting messages from the application to a remote HTTP endpoint (typically an API). It decouples message generation from message transmission using an asynchronous queue system.

**Location**: `mom/broker.py`

## Overview

The Broker operates on a "fire-and-forget" principle from the perspective of the main application, while internally managing delivery reliability. It runs a dedicated background thread that continuously processes a message queue.

### Key Features

*   **Asynchronous Processing**: Utilizes `asyncio` and `httpx` for non-blocking HTTP requests.
*   **Message Buffering**: Uses a `MessageContainer` to queue messages when the consumer is busy or the network is unavailable.
*   **Background Execution**: Runs in a separate `threading.Thread` so it does not block the main application UI or logic.
*   **Reliability**: Messages are removed from the local queue only after a successful HTTP response (HTTP 200 OK) is received.

## Class Definition

### `Broker`

#### Initialization
```python
def __init__(self, url: str = "http://127.0.0.1:8005/api/v1/phef/test")
```
*   **url**: The target endpoint URL where messages will be POSTed.

#### Properties

*   **`is_running`**: Returns `True` if the broker's processing loop is active.

#### Methods

| Method | Description |
| :--- | :--- |
| `start()` | Starts the background thread and the asyncio event loop. |
| `stop()` | Signals the loop to stop and joins the background thread (waits up to 5 seconds). |
| `send_message(message: Message)` | Adds a `Message` object to the internal queue for processing. Raises `TypeError` if the input is not a valid Message. |
![img_seq_broker.png](img_seq_broker.png)
## Internal Logic

1.  **The Loop (`_run_loop`)**:
    *   Checks the queue every 1 second.
    *   If a message exists, it attempts to send it via `_send_message_to_hr`.
    *   If the sending succeeds (returns `success: True`), the message is permanently deleted from the queue.
    *   If it fails, the message remains in the queue for a retry (FIFO behavior implies it might block newer messages depending on queue implementation, but ensures delivery).

2.  **Sending (`_send_message_to_hr`)**:
    *   Converts the message to a dictionary.
    *   Sends a POST request with headers `{'accept': 'application/json', 'Content-Type': 'application/json'}`.

## Usage Example

```python
import time
from mom.message import Message
from mom.broker import Broker, PhefTestDto
from data.db.db_model import PhefTest

# 1. Initialize Broker
broker = Broker(url="http://localhost:8005/api/v1/endpoint")

# 2. Start the background service
broker.start()

# 3. Create data and send
data = PhefTest(serial_number="12345", running_time=120.0)
dto = PhefTestDto(data)
msg = Message(content=dto)

broker.send_message(msg)

# 4. Stop when done (usually at app exit)
broker.stop()
```