"""PDF audit report generator.

Usage:
    from report import build_report
    pdf_bytes = build_report(data, params, result)
"""

from report.builder import build_report, build_report_html

__all__ = ["build_report", "build_report_html"]
