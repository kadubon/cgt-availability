"""Report renderers."""

from cgt_availability.renderers.json import render_json_report
from cgt_availability.renderers.markdown import render_markdown_report

__all__ = ["render_json_report", "render_markdown_report"]
