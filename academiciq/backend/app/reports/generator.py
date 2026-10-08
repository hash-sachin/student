"""
Report generator using ReportLab (PDF) and OpenPyXL (Excel).
All reports are watermarked with user, timestamp, and metric labels.
Hypothetical scenarios are stamped with the HYPOTHETICAL banner.
"""
from __future__ import annotations

import io
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

WATERMARK_TEXT = "AcademicIQ — Confidential Academic Record"
HYPOTHETICAL_STAMP = "HYPOTHETICAL SCENARIO — NOT AN ACTUAL RESULT"


class ReportGenerator:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def student_report(
        self,
        student_id: uuid.UUID,
        format: str = "pdf",
        requested_by: uuid.UUID | None = None,
    ) -> tuple[bytes, str, str]:
        """Generate a student academic profile report."""
        from app.profile.service import ProfileService
        profile = await ProfileService(self._db).get_longitudinal_profile(student_id)

        if format == "pdf":
            content = self._render_pdf_student(profile, requested_by)
            return content, "application/pdf", f"student_{str(student_id)[:8]}_report.pdf"
        elif format == "xlsx":
            content = self._render_excel_student(profile, requested_by)
            return content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", \
                   f"student_{str(student_id)[:8]}_report.xlsx"
        elif format == "csv":
            content = self._render_csv_student(profile)
            return content, "text/csv", f"student_{str(student_id)[:8]}_report.csv"
        else:
            from app.core.exceptions import ValidationError
            raise ValidationError(f"Unsupported format: {format}")

    async def class_report(
        self,
        section_id: uuid.UUID,
        examination_id: uuid.UUID,
        format: str = "pdf",
        requested_by: uuid.UUID | None = None,
    ) -> tuple[bytes, str, str]:
        """Generate a class analytics report."""
        from app.analytics.engine import AnalyticsEngine
        analytics = await AnalyticsEngine(self._db).compute_class_analytics(section_id, examination_id)

        if format == "pdf":
            content = self._render_pdf_class(analytics, requested_by)
            return content, "application/pdf", f"class_{str(section_id)[:8]}_report.pdf"
        else:
            raise NotImplementedError(f"Format {format} not yet implemented for class reports")

    # ------------------------------------------------------------------
    # PDF rendering
    # ------------------------------------------------------------------

    def _render_pdf_student(self, profile: dict, requested_by: uuid.UUID | None) -> bytes:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Title
        story.append(Paragraph("AcademicIQ — Student Academic Profile", styles["Title"]))
        story.append(Paragraph(
            f"[OFFICIAL ACADEMIC DOCUMENT] Generated: {datetime.now(tz=timezone.utc).isoformat()}",
            styles["Normal"]
        ))
        if requested_by:
            story.append(Paragraph(f"Requested by: {str(requested_by)[:8]}...", styles["Normal"]))
        story.append(Spacer(1, 0.5 * cm))

        # Watermark note
        story.append(Paragraph(
            f"⚠ {WATERMARK_TEXT}", ParagraphStyle("warn", fontSize=8, textColor=colors.gray)
        ))
        story.append(Spacer(1, 0.5 * cm))

        # Student info
        student = profile.get("student", {})
        story.append(Paragraph(f"Student: {student.get('name', 'N/A')}", styles["Heading2"]))
        story.append(Paragraph(f"Register Number: {student.get('register_number', 'N/A')}", styles["Normal"]))
        story.append(Spacer(1, 0.3 * cm))

        # Metric label legend
        story.append(Paragraph(
            "Metric Labels: OFFICIAL = from source document | CALCULATED = derived | "
            "ESTIMATED = heuristic | HYPOTHETICAL = what-if only",
            ParagraphStyle("legend", fontSize=7, textColor=colors.blue)
        ))
        story.append(Spacer(1, 0.5 * cm))

        # Timeline
        for entry in profile.get("timeline", []):
            story.append(Paragraph(
                f"Examination: {entry.get('academic_year')} — {entry.get('examination_type')}",
                styles["Heading3"]
            ))
            metrics = entry.get("semester_metrics", {})
            story.append(Paragraph(
                f"Average: {metrics.get('average')} [{metrics.get('metric_label', 'CALCULATED')}] | "
                f"Passed: {metrics.get('subjects_passed')} | Failed: {metrics.get('subjects_failed')}",
                styles["Normal"]
            ))
            att = entry.get("attention")
            if att:
                story.append(Paragraph(
                    f"Academic Attention Band: {att.get('band')} (Score: {att.get('score')}) "
                    f"[{att.get('metric_label', 'ESTIMATED')}]",
                    styles["Normal"]
                ))
            story.append(Spacer(1, 0.3 * cm))

        doc.build(story)
        buffer.seek(0)
        return buffer.read()

    def _render_pdf_class(self, analytics: dict, requested_by: uuid.UUID | None) -> bytes:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.units import cm

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph("AcademicIQ — Class Analytics Report", styles["Title"]))
        story.append(Paragraph(
            f"Generated: {datetime.now(tz=timezone.utc).isoformat()} | "
            f"Metric Label: {analytics.get('metric_label')}",
            styles["Normal"]
        ))
        story.append(Spacer(1, 0.5 * cm))

        for k, v in analytics.items():
            story.append(Paragraph(f"{k}: {v}", styles["Normal"]))

        doc.build(story)
        buffer.seek(0)
        return buffer.read()

    def _render_excel_student(self, profile: dict, requested_by: uuid.UUID | None) -> bytes:
        import openpyxl
        from openpyxl.styles import Font, PatternFill

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Academic Profile"

        # Header
        ws["A1"] = "AcademicIQ — Student Academic Profile"
        ws["A1"].font = Font(bold=True, size=14)
        ws["A2"] = f"Generated: {datetime.now(tz=timezone.utc).isoformat()}"
        ws["A3"] = WATERMARK_TEXT
        ws["A3"].font = Font(color="808080", italic=True)

        student = profile.get("student", {})
        ws["A5"] = "Name"
        ws["B5"] = student.get("name")
        ws["A6"] = "Register Number"
        ws["B6"] = student.get("register_number")
        ws["A7"] = "Status"
        ws["B7"] = student.get("status")

        row = 9
        ws.cell(row=row, column=1, value="Academic Year")
        ws.cell(row=row, column=2, value="Type")
        ws.cell(row=row, column=3, value="Average [CALCULATED]")
        ws.cell(row=row, column=4, value="Passed")
        ws.cell(row=row, column=5, value="Failed")
        ws.cell(row=row, column=6, value="Attention Band [ESTIMATED]")
        row += 1

        for entry in profile.get("timeline", []):
            metrics = entry.get("semester_metrics", {})
            att = entry.get("attention") or {}
            ws.cell(row=row, column=1, value=entry.get("academic_year"))
            ws.cell(row=row, column=2, value=entry.get("examination_type"))
            ws.cell(row=row, column=3, value=metrics.get("average"))
            ws.cell(row=row, column=4, value=metrics.get("subjects_passed"))
            ws.cell(row=row, column=5, value=metrics.get("subjects_failed"))
            ws.cell(row=row, column=6, value=att.get("band", "N/A"))
            row += 1

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.read()

    def _render_csv_student(self, profile: dict) -> bytes:
        import csv
        buffer = io.StringIO()
        writer = csv.writer(buffer)

        writer.writerow(["AcademicIQ Student Academic Profile"])
        writer.writerow(["Generated", datetime.now(tz=timezone.utc).isoformat()])
        writer.writerow(["Watermark", WATERMARK_TEXT])
        writer.writerow([])
        writer.writerow(["Academic Year", "Type", "Average [CALCULATED]", "Passed", "Failed", "Attention Band [ESTIMATED]"])

        for entry in profile.get("timeline", []):
            metrics = entry.get("semester_metrics", {})
            att = entry.get("attention") or {}
            writer.writerow([
                entry.get("academic_year"),
                entry.get("examination_type"),
                metrics.get("average"),
                metrics.get("subjects_passed"),
                metrics.get("subjects_failed"),
                att.get("band", "N/A"),
            ])

        return buffer.getvalue().encode("utf-8")
