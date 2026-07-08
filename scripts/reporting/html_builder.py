# scripts/reporting/html_builder.py
from .html_data_processor import DataProcessor
from .html_template import render_html

def build_html_structure(summary, governance, app_points, domains, identity_analytics, ad_users=None, maximo_users=None, sanity_data=None, migration_data=None, allocation_data=None):
    """
    Orchestrates the data processing and HTML rendering.
    """
    processor = DataProcessor(summary, governance, app_points, domains, identity_analytics)
    processed_data = processor.get_all_data()
    # Injeta dados de AD e Maximo para a Aba 7
    processed_data['ad_users'] = ad_users or []
    processed_data['maximo_users'] = maximo_users or []
    # Injeta dados de sanity analysis
    processed_data['sanity_data'] = sanity_data
    # Injeta dados de migration analysis
    processed_data['migration_data'] = migration_data
    # Injeta dados de allocation analysis (Maximo 9)
    processed_data['allocation_data'] = allocation_data
    return render_html(processed_data)
