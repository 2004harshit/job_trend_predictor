# dashboards/utils/pipeline_loader.py
"""
Single place where the AnalyticsPipeline is loaded and cached.
All dashboard pages import from here — never import AnalyticsPipeline directly.
"""
import streamlit as st
import pandas as pd
from pipelines.analytics_pipeline import AnalyticsPipeline

DATA_PATH = r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv"


@st.cache_data(show_spinner="Loading job market data…")
def load_dataframe() -> pd.DataFrame:
    """Cached CSV load — runs once per session."""
    return pd.read_csv(DATA_PATH)


@st.cache_data(show_spinner="Computing global market metrics…")
def get_global_metrics(_df: pd.DataFrame) -> dict:
    """
    Phase 1 — runs ONCE at app startup, cached for the entire session.
    MarketDemandEngine is expensive; this prevents it re-running on every click.

    Note: leading underscore on _df tells Streamlit not to hash the DataFrame.
    """
    return AnalyticsPipeline(_df).run_global_phase()


def run_domain_analytics(
    df: pd.DataFrame,
    domain: str,
    experience_band: tuple,
    location: str,
    recommended_domains: list = None,
    global_results: dict = None,
) -> dict:
    """
    Phase 2 — called after user selects domain on any dashboard form.
    Result is stored in st.session_state["domain_analytics"].
    """
    pipeline = AnalyticsPipeline(df)
    return pipeline.run_domain_phase(
        domain=domain,
        experience_band=experience_band,
        location=location,
        recommended_domains=recommended_domains,
        global_results=global_results,
    )


def run_profile_analytics(
    df: pd.DataFrame,
    domain: str,
    experience_band: tuple,
    location: str,
    user_skills: list,
    prior_knowledge: str,
    user_project_stats: dict,
    domain_results: dict,
    target_domain_2: str = None,
) -> dict:
    """
    Phase 3 — called after user completes the full profiler form.
    Result is stored in st.session_state["profile_analytics"].
    """
    pipeline = AnalyticsPipeline(df)
    return pipeline.run_profile_phase(
        domain=domain,
        experience_band=experience_band,
        location=location,
        user_skills=user_skills,
        prior_knowledge=prior_knowledge,
        user_project_stats=user_project_stats,
        domain_results=domain_results,
        target_domain_2=target_domain_2,
    )