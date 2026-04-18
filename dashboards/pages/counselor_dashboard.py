"""
Career Counselor Dashboard page.

This file is intentionally a thin wrapper around the core implementation in
`dashboards.components.career_counslor_dashboard`.
"""


def render(navigate_to):
    """Main render function for the Career Counselor Dashboard page."""
    # The core implementation builds the Streamlit UI at import-time.
    # Importing it here ensures `app.py` has already called `st.set_page_config()`.
    _ = navigate_to
    from dashboards.components import career_counslor_dashboard  # noqa: F401

