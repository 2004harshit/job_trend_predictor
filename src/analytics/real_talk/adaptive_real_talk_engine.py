from typing import Dict, List, Optional, Tuple
import logging

class AdaptiveRealTalkEngine:
    
    # ── Persona Definitions ───────────────────────────────────────────
    # Each persona: classification conditions, name, archetype description
    PERSONAS = {
        "THE_GAUNTLET": {
            "name":       "The Gauntlet",
            "emoji":      "⚔️",
            "tagline":    "High barrier, high reward. Only the prepared survive.",
            "archetypes": ["ML Engineer", "Data Scientist", "Quant Analyst", "AI Researcher"],
            "condition":  lambda m: m['barrier_depth'] >= 2 and m['competition'] >= 6.5
        },
        "THE_CROWDED_ROOM": {
            "name":       "The Crowded Room",
            "emoji":      "🏟️",
            "tagline":    "Everyone is here. Standing out is the only game.",
            "archetypes": ["Frontend Developer", "UI/UX Designer", "Manual QA", "Web Developer"],
            "condition":  lambda m: m['competition'] >= 7.5 and m['barrier_depth'] < 2
        },
        "THE_GOLD_RUSH": {
            "name":       "The Gold Rush",
            "emoji":      "🪙",
            "tagline":    "Hot now, uncertain tomorrow. First movers win.",
            "archetypes": ["GenAI Engineer", "Blockchain Dev", "Prompt Engineer", "MLOps"],
            "condition":  lambda m: m['growth'] >= 0.4 and m['stability'] < 0.45
        },
        "THE_STEADY_CLIMB": {
            "name":       "The Steady Climb",
            "emoji":      "🏔️",
            "tagline":    "Not glamorous. But it pays reliably and grows steadily.",
            "archetypes": ["Backend Java", "DevOps", "SQL Developer", "Cloud Engineer"],
            "condition":  lambda m: m['growth'] >= 0.0 and m['stability'] >= 0.50
        },
        "THE_SHRINKING_POOL": {
            "name":       "The Shrinking Pool",
            "emoji":      "🌊",
            "tagline":    "Demand declining. Strategic pivot needed before the tide goes out.",
            "archetypes": ["Manual Tester", "Flash Developer", "Mainframe Programmer"],
            "condition":  lambda m: m['growth'] < -0.1 and m['stability'] < 0.40
        },
        "THE_HIDDEN_GEM": {
            "name":       "The Hidden Gem",
            "emoji":      "💎",
            "tagline":    "Low competition, high demand. Most people don't know this exists.",
            "archetypes": ["Cybersecurity", "Embedded Systems", "Compiler Engineering"],
            "condition":  lambda m: m['competition'] < 5.0 and m['demand'] >= 6.0
        },
        "THE_PIVOT_ZONE": {
            "name":       "The Pivot Zone",
            "emoji":      "🔀",
            "tagline":    "Skills transfer well here. Switchers have an edge over freshers.",
            "archetypes": ["Product Manager (from Dev)", "DevRel", "Solutions Architect"],
            "condition":  lambda m: m.get('transferability', 0) >= 0.55 and m['barrier_depth'] < 2
        },
        "THE_AI_CROSSROADS": {
            "name":       "The AI Crossroads",
            "emoji":      "🤖",
            "tagline":    "AI is actively reshaping this role. Adapt or be replaced.",
            "archetypes": ["Data Entry", "Report Analyst", "Basic QA Tester"],
            "condition":  lambda m: m.get('ai_risk', 0) >= 0.60
        },
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def _classify_persona(self, metrics: Dict) -> Tuple[str, float]:
        """
        Evaluate all persona conditions and return best match + confidence.
        Confidence = how clearly this persona dominates over others.
        """
        scores = {}
        
        for persona_id, defn in self.PERSONAS.items():
            try:
                if defn["condition"](metrics):
                    # Score = sum of how far metrics exceed thresholds
                    scores[persona_id] = 1.0
            except (KeyError, TypeError):
                continue
        
        if not scores:
            return "THE_STEADY_CLIMB", 0.50  # Default fallback
        
        if len(scores) == 1:
            return list(scores.keys())[0], 0.85  # Clear match
        
        # Multiple personas match — use priority order
        # AI risk overrides everything (most critical)
        priority = [
            "THE_AI_CROSSROADS", "THE_SHRINKING_POOL", "THE_GAUNTLET",
            "THE_HIDDEN_GEM",    "THE_GOLD_RUSH",       "THE_CROWDED_ROOM",
            "THE_PIVOT_ZONE",    "THE_STEADY_CLIMB"
        ]
        for p in priority:
            if p in scores:
                confidence = 0.65  # Multiple matches = less certain
                return p, confidence
        
        return "THE_STEADY_CLIMB", 0.50
    
    def build_metrics_from_engines(self,
                                     career_path_report: Dict,
                                     demand_report: Dict = None,
                                     saturation_report: Dict = None,
                                     ai_risk_report: Dict = None,
                                     velocity_report: Dict = None,
                                     salary_report: Dict = None,
                                     transferability_report: Dict = None) -> Dict:
        """
        Converts raw engine outputs into normalized metrics dict.
        All values normalized to consistent scales before persona classification.

        This replaces the manual metrics dict construction by the caller.
        """
        metrics = {}

        # ── Barrier Depth (0-5 scale from PrerequisiteEngine + HiddenBlockerDetector)
        readiness = career_path_report.get("Readiness_Score", {})
        blocker   = career_path_report.get("Hidden_Blockers", {})

        blocker_count    = blocker.get("Count", 0)
        blocker_risk_raw = blocker.get("Overall_Risk", "Unknown")

        # Infer numeric risk if string label provided
        blocker_risk = {
            "No Blockers Detected": 0.0,
            "Low Barrier":          0.2,
            "Moderate Barrier":     0.4,
            "High Barrier":         0.6,
            "Very High Barrier":    0.8,
            "Extreme Barrier":      1.0,
        }.get(blocker_risk_raw, 0.3)

        # Barrier depth: combine blocker severity + interview difficulty
        interview_index = career_path_report.get(
            "Interview_Difficulty", {}
        ).get("Index", 5.0)

        metrics['barrier_depth'] = round(
            (blocker_risk * 2.0) + (interview_index / 10 * 3.0), 2
        )  # Scale 0-5

        # ── Competition (0-10 scale from SaturationRiskIndicator)
        if saturation_report:
            sat_score = saturation_report.get("saturation_score", 
                        saturation_report.get("Score", 5.0))
            metrics['competition'] = round(float(sat_score), 2)
        else:
            # Fallback: infer from readiness score components
            blocker_comp = readiness.get("components", {}).get("blocker_clearance", 70)
            metrics['competition'] = round((100 - blocker_comp) / 10, 2)

        # ── Growth (velocity signal, -1 to +1 scale)
        if velocity_report:
            direction = velocity_report.get("direction_score", 0.0)
            metrics['growth'] = round(float(direction), 3)
        elif demand_report:
            demand_score = demand_report.get("demand_score", 5.0)
            metrics['growth'] = round((demand_score - 5.0) / 5.0, 3)
        else:
            metrics['growth'] = 0.1  # Neutral default

        # ── Stability (0-1 scale from DomainStabilityEngine)
        metrics['stability'] = 0.55  # Default: moderately stable
        # (Would be populated from DomainStabilityEngine when connected)

        # ── Demand (0-10 from MarketDemandEngine)
        if demand_report:
            metrics['demand'] = round(
                float(demand_report.get("demand_score", 5.0)), 2
            )
        else:
            metrics['demand'] = 5.0

        # ── AI Risk (0-1 from AIReplacementRiskEngine)
        if ai_risk_report:
            metrics['ai_risk'] = round(
                float(ai_risk_report.get("Risk_Score", 
                      ai_risk_report.get("AI_Risk_Score", 0.3))), 3
            )
        else:
            metrics['ai_risk'] = 0.3  # Default: moderate

        # ── Transferability (0-1 from SkillTransferabilityEngine)
        if transferability_report:
            metrics['transferability'] = round(
                float(transferability_report.get(
                    "Transferability", {}
                ).get("Composite_Score", 0.4)), 3
            )
        else:
            metrics['transferability'] = 0.4

        # ── Readiness Score (0-100 from CareerPathEngine)
        metrics['readiness_score'] = readiness.get("score", 50.0)
        metrics['readiness_label'] = readiness.get("label", "Unknown")

        return metrics

    def _get_experience_modifier(self,
                                   experience_level: str) -> Dict:
        """
        Same domain, same persona, but message tone and advice depth
        differ completely between fresher and 3-year developer.
        """
        LEVELS = {
            "fresher": {
                "label":      "Fresher / Student",
                "prefix":     "As someone just starting out",
                "urgency":    "high",
                "focus":      "entry barriers, learning path, first job strategy",
                "tone":       "encouraging but honest",
            },
            "junior": {
                "label":      "Junior (0-2 years)",
                "prefix":     "As a junior professional",
                "urgency":    "medium",
                "focus":      "skill gaps, project quality, interview prep",
                "tone":       "direct and strategic",
            },
            "intermediate": {
                "label":      "Intermediate (2-5 years)",
                "prefix":     "At your experience level",
                "urgency":    "low",
                "focus":      "specialization, salary negotiation, positioning",
                "tone":       "peer-level, strategic",
            },
            "senior": {
                "label":      "Senior (5+ years)",
                "prefix":     "As an experienced professional",
                "urgency":    "very_low",
                "focus":      "leadership, architecture, market positioning",
                "tone":       "strategic and forward-looking",
            },
        }

        return LEVELS.get(experience_level.lower(), LEVELS["junior"])


    def _build_persona_content(self,
                                 persona_id: str,
                                 domain: str,
                                 metrics: Dict,
                                 exp_modifier: Dict,
                                 career_report: Dict) -> Dict:
        """
        Builds persona content with actual metric values injected.
        No more generic static strings.
        """
        readiness   = metrics.get("readiness_score", 50)
        competition = metrics.get("competition", 5.0)
        barrier     = metrics.get("barrier_depth", 2.0)
        ai_risk     = metrics.get("ai_risk", 0.3)
        growth      = metrics.get("growth", 0.1)
        months      = career_report.get("Learning_Plan", {}).get("months", "?")
        overlap_pct = round(
            career_report.get("Skill_Overlap", {})
            .get("weighted_coverage", 0.5) * 100
        )
        exp_prefix  = exp_modifier["prefix"]
        top_blockers = career_report.get("Hidden_Blockers", {}).get("Top_Blockers", [])
        blocker_msg  = (
            top_blockers[0].get("message", "") if top_blockers else ""
        )

        CONTENT = {
            "THE_GAUNTLET": {
                "harsh_truth": (
                    f"{exp_prefix}, {domain} is an interview gauntlet "
                    f"(difficulty: {metrics.get('interview_difficulty', barrier*2):.1f}/10). "
                    f"Interviewers test theory, not just syntax — "
                    f"if you can't derive the math behind the library, you're out. "
                    f"Your current skill overlap is {overlap_pct}% — "
                    f"{'strong foundation' if overlap_pct > 60 else 'significant gap to close'}."
                ),
                "silver_lining": (
                    f"Those who clear the gauntlet earn premium salaries and face far less competition. "
                    f"{domain} has {competition:.1f}/10 competition — hard to get in, but rare to be replaced once in."
                ),
                "traps": [
                    "Memorizing ML APIs without understanding the statistics underneath",
                    "Spending 6 months on LeetCode easy problems — gauntlet roles need medium-hard",
                    "Building Jupyter notebook projects with no deployment — looks like coursework, not engineering",
                ],
                "patterns": [
                    "Candidates with published research or math-heavy GitHub repos bypass ATS filters",
                    f"Target {domain} roles at startups first — lower bar than FAANG, same skill building",
                    "One strong open-source contribution to a major library > 10 tutorial projects",
                ],
            },
            "THE_CROWDED_ROOM": {
                "harsh_truth": (
                    f"Competition score: {competition:.1f}/10. "
                    f"{exp_prefix}, your resume has approximately 6 seconds with a recruiter. "
                    f"{'With ' + str(overlap_pct) + '% skill overlap, you qualify — but so do 1,000+ others.' if overlap_pct > 50 else 'At ' + str(overlap_pct) + '% skill overlap, you are not yet in the qualified pool.'}"
                    f"{(' Active blocker: ' + blocker_msg) if blocker_msg else ''}"
                ),
                "silver_lining": (
                    f"High volume means more hiring. If you differentiate on niche skills or referrals, "
                    f"landing roles is achievable within {months} months of focused prep."
                ),
                "traps": [
                    f"Building the same projects everyone else builds (Netflix clone, todo app, weather app)",
                    "Applying to 200 jobs with the same generic resume — quantity over quality strategy fails here",
                    "Ignoring LinkedIn — in a crowded room, visibility is the first filter",
                ],
                "patterns": [
                    "Referrals bypass 80% of the resume screening — build LinkedIn connections strategically",
                    f"Niche specializations (WebGL, Accessibility, Performance) command 30-50% salary premium in {domain}",
                    "Building in public (open PRs, blog posts, Twitter/X threads) creates inbound opportunities",
                ],
            },
            "THE_GOLD_RUSH": {
                "harsh_truth": (
                    f"{domain} is growing fast (growth signal: {growth:+.2f}) but the tech stack changes every 6-12 months. "
                    f"{exp_prefix}, what you learn today has a shorter shelf life here than any other domain. "
                    f"{'At ' + str(overlap_pct) + '% skill overlap, you are positioned to enter, but foundational skills will outlast any specific tool.' if overlap_pct > 40 else 'Your current overlap (' + str(overlap_pct) + '%) needs significant investment — move fast or the window narrows.'}"
                ),
                "silver_lining": (
                    f"Early movers in {domain} can 3-5x their salary in 18-24 months. "
                    f"Demand is outpacing supply right now — this is rare and time-limited."
                ),
                "traps": [
                    f"Chasing {domain} salaries without solid programming fundamentals underneath",
                    "Learning tool A when the market just moved to tool B — follow job postings weekly",
                    "No foundational engineering skills — when the gold rush ends, generalists get cut first",
                ],
                "patterns": [
                    f"Build and publish open-source tools for the emerging {domain} ecosystem — first mover advantage",
                    "Get certified early — when a field matures, certifications become table stakes",
                    "Pair emerging skills with a solid foundation (Python, system design) for durability",
                ],
            },
            "THE_STEADY_CLIMB": {
                "harsh_truth": (
                    f"{domain} is reliable (stability: {metrics.get('stability', 0.6):.2f}/1.0) but not glamorous. "
                    f"{exp_prefix}, the risk is complacency — once hired, learning often stops. "
                    f"In 3 years, the developer who kept upskilling is earning 2x the one who didn't. "
                    f"Your overlap is {overlap_pct}% — {'solid base to build from' if overlap_pct > 55 else 'needs structured upskilling plan'}."
                ),
                "silver_lining": (
                    f"Steady demand means job security. Competition is {competition:.1f}/10 — more manageable than trendy domains. "
                    f"This is the domain where consistent effort predictably converts to seniority and salary."
                ),
                "traps": [
                    "Stopping skill development after landing the first job",
                    "Ignoring cloud and DevOps skills — they've become baseline expectations in most backend roles",
                    "Staying at one company too long without switching for a market-rate salary correction",
                ],
                "patterns": [
                    f"Cloud certifications (AWS/Azure/GCP) add 20-40% to your {domain} market value",
                    "Job-switching every 18-24 months is the fastest salary growth mechanism in this domain",
                    "System design skills are underrepresented — mastering them fast-tracks to senior level",
                ],
            },
            "THE_SHRINKING_POOL": {
                "harsh_truth": (
                    f"Honest signal: {domain} demand is declining (growth: {growth:+.2f}). "
                    f"{exp_prefix}, the risk of investing heavily here is real. "
                    f"Roles are contracting and AI is automating core tasks (AI risk: {ai_risk:.0%}). "
                    f"This is a data-based warning, not a guarantee."
                ),
                "silver_lining": (
                    f"Existing practitioners with deep expertise still command strong salaries. "
                    f"If you're already here, transition to adjacent growing roles rather than abandoning skills entirely."
                ),
                "traps": [
                    f"Doubling down on {domain} skills without building adjacent transferable skills",
                    "Ignoring AI tooling — if you can't use AI in this role, you become the one AI replaces",
                    "Waiting too long to pivot — each year makes the transition harder",
                ],
                "patterns": [
                    "Map your skills to adjacent growing domains (use Skill Transferability Engine results)",
                    "Automation expertise + domain knowledge creates a unique hybrid profile that's hard to replace",
                    "Target companies modernizing legacy systems — they still need domain expertise during transition",
                ],
            },
            "THE_HIDDEN_GEM": {
                "harsh_truth": (
                    f"{domain} has low competition ({competition:.1f}/10) but high barrier ({barrier:.1f}/5). "
                    f"{exp_prefix}, most people overlook this domain because the entry path is harder to find. "
                    f"That's exactly why those who get in face far less competition later."
                ),
                "silver_lining": (
                    f"Once inside, {domain} professionals are hard to replace. "
                    f"Salaries are above market average with significantly less competition than mainstream roles."
                ),
                "traps": [
                    "Underestimating the barrier — low competition doesn't mean easy entry",
                    "Expecting the same volume of online learning resources as mainstream domains",
                    "Skipping the fundamentals because the domain seems niche — depth matters more here",
                ],
                "patterns": [
                    "Certifications carry more weight here than in mainstream domains — pursue them",
                    "Community involvement (conferences, forums) is a faster networking path than LinkedIn",
                    f"Building projects that solve real {domain} problems signals expertise more than tutorials",
                ],
            },
            "THE_PIVOT_ZONE": {
                "harsh_truth": (
                    f"{exp_prefix}, {domain} rewards career switchers over pure freshers. "
                    f"Your transferability score suggests {overlap_pct}% of your existing skills carry over. "
                    f"{'This is a strong pivot position — move now.' if overlap_pct > 55 else 'The transfer is possible but requires deliberate bridge-skill investment.'}"
                ),
                "silver_lining": (
                    f"Switchers bring domain context that freshers can't replicate. "
                    f"Combined background is often valued at a premium in {domain} roles."
                ),
                "traps": [
                    "Trying to compete as a fresher instead of leveraging your prior domain context",
                    "Undervaluing transferable skills in interviews — your prior experience IS your differentiation",
                    "Not positioning your resume to show the pivot story clearly",
                ],
                "patterns": [
                    "Lead with your unique cross-domain experience in every interview",
                    "Identify and fill only the critical skill gaps — don't restart from zero",
                    f"Target companies in your previous industry that are adopting {domain} — double advantage",
                ],
            },
            "THE_AI_CROSSROADS": {
                "harsh_truth": (
                    f"AI risk for {domain}: {ai_risk:.0%}. "
                    f"{exp_prefix}, core tasks in this role are being automated right now. "
                    f"This is not a future concern — it is a present-tense market reality. "
                    f"The question is not 'will AI affect this?' but 'what do you do about it today?'"
                ),
                "silver_lining": (
                    f"Professionals who learn to direct AI tools in {domain} become 10x more productive. "
                    f"The role is transforming, not disappearing — but only for those who adapt."
                ),
                "traps": [
                    "Ignoring AI tooling and hoping the role stays the same",
                    "Learning only the automation-vulnerable parts of the role",
                    "Competing on execution speed — AI wins that race, humans win on judgment and strategy",
                ],
                "patterns": [
                    f"Learn to use AI tools as force multipliers in {domain} — become the person directing AI",
                    "Shift focus to tasks requiring judgment, stakeholder communication, and creative problem-solving",
                    "Upskill into adjacent roles that AI is creating demand for (AI trainer, prompt engineer, AI auditor)",
                ],
            },
        }

        return CONTENT.get(persona_id, CONTENT["THE_STEADY_CLIMB"])

    def _generate_urgency_signal(self,
                                   metrics: Dict,
                                   career_report: Dict,
                                   persona_id: str) -> dict:
        """
        Translates all signals into a single urgency recommendation.
        Answers: "Should I apply now, upskill first, or reconsider entirely?"
        """
        readiness = metrics.get("readiness_score", 50)
        months    = career_report.get("Learning_Plan", {}).get("months", 6)
        blockers  = career_report.get("Hidden_Blockers", {}).get("Count", 0)
        growth    = metrics.get("growth", 0.1)

        # Critical blocker override
        if blockers > 0:
            top_blocker = career_report.get("Hidden_Blockers", {}).get("Top_Blockers", [{}])[0]
            sev = top_blocker.get("severity", 0)
            if sev > 0.70:
                return {
                    "signal":  "🚨 Resolve Blocker First",
                    "color":   "red",
                    "message": (
                        f"A critical blocker ({top_blocker.get('blocker_id', 'unknown')}) "
                        f"will prevent interviews regardless of skill level. "
                        f"Action: {top_blocker.get('resolution', 'Address the blocker identified above.')}"
                    )
                }

        # Shrinking domain warning
        if persona_id == "THE_SHRINKING_POOL":
            return {
                "signal":  "⚠️ Reconsider Direction",
                "color":   "orange",
                "message": "Domain demand is declining. Evaluate adjacent growing domains before investing further."
            }

        # Apply now
        if readiness >= 75 and blockers == 0:
            return {
                "signal":  "✅ Apply Immediately",
                "color":   "green",
                "message": (
                    f"Readiness score: {readiness:.0f}/100. "
                    f"You are qualified to apply now. "
                    f"Focus energy on interview prep and portfolio polish, not more learning."
                )
            }

        # Close gap then apply
        if readiness >= 50 and months <= 4:
            return {
                "signal":  "🟡 Apply in {months} Months",
                "color":   "yellow",
                "message": (
                    f"Readiness score: {readiness:.0f}/100. "
                    f"~{months} months of focused upskilling bridges your current gap. "
                    f"Start applying while you learn — don't wait until 100% ready."
                )
            }

        # Significant prep needed
        if readiness >= 30:
            return {
                "signal":  "🟠 Structured Preparation Needed",
                "color":   "orange",
                "message": (
                    f"Readiness score: {readiness:.0f}/100. "
                    f"~{months} months at 10hrs/week to job-ready. "
                    f"Follow the priority actions in the learning plan — don't skip fundamentals."
                )
            }

        # Starting from scratch
        return {
            "signal":  "🔴 Build Foundation First",
            "color":   "red",
            "message": (
                f"Readiness score: {readiness:.0f}/100. "
                f"This domain requires a strong foundation you're still building. "
                f"Start with prerequisite skills before targeting this role directly."
            )
        }

    def generate_real_talk(self,
                            domain: str,
                            career_path_report: Dict,
                            experience_level: str = "junior",
                            demand_report: Dict = None,
                            saturation_report: Dict = None,
                            ai_risk_report: Dict = None,
                            velocity_report: Dict = None,
                            salary_report: Dict = None,
                            transferability_report: Dict = None) -> dict:
        """
        Main entry point. Full personalized Real Talk report.

        Parameters:
            domain:              Target job domain
            career_path_report:  Output from CareerPathEngine.calculate_learning_readiness()
            experience_level:    "fresher" | "junior" | "intermediate" | "senior"
            All other params:    Optional outputs from respective engines
        """
        # 1. Build normalized metrics from engine outputs
        metrics = self.build_metrics_from_engines(
            career_path_report  = career_path_report,
            demand_report       = demand_report,
            saturation_report   = saturation_report,
            ai_risk_report      = ai_risk_report,
            velocity_report     = velocity_report,
            salary_report       = salary_report,
            transferability_report = transferability_report
        )

        # 2. Classify persona
        persona_id, confidence = self._classify_persona(metrics)
        persona_defn           = self.PERSONAS[persona_id]

        # 3. Experience modifier
        exp_modifier = self._get_experience_modifier(experience_level)

        # 4. Build data-injected content
        content = self._build_persona_content(
            persona_id, domain, metrics, exp_modifier, career_path_report
        )

        # 5. Urgency signal
        urgency = self._generate_urgency_signal(
            metrics, career_path_report, persona_id
        )

        # 6. Evolution preview
        evolution = career_path_report.get("Evolution_Preview")
        evolution_note = None
        if evolution and evolution.get("first_step"):
            evolution_note = (
                f"📈 Natural next step from {domain}: "
                f"**{evolution['first_step']}** "
                f"(~{evolution.get('years_to_senior', '?')} years to senior level)"
            )

        # 7. Salary context
        salary_context = None
        sal = career_path_report.get("Salary_Benchmark")
        if sal:
            salary_context = (
                f"💰 Market median: ₹{sal['median_lpa']} LPA "
                f"(P25: ₹{sal['p25_lpa']} | P75: ₹{sal['p75_lpa']} LPA)"
            )

        return {
            "domain":             domain,
            "experience_level":   exp_modifier["label"],

            "persona": {
                "id":          persona_id,
                "name":        persona_defn["name"],
                "emoji":       persona_defn["emoji"],
                "tagline":     persona_defn["tagline"],
                "confidence":  f"{confidence:.0%}",
                "archetypes":  persona_defn["archetypes"]
            },

            "readiness_snapshot": {
                "score":          metrics.get("readiness_score"),
                "label":          metrics.get("readiness_label"),
                "skill_overlap":  f"{round(career_path_report.get('Skill_Overlap', {}).get('weighted_coverage', 0) * 100)}%",
                "months_to_ready": career_path_report.get("Learning_Plan", {}).get("months"),
                "active_blockers": career_path_report.get("Hidden_Blockers", {}).get("Count", 0),
            },

            "market_pulse": {
                "competition":  f"{metrics.get('competition', 0):.1f}/10",
                "barrier_depth": f"{metrics.get('barrier_depth', 0):.1f}/5",
                "ai_risk":      f"{metrics.get('ai_risk', 0):.0%}",
                "growth_signal": (
                    "📈 Growing" if metrics.get('growth', 0) > 0.1 else
                    "📉 Declining" if metrics.get('growth', 0) < -0.1 else
                    "➡️  Stable"
                ),
            },

            "real_talk": {
                "harsh_truth":     content["harsh_truth"],
                "silver_lining":   content["silver_lining"],
                "beginner_traps":  content["traps"],
                "success_patterns": content["patterns"],
            },

            "urgency":         urgency,
            "evolution_note":  evolution_note,
            "salary_context":  salary_context,

            "priority_action": career_path_report.get("Priority_Action", "See learning plan above."),
        }


if __name__ == "__main__":
    # Example usage of AdaptiveRealTalkEngine

    # Create engine instance
    engine = AdaptiveRealTalkEngine()

    # Mock career path report (simplified for demonstration)
    mock_career_path_report = {
        "Readiness_Score": {
            "score": 65.0,
            "label": "Needs Development",
            "components": {
                "blocker_clearance": 70.0
            }
        },
        "Interview_Difficulty": {
            "Index": 7.5
        },
        "Hidden_Blockers": {
            "Count": 1,
            "Overall_Risk": "Moderate Barrier",
            "Top_Blockers": [
                {
                    "blocker_id": "skill_gap",
                    "severity": 0.6,
                    "message": "Missing advanced Python libraries experience",
                    "resolution": "Complete 2-3 projects using pandas, scikit-learn, and TensorFlow"
                }
            ]
        },
        "Learning_Plan": {
            "months": 4
        },
        "Skill_Overlap": {
            "weighted_coverage": 0.55
        },
        "Evolution_Preview": {
            "first_step": "Senior Data Scientist",
            "years_to_senior": 3
        },
        "Salary_Benchmark": {
            "median_lpa": 12.0,
            "p25_lpa": 8.0,
            "p75_lpa": 18.0
        },
        "Priority_Action": "Focus on building a portfolio of ML projects and gaining experience with cloud platforms"
    }

    # Mock other reports (optional)
    mock_saturation_report = {
        "saturation_score": 6.8
    }

    mock_velocity_report = {
        "direction_score": 0.3
    }

    mock_ai_risk_report = {
        "Risk_Score": 0.25
    }

    # Generate Real Talk report
    result = engine.generate_real_talk(
        domain="Data Scientist",
        career_path_report=mock_career_path_report,
        experience_level="junior",
        saturation_report=mock_saturation_report,
        velocity_report=mock_velocity_report,
        ai_risk_report=mock_ai_risk_report
    )

    # Print the results in a readable format
    print("Adaptive Real Talk Engine Report")
    print("=" * 50)
    print(f"Domain: {result['domain']}")
    print(f"Experience Level: {result['experience_level']}")
    print()

    persona = result['persona']
    print(f"Persona: {persona['emoji']} {persona['name']}")
    print(f"Tagline: {persona['tagline']}")
    print(f"Confidence: {persona['confidence']}")
    print(f"Archetypes: {', '.join(persona['archetypes'])}")
    print()

    readiness = result['readiness_snapshot']
    print("Readiness Snapshot:")
    print(f"  Score: {readiness['score']}/100 ({readiness['label']})")
    print(f"  Skill Overlap: {readiness['skill_overlap']}")
    print(f"  Months to Ready: {readiness['months_to_ready']}")
    print(f"  Active Blockers: {readiness['active_blockers']}")
    print()

    pulse = result['market_pulse']
    print("Market Pulse:")
    print(f"  Competition: {pulse['competition']}")
    print(f"  Barrier Depth: {pulse['barrier_depth']}")
    print(f"  AI Risk: {pulse['ai_risk']}")
    print(f"  Growth Signal: {pulse['growth_signal']}")
    print()

    talk = result['real_talk']
    print("Real Talk:")
    print(f"  Harsh Truth: {talk['harsh_truth']}")
    print(f"  Silver Lining: {talk['silver_lining']}")
    print("  Beginner Traps:")
    for i, trap in enumerate(talk['beginner_traps'], 1):
        print(f"    {i}. {trap}")
    print("  Success Patterns:")
    for i, pattern in enumerate(talk['success_patterns'], 1):
        print(f"    {i}. {pattern}")
    print()

    urgency = result['urgency']
    print(f"Urgency Signal: {urgency['signal']} ({urgency['color']})")
    print(f"  Message: {urgency['message']}")
    print()

    if result['evolution_note']:
        print(f"Evolution Note: {result['evolution_note']}")
    if result['salary_context']:
        print(f"Salary Context: {result['salary_context']}")
    print()

    print(f"Priority Action: {result['priority_action']}")
    