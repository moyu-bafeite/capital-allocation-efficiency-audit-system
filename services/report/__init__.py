"""PDF audit report generator.

Usage:
    from services.report import build_report
    pdf_bytes = build_report(data, params, result)
"""

from services.report.builder import build_report, build_report_html

__all__ = ["build_report", "build_report_html"]
