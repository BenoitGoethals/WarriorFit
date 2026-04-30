# Message Broker

Asynchronous message broker for HR system integration. Implements the transactional outbox pattern: fitness test results are queued in-memory, persisted to the `hr_messages` table, then forwarded to the external HR API with exponential back-off retry and dead-letter handling.

::: warriorfit.mom.broker
    options:
      members_order: source
      show_source: true
