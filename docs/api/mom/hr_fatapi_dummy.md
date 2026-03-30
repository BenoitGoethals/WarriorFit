# HR FastAPI Dummy

Dummy FastAPI endpoint simulating the Defence HR system. Receives PHEF test results via POST and returns acknowledgements.

## Pydantic Models

- **`MessageContent`** — PHEF test result payload
- **`MessageIn`** — Wrapper with timestamp
- **`AckResponse`** — Acknowledgement response

::: warriorfit.mom.hr_fatapi_dummy
    options:
      members_order: source
      show_source: true
