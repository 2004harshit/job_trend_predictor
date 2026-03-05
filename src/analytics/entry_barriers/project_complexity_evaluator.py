import re
import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

class ProjectComplexityEvaluator:
    
    MIN_SAMPLES = 8
    
    # ── Project Complexity Keyword Banks ─────────────────────────────
    COMPLEXITY_KEYWORDS = {
        
        "features": {
            # Each tier represents increasing project feature complexity
            "basic": [
                'crud', 'todo', 'login', 'registration', 'form',
                'basic search', 'single page', 'simple dashboard',
                'weather app', 'calculator', 'to-do list'
            ],
            "intermediate": [
                'authentication', 'authorization', 'oauth', 'payment',
                'real-time', 'search filter', 'recommendation',
                'multi-user', 'role-based', 'notification system',
                'file upload', 'image processing', 'email integration'
            ],
            "advanced": [
                'machine learning model', 'nlp pipeline', 'computer vision',
                'streaming data', 'event-driven', 'distributed',
                'multi-tenant', 'workflow engine', 'rule engine',
                'predictive model', 'personalization engine', 'ab testing'
            ]
        },
        
        "integration": {
            "basic": [
                'rest api', 'json', 'csv', 'basic database', 'sqlite',
                'simple api call', 'http request', 'fetch api'
            ],
            "intermediate": [
                'third party api', 'payment gateway', 'aws s3', 'firebase',
                'redis cache', 'message queue', 'webhook', 'oauth provider',
                'stripe', 'twilio', 'sendgrid', 'elasticsearch'
            ],
            "advanced": [
                'microservices', 'kafka', 'rabbitmq', 'graphql',
                'grpc', 'websocket', 'event sourcing', 'cqrs',
                'api gateway', 'service mesh', 'multi-cloud'
            ]
        },
        
        "deployment": {
            "none": ['localhost', 'local only', 'not deployed', 'demo only'],
            "basic": [
                'heroku', 'netlify', 'vercel', 'github pages',
                'render', 'railway', 'fly.io', 'replit'
            ],
            "intermediate": [
                'aws ec2', 'azure vm', 'gcp compute', 'digital ocean',
                'docker', 'docker compose', 'nginx', 'ssl certificate',
                'domain name', 'cloud hosting'
            ],
            "advanced": [
                'kubernetes', 'k8s', 'ci/cd', 'github actions',
                'jenkins', 'terraform', 'helm', 'auto scaling',
                'load balancer', 'cdn', 'monitoring', 'logging pipeline',
                'blue green deployment', 'canary release'
            ]
        },
        
        "data_complexity": {
            "basic": [
                'csv file', 'excel file', 'single table', 'small dataset',
                'static data', 'hardcoded data'
            ],
            "intermediate": [
                'relational database', 'multiple tables', 'joins',
                'api data source', 'real-time data', 'data pipeline',
                'data cleaning', 'feature engineering', 'multiple sources'
            ],
            "advanced": [
                'big data', 'data warehouse', 'spark', 'hadoop',
                'streaming pipeline', 'etl pipeline', 'data lake',
                'multiple data sources', 'petabyte', 'time series'
            ]
        }
    }
    
    # ── Domain-Specific Project Archetypes ───────────────────────────
    DOMAIN_ARCHETYPES = {
        "data scientist": {
            "simple":   "Single dataset EDA notebook with matplotlib visualizations",
            "medium":   "End-to-end ML pipeline: data collection → feature engineering → model → evaluation dashboard",
            "advanced": "Production ML system: real-time inference API + model monitoring + retraining pipeline + A/B testing"
        },
        "ml engineer": {
            "simple":   "Trained model in Jupyter notebook with sklearn",
            "medium":   "Dockerized model serving API with FastAPI + basic monitoring",
            "advanced": "MLOps pipeline: automated training, versioning (MLflow), serving (Seldon/BentoML), drift detection"
        },
        "web developer": {
            "simple":   "Static website or basic CRUD app with no auth",
            "medium":   "Full-stack app with auth, database, deployed to cloud with basic CI/CD",
            "advanced": "Scalable SaaS with microservices, real-time features, payment, multi-tenancy, monitoring"
        },
        "backend developer": {
            "simple":   "REST API with basic CRUD and SQLite",
            "medium":   "Production API with auth, PostgreSQL, Redis cache, deployed with Docker",
            "advanced": "Distributed system with event-driven architecture, message queues, API gateway, auto-scaling"
        },
        "frontend developer": {
            "simple":   "Static HTML/CSS site or basic React app",
            "medium":   "React SPA with state management, API integration, responsive design, deployed",
            "advanced": "Complex React app with server-side rendering, performance optimization, design system, testing suite"
        },
        "devops engineer": {
            "simple":   "Basic bash scripts and manual deployment",
            "medium":   "Docker + CI/CD pipeline with GitHub Actions, infrastructure on one cloud provider",
            "advanced": "Full IaC with Terraform, multi-cloud, Kubernetes orchestration, monitoring stack (Prometheus/Grafana)"
        },
        "cybersecurity": {
            "simple":   "Basic vulnerability scanner or CTF writeup",
            "medium":   "Security audit tool with reporting, basic SIEM integration",
            "advanced": "Full penetration testing framework or SIEM with ML-based anomaly detection"
        }
    }
    
    # ── Deployment Score Mapping (replaces 1/2/3 integer only) ───────
    DEPLOYMENT_SCORES = {
        "none":         0.0,
        "local":        1.0,
        "free_hosting": 3.0,   # Vercel, Netlify, Heroku
        "cloud_basic":  5.5,   # AWS EC2, Docker, DigitalOcean
        "cloud_full":   7.5,   # Docker + CI/CD + domain
        "production":   10.0   # K8s, auto-scaling, monitoring
    }
    
    def __init__(self, weights: Dict = None):
        default_weights = {
            "feature_depth":      0.35,  # How complex are the core features?
            "tech_stack":         0.20,  # How diverse is the tech stack?
            "integration_depth":  0.25,  # How many external systems connected?
            "deployment_level":   0.20,  # How production-ready is the deployment?
        }
        self.weights = weights or default_weights
        self._validate_weights()
        self.logger = logging.getLogger(__name__)
    
    def _validate_weights(self):
        total = sum(self.weights.values())
        if not (0.98 <= total <= 1.02):
            raise ValueError(f"Weights must sum to 1.0, got {total:.3f}")
        
    def _filter_domain(self, df: pd.DataFrame,
                        target_domain: str,
                        experience_band: Tuple = (0, 3)) -> pd.DataFrame:
        """Job_Type first, Title fallback. Safe copy. Experience filtered."""
        df = df.copy()

        if 'TItle_Cleaned' in df.columns and 'Title_Cleaned' not in df.columns:
            df = df.rename(columns={'TItle_Cleaned': 'Title_Cleaned'})

        if 'Job_Type' in df.columns:
            exact = df[df['Job_Type'].str.lower() == target_domain.lower()]
            domain_df = exact if len(exact) >= self.MIN_SAMPLES else pd.DataFrame()
        else:
            domain_df = pd.DataFrame()

        if domain_df.empty:
            col = 'Title_Cleaned' if 'Title_Cleaned' in df.columns else None
            if col:
                pattern = r'\b' + re.escape(target_domain) + r'\b'
                domain_df = df[df[col].str.contains(
                    pattern, case=False, na=False, regex=True
                )]

        if domain_df.empty:
            return pd.DataFrame()

        # Experience filter — fresher project bar ≠ senior project bar
        if 'Min_Experience' in domain_df.columns:
            min_e, max_e = experience_band
            domain_df = domain_df[
                (domain_df['Min_Experience'] >= min_e) &
                (domain_df['Min_Experience'] <= max_e + 1)
            ]

        return domain_df.copy()

    def _safe_keyword_pct(self, series: pd.Series,
                           keywords: List[str]) -> float:
        """NaN-safe keyword match percentage (0-100)."""
        valid = series.dropna().astype(str)
        if valid.empty:
            return 0.0
        pattern = r'\b(?:' + '|'.join(re.escape(k) for k in keywords) + r')\b'
        return float(valid.str.contains(pattern, case=False, na=False).mean() * 100)

    def _extract_market_complexity(self, domain_df: pd.DataFrame) -> dict:
        """
        Multi-signal market benchmark replacing skill_count / 1.5.

        Signals:
        1. Description keyword tiers (primary)
        2. Skill count median (secondary)
        3. Deployment mentions (tertiary)
        4. Competition intensity modifier
        """
        if domain_df.empty:
            return {
                "score": 5.0, "label": "Medium Complexity",
                "confidence": "None", "signals": {}
            }

        signals = {}

        # ── Signal 1: Feature Complexity from Descriptions ──
        if 'Description_Cleaned' in domain_df.columns:
            desc = domain_df['Description_Cleaned']

            basic_pct    = self._safe_keyword_pct(desc, self.COMPLEXITY_KEYWORDS["features"]["basic"])
            inter_pct    = self._safe_keyword_pct(desc, self.COMPLEXITY_KEYWORDS["features"]["intermediate"])
            adv_pct      = self._safe_keyword_pct(desc, self.COMPLEXITY_KEYWORDS["features"]["advanced"])

            # Weighted feature score (0-10)
            feature_score = (
                (basic_pct    * 0.15) +
                (inter_pct    * 0.35) +
                (adv_pct      * 0.50)
            ) / 10  # Normalize: 100% * max_weight = max 50 → /10 gives 0-5 range

            feature_score = min(10.0, feature_score * 2)  # Scale to 0-10
            signals["feature_complexity"] = round(feature_score, 2)

        # ── Signal 2: Integration Depth ──
        if 'Description_Cleaned' in domain_df.columns:
            desc = domain_df['Description_Cleaned']

            int_basic = self._safe_keyword_pct(desc, self.COMPLEXITY_KEYWORDS["integration"]["basic"])
            int_inter = self._safe_keyword_pct(desc, self.COMPLEXITY_KEYWORDS["integration"]["intermediate"])
            int_adv   = self._safe_keyword_pct(desc, self.COMPLEXITY_KEYWORDS["integration"]["advanced"])

            int_score = (
                (int_basic * 0.10) + (int_inter * 0.40) + (int_adv * 0.50)
            ) / 10
            int_score = min(10.0, int_score * 2)
            signals["integration_depth"] = round(int_score, 2)

        # ── Signal 3: Deployment Complexity ──
        if 'Description_Cleaned' in domain_df.columns:
            desc = domain_df['Description_Cleaned']

            dep_basic = self._safe_keyword_pct(desc, self.COMPLEXITY_KEYWORDS["deployment"]["basic"])
            dep_inter = self._safe_keyword_pct(desc, self.COMPLEXITY_KEYWORDS["deployment"]["intermediate"])
            dep_adv   = self._safe_keyword_pct(desc, self.COMPLEXITY_KEYWORDS["deployment"]["advanced"])

            dep_score = (
                (dep_basic * 0.10) + (dep_inter * 0.35) + (dep_adv * 0.55)
            ) / 10
            dep_score = min(10.0, dep_score * 2)
            signals["deployment_complexity"] = round(dep_score, 2)

        # ── Signal 4: Skill Count (Secondary) ──
        if 'Skill_Count' in domain_df.columns:
            median_skills = pd.to_numeric(
                domain_df['Skill_Count'], errors='coerce'
            ).median()

            if not pd.isna(median_skills):
                # Market-relative: normalize against reasonable ceiling of 20 skills
                skill_score = min(10.0, (median_skills / 20) * 10)
                signals["skill_breadth"] = round(skill_score, 2)

        # ── Signal 5: Competition Modifier ──
        # High-competition domains raise the bar — need stronger projects to stand out
        APPLICANT_COL = 'No of applicant applied cleaned'
        OPENINGS_COL  = 'No of job opening cleaned '

        competition_modifier = 0.0
        if APPLICANT_COL in domain_df.columns and OPENINGS_COL in domain_df.columns:
            apps  = pd.to_numeric(domain_df[APPLICANT_COL], errors='coerce').sum()
            opens = max(pd.to_numeric(domain_df[OPENINGS_COL], errors='coerce').fillna(1).sum(), 1)
            ratio = apps / opens

            if ratio > 100:
                competition_modifier = 1.5   # Very high competition → higher bar
            elif ratio > 50:
                competition_modifier = 0.75
            elif ratio > 25:
                competition_modifier = 0.25

            signals["competition_ratio"] = round(ratio, 1)

        # ── Composite Benchmark ──
        available_scores = [v for k, v in signals.items() 
                            if k not in ("competition_ratio",)]

        if available_scores:
            # Weighted blend: description signals carry more weight than skill count
            score_weights = {
                "feature_complexity":   0.35,
                "integration_depth":    0.25,
                "deployment_complexity": 0.25,
                "skill_breadth":        0.15,
            }

            weighted_sum = sum(
                signals.get(k, 0) * w 
                for k, w in score_weights.items()
            )
            total_weight = sum(
                w for k, w in score_weights.items() 
                if k in signals
            )

            base_score = weighted_sum / total_weight if total_weight > 0 else 5.0
        else:
            base_score = 5.0  # True fallback

        # Apply competition modifier
        final_score = min(10.0, base_score + competition_modifier)

        # Percentile-based label
        label, tier = self._label_complexity(final_score)

        # Confidence
        n_desc = domain_df['Description_Cleaned'].notna().sum() if 'Description_Cleaned' in domain_df else 0
        confidence = (
            "High"   if n_desc >= 50 else
            "Medium" if n_desc >= 20 else
            "Low"
        )

        return {
            "score":        round(final_score, 2),
            "label":        label,
            "tier":         tier,
            "confidence":   confidence,
            "signals":      signals,
            "sample_size":  len(domain_df)
        }

    def _label_complexity(self, score: float) -> Tuple[str, str]:
        """5-tier complexity label."""
        if score < 2.5:
            return "🟢 Basic / CRUD Level",          "basic"
        elif score < 4.5:
            return "🟡 Simple-Intermediate",          "simple_intermediate"
        elif score < 6.5:
            return "🟠 Medium Complexity",             "medium"
        elif score < 8.0:
            return "🔴 Advanced / Production-Ready",  "advanced"
        else:
            return "🚨 Expert-Level / Scalable Systems", "expert"


    def _validate_user_project_stats(self, stats: Dict) -> Tuple[bool, str]:
        """
        Validate user project stats with clear error messages.
        No more silent 0s from wrong key names.
        """
        REQUIRED_KEYS = {
            "features":    "Number of distinct features (int, 1-20)",
            "tech_count":  "Number of technologies used (int, 1-20)",
            "integrations":"Number of external APIs/services (int, 0-10)",
            "deployment":  f"Deployment level: one of {list(self.DEPLOYMENT_SCORES.keys())}"
        }

        missing = [k for k in REQUIRED_KEYS if k not in stats]
        if missing:
            details = {k: REQUIRED_KEYS[k] for k in missing}
            return False, f"Missing required keys: {details}"

        if stats["deployment"] not in self.DEPLOYMENT_SCORES:
            return False, (
                f"Invalid deployment value '{stats['deployment']}'. "
                f"Must be one of: {list(self.DEPLOYMENT_SCORES.keys())}"
            )

        for key in ["features", "tech_count", "integrations"]:
            if not isinstance(stats[key], (int, float)) or stats[key] < 0:
                return False, f"'{key}' must be a non-negative number, got: {stats[key]}"

        return True, "Valid"

    def calculate_project_score(self, stats: Dict) -> dict:
        """
        Score a user's project on 0-10 scale.
        All inputs validated and normalized to same scale.
        """
        valid, msg = self._validate_user_project_stats(stats)
        if not valid:
            return {"error": msg}

        # Normalize each dimension to 0-10
        feature_score    = min(10.0, stats["features"] / 2.0)          # 20 features = 10/10
        tech_score       = min(10.0, stats["tech_count"] / 2.0)        # 20 techs = 10/10
        integration_score = min(10.0, stats["integrations"] / 1.0)     # 10 integrations = 10/10
        deploy_score     = self.DEPLOYMENT_SCORES[stats["deployment"]]  # Named tier → score

        # Weighted composite
        total = (
            feature_score     * self.weights["feature_depth"]     +
            tech_score        * self.weights["tech_stack"]         +
            integration_score * self.weights["integration_depth"]  +
            deploy_score      * self.weights["deployment_level"]
        )
        total = round(float(np.clip(total, 0.0, 10.0)), 2)

        label, tier = self._label_complexity(total)

        return {
            "composite_score": total,
            "label":           label,
            "tier":            tier,
            "dimension_scores": {
                "features":     round(feature_score, 2),
                "tech_stack":   round(tech_score, 2),
                "integrations": round(integration_score, 2),
                "deployment":   round(deploy_score, 2)
            }
        }

    def _analyze_gap(self, user_score: dict,
                      market: dict,
                      target_domain: str) -> dict:
        """
        Quantify gap per dimension and generate specific improvement actions.
        """
        if "error" in user_score:
            return {"error": user_score["error"]}

        market_score = market["score"]
        user_total   = user_score["composite_score"]
        gap          = market_score - user_total

        # Per-dimension gaps
        # Infer market dimension scores from signals
        market_signals = market.get("signals", {})
        market_dims = {
            "features":     market_signals.get("feature_complexity",   market_score),
            "tech_stack":   market_signals.get("skill_breadth",        market_score * 0.8),
            "integrations": market_signals.get("integration_depth",    market_score),
            "deployment":   market_signals.get("deployment_complexity", market_score * 0.7),
        }

        user_dims = user_score["dimension_scores"]

        dim_gaps = {}
        suggestions = []

        # Feature gap
        feat_gap = market_dims["features"] - user_dims["features"]
        if feat_gap > 1.5:
            dim_gaps["features"] = round(feat_gap, 2)
            suggestions.append({
                "dimension": "Feature Depth",
                "gap":       round(feat_gap, 2),
                "action":    "Add a complex feature: real-time updates, recommendation engine, or multi-user collaboration."
            })

        # Tech stack gap
        tech_gap = market_dims["tech_stack"] - user_dims["tech_stack"]
        if tech_gap > 1.5:
            dim_gaps["tech_stack"] = round(tech_gap, 2)
            suggestions.append({
                "dimension": "Tech Stack Breadth",
                "gap":       round(tech_gap, 2),
                "action":    "Add caching (Redis), a message queue, or a secondary database to your stack."
            })

        # Integration gap
        int_gap = market_dims["integrations"] - user_dims["integrations"]
        if int_gap > 1.5:
            dim_gaps["integrations"] = round(int_gap, 2)
            suggestions.append({
                "dimension": "Integration Depth",
                "gap":       round(int_gap, 2),
                "action":    "Integrate a third-party API (payment, auth, email, or analytics service)."
            })

        # Deployment gap
        dep_gap = market_dims["deployment"] - user_dims["deployment"]
        if dep_gap > 1.5:
            dim_gaps["deployment"] = round(dep_gap, 2)

            # Smart deployment suggestion based on current level
            current_deploy = None
            for tier, score in sorted(self.DEPLOYMENT_SCORES.items(), key=lambda x: x[1]):
                if score <= user_dims["deployment"]:
                    current_deploy = tier

            next_step = {
                "none":         "Deploy to Vercel/Netlify (free, 1 day effort).",
                "local":        "Deploy to Vercel/Netlify or Render (free, 1 day effort).",
                "free_hosting": "Add Docker + deploy to cloud VM (AWS EC2 free tier).",
                "cloud_basic":  "Add CI/CD pipeline with GitHub Actions.",
                "cloud_full":   "Add monitoring (Prometheus/Grafana) and auto-scaling.",
            }.get(current_deploy, "Improve deployment infrastructure.")

            suggestions.append({
                "dimension": "Deployment Level",
                "gap":       round(dep_gap, 2),
                "action":    next_step
            })

        # Sort by gap size
        suggestions.sort(key=lambda x: x["gap"], reverse=True)

        # Overall status
        if gap <= 0:
            status = "✅ Market Ready"
            status_detail = f"Your project score ({user_total}) meets or exceeds market expectation ({market_score})."
        elif gap <= 1.5:
            status = "🟡 Minor Gap"
            status_detail = f"Gap of {gap:.1f} points. 1-2 targeted improvements will close this."
        elif gap <= 3.5:
            status = "🟠 Moderate Gap"
            status_detail = f"Gap of {gap:.1f} points. Need meaningful project upgrades across {len(suggestions)} dimensions."
        else:
            status = "🔴 Significant Gap"
            status_detail = f"Gap of {gap:.1f} points. Consider rebuilding your flagship project with market expectations in mind."

        return {
            "overall_gap":       round(gap, 2),
            "status":            status,
            "status_detail":     status_detail,
            "dimension_gaps":    dim_gaps,
            "improvement_actions": suggestions,
            "priority_action":   suggestions[0]["action"] if suggestions else "Project meets market standards."
        }

    def _get_domain_archetype(self, target_domain: str, tier: str) -> Optional[str]:
        """Get concrete project example for domain + tier."""
        domain_lower = target_domain.lower()

        # Find best matching archetype
        for known_domain, tiers in self.DOMAIN_ARCHETYPES.items():
            if known_domain in domain_lower or domain_lower in known_domain:
                return tiers.get(tier, tiers.get("medium"))

        # Fallback by tier
        return {
            "basic":              "Simple CRUD application with basic UI",
            "simple_intermediate": "Full-stack app with auth and database",
            "medium":             "Multi-feature app with external API and deployment",
            "advanced":           "Production system with scalable architecture and monitoring",
            "expert":             "Distributed system with advanced architecture patterns"
        }.get(tier, "Production-quality project with full deployment")

    def evaluate_portfolio_readiness(self,
                                       df: pd.DataFrame,
                                       target_domain: str,
                                       user_project_stats: Dict = None,
                                       experience_band: Tuple = (0, 3)) -> dict:
        """Main entry point. Full portfolio complexity evaluation."""

        # 1. Filter domain
        domain_df = self._filter_domain(df, target_domain, experience_band)

        if domain_df.empty:
            return {"error": f"No data found for domain: '{target_domain}'"}

        if len(domain_df) < self.MIN_SAMPLES:
            return {
                "error": f"Insufficient data: {len(domain_df)} records "
                         f"(need {self.MIN_SAMPLES}+)."
            }

        # 2. Market benchmark (rich multi-signal)
        market = self._extract_market_complexity(domain_df)

        # 3. Domain archetype example
        archetype = self._get_domain_archetype(target_domain, market["tier"])

        # 4. User project assessment (if provided)
        user_score = None
        gap_analysis = None

        if user_project_stats:
            user_score   = self.calculate_project_score(user_project_stats)

            if "error" not in user_score:
                gap_analysis = self._analyze_gap(user_score, market, target_domain)

        # 5. Target specifications (data-driven)
        target_specs = self._derive_target_specs(market)

        return {
            "Domain":           target_domain,
            "Experience_Band":  experience_band,
            "Sample_Size":      len(domain_df),

            "Market_Benchmark": {
                "Score":          market["score"],
                "Label":          market["label"],
                "Confidence":     market["confidence"],
                "Signals":        market["signals"],
                "Example_Project": archetype
            },

            "User_Project": user_score,

            "Gap_Analysis": gap_analysis,

            "Target_Specifications": target_specs,

            "Quick_Verdict": self._quick_verdict(
                market, user_score, gap_analysis
            )
        }

    def _derive_target_specs(self, market: dict) -> dict:
        """Data-driven specs replacing hardcoded '6+' suggestions."""
        score = market["score"]

        return {
            "minimum_features":   2 + int(score / 2),        # 5 for score=6, 7 for score=8
            "recommended_techs":  3 + int(score / 2),        # 6 for score=6, 8 for score=8
            "integrations":       max(1, int(score / 3)),     # 2 for score=6, 3 for score=9
            "deployment_target":  (
                "production"   if score >= 8.0 else
                "cloud_full"   if score >= 6.5 else
                "cloud_basic"  if score >= 4.5 else
                "free_hosting" if score >= 2.5 else
                "local"
            ),
            "data_complexity":    (
                "Multiple real-time sources with pipeline" if score >= 7.5 else
                "Multiple sources with API integration"    if score >= 5.5 else
                "Single external API or database"          if score >= 3.5 else
                "Static data or single CSV"
            )
        }

    def _quick_verdict(self, market: dict,
                        user_score: Optional[dict],
                        gap: Optional[dict]) -> str:
        """Plain-English for AdaptiveRealTalkEngine."""
        if user_score is None:
            return (
                f"Market expects {market['label']} projects. "
                f"Provide your project stats to get a personalized gap analysis."
            )

        if "error" in user_score:
            return f"Could not assess user project: {user_score['error']}"

        if gap is None:
            return "Gap analysis unavailable."

        status = gap["status"]
        action = gap.get("priority_action", "")

        return f"{status} — {gap['status_detail']} Next: {action}"


if __name__ == "__main__":
    import json
    import pandas as pd

    # Example usage
    df = pd.read_csv(r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv")
    evaluator = ProjectComplexityEvaluator()
    result = evaluator.evaluate_portfolio_readiness(
        df, target_domain="Data Scientist", experience_band=(0, 3),
        user_project_stats={
            "features": 4,
            "tech_count": 5,
            "integrations": 1,
            "deployment": "cloud_basic"
        }
    )
    
    print(json.dumps(result, indent=2))
