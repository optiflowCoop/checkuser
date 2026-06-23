# scripts/reporting/html_builder.py
from .html_data_processor import DataProcessor
from .html_template import render_html

def build_html_structure(summary, governance, app_points, domains):
    """
    Orchestrates the data processing and HTML rendering.
    """
    processor = DataProcessor(summary, governance, app_points, domains)
    processed_data = processor.get_all_data()
    return render_html(processed_data)
