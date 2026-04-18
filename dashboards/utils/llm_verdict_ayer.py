import os
import json
import streamlit as st
from groq import Groq  # pip install groq

# Reads GROQ_API_KEY from .env (or environment)
# Recommended: use python-dotenv if you want explicit loading
from dotenv import load_dotenv
load_dotenv()

client = Groq()   # automatically uses GROQ_API_KEY from env

@st.cache_data(ttl=3600, show_spinner=False)
def generate_verdict(
    user_profile: dict,
    top_domains: list,      # from your existing recommender
    domain_analytics: dict, # from fetch_domain_analytics()
) -> dict | None:
    """
    Converts structured ML output into a personalized plain-English verdict.
    Cached per user_profile + top_domain for 1 hour.
    """
    primary = top_domains[0] if top_domains else {}
    sal = domain_analytics.get("salary", {})
    comp = domain_analytics.get("competition", {})
    sat = domain_analytics.get("saturation", {})
    jobs = domain_analytics.get("job_openings", {})

    # Build a clean, minimal context
    context = {
        "user": {
            "experience": user_profile.get("experience", "Fresher"),
            "skills": user_profile.get("skills", []),
            "math_comfort": user_profile.get("math_comfort", "Moderate"),
            "location": user_profile.get("location", "Jaipur"),
        },
        "top_match": {
            "domain": primary.get("domain", ""),
            "match_pct": primary.get("match_percentage", 0),
        },
        "other_domains": [d.get("domain") for d in top_domains[1:3]],
        "market": {
            "demand_score": domain_analytics.get("demand_score", 0),
            "competition": comp.get("level", "Medium"),
            "candidates_per_job": comp.get("candidates_per_job", 0),
            "saturation_risk": sat.get("risk_level", "Safe"),
            "salary_range_lpa": f"₹{sal.get('low',0)}–₹{sal.get('high',0)}",
            "local_openings_30d": jobs.get("local_30d", 0),
        },
    }

    prompt = f"""You are a career counselor helping an Indian tech student pick their domain.
Be direct, specific, and honest. No fluff.

DATA:
{json.dumps(context, indent=2)}

Reply ONLY with valid JSON, no markdown, no preamble:
{{
  "verdict": "One sentence. Name the domain. Mention 1-2 specific things from their profile or market data that make it the right choice right now.",
  "why_not_others": "One sentence. Why domain 2 or 3 ranks lower FOR THIS PERSON specifically.",
  "entry_reality": "Two sentences. How hard is it to actually get hired? Be honest — mention the competition number or saturation level if relevant.",
  "next_steps": ["step 1 (specific, actionable, <= 15 words)", "step 2", "step 3"],
  "red_flag": "One honest warning, or null if there isn't one worth mentioning."
}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",   # fast & strong reasoning on Groq (good replacement for Claude Sonnet)
            # Other strong options:
            # "llama-3.1-70b-versatile" (if still available)
            # "deepseek-r1" or "qwen-qwq-32b" etc. — pick based on your needs
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.7,          # adjust if you want more/less creativity
            response_format={"type": "json_object"},  # helps enforce JSON output
        )

        raw = response.choices[0].message.content.strip()

        # Strip accidental code fences (just in case)
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        return json.loads(raw)

    except Exception as e:
        st.warning(f"Could not generate personalized verdict: {e}")
        return None