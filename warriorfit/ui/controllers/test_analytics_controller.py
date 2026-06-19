"""Controller for the Test Analytics page.

Builds plotly HTML for four cohort-level diagnostic charts:

- MFFT bottleneck bar — which of the 8 events most often causes failure.
- MFFT per-event histograms — raw distribution per event with tier thresholds.
- Pass rate per age bracket — grouped bar across all five test types.
- Coverage gauges — % of unit who completed each test this year.
- Monthly pass-rate trend — line per test type over the calendar year.

All methods return ``str | None``: a Plotly HTML fragment, or ``None`` when
there is no data to render so the page can show a placeholder.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from warriorfit.config.application_config import ApplicationConfig
from warriorfit.core.mfft_level import MfftLevel
from warriorfit.core.type_fitness_test import TypeFitnessTest
from warriorfit.data.model.db_model import (
    CombatSwimmingTest,
    CombatTestParatrooper,
    FunctionalTest,
    MfftEvalTest,
    PhefTest,
    ServiceMen,
)
from warriorfit.logic.mfft_eval_calculator import (
    COMBAT_THRESHOLDS,
    MfftEvalCalculator,
)
from warriorfit.logic.phef_calculator import PhefCalculator
from warriorfit.services.military_service import MilitaryService
from warriorfit.services.service_march import ServiceMarch
from warriorfit.services.service_test import ServiceTest

_TIER_COLORS: dict[MfftLevel, str] = {
    MfftLevel.GOLD: "#d4af37",
    MfftLevel.SILVER: "#8a8a8a",
    MfftLevel.BRONZE: "#cd7f32",
    MfftLevel.FIT: "#198754",
    MfftLevel.UNFIT: "#dc3545",
}

_TEST_COLORS: dict[str, str] = {
    "PHEF": "#0d6efd",
    "Combat": "#198754",
    "Functional": "#ffc107",
    "Swimming": "#0dcaf0",
    "MFFT": "#6f42c1",
}

_AGE_BRACKETS: tuple[str, ...] = ("<30", "30-39", "40-49", "50+")

_MFFT_EVENT_LABELS: tuple[str, ...] = (
    "Pull-ups",
    "Burpees step-over",
    "Farmer walk (m)",
    "Push-ups & release",
    "Casualty drag (m)",
    "Sandbag carry (m)",
    "Combat run (s)",
    "Combat swim (s)",
)

_MFFT_EVENT_ATTRS: tuple[str, ...] = (
    "pull_ups",
    "burpees_step_over",
    "farmer_walk_m",
    "push_ups_release",
    "casualty_drag_m",
    "sandbag_carry_m",
    "combat_run_seconds",
    "combat_swim_seconds",
)


def _age_bracket(age: int) -> str:
    if age < 30:
        return "<30"
    if age < 40:
        return "30-39"
    if age < 50:
        return "40-49"
    return "50+"


class TestAnalyticsController:
    """Aggregates unit test data into chart-ready dataframes / HTML."""

    def __init__(
        self,
        test_service: ServiceTest | None = None,
        mil_service: MilitaryService | None = None,
        march_service: ServiceMarch | None = None,
        config: ApplicationConfig | None = None,
    ) -> None:
        _config = config if config is not None else ApplicationConfig()
        self._service = test_service if test_service is not None else ServiceTest()
        self.be_mil_service = mil_service if mil_service is not None else MilitaryService()
        self._march_service = march_service if march_service is not None else ServiceMarch()
        self.unit_name = _config.own_unit
        self._logger = logging.getLogger(__name__)
        self._mils: dict[str, ServiceMen] | None = None
        self._serials: set[str] | None = None
        self._tests_cache: dict[str, list[Any]] = {}

    # -----------------------
    # Cache helpers
    # -----------------------
    def reset_cache(self) -> None:
        self._mils = None
        self._serials = None
        self._tests_cache.clear()

    async def _all_mils(self) -> dict[str, ServiceMen]:
        if self._mils is None:
            try:
                people = await self.be_mil_service.get_all_be_mil_from_unit(self.unit_name)
                self._mils = {p.service_number: p for p in (people or [])}
            except (AttributeError, TypeError):
                self._mils = {}
        return self._mils

    async def _own_unit_serials(self) -> set[str]:
        if self._serials is None:
            mils = await self._all_mils()
            self._serials = set(mils.keys())
        return self._serials

    async def _tests_for_unit(self, t: TypeFitnessTest) -> list[Any]:
        """Fetch (and cache) every test of type ``t`` linked to the unit's serials.

        Each returned object additionally carries a ``_session_dt`` attribute so
        downstream charts can group by month without re-querying.
        """
        key = t.name
        if key in self._tests_cache:
            return self._tests_cache[key]
        sessions = await self._service.get_all_test_sessions()
        serials = await self._own_unit_serials()
        results: list[Any] = []
        for sess in sessions or []:
            if t == TypeFitnessTest.PHEF:
                tests = await self._service.get_all_phef(sess.id)
            elif t == TypeFitnessTest.COMBAT:
                tests = await self._service.get_all_combat_test(sess.id)
            elif t == TypeFitnessTest.FUNCTIONAL:
                tests = await self._service.get_all_functional_test(sess.id)
            elif t == TypeFitnessTest.SWIMMING:
                tests = await self._service.get_all_combat_swimming_test(sess.id)
            elif t == TypeFitnessTest.MFFT_EVAL:
                tests = await self._service.get_all_mfft_eval(sess.id)
            else:
                tests = []
            for test in tests:
                if getattr(test, "serial_number", None) in serials:
                    setattr(test, "_session_dt", sess.datetime_start)  # noqa: B010
                    results.append(test)
        self._tests_cache[key] = results
        return results

    # -----------------------
    # Pass/fail classification (per test type)
    # -----------------------
    @staticmethod
    def _passed_combat(test: CombatTestParatrooper) -> bool:
        return bool(test.rope_passed and test.obstacle_passed and (test.running_time or 0) <= 7200)

    @staticmethod
    def _passed_functional(test: FunctionalTest) -> bool:
        total = int(test.push_ups or 0) + int(test.sit_ups or 0) + int(test.pull_ups or 0)
        return total >= 50

    @staticmethod
    def _passed_swim(test: CombatSwimmingTest) -> bool:
        return bool(test.swim_paased)

    def _passed_phef(self, test: PhefTest, sm: ServiceMen) -> bool:
        try:
            return bool(
                PhefCalculator.calculate_phef_score(
                    test.running_time,
                    test.sideBridge_l,
                    test.sideBridge_r,
                    sm.age_from_birthdate(),
                    sm.gender,
                )[4]
            )
        except (AttributeError, TypeError, ValueError, IndexError):
            return False

    def _passed_mfft(self, test: MfftEvalTest, sm: ServiceMen) -> bool:
        try:
            age = sm.age_from_birthdate()
            return MfftEvalCalculator.evaluate(test, sm.cluster, age, sm.gender).passed
        except (AttributeError, TypeError, KeyError, ValueError):
            return False

    async def _passed(self, test: Any, test_type: str, sm: ServiceMen | None) -> bool:
        """Dispatch to the right pass/fail check by test type label."""
        if test_type == "PHEF" and sm is not None:
            return self._passed_phef(test, sm)
        if test_type == "Combat":
            return self._passed_combat(test)
        if test_type == "Functional":
            return self._passed_functional(test)
        if test_type == "Swimming":
            return self._passed_swim(test)
        if test_type == "MFFT" and sm is not None:
            return self._passed_mfft(test, sm)
        return False

    # -----------------------
    # 1. MFFT bottleneck bar
    # -----------------------
    async def mfft_bottleneck_html(self) -> str | None:
        tests: list[MfftEvalTest] = await self._tests_for_unit(TypeFitnessTest.MFFT_EVAL)
        if not tests:
            return None

        mils = await self._all_mils()
        per_event_unfit = [0] * 8
        total_failed = 0

        for test in tests:
            sm = mils.get(test.serial_number)
            if sm is None:
                continue
            try:
                res = MfftEvalCalculator.evaluate(
                    test, sm.cluster, sm.age_from_birthdate(), sm.gender
                )
            except (AttributeError, TypeError, KeyError, ValueError):
                continue
            if res.passed:
                continue
            total_failed += 1
            for idx, tier in enumerate(res.per_event):
                if tier is MfftLevel.UNFIT:
                    per_event_unfit[idx] += 1

        if total_failed == 0:
            return None

        percentages = [c / total_failed * 100 for c in per_event_unfit]
        fig = go.Figure(
            data=[
                go.Bar(
                    x=list(_MFFT_EVENT_LABELS),
                    y=percentages,
                    marker_color="#dc3545",
                    text=[f"{p:.0f}%" for p in percentages],
                    textposition="outside",
                )
            ]
        )
        fig.update_layout(
            xaxis_title="Event",
            yaxis_title="% of failed MFFTs failing this event",
            yaxis_range=[0, 100],
            margin=dict(t=30, b=80, l=50, r=20),
        )
        return fig.to_html(include_plotlyjs="cdn", div_id="mfft_bottleneck")

    # -----------------------
    # 2. MFFT per-event histograms (8 subplots)
    # -----------------------
    async def mfft_event_histograms_html(self) -> str | None:
        tests: list[MfftEvalTest] = await self._tests_for_unit(TypeFitnessTest.MFFT_EVAL)
        if not tests:
            return None

        fig = make_subplots(
            rows=2,
            cols=4,
            subplot_titles=_MFFT_EVENT_LABELS,
            horizontal_spacing=0.06,
            vertical_spacing=0.20,
        )

        for i, attr in enumerate(_MFFT_EVENT_ATTRS):
            values = [getattr(t, attr) for t in tests if getattr(t, attr, None) is not None]
            if not values:
                continue
            row = i // 4 + 1
            col = i % 4 + 1
            fig.add_trace(
                go.Histogram(
                    x=values,
                    marker_color="#0d6efd",
                    showlegend=False,
                    nbinsx=15,
                ),
                row=row,
                col=col,
            )
            gold = COMBAT_THRESHOLDS[MfftLevel.GOLD][i]
            silver = COMBAT_THRESHOLDS[MfftLevel.SILVER][i]
            bronze = COMBAT_THRESHOLDS[MfftLevel.BRONZE][i]
            fit = COMBAT_THRESHOLDS[MfftLevel.FIT][i]
            for thr, color in (
                (gold, _TIER_COLORS[MfftLevel.GOLD]),
                (silver, _TIER_COLORS[MfftLevel.SILVER]),
                (bronze, _TIER_COLORS[MfftLevel.BRONZE]),
                (fit, _TIER_COLORS[MfftLevel.FIT]),
            ):
                fig.add_vline(
                    x=thr,
                    line_color=color,
                    line_dash="dash",
                    line_width=1.5,
                    row=row,
                    col=col,
                )

        fig.update_layout(
            height=520,
            margin=dict(t=40, b=20, l=40, r=20),
            showlegend=False,
        )
        return fig.to_html(include_plotlyjs="cdn", div_id="mfft_event_histograms")

    # -----------------------
    # 3. Pass rate per age bracket per test type
    # -----------------------
    async def pass_rate_by_age_html(self) -> str | None:
        mils = await self._all_mils()
        if not mils:
            return None

        type_tests: list[tuple[str, TypeFitnessTest]] = [
            ("PHEF", TypeFitnessTest.PHEF),
            ("Combat", TypeFitnessTest.COMBAT),
            ("Functional", TypeFitnessTest.FUNCTIONAL),
            ("Swimming", TypeFitnessTest.SWIMMING),
            ("MFFT", TypeFitnessTest.MFFT_EVAL),
        ]

        passed_counts: dict[str, dict[str, int]] = {
            label: dict.fromkeys(_AGE_BRACKETS, 0) for label, _ in type_tests
        }
        total_counts: dict[str, dict[str, int]] = {
            label: dict.fromkeys(_AGE_BRACKETS, 0) for label, _ in type_tests
        }

        any_data = False
        for label, ftype in type_tests:
            tests = await self._tests_for_unit(ftype)
            for test in tests:
                sm = mils.get(test.serial_number)
                if sm is None:
                    continue
                bracket = _age_bracket(sm.age_from_birthdate())
                total_counts[label][bracket] += 1
                any_data = True
                if await self._passed(test, label, sm):
                    passed_counts[label][bracket] += 1

        if not any_data:
            return None

        fig = go.Figure()
        for label, _ in type_tests:
            rates = []
            for bracket in _AGE_BRACKETS:
                total = total_counts[label][bracket]
                rates.append((passed_counts[label][bracket] / total * 100) if total > 0 else 0)
            fig.add_trace(
                go.Bar(
                    name=label,
                    x=list(_AGE_BRACKETS),
                    y=rates,
                    marker_color=_TEST_COLORS[label],
                )
            )
        fig.update_layout(
            barmode="group",
            xaxis_title="Age bracket",
            yaxis_title="Pass rate (%)",
            yaxis_range=[0, 100],
            margin=dict(t=30, b=40, l=50, r=20),
            legend_title_text="Test type",
        )
        return fig.to_html(include_plotlyjs="cdn", div_id="pass_rate_by_age")

    # -----------------------
    # 4. Coverage gauges
    # -----------------------
    async def coverage_html(self) -> str | None:
        serials = await self._own_unit_serials()
        if not serials:
            return None
        total = len(serials)

        type_tests: list[tuple[str, TypeFitnessTest]] = [
            ("PHEF", TypeFitnessTest.PHEF),
            ("Combat", TypeFitnessTest.COMBAT),
            ("Functional", TypeFitnessTest.FUNCTIONAL),
            ("Swimming", TypeFitnessTest.SWIMMING),
            ("MFFT", TypeFitnessTest.MFFT_EVAL),
        ]

        coverage: list[tuple[str, float, int]] = []
        for label, ftype in type_tests:
            tests = await self._tests_for_unit(ftype)
            done = {t.serial_number for t in tests if t.serial_number in serials}
            pct = len(done) / total * 100 if total > 0 else 0
            coverage.append((label, pct, len(done)))

        fig = make_subplots(
            rows=1,
            cols=len(coverage),
            specs=[[{"type": "indicator"}] * len(coverage)],
            subplot_titles=[label for label, _, _ in coverage],
            horizontal_spacing=0.05,
        )
        for i, (label, pct, done) in enumerate(coverage, start=1):
            fig.add_trace(
                go.Indicator(
                    mode="gauge+number",
                    value=round(pct, 1),
                    number={"suffix": "%", "valueformat": ".1f"},
                    title={"text": f"{done}/{total}", "font": {"size": 12}},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": _TEST_COLORS[label]},
                        "steps": [
                            {"range": [0, 50], "color": "#f8d7da"},
                            {"range": [50, 80], "color": "#fff3cd"},
                            {"range": [80, 100], "color": "#d4edda"},
                        ],
                    },
                ),
                row=1,
                col=i,
            )
        fig.update_layout(height=300, margin=dict(t=40, b=20, l=20, r=20))
        return fig.to_html(include_plotlyjs="cdn", div_id="coverage_gauges")

    # -----------------------
    # 5. Monthly pass-rate trend
    # -----------------------
    async def monthly_pass_rate_html(self) -> str | None:
        mils = await self._all_mils()
        if not mils:
            return None

        type_tests: list[tuple[str, TypeFitnessTest]] = [
            ("PHEF", TypeFitnessTest.PHEF),
            ("Combat", TypeFitnessTest.COMBAT),
            ("Functional", TypeFitnessTest.FUNCTIONAL),
            ("Swimming", TypeFitnessTest.SWIMMING),
            ("MFFT", TypeFitnessTest.MFFT_EVAL),
        ]

        # buckets[label][YYYY-MM] = (passed, total)
        buckets: dict[str, dict[str, list[int]]] = {
            label: defaultdict(lambda: [0, 0]) for label, _ in type_tests
        }
        any_data = False

        for label, ftype in type_tests:
            tests = await self._tests_for_unit(ftype)
            for test in tests:
                sm = mils.get(test.serial_number)
                if sm is None:
                    continue
                dt = getattr(test, "_session_dt", None)
                if dt is None:
                    continue
                key = dt.strftime("%Y-%m")
                bucket = buckets[label][key]
                bucket[1] += 1
                any_data = True
                if await self._passed(test, label, sm):
                    bucket[0] += 1

        if not any_data:
            return None

        # Sorted union of months across all test types
        all_months = sorted({m for label in buckets for m in buckets[label]})
        if not all_months:
            return None

        # Human-friendly labels (e.g. "Jun 2026") for a discrete category axis.
        # Without a category axis Plotly treats "YYYY-MM" as a continuous
        # datetime; with a single month it zooms to a sub-second range and
        # renders unreadable "23:59:59.999" style ticks.
        month_labels = [datetime.strptime(m, "%Y-%m").strftime("%b %Y") for m in all_months]

        fig = go.Figure()
        for label, _ in type_tests:
            series = []
            for m in all_months:
                p, t = buckets[label].get(m, [0, 0])
                series.append((p / t * 100) if t > 0 else None)
            fig.add_trace(
                go.Scatter(
                    name=label,
                    x=month_labels,
                    y=series,
                    mode="lines+markers",
                    line=dict(color=_TEST_COLORS[label], width=2),
                    marker=dict(size=7),
                    connectgaps=False,
                )
            )
        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Pass rate (%)",
            yaxis_range=[0, 105],
            xaxis=dict(type="category", categoryorder="array", categoryarray=month_labels),
            margin=dict(t=30, b=40, l=50, r=20),
            legend_title_text="Test type",
            hovermode="x unified",
        )
        return fig.to_html(include_plotlyjs="cdn", div_id="monthly_pass_rate")

    # Unused import guard (keep imports stable while px/pd may be useful later)
    _unused_px = px  # noqa: RUF100
    _unused_pd = pd  # noqa: RUF100
