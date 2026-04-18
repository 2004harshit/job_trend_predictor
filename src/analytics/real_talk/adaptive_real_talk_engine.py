# adaptive_real_talk_engine.py  (Improved Rule-based Version)

from typing import Dict, List, Optional, Tuple
import logging

class AdaptiveRealTalkEngine:
    
    PERSONAS = {
        "THE_GAUNTLET": {
            "name": "The Gauntlet",
            "emoji": "⚔️",
            "tagline": "High barrier, high reward. Only the prepared survive.",
            "archetypes": ["Data Scientist", "ML Engineer", "AI Engineer"],
            "condition": lambda m: m.get('barrier_depth', 0) >= 2.5 and m.get('competition', 0) >= 6.5
        },
        "THE_CROWDED_ROOM": {
            "name": "The Crowded Room",
            "emoji": "🏟️",
            "tagline": "Everyone is here. Standing out is the only game.",
            "archetypes": ["Software Engineer", "Full Stack Developer", "Frontend Developer"],
            "condition": lambda m: m.get('competition', 0) >= 7.0 and m.get('barrier_depth', 0) < 2.5
        },
        "THE_GOLD_RUSH": {
            "name": "The Gold Rush",
            "emoji": "🪙",
            "tagline": "Hot now, uncertain tomorrow. First movers win.",
            "archetypes": ["GenAI Engineer", "MLOps", "Prompt Engineer"],
            "condition": lambda m: m.get('growth', 0) >= 0.35
        },
        "THE_STEADY_CLIMB": {
            "name": "The Steady Climb",
            "emoji": "🏔️",
            "tagline": "Reliable but not glamorous. Consistent effort wins.",
            "archetypes": ["Software Engineer", "Backend Developer", "DevOps"],
            "condition": lambda m: m.get('growth', 0) >= 0.0 and m.get('stability', 0) >= 0.5
        },
        "THE_SHRINKING_POOL": {
            "name": "The Shrinking Pool",
            "emoji": "🌊",
            "tagline": "Demand is declining. Strategic pivot needed.",
            "archetypes": ["Manual QA", "Legacy Support"],
            "condition": lambda m: m.get('growth', 0) < -0.1
        },
        "THE_HIDDEN_GEM": {
            "name": "The Hidden Gem",
            "emoji": "💎",
            "tagline": "Low competition, high demand. Most people miss it.",
            "archetypes": ["Cybersecurity", "Embedded Systems"],
            "condition": lambda m: m.get('competition', 0) < 5.0 and m.get('demand', 0) >= 6.0
        },
        "THE_PIVOT_ZONE": {
            "name": "The Pivot Zone",
            "emoji": "🔀",
            "tagline": "Good for career switchers.",
            "archetypes": ["Product Manager (from Tech)", "Solutions Architect"],
            "condition": lambda m: m.get('transferability', 0) >= 0.55
        },
        "THE_AI_CROSSROADS": {
            "name": "The AI Crossroads",
            "emoji": "🤖",
            "tagline": "AI is reshaping this role. Adapt or be replaced.",
            "archetypes": ["Basic QA", "Data Entry", "Report Analyst"],
            "condition": lambda m: m.get('ai_risk', 0) >= 0.60
        },
    }

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def build_metrics_from_engines(self, career_path_report: Dict, **kwargs) -> Dict:
        """Improved metric building with better defaults and skill awareness"""
        metrics = {}

        readiness = career_path_report.get("Readiness_Score", {})
        blockers = career_path_report.get("Hidden_Blockers", {})
        skill_overlap = career_path_report.get("Skill_Overlap", {})

        # Barrier Depth (0-5)
        blocker_risk = {
            "No Blockers Detected": 0.0, "Low Barrier": 0.2, "Moderate Barrier": 0.4,
            "High Barrier": 0.6, "Very High Barrier": 0.8, "Extreme Barrier": 1.0
        }.get(blockers.get("Overall_Risk", "Moderate Barrier"), 0.4)

        interview_idx = career_path_report.get("Interview_Difficulty", {}).get("Index", 6.0)

        metrics['barrier_depth'] = round(blocker_risk * 2.0 + (interview_idx / 10) * 3.0, 2)
        metrics['competition'] = round(float(kwargs.get('saturation_report', {}).get('saturation_score', 5.5)), 2)
        metrics['growth'] = round(float(kwargs.get('velocity_report', {}).get('direction_score', 0.1)), 2)
        metrics['demand'] = round(float(kwargs.get('demand_report', {}).get('demand_score', 5.0)), 2)
        metrics['ai_risk'] = round(float(kwargs.get('ai_risk_report', {}).get('AI_Risk_Score', 0.3)), 2)
        metrics['transferability'] = round(float(kwargs.get('transferability_report', {}).get('Transferability', {}).get('Composite_Score', 0.45)), 2)
        metrics['readiness_score'] = readiness.get("score", 50)
        metrics['skill_overlap_pct'] = round(skill_overlap.get("weighted_coverage", 0.5) * 100)

        return metrics

    def _classify_persona(self, metrics: Dict) -> Tuple[str, float]:
        """Improved classification with better priority and confidence"""
        matches = []
        for pid, defn in self.PERSONAS.items():
            try:
                if defn["condition"](metrics):
                    matches.append(pid)
            except:
                continue

        if not matches:
            return "THE_STEADY_CLIMB", 0.55

        # Priority order (most critical first)
        priority = ["THE_AI_CROSSROADS", "THE_SHRINKING_POOL", "THE_GAUNTLET",
                    "THE_GOLD_RUSH", "THE_CROWDED_ROOM", "THE_HIDDEN_GEM",
                    "THE_PIVOT_ZONE", "THE_STEADY_CLIMB"]

        for p in priority:
            if p in matches:
                confidence = 0.85 if len(matches) == 1 else 0.65
                return p, confidence

        return "THE_STEADY_CLIMB", 0.55

    def _get_experience_modifier(self, experience_level: str) -> Dict:
        # Same as before (no major change needed)
        levels = {
            "fresher": {"label": "Fresher", "prefix": "As a complete fresher", "tone": "encouraging but honest"},
            "junior":  {"label": "Junior (0-2 years)", "prefix": "As a junior developer", "tone": "direct"},
            "intermediate": {"label": "Intermediate", "prefix": "At your level", "tone": "strategic"},
            "senior": {"label": "Senior", "prefix": "As an experienced professional", "tone": "forward-looking"}
        }
        return levels.get(experience_level.lower(), levels["fresher"])

    def _build_persona_content(self, persona_id: str, domain: str, metrics: Dict, 
                               exp_modifier: Dict, career_report: Dict, user_skills: List[str]) -> Dict:
        """MAJOR IMPROVEMENT: More domain + skill aware content"""
        overlap = metrics.get('skill_overlap_pct', 45)
        months = career_report.get("Learning_Plan", {}).get("months", 6)
        competition = metrics.get('competition', 5.5)
        barrier = metrics.get('barrier_depth', 2.0)
        prefix = exp_modifier["prefix"]

        # Skill-aware message
        skill_msg = ""
        if user_skills:
            skill_str = ", ".join(user_skills[:3])
            skill_msg = f"You already know {skill_str} — "

        CONTENT_TEMPLATES = {
            "THE_GAUNTLET": {
                "harsh_truth": f"{prefix}, {domain} is a tough interview gauntlet (difficulty ~{barrier:.1f}/5). "
                              f"{skill_msg}Companies test deep concepts and math. Your skill overlap is only {overlap}% — "
                              f"you have a noticeable gap to close before you can compete seriously.",
                "silver_lining": f"Those who clear this gauntlet get premium salaries and face much less day-to-day competition. "
                                f"Once inside, the role is stable and respected.",
                "traps": [
                    "Relying only on video tutorials without understanding the math behind the algorithms",
                    "Building only basic notebook projects without deployment or scaling",
                    "Ignoring system design — many interviews fail at this round"
                ],
                "patterns": [
                    "Build 2–3 end-to-end projects with proper deployment and documentation",
                    "Focus on understanding statistics and linear algebra — not just calling libraries",
                    "Contribute to open-source ML repositories to show real understanding"
                ]
            },
            "THE_CROWDED_ROOM": {
                "harsh_truth": f"{prefix}, {domain} has high competition ({competition:.1f}/10). "
                              f"{skill_msg}Thousands of freshers are applying with similar profiles. "
                              f"Your {overlap}% skill overlap means you are in the pool — but not standing out yet.",
                "silver_lining": f"High volume of openings exists. If you differentiate through strong projects and communication, "
                                f"you can land a role in {months} months.",
                "traps": [
                    "Applying with generic resume and same projects as everyone else",
                    "Focusing only on LeetCode without building real applications",
                    "Ignoring LinkedIn and networking — referrals matter a lot here"
                ],
                "patterns": [
                    "Build 3–4 unique, deployed projects and write detailed READMEs",
                    "Share your learning journey publicly on LinkedIn and Twitter",
                    "Target startups first — they have lower competition than big companies"
                ]
            },
            "THE_STEADY_CLIMB": {
                "harsh_truth": f"{prefix}, {domain} is a reliable choice with moderate competition. "
                              f"{skill_msg}The risk here is complacency after getting the first job.",
                "silver_lining": f"Consistent effort and job switching every 18–24 months can give you very good salary growth.",
                "traps": [
                    "Stopping learning after landing the first job",
                    "Staying at one company for too long without salary correction",
                    "Ignoring cloud and DevOps skills which have become baseline"
                ],
                "patterns": [
                    "Learn cloud fundamentals (AWS/Azure) — they add big value",
                    "Job switch every 1.5–2 years for market rate correction",
                    "Build strong system design knowledge to reach senior level faster"
                ]
            }
            # Add more personas similarly if needed
        }

        default = CONTENT_TEMPLATES.get("THE_STEADY_CLIMB")
        return CONTENT_TEMPLATES.get(persona_id, default)

    def generate_real_talk(self,
                           domain: str,
                           career_path_report: Dict,
                           experience_level: str = "fresher",
                           user_skills: List[str] = None,
                           demand_report: Dict = None,
                           saturation_report: Dict = None,
                           ai_risk_report: Dict = None,
                           velocity_report: Dict = None,
                           transferability_report: Dict = None) -> dict:

        user_skills = user_skills or []

        metrics = self.build_metrics_from_engines(
            career_path_report=career_path_report,
            demand_report=demand_report,
            saturation_report=saturation_report,
            ai_risk_report=ai_risk_report,
            velocity_report=velocity_report,
            transferability_report=transferability_report
        )

        persona_id, confidence = self._classify_persona(metrics)
        exp_modifier = self._get_experience_modifier(experience_level)

        content = self._build_persona_content(
            persona_id, domain, metrics, exp_modifier, career_path_report, user_skills
        )

        # Urgency (can keep existing or improve later)
        urgency = {
            "signal": "🟡 Structured Preparation Needed",
            "color": "yellow",
            "message": f"Readiness is moderate. Focus on the priority actions in the learning plan. Expected time: {career_path_report.get('Learning_Plan', {}).get('months', 6)} months."
        }

        return {
            "domain": domain,
            "experience_level": exp_modifier["label"],
            "persona": {
                "id": persona_id,
                "name": self.PERSONAS[persona_id]["name"],
                "emoji": self.PERSONAS[persona_id]["emoji"],
                "tagline": self.PERSONAS[persona_id]["tagline"],
                "confidence": f"{confidence:.0%}"
            },
            "readiness_snapshot": {
                "score": metrics.get("readiness_score"),
                "skill_overlap": f"{metrics.get('skill_overlap_pct')}%",
                "months_to_ready": career_path_report.get("Learning_Plan", {}).get("months"),
            },
            "market_pulse": {
                "competition": f"{metrics.get('competition', 5.5):.1f}/10",
                "barrier_depth": f"{metrics.get('barrier_depth', 2.0):.1f}/5",
                "ai_risk": f"{metrics.get('ai_risk', 0.3):.0%}"
            },
            "real_talk": {
                "harsh_truth": content["harsh_truth"],
                "silver_lining": content["silver_lining"],
                "beginner_traps": content["traps"],
                "success_patterns": content["patterns"]
            },
            "urgency": urgency,
            "priority_action": career_path_report.get("Priority_Action", "Follow the structured learning plan.")
        }