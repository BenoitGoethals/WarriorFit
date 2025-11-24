# Python
from __future__ import annotations

from typing import List, Dict, Tuple
from dataclasses import dataclass

from warriorfit.services.report_generator_csv import ReportGeneratorCsv
from warriorfit.services.report_generator_pdf import ReportGeneratorPdf
from warriorfit.services.report_type import ReportType


@dataclass
class ReportRequest:
    title: str
    test_type: str  # "all" or specific type name compatible with ReportType.from_str
    own_unit: bool
    this_year: bool
    format: str  # "pdf" | "csv" | "both"


class ReportsController:
    def __init__(self):
        self._csv_gen = ReportGeneratorCsv()
        self._pdf_gen = ReportGeneratorPdf()

    def _resolve_targets(self, test_type: str) -> List[ReportType]:
        if test_type == "all":
            return [ReportType.PHEF, ReportType.FUNCTIONAL, ReportType.COMBAT, ReportType.SWIMMING]
        return [ReportType.from_str(test_type)]

    async def generate(self, req: ReportRequest) -> Tuple[List[str], Tuple[str, str]]:
        try:
            report_name = (req.title or "Report").strip().replace(" ", "_")
            targets = self._resolve_targets(req.test_type)
            paths: List[str] = []

            for t in targets:
                if req.format in ("csv", "both"):
                    csv_result: Dict[str, str] = await self._csv_gen.generate_report(
                        report_name, t, req.own_unit, req.this_year
                    )
                    for v in (csv_result or {}).values():
                        if v:
                            paths.append(v)
                if req.format in ("pdf", "both"):
                    pdf_result: Dict[str, str] = await self._pdf_gen.generate_report(
                        report_name, t, req.own_unit, req.this_year
                    )
                    for v in (pdf_result or {}).values():
                        if v:
                            paths.append(v)

            if paths:
                return paths, ("success", "Report generated successfully.")
            return [], ("warning", "No files were generated.")
        except Exception as e:
            return [], ("danger", f"Error generating report: {e}")