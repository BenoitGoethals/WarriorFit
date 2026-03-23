"""Unit tests for ServiceCross.read_xml_chronos_and_save."""
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from warriorfit.services.service_cross import ServiceCross

# ---------------------------------------------------------------------------
# XML content
# ---------------------------------------------------------------------------

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


def _xml_with_net(net_value: str) -> str:
    return f"""\
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_service(repo_result: bool = True) -> tuple[ServiceCross, AsyncMock, AsyncMock]:
    """Return (service, add_runners_mock, audit_log_mock)."""
    add_runners: AsyncMock = AsyncMock(return_value=repo_result)
    audit_log: AsyncMock = AsyncMock(return_value=None)
    mock_repo = MagicMock()
    mock_repo.add_runners_to_cross = add_runners
    svc = ServiceCross(cross_repository=mock_repo, user_repository=None)
    svc.add_audit_log = audit_log
    return svc, add_runners, audit_log


def _write_xml(directory: Path, name: str, content: str) -> list[dict]:
    p = directory / name
    p.write_text(content, encoding="utf-8")
    return [{"datapath": str(p)}]


def run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def svc_ok() -> tuple[ServiceCross, AsyncMock, AsyncMock]:
    """service, add_runners mock (returns True), audit_log mock."""
    return _build_service(repo_result=True)


@pytest.fixture()
def svc_fail() -> tuple[ServiceCross, AsyncMock, AsyncMock]:
    """service, add_runners mock (returns False), audit_log mock."""
    return _build_service(repo_result=False)


@pytest.fixture()
def valid_xml_file(tmp_path) -> list[dict]:
    return _write_xml(tmp_path, "valid.xml", VALID_XML)


@pytest.fixture()
def invalid_xml_file(tmp_path) -> list[dict]:
    return _write_xml(tmp_path, "invalid.xml", INVALID_XML)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_valid_xml_returns_true(svc_ok, valid_xml_file):
    svc, _, _ = svc_ok
    assert run(svc.read_xml_chronos_and_save(valid_xml_file, cross_id=1)) is True


def test_valid_xml_passes_cross_id(svc_ok, valid_xml_file):
    svc, add_runners, _ = svc_ok
    run(svc.read_xml_chronos_and_save(valid_xml_file, cross_id=42))
    cross_id_arg, _ = add_runners.call_args[0]
    assert cross_id_arg == 42


def test_valid_xml_passes_two_runners(svc_ok, valid_xml_file):
    svc, add_runners, _ = svc_ok
    run(svc.read_xml_chronos_and_save(valid_xml_file, cross_id=1))
    _, runners = add_runners.call_args[0]
    assert len(runners) == 2


def test_valid_xml_runner_bibs(svc_ok, valid_xml_file):
    svc, add_runners, _ = svc_ok
    run(svc.read_xml_chronos_and_save(valid_xml_file, cross_id=1))
    _, runners = add_runners.call_args[0]
    assert {r.serial_number for r in runners} == {"101", "202"}


def test_valid_xml_runner_times(svc_ok, valid_xml_file):
    svc, add_runners, _ = svc_ok
    run(svc.read_xml_chronos_and_save(valid_xml_file, cross_id=1))
    _, runners = add_runners.call_args[0]
    times = {r.serial_number: r.running_time for r in runners}
    assert times["101"] == pytest.approx(2110.0)   # 0:35:10
    assert times["202"] == pytest.approx(2250.0)   # 0:37:30


def test_audit_log_called_on_success(svc_ok, valid_xml_file):
    svc, _, audit_log = svc_ok
    run(svc.read_xml_chronos_and_save(valid_xml_file, cross_id=7))
    assert audit_log.await_count == 1


# ---------------------------------------------------------------------------
# XSD validation failure
# ---------------------------------------------------------------------------

def test_invalid_xml_returns_false(svc_ok, invalid_xml_file):
    svc, _, _ = svc_ok
    assert run(svc.read_xml_chronos_and_save(invalid_xml_file, cross_id=1)) is False


def test_invalid_xml_does_not_save(svc_ok, invalid_xml_file):
    svc, add_runners, _ = svc_ok
    run(svc.read_xml_chronos_and_save(invalid_xml_file, cross_id=1))
    add_runners.assert_not_awaited()


# ---------------------------------------------------------------------------
# Repository failure
# ---------------------------------------------------------------------------

def test_repo_failure_returns_false(svc_fail, valid_xml_file):
    svc, _, _ = svc_fail
    assert run(svc.read_xml_chronos_and_save(valid_xml_file, cross_id=1)) is False


# ---------------------------------------------------------------------------
# File not found
# ---------------------------------------------------------------------------

def test_missing_file_returns_false(svc_ok):
    svc, _, _ = svc_ok
    result = run(svc.read_xml_chronos_and_save(
        [{"datapath": "/nonexistent/path/file.xml"}], cross_id=1
    ))
    assert result is False


# ---------------------------------------------------------------------------
# Net time parsing
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("net_value, expected_seconds", [
    ("0:35:10", 2110.0),   # hh:mm:ss
    ("35:10",   2110.0),   # mm:ss
    ("2110",    2110.0),   # plain seconds
    ("1:00:00", 3600.0),   # exactly 1 hour
])
def test_net_time_parsing(svc_ok, tmp_path, net_value: str, expected_seconds: float):
    svc, add_runners, _ = svc_ok
    xml_file = _write_xml(tmp_path, f"net_{net_value.replace(':', '_')}.xml", _xml_with_net(net_value))
    run(svc.read_xml_chronos_and_save(xml_file, cross_id=1))
    _, runners = add_runners.call_args[0]
    assert runners[0].running_time == pytest.approx(expected_seconds)
