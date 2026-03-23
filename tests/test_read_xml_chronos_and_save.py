"""Unit tests for ServiceCross.read_xml_chronos_and_save."""
import asyncio
import tempfile
from unittest.mock import AsyncMock, MagicMock

import pytest

from warriorfit.services.service_cross import ServiceCross


VALID_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<results>
  <race name="Cross test" date="2026-03-23">
    <athlete>
      <bib>101</bib>
      <name>Alice Dupont</name>
      <category>SEN</category>
      <finish>2026-03-23T10:45:00</finish>
      <net>0:35:10</net>
      <rank>1</rank>
    </athlete>
    <athlete>
      <bib>202</bib>
      <name>Bob Martin</name>
      <category>M40</category>
      <finish>2026-03-23T10:47:30</finish>
      <net>0:37:30</net>
      <rank>2</rank>
    </athlete>
  </race>
</results>
"""

INVALID_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<results>
  <race name="Cross test" date="2026-03-23">
    <athlete>
      <bib>101</bib>
    </athlete>
  </race>
</results>
"""


def _make_xml_file_arg(content: str):
    """Write *content* to a temp file and return a Shiny-style file arg."""
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False, encoding="utf-8")
    tmp.write(content)
    tmp.flush()
    tmp.close()
    return [{"datapath": tmp.name}]


def _make_service(add_runners_result: bool = True) -> ServiceCross:
    mock_repo = MagicMock()
    mock_repo.add_runners_to_cross = AsyncMock(return_value=add_runners_result)
    service = ServiceCross(cross_repository=mock_repo, user_repository=None)
    service.add_audit_log = AsyncMock(return_value=None)
    return service


def run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_valid_xml_returns_true():
    service = _make_service(add_runners_result=True)
    result = run(service.read_xml_chronos_and_save(_make_xml_file_arg(VALID_XML), cross_id=1))
    assert result is True


def test_valid_xml_passes_correct_runners():
    service = _make_service(add_runners_result=True)
    run(service.read_xml_chronos_and_save(_make_xml_file_arg(VALID_XML), cross_id=42))

    cross_id_arg, runners_arg = service._cross_repo.add_runners_to_cross.call_args[0]

    assert cross_id_arg == 42
    assert len(runners_arg) == 2

    bibs = [r.serial_number for r in runners_arg]
    assert "101" in bibs
    assert "202" in bibs

    times = {r.serial_number: r.running_time for r in runners_arg}
    # 0:35:10 → 35*60 + 10 = 2110 seconds
    assert times["101"] == pytest.approx(2110.0)
    # 0:37:30 → 37*60 + 30 = 2250 seconds
    assert times["202"] == pytest.approx(2250.0)


def test_audit_log_called_on_success():
    service = _make_service(add_runners_result=True)
    run(service.read_xml_chronos_and_save(_make_xml_file_arg(VALID_XML), cross_id=7))
    service.add_audit_log.assert_awaited_once()


# ---------------------------------------------------------------------------
# XSD validation failure
# ---------------------------------------------------------------------------

def test_invalid_xml_returns_false():
    service = _make_service()
    result = run(service.read_xml_chronos_and_save(_make_xml_file_arg(INVALID_XML), cross_id=1))
    assert result is False


def test_invalid_xml_does_not_save():
    service = _make_service()
    run(service.read_xml_chronos_and_save(_make_xml_file_arg(INVALID_XML), cross_id=1))
    service._cross_repo.add_runners_to_cross.assert_not_awaited()


# ---------------------------------------------------------------------------
# Repository failure
# ---------------------------------------------------------------------------

def test_repo_failure_returns_false():
    service = _make_service(add_runners_result=False)
    result = run(service.read_xml_chronos_and_save(_make_xml_file_arg(VALID_XML), cross_id=1))
    assert result is False


# ---------------------------------------------------------------------------
# File not found / bad input
# ---------------------------------------------------------------------------

def test_missing_file_returns_false():
    service = _make_service()
    result = run(service.read_xml_chronos_and_save([{"datapath": "/nonexistent/path/file.xml"}], cross_id=1))
    assert result is False


# ---------------------------------------------------------------------------
# Net time parsing edge cases
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "net_value, expected_seconds",
    [
        ("0:35:10", 2110.0),   # hh:mm:ss
        ("35:10", 2110.0),     # mm:ss
        ("2110", 2110.0),      # plain seconds
        ("1:00:00", 3600.0),   # exactly 1 hour
    ],
)
def test_net_time_parsing(net_value: str, expected_seconds: float):
    xml = f"""\
<?xml version="1.0" encoding="UTF-8"?>
<results>
  <race name="T" date="2026-03-23">
    <athlete>
      <bib>1</bib>
      <name>Tester</name>
      <category>SEN</category>
      <finish>2026-03-23T10:00:00</finish>
      <net>{net_value}</net>
      <rank>1</rank>
    </athlete>
  </race>
</results>
"""
    service = _make_service(add_runners_result=True)
    run(service.read_xml_chronos_and_save(_make_xml_file_arg(xml), cross_id=1))

    _, runners = service._cross_repo.add_runners_to_cross.call_args[0]
    assert runners[0].running_time == pytest.approx(expected_seconds)
