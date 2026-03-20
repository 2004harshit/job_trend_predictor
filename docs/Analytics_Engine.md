---

# Engine 1 — `MarketDemandEngine` (Demand Score Calculator)

**File:** `demand_score_calculator.py`  
**Class:** `MarketDemandEngine`

---

## 1. Introduction — What is this Engine and What Does it Do?

Imagine you are trying to figure out which job domains (like "Data Science", "Web Development", "DevOps", etc.) are actually **in demand right now** for freshers and entry-level candidates.

You could simply count job postings — but that would be too simple. A domain might have lots of old, irrelevant postings. Or it might have very few companies hiring, meaning you are competing with everyone for one or two spots. Or the number of applicants might be 500x the number of openings — which means it looks popular but is actually very hard to get into.

**`MarketDemandEngine` solves this problem.**

It looks at the job market from **5 different angles** (called sub-scores), combines them using a weighted formula, and produces a single **Demand Score (0–10)** for each domain. This score tells you how genuinely "in demand" that domain is for a fresher right now.

> Think of it like a restaurant review app — instead of just counting how many people visited, it also checks food quality, price, wait time, and ambience, then gives a final star rating.

---

## 2. Data Fields Required by This Engine

The engine needs a pandas DataFrame (basically a table/spreadsheet) with the following columns:

| Column Name | What it Means | Required? |
|---|---|---|
| `Job_Type` | The domain/role category (e.g., "Data Science", "Web Dev") | ✅ Yes |
| `Scraped_At_Cleaned` | The date when this job posting was collected/scraped | ✅ Yes |
| `Min_Experience` | Minimum years of experience required for the job | ✅ Yes |
| `Company_Cleaned` | Name of the company posting the job | ✅ Yes |
| `Max_Experience` | Maximum years of experience accepted | ✅ Yes (used in filtering) |
| `Posted_Date` | The original date the job was posted on the portal | ❌ Optional (parsed if present) |
| `No of applicant applied cleaned` | How many people applied for jobs in this domain | ❌ Optional (defaults to 5.0 if missing) |
| `No of job opening cleaned ` | How many open positions exist in this domain | ❌ Optional (defaults to 5.0 if missing) |

> **Note:** If the optional columns are missing, the engine still works — it simply gives a neutral score (5.0 out of 10) for that particular sub-score.

---

## 3. Core Logic — How Does the Engine Calculate the Score?

The engine calculates **5 individual sub-scores** (each on a scale of 0–10), then combines them into one final **Demand Score** using a weighted average.

### Final Score Formula

```
Demand Score = (Frequency Score × 0.30)
             + (Trend Score      × 0.25)
             + (ADR Score        × 0.20)
             + (Diversity Score  × 0.15)
             + (Flex Score       × 0.10)
```

---

### Sub-Score 1 — Job Posting Frequency Score (Volume)

**What it measures:** How many recent job postings exist for this domain — but with a twist. **Recent postings count more than old ones.**

**Formula:**
```
decay_weight  = e^( -0.693 × days_ago / 30 )
weighted_freq = sum of all decay_weights for domain
Frequency Score = (weighted_freq / max_freq_across_all_domains) × 10
```

**Plain English Example:**
- A job posted today gets a weight of `1.0` (full credit).
- A job posted 30 days ago gets a weight of `~0.5` (half credit).
- A job posted 60 days ago gets a weight of `~0.25` (quarter credit).

So if "Data Science" has 100 postings but they are all 2 months old, and "Web Dev" has 50 postings all from this week — Web Dev will get a higher frequency score.

---

### Sub-Score 2 — Trend Direction Score (Growth)

**What it measures:** Is this domain **growing** or **shrinking**? It compares job postings from the **last 30 days** vs the **30 days before that**.

**Formula:**
```
growth_ratio  = current_month_count / previous_month_count
damped_growth = log₂(growth_ratio + tiny_number)
Trend Score   = clip( 5 + (damped_growth × 2.5), min=0, max=10 )
```

**Plain English Example:**

| Situation | growth_ratio | Trend Score |
|---|---|---|
| Same postings as last month | 1.0 | 5.0 (Stable) |
| Double the postings | 2.0 | 7.5 (Growing) |
| 4x the postings | 4.0 | 10.0 (Capped) |
| Half the postings | 0.5 | 2.5 (Declining) |

> The `log₂` is used so that a domain going from 10→20 jobs (2x) and one going from 100→200 jobs (also 2x) get the same trend score. It prevents large domains from always looking "more growing" just because of size.

**Edge Cases:**
- If both months have fewer than 5 postings → Score = 5.0 (not enough data to judge)
- If previous month had 0 postings but current has some → Score = 6.5 (new/emerging domain)

---

### Sub-Score 3 — Applicant Demand Ratio (ADR)

**What it measures:** How **competitive** is this domain? High applicants + few openings = hard to get in = **lower score**. Few applicants + many openings = easy to get in = **higher score**.

**Formula:**
```
ratio     = total_applicants / total_openings
ADR Score = clip( 10 - (log₁₀(ratio + 1) × 4), min=0, max=10 )
```

**Plain English Example:**

| Applicants | Openings | Ratio | ADR Score | Meaning |
|---|---|---|---|---|
| 100 | 100 | 1.0 | ~8.8 | Easy to get in |
| 500 | 100 | 5.0 | ~7.2 | Moderate competition |
| 5000 | 100 | 50 | ~4.3 | High competition |
| 50000 | 100 | 500 | ~1.7 | Very tough |

> `log₁₀` is used to "soften" extreme ratios so that a ratio of 1000 doesn't make the score go to -infinity. It brings large numbers into a manageable range.

---

### Sub-Score 4 — Skill/Market Diversity Score

**What it measures:** How many **different companies** are hiring in this domain? More companies = healthier market = higher score. If only 1–2 companies are posting, the domain is risky even if postings seem high.

**Formula:**
```
Diversity Score = ( log(1 + domain_companies) / log(1 + total_companies) ) × 10
```

**Plain English Example:**
- If 50 out of 200 total companies hire for "Data Science" → high diversity score
- If only 3 companies hire for "Blockchain" → low diversity score, even if those 3 post many jobs

> `log1p` (log of 1 + value) is used to handle the case where a domain has 0 companies (avoids log of 0 error) and to compress the scale fairly.

---

### Sub-Score 5 — Experience Flexibility Score

**What it measures:** What **percentage** of jobs in this domain are open to freshers (0–5 years experience)? A domain where 90% of jobs need 5+ years of experience is NOT good for freshers even if total postings are high.

**Formula:**
```
Flex Score = (fresher_job_count / total_domain_job_count) × 10
```

**Plain English Example:**
- Domain has 100 total jobs, 80 are for freshers → Score = 8.0
- Domain has 100 total jobs, 20 are for freshers → Score = 2.0

---

## 4. Weights — What They Mean and Why These Values

| Weight Name | Value | Why This Weight? |
|---|---|---|
| `Job_Posting_Frequency` | **0.30** | The most important signal. How many jobs are available right now matters most for a job seeker. Gets highest weight. |
| `Trend_Direction` | **0.25** | Second most important. A growing domain is better than a stable or declining one. Forward-looking signal. |
| `Applicant_Demand_Ratio` | **0.20** | Third. Competition level directly affects your chance of getting hired. High weight because it reflects real market difficulty. |
| `Skill_Diversity` | **0.15** | Fourth. More companies = more chances = more stable market. But less directly actionable for a job seeker. |
| `Experience_Flexibility` | **0.10** | Lowest. It acts as a filter/bonus for fresher-friendliness but is less differentiating since we already filtered fresher data. |

> **Key Rule:** All weights must sum to exactly **1.0** (with a ±0.02 tolerance). The engine validates this at startup and throws an error if weights are wrong. This ensures the final score always stays on a 0–10 scale.

---

## 5. Functions — What They Do and How They Are Called

```
calculate_metrics()          ← Main entry point (you call this)
    │
    ├── _filter_fresher_data()       → Keeps only 0–5 years experience jobs
    ├── _get_valid_domains()         → Removes domains with < 10 jobs (too little data)
    ├── _get_time_metrics()          → Sets up current month vs previous month windows
    │
    ├── [For each domain:]
    │     ├── _calculate_frequency_score()        → Volume sub-score (decay-weighted)
    │     ├── _calculate_trend_score()             → Growth sub-score (log₂ based)
    │     ├── _calculate_applicant_demand_ratio()  → Competition sub-score (log₁₀ based)
    │     ├── _calculate_diversity_score()         → Company spread sub-score (log1p based)
    │     └── [Flex score calculated inline]       → Fresher % sub-score
    │
    └── _label_score()               → Converts number to human-readable label
```

| Function | Role |
|---|---|
| `__init__()` | Sets up the engine, loads data, sets weights, parses dates |
| `_validate_required_columns()` | Checks all needed columns exist before running |
| `_validate_weights()` | Makes sure weights add up to 1.0 |
| `_filter_fresher_data()` | Filters dataset to only fresher-level jobs (0–5 yrs exp) |
| `_get_valid_domains()` | Skips domains with too few postings to be statistically reliable |
| `_get_time_metrics()` | Returns date boundaries for "this month" and "last month" |
| `_calculate_frequency_score()` | Computes time-decayed volume score |
| `_calculate_trend_score()` | Computes growth/decline score by comparing two months |
| `_calculate_applicant_demand_ratio()` | Computes competition score from applicant/opening ratio |
| `_calculate_diversity_score()` | Computes how many unique companies hire in this domain |
| `calculate_metrics()` | **Master function** — orchestrates all above, returns final report |
| `_label_score()` | Converts numeric score to emoji label |

---

## 6. Output — What Does the Engine Return?

The engine returns a **Python dictionary** where each key is a domain name, and the value contains the full demand report.

### Sample Output

```json
{
    "Data Science": {
        "Overall_Demand_Score": 7.43,
        "Score_Label": "📈 Growing",
        "Breakdown": {
            "Volume": 8.2,
            "Growth_Trend": 7.1,
            "Applicant_Ratio": 6.5,
            "Market_Diversity": 7.8,
            "Entry_Flexibility": 6.0
        },
        "Raw_Counts": {
            "Fresher_Jobs": 312,
            "Total_Domain_Jobs": 480
        }
    },
    "Web Development": {
        "Overall_Demand_Score": 8.91,
        "Score_Label": "🔥 High Demand",
        "Breakdown": {
            "Volume": 9.5,
            "Growth_Trend": 8.8,
            "Applicant_Ratio": 7.9,
            "Market_Diversity": 9.1,
            "Entry_Flexibility": 8.5
        },
        "Raw_Counts": {
            "Fresher_Jobs": 621,
            "Total_Domain_Jobs": 700
        }
    }
}
```

### Score Labels

| Score Range | Label | Meaning |
|---|---|---|
| 8.0 – 10.0 | 🔥 High Demand | Excellent time to enter this domain |
| 6.0 – 7.9 | 📈 Growing | Domain is expanding, good opportunity |
| 4.0 – 5.9 | ⚖️ Stable | Neither growing nor shrinking |
| 2.0 – 3.9 | 📉 Declining | Market shrinking, be cautious |
| 0.0 – 1.9 | 🧊 Very Low Demand | Avoid or reconsider |

---

## 7. How Robust Are the Formulas and Weights?

### What Makes Them Solid ✅

| Feature | Why It's Good |
|---|---|
| **Time-decay in frequency** | Recent jobs matter more than old stale postings. Prevents outdated data from inflating scores. |
| **Log-based growth (log₂)** | Prevents big domains from always "winning" just because of size. A 2x growth is treated equally whether it's 10→20 or 1000→2000. |
| **Log-based ADR (log₁₀)** | A ratio of 5000:1 and 50000:1 don't both crash the score to zero — the log compression keeps things proportional. |
| **Log-based diversity (log1p)** | Handles zero-company edge case cleanly. Compresses scale so 50 companies vs 51 companies isn't treated as dramatically different. |
| **Minimum sample threshold** | Domains with fewer than 10 jobs are skipped — avoids unreliable scores from tiny samples. |
| **Weight validation** | Automatically rejects invalid weight configurations before any calculation runs. |
| **Fallback defaults** | If optional columns (applicants, openings) are missing, engine defaults to 5.0 instead of crashing. |

---

## 8. Advantages of the Current Implementation

- **Multi-dimensional:** Unlike simply counting job postings, this engine looks at 5 different angles giving a much more realistic picture.
- **Fresher-focused:** Explicitly filters for entry-level jobs (0–5 years experience) — relevant for the target audience.
- **Recency-aware:** The exponential decay ensures that a burst of job postings from 3 months ago doesn't mislead today's analysis.
- **Graceful degradation:** Missing columns don't crash the engine — it continues with neutral scores.
- **Configurable weights:** Users can pass custom weights if they want to prioritize, say, trend over volume.
- **Statistically safe:** Minimum sample check prevents misleading scores from domains with 2–3 job postings.
- **Human-readable output:** Score labels (🔥 High Demand, 📉 Declining) make it usable even for non-technical users.

---

## 9. Disadvantages and How to Improve Them

### Current Limitations

| Limitation | Problem | Suggested Fix |
|---|---|---|
| **Static weights (hardcoded defaults)** | The 0.30/0.25/0.20/0.15/0.10 split was chosen manually. There is no data-driven proof these are optimal. | Use a machine learning model (e.g., logistic regression or gradient boosting) trained on actual hiring outcomes to learn optimal weights. |
| **Only looks at 30-day windows** | The trend score compares just last 30 days vs 30 days before. This is too short — seasonal spikes (like campus hiring in Oct–Nov) can mislead the trend. | Use a **3-month or 6-month rolling window**, or add seasonal decomposition (e.g., STL decomposition). |
| **No salary data in scoring** | The score doesn't consider average salary for freshers in a domain, which is a huge factor in real demand attractiveness. | Add a `Salary_Score` sub-component based on median fresher salary per domain. |
| **Trend score edge cases are hardcoded** | When previous month has 0 jobs, it returns 6.5 (an arbitrary number). When both months have <5 jobs, it returns 5.0. These values were chosen manually. | These neutral defaults should be configurable parameters rather than hardcoded magic numbers. |
| **Applicant data often missing** | Many scraped datasets don't have applicant count → ADR defaults to 5.0 for every domain, making this sub-score useless. | Improve the scraping pipeline to capture applicant counts more reliably, or replace with a **skills-to-openings ratio** as a proxy. |
| **No location-level granularity** | The score is computed globally. "Data Science in Bangalore" and "Data Science in Jaipur" will have the same score even if the markets are very different. | Add an optional `location` filter parameter to `calculate_metrics()` so city-level scores can be generated. |
| **`_label_score` thresholds are fixed** | The 8.0/6.0/4.0/2.0 thresholds for labels were decided manually and may not reflect the actual distribution of scores. | Compute thresholds dynamically using **percentile-based bucketing** (e.g., top 20% = High Demand, bottom 20% = Very Low Demand) based on current dataset distribution. |

### Formula Improvement Suggestions

```
# Current ADR formula (simple log compression):
score = 10 - (log10(ratio + 1) * 4)

# Improved: Use a sigmoid-based approach for smoother, more interpretable score:
score = 10 / (1 + exp(0.1 * (ratio - 10)))
# This gives score ~10 when ratio=1, ~5 when ratio=10, ~1 when ratio=100
```

```
# Current trend formula (symmetric around 5):
score = clip( 5 + log2(growth_ratio) * 2.5, 0, 10 )

# Improved: Asymmetric scoring — reward growth more than penalizing decline
# because for a job seeker, a declining domain is worse than the mirror image of a growing one
score = clip( 5 + log2(growth_ratio) * 3.5, 0, 10 )  # steeper upside
```

---

*End of Engine 1 Documentation*

---


---

# Engine 2 — `CompetitionLevelCalculator` (Competition Level Engine)

**File:** `competition_level_calculator.py`  
**Class:** `CompetitionLevelCalculator`

---

## 1. Introduction — What is this Engine and What Does it Do?

Imagine two candidates are both applying for "Data Science" jobs. Both see 500 job postings online. But one of them knows Python, SQL, and Machine Learning — exactly what companies are asking for. The other knows HTML and Java — completely wrong skills.

For the first candidate, the market is **easier** than it looks. For the second, it is **harder** than it looks.

**`CompetitionLevelCalculator` answers one key question:**

> *"How hard is it REALLY to get a job in this domain — both for a typical candidate AND specifically for YOU?"*

It does this by looking at two things together:
1. **How many people are competing for how many seats** (Supply vs Demand)
2. **How well your skills match what companies actually want** (Skill Overlap)

It then combines both to give you two separate competition levels:
- **Market Competition** — how tough the domain is for everyone in general
- **Your Competition** — how tough it actually is for you, given your specific skills

> Think of it like a college entrance exam. The general cutoff is 85%. But if you are great at the subjects being tested, your effective difficulty is lower than 85%. If your subjects are wrong, your difficulty is higher — even if the exam looks the same for everyone.

---

## 2. Data Fields Required by This Engine

### Required Columns (Engine will warn if missing, but still tries to run)

| Column Name | What it Means | Required? |
|---|---|---|
| `Skill_Count` | Number of skills required by a job posting | ✅ Core (warns if missing) |
| `Min_Experience` | Minimum years of experience for the job | ✅ Core (warns if missing) |
| `Max_Experience` | Maximum years of experience accepted | ✅ Used in experience filtering |
| `Job_Type` | Domain/category of the job (e.g., "Data Scientist") | ✅ Primary filter |

### Optional but Highly Recommended Columns

| Column Name | What it Means | Fallback if Missing |
|---|---|---|
| `No of applicant applied cleaned` | How many people applied | Estimated using domain-specific ratios |
| `No of job opening cleaned ` | Actual number of open positions | Assumes 1 opening per listing |
| `Posted_Date` | When the job was originally posted | Falls back to `Scraped_At_Cleaned` |
| `Scraped_At_Cleaned` | When the job was collected by scraper | All listings treated as active |
| `Title_Cleaned` | Job title text (for fallback domain matching) | Domain matching fails gracefully |
| `Combined_Skills` | Text of all skills listed in job posting | Qualitative skill match skipped |
| `Star_Skills` | Must-have / critical skills for the role | Missing skills gap not identified |
| `Location` | City/location of the job | National-level data used |

### Inputs Passed at Runtime (not columns)

| Parameter | What it Means | Default |
|---|---|---|
| `target_domain` | Domain you want to analyze (e.g., "Data Scientist") | Required |
| `user_skills` | List of skills the user has (e.g., `["Python", "SQL"]`) | `None` (only market view given) |
| `experience_band` | Tuple of (min, max) experience years e.g., `(0, 3)` | `(0, 3)` |
| `location` | City to filter jobs (e.g., `"Bangalore"`) | `None` (national) |

---

## 3. Core Logic — How Does the Engine Calculate Competition?

The engine works in **3 stages** that build on each other:

---

### Stage 1 — Supply vs Demand (Raw Competition Ratio)

**What it measures:** For every 1 job opening, how many candidates are competing?

```
Raw Ratio = Total Applicants / Total Openings
```

**Plain English Example:**

| Domain | Applicants | Openings | Raw Ratio | Meaning |
|---|---|---|---|---|
| DevOps | 500 | 100 | 5.0 | 5 people per seat — easy |
| Web Dev | 8,000 | 100 | 80.0 | 80 people per seat — very tough |
| Data Science | 3,000 | 100 | 30.0 | 30 people per seat — hard |

> **Important Design Choice:** The engine counts **actual job openings**, not just job listings. One listing that says "hiring 50 people" is treated as 50 openings — not as 1. This is a key fix over naive approaches.

---

### Stage 2 — Skill Overlap (How Well Do You Fit?)

This stage calculates two overlap factors — one for the **market average** and one **specific to you**.

#### Market Overlap Factor

**What it measures:** What percentage of a typical Indian fresher's skills match what companies need?

```
Market Overlap = clip( 7 / avg_required_skills , min=0.1, max=1.0 )
```

> `7` is used as the typical number of skills a fresh Indian job seeker knows (based on Naukri dataset context).

**Plain English Example:**
- If a domain requires 7 skills on average → Market Overlap = 7/7 = **1.0** (perfect fit for average candidate)
- If a domain requires 14 skills on average → Market Overlap = 7/14 = **0.5** (average candidate has only half the skills needed)
- If a domain requires 4 skills on average → Market Overlap = clipped to **1.0** (average candidate over-qualifies)

---

#### User Overlap Factor (only when `user_skills` is provided)

This has **two components** combined:

**Component 1 — Quantitative Match (60% weight):**
```
Count Match = min( 1.0 , len(user_skills) / avg_required_skills )
```
Do you have *enough* skills in terms of quantity?

**Component 2 — Qualitative Match (40% weight):**
```
Qual Match = skills_you_have_that_appear_in_job_postings / total_user_skills
```
Are your skills the *right* skills that companies actually list?

**Combined User Overlap:**
```
User Overlap = (0.6 × Count Match) + (0.4 × Qual Match)
User Match % = User Overlap × 100
```

**Plain English Example:**

A user has skills: `["Python", "SQL", "Excel"]`  
Domain requires on average 6 skills. Job postings mention: Python, SQL, TensorFlow, Docker, AWS, Spark.

- Count Match = 3/6 = **0.5** (has half the quantity needed)
- Qualitative: Python ✅, SQL ✅, Excel ❌ (not in job postings) → 2/3 = **0.667**
- User Overlap = (0.6 × 0.5) + (0.4 × 0.667) = 0.30 + 0.267 = **0.567**
- User Match % = **56.7%**

---

### Stage 3 — Competition Index (Final Score)

Two indexes are computed:

#### Market Competition Index
```
Competition Index = (Total Applicants × Market Overlap Factor) / Total Openings
```

This adjusts the raw ratio by how hard the skill bar actually is. If the domain needs very advanced skills, even though many people apply, fewer will truly qualify.

#### Your (User) Competition Index
```
User Advantage    = User Overlap Factor / Market Overlap Factor
User Competition  = Competition Index / max(User Advantage, 0.1)
```

**Plain English Intuition:**
- If your skills match the market **better than average** → User Advantage > 1.0 → Your effective competition is **lower**
- If your skills match **worse than average** → User Advantage < 1.0 → Your effective competition is **higher**

**Example:**

| Situation | Market Index | User Advantage | Your Index | Meaning |
|---|---|---|---|---|
| User matches market perfectly | 25.0 | 1.0 | 25.0 | Same as everyone |
| User is better than average (2x overlap) | 25.0 | 2.0 | 12.5 | Half the competition for you |
| User is worse than average (0.5x overlap) | 25.0 | 0.5 | 50.0 | Double the competition for you |

---

### Stage 4 — Dynamic Classification (Percentile-Based Labels)

Instead of hardcoded thresholds like "ratio > 30 = High", the engine **compares your domain to all other domains** using percentiles.

```
Percentile = (number of domains with lower ratio than yours / total domains) × 100

if percentile < 20  → "Very Low"   (you're in easiest 20% of all domains)
if percentile < 40  → "Low"
if percentile < 60  → "Medium"
if percentile < 80  → "High"
else                → "Very High"  (you're in hardest 20% of all domains)
```

**Why this is smarter than fixed thresholds:**

In 2020, a ratio of 20:1 might be "High". In 2025 after tech layoffs, 20:1 might be "Low" because everything has gotten harder. Percentile-based classification automatically adjusts to current market conditions.

**Fallback** (if market data is insufficient for percentile):

| Raw Ratio | Label |
|---|---|
| < 5 | Very Low |
| 5 – 14 | Low |
| 15 – 29 | Medium |
| 30 – 59 | High |
| ≥ 60 | Very High |

---

## 4. Weights — What They Mean and Why These Values

| Weight / Constant | Value | Purpose and Justification |
|---|---|---|
| `Count Match weight` | **0.60** | Quantity of skills matters more than exact match — having enough skills is the primary barrier to getting an interview shortlist. |
| `Qual Match weight` | **0.40** | Qualitative relevance matters too — having the "right" skills (not just many skills) is what wins interviews. Weighted slightly lower than count because partial skill overlap still gets you through many ATS filters. |
| `TYPICAL_SEEKER_SKILLS` | **7** | Based on the Naukri dataset context — typical Indian fresher's skill profile. Used as the market baseline for overlap calculation. Should be updated if dataset changes. |
| `ACTIVE_LISTING_DAYS` | **60** | Jobs older than 60 days are considered stale/filled. Prevents old listings from inflating "available positions". Extended to 120 days if fewer than 10 active listings found. |
| `MIN_SAMPLE_THRESHOLD` | **5** | Domains with fewer than 5 active listings are skipped for market baseline — too little data to be statistically meaningful. |
| `User Advantage floor` | **0.1** | Prevents division-by-zero when user overlap is very low. Ensures user competition index doesn't explode to infinity. |
| **Percentile bands** | 20/40/60/80/100 | Equal 20-percentile buckets — gives each label exactly 20% of the domain distribution. Balanced, unbiased classification. |

---

## 5. Functions — What They Do and How They Are Called

```
calculate_competition_level()        ← Main entry point (you call this)
    │
    ├── _filter_active_listings()    → Keep only jobs from last 60 days (or 120 if sparse)
    ├── _filter_domain()             → Find rows matching target domain + experience band
    │       └── Falls back to Title_Cleaned if Job_Type doesn't match
    │
    ├── _calculate_supply_demand()   → Count actual applicants and openings
    │       └── Clips outlier applicant counts at 95th percentile
    │       └── Estimates applicants if data missing (domain-specific ratios)
    │
    ├── _calculate_skill_overlap()   → Compute market + user skill match factors
    │       ├── Market Overlap: typical 7-skill fresher vs avg required skills
    │       ├── User Overlap:   count match (60%) + qualitative match (40%)
    │       └── Identifies missing Star Skills for user
    │
    ├── _build_market_baseline()     → Compute raw ratios for ALL domains (for percentile)
    │       └── Calls _calculate_supply_demand() for each domain
    │
    ├── _classify_competition()      → Assign "Very Low/Low/Medium/High/Very High"
    │       └── Uses percentile if market data available, absolute thresholds otherwise
    │
    └── _interpret_competition()     → Plain English summary string for UI display
```

| Function | Role |
|---|---|
| `__init__()` | Sets up logger and empty cache |
| `_filter_active_listings()` | Removes stale job listings (>60 days old) |
| `_filter_domain()` | Finds jobs matching domain name + experience band |
| `_calculate_supply_demand()` | Core supply/demand counting with outlier clipping |
| `_calculate_skill_overlap()` | Computes both market-level and user-level skill fit |
| `_build_market_baseline()` | Builds a series of all domain ratios for percentile comparison |
| `_classify_competition()` | Converts ratio to label using dynamic or fallback thresholds |
| `calculate_competition_level()` | **Master function** — orchestrates all above, builds final output |
| `_interpret_competition()` | Converts labels to a human-readable, actionable sentence |

---

## 6. Output — What Does the Engine Return?

The engine returns a **Python dictionary** with 6 sections.

### Sample Output

```json
{
    "Domain": "Data Scientist",
    "Experience_Band": [0, 3],
    "Location": "National",
    "Data_Quality": "Actual",

    "Market_Competition": {
        "Level": "High",
        "Competition_Index": 18.75,
        "Candidates_Per_Job": 30.0,
        "Listing_Count": 124
    },

    "Your_Competition": {
        "Level": "Medium",
        "Your_Skill_Match": 72.5,
        "Missing_Star_Skills": ["TensorFlow", "Docker", "Spark"],
        "Effective_Index": 9.38
    },

    "Skill_Insights": {
        "Avg_Skills_Required": 8.0,
        "Market_Avg_Match_Pct": 87.5
    },

    "Raw_Numbers": {
        "Total_Applicants": 3000,
        "Total_Openings": 100
    },

    "Interpretation": "🔴 Tough market — you need strong projects + network. 
                       Your skills put you at 'Medium' level personally. 
                       Gap: learn TensorFlow, Docker, Spark to improve your odds."
}
```

### Key Output Fields Explained

| Field | What it Tells You |
|---|---|
| `Market_Competition.Level` | How hard is this domain for EVERYONE |
| `Market_Competition.Candidates_Per_Job` | Raw number — how many people per seat |
| `Your_Competition.Level` | How hard is it specifically FOR YOU |
| `Your_Competition.Your_Skill_Match` | What % of job requirements you already meet |
| `Your_Competition.Missing_Star_Skills` | The top must-have skills you are missing |
| `Your_Competition.Effective_Index` | Your personal competition score (lower = better) |
| `Data_Quality` | "Actual" if real data used, "Estimated" if proxy values used |
| `Interpretation` | Plain English summary — ready to show directly to user |

---

## 7. How Robust Are the Formulas and Weights?

### What Makes Them Solid ✅

| Feature | Why It's Good |
|---|---|
| **Percentile-based classification** | Adapts to current market automatically. No hardcoded cutoffs that become stale. |
| **Actual openings vs listing count** | 1 listing with 50 openings is correctly treated as 50 seats, not 1. Much more accurate than simple listing count. |
| **Outlier clipping at 95th percentile** | Viral job postings with 50,000 applicants won't distort the entire domain's competition score. |
| **Two-level skill overlap** | Separates "how many skills do you have" from "are they the RIGHT skills" — both matter differently. |
| **Graceful fallback chain** | Missing applicant data → domain-specific estimation. Missing Job_Type → title text search. Missing date → all listings used. Engine never crashes silently. |
| **Location filter with minimum sample check** | If city-level data has fewer than 5 jobs, falls back to national data automatically with a warning. |
| **User Advantage floor of 0.1** | Prevents mathematically undefined results when user has essentially zero relevant skills. |

---

## 8. Advantages of the Current Implementation

- **Dual perspective output** — gives both market-level and user-specific competition, which is far more actionable than generic domain rankings.
- **Context-aware competition** — a ratio of 20:1 in DevOps might be "Low" while the same ratio in Web Dev might be "Medium" — the percentile system handles this correctly.
- **Missing Star Skills identification** — directly tells the user what to learn next to improve their odds.
- **Plain English interpretation string** — output is ready to display in a UI or chatbot without any post-processing.
- **Data quality flag** — user knows whether the result is based on real data or estimated values, so they can trust it accordingly.
- **Location-level analysis** — allows city-specific competition analysis, e.g., "Data Science in Jaipur" vs national level.
- **Experience band filtering** — ensures you're not comparing entry-level competition with senior-level competition in the same pool.

---

## 9. Disadvantages and How to Improve Them

| Limitation | Problem | Suggested Fix |
|---|---|---|
| **`TYPICAL_SEEKER_SKILLS = 7` is hardcoded** | This number was estimated from Naukri dataset context. If dataset changes or different platform data is used, this baseline becomes wrong and all market overlap scores shift. | Make this a computed value: `median(skill_count of all users in dataset)` if user profiles are available, or calculate it as `median(Skill_Count across all fresher job listings)` as a proxy. |
| **Skill matching uses simple string `in` check** | `"Python" in all_skills_text` will also match "Python3", "CPython", "IronPython" — leading to false positives. Also misses semantic matches like "ML" vs "Machine Learning". | Use tokenized exact matching or fuzzy matching (`rapidfuzz` library). For better semantic matching, use pre-computed skill embeddings (Word2Vec trained on job posting data). |
| **Star Skills extracted by comma-split only** | `star_text.split(',')` assumes skills are always comma-separated in the `Star_Skills` column. If formatting varies, this will generate garbage tokens. | Add a proper skill extraction function with multiple delimiter handling and a skill vocabulary lookup table to validate extracted tokens. |
| **Domain estimation ratios are hardcoded** | The `DOMAIN_RATIO_RANGES` dict has fixed ratios for 6 domains and a generic fallback for everything else. Any new domain uses a generic 15–35 estimate which could be very wrong. | Replace estimation with a model trained on historical applicant data, or compute domain-specific medians directly from the dataset when applicant data IS available and cache them. |
| **`_build_market_baseline()` recalculates on every call** | Every call to `calculate_competition_level()` triggers a full pass over all domains to build the baseline. This is O(n × domains) and becomes slow with large datasets. | Use `self._market_index_cache` (already defined in `__init__` but never used) to store the baseline Series. Invalidate cache only when data changes. |
| **User overlap is binary for qualitative match** | `if skill in all_skills_text` gives 1 or 0 per skill. A user with "Deep Learning" gets 0 match if jobs say "Neural Networks" — even though they're the same thing. | Use a **skill taxonomy / ontology** (e.g., a CSV mapping skill aliases to canonical names) to normalize skills before matching. |
| **No time-weighting in skill overlap** | Skills required in jobs from 2 years ago count equally to skills required this month. An emerging skill like "LLM Fine-tuning" appearing in recent postings is treated the same as an old skill. | Apply recency weighting to `Combined_Skills` aggregation — weight recent postings' skills more heavily when computing `all_skills_text`. |

### Formula Improvement Suggestions

```python
# Current user overlap (fixed 60/40 split):
user_overlap = 0.6 * count_match + 0.4 * qual_match

# Improved: Make the split adaptive.
# When avg_required_skills is high (10+), quality matters more than quantity.
# When avg_required_skills is low (3-5), quantity is less meaningful.
quality_weight = min(0.6, avg_required / 20)   # scales from 0 to 0.6
count_weight   = 1.0 - quality_weight
user_overlap   = count_weight * count_match + quality_weight * qual_match
```

```python
# Current market baseline (simple mean of ratio range for estimation):
estimated_ratio = np.mean(ratio_range)

# Improved: Use median + std from actual data to estimate, with uncertainty flag:
# If we have at least 30 data points for similar domains, compute empirically.
# Flag outputs based on estimated data with lower confidence in the UI.
```

```python
# Current competition index (linear applicant × overlap):
competition_index = (total_applicants * market_overlap_factor) / total_openings

# Improved: Add a recency weight — recent applicants matter more than stale ones:
# Applicants on active listings (< 7 days old) should count more than month-old listings.
# This would require per-listing applicant data, not just domain totals.
```

---

*End of Engine 2 Documentation*

---

---

# Engine 3 — `AverageSalaryRangeCalculator` (Average Salary Range Engine)

**File:** `average_salary_calculator.py`  
**Class:** `AverageSalaryRangeCalculator`

---

## 1. Introduction — What is this Engine and What Does it Do?

When someone asks *"What salary can I expect as a fresher Data Analyst in Bangalore?"*, a naive answer would just average all salaries in the dataset. But that is **deeply misleading** for three reasons:

1. **Old salary data** from 2 years ago doesn't reflect today's market
2. **Outlier entries** like a ₹1/month test record or a ₹1 Crore CXO salary will completely destroy the average
3. **Bangalore's market** pays differently than Jaipur — using national averages for local decisions is wrong

**`AverageSalaryRangeCalculator` solves all three problems** and goes further — instead of giving one "average" number, it gives you the **full salary distribution** (P10 to P90) so a user can see:
- What the bottom earners make (P10)
- What the typical fresher makes (P50 — the median)
- What the top earners make (P90)
- How confident the estimate is (based on sample size)

> Think of it like a salary report card — not just a grade, but the full distribution: "60% of freshers in this role earn between ₹5–8 LPA, the median is ₹6.5 LPA, top performers earn ₹10+ LPA." That's far more useful than "average salary is ₹7 LPA".

It also has a **location adjustment system** — Bangalore salaries for the same role are adjusted separately from Jaipur salaries, using domain-specific comparisons (not a generic city multiplier).

---

## 2. Data Fields Required by This Engine

### Required Columns

| Column Name | What it Means | Required? |
|---|---|---|
| `Avg_Salary` | Average salary for that job posting (in LPA) | ✅ Yes — core calculation column |
| `Min_Experience` | Minimum years of experience required | ✅ Yes — for experience band filtering |
| `Max_Experience` | Maximum years of experience accepted | ✅ Yes — for experience band filtering |

### Optional but Important Columns

| Column Name | What it Means | Fallback if Missing |
|---|---|---|
| `Min_Salary` | Minimum salary offered in job posting | P25 of Raw_Salary_Band will be `None` |
| `Max_Salary` | Maximum salary offered in job posting | P75 of Raw_Salary_Band will be `None` |
| `Job_Type` | Domain/category of the job | Falls back to title text search |
| `Title_Cleaned` | Job title text | Domain matching may fail |
| `TItle_Cleaned` | *(Typo variant)* Auto-fixed to `Title_Cleaned` by engine | Auto-renamed with a warning |
| `Scraped_At_Cleaned` | Date when job was collected | All jobs treated as equal weight |
| `Location` | City/location of the job | Location factor will be 1.0 (no adjustment) |
| `Employment Type` | Full-time / Contract / Part-time | All job types included if column missing |

### Inputs Passed at Runtime

| Parameter | What it Means | Default |
|---|---|---|
| `target_domain` | Domain to analyze (e.g., `"Data Analyst"`) | Required |
| `target_location` | City to filter/adjust for (e.g., `"Bangalore"`) | `None` (national) |
| `experience_band` | Either a string label OR a tuple | `"fresher"` |
| `lambda_val` | Time decay rate (set in `__init__`) | `0.1` |

### Experience Band Options

| Band Label | Experience Range | Who it's for |
|---|---|---|
| `"fresher"` | 0 – 1 year | Fresh graduates, campus placements |
| `"junior"` | 1 – 3 years | Early career professionals |
| `"mid"` | 3 – 6 years | Mid-level roles |
| `(0, 3)` *(tuple)* | Custom range | Passed by pipeline (auto-converted to label) |

---

## 3. Core Logic — How Does the Engine Calculate Salary?

The engine runs **10 sequential steps** to produce the final salary report. Each step builds on the previous one.

---

### Step 1 — Domain Filtering

Finds all job rows that match the `target_domain`:

- **Primary:** Exact match on `Job_Type` column (case-insensitive)
- **Fallback:** Text search in `Title_Cleaned` if `Job_Type` match returns fewer than 5 rows

---

### Step 2 — Employment Type Filter

Removes contract, freelance, and part-time jobs because they pay lower and would drag down the "real" salary picture.

Keywords kept: `full time`, `full-time`, `permanent`, `regular`

> Fallback: If this filter removes too many rows (fewer than 5 left), all employment types are kept.

---

### Step 3 — Experience Band Filter

Segments data to only the relevant career stage. Uses **both** Min and Max experience columns for accurate bracket detection.

```
Band "fresher" → keeps jobs where Min_Experience >= 0 AND Max_Experience <= 2
(the +1 tolerance handles "0-3 yrs" style listings that are clearly for freshers)
```

> Fallback: If fewer than 5 records match, expands filter to `Min_Experience <= max_exp + 2`.

---

### Step 4 — Outlier Removal (IQR Method)

Salary data always has extreme outliers — test entries (₹1/month), CXO roles accidentally included, or data entry errors. These completely break averages.

**Formula:**
```
Q1    = 25th percentile of Avg_Salary
Q3    = 75th percentile of Avg_Salary
IQR   = Q3 - Q1

Lower bound = Q1 - (2.5 × IQR)
Upper bound = Q3 + (2.5 × IQR)

Keep only: Lower bound ≤ Avg_Salary ≤ Upper bound
```

**Why 2.5× and not the standard 1.5×?**

Salary distributions are naturally **right-skewed** — a few high earners in every domain pull the upper tail. Using the standard 1.5× multiplier would incorrectly remove legitimate high salaries. 2.5× keeps genuine high earners while still catching true outliers.

**Plain English Example:**

| Salary Data | Q1 | Q3 | IQR | Lower | Upper | Removed? |
|---|---|---|---|---|---|---|
| ₹0.001 LPA (test entry) | 5 | 10 | 5 | -7.5 | 22.5 | ✅ Removed |
| ₹4 LPA (fresher) | 5 | 10 | 5 | -7.5 | 22.5 | ✅ Kept |
| ₹25 LPA (outlier) | 5 | 10 | 5 | -7.5 | 22.5 | ✅ Removed |

> Safety: If outlier removal leaves fewer than 5 rows, the original (unfiltered) data is used instead.

---

### Step 5 — Time Decay Weighting

Newer salary data reflects current market better than 2-year-old data. Each row gets a **weight** based on how old it is.

**Formula:**
```
months_old    = (max_date_in_data - scraped_date) / 30
decay_weight  = e^(−λ × months_old)
```

**Where λ (lambda) controls how fast older data fades:**

| λ value | Meaning | Use case |
|---|---|---|
| `0.05` | Slow decay — 6-month-old data keeps ~74% weight | Stable markets (e.g., government IT) |
| `0.10` *(default)* | Moderate decay — 6-month-old data keeps ~55% weight | Most domains |
| `0.20` | Fast decay — 6-month-old data keeps ~30% weight | Fast-moving markets (AI/ML) |

**Plain English Example (λ = 0.1):**

| Data Age | Decay Weight | Influence |
|---|---|---|
| Today | 1.00 | Full weight |
| 1 month old | 0.90 | 90% weight |
| 3 months old | 0.74 | 74% weight |
| 6 months old | 0.55 | 55% weight |
| 12 months old | 0.30 | 30% weight |

> If `Scraped_At_Cleaned` column is missing → all records get weight = 1.0 (equal treatment).  
> If a date is unparseable → that record gets weight for "6 months old" as a conservative estimate.

---

### Step 6 — Weighted Percentile Calculation

Instead of a simple median, the engine computes a **weighted percentile** where recent data counts more.

**Formula (midpoint CDF convention):**
```
1. Sort salary values ascending
2. For each value, compute cumulative weight
3. Normalize: CDF = (cumulative_weight - half_of_own_weight) / total_weight
4. Use interpolation to find salary at target percentile
```

Five percentiles are computed: **P10, P25, P50, P75, P90**

**Plain English:**
Think of it like a weighted average, but instead of the mean, we find the "middle" — except the more recent a salary data point is, the heavier it sits on the scale. Old data is lighter and gets pulled toward the edges.

---

### Step 7 — Location Factor Adjustment

**Formula:**
```
Location Factor = Local Domain Median / National Domain Median
Adjusted Median = P50 × Location Factor
```

**Critical Design Choice:**  
Both the local AND national medians are computed **for the same domain** (e.g., "Data Analyst"). This is a bug fix over naive implementations that compared local domain salary against **all-jobs national average** — which was always wrong because domain mix varies by city.

**Plain English Example:**

| Scenario | National Data Analyst Median | Bangalore Data Analyst Median | Location Factor | Adjusted Median |
|---|---|---|---|---|
| Bangalore premium | ₹7.0 LPA | ₹9.1 LPA | 1.30 | ₹9.1 LPA |
| Jaipur discount | ₹7.0 LPA | ₹5.6 LPA | 0.80 | ₹5.6 LPA |
| Same as national | ₹7.0 LPA | ₹7.0 LPA | 1.00 | ₹7.0 LPA |

**Safety cap:** Location factor is clamped between **0.5 and 2.0** — so no city can claim to pay more than 2× or less than 0.5× the national median. Prevents garbage data from producing absurd adjustments.

> Fallback: If fewer than 3 local records exist for that city+domain combination, location factor = 1.0 (national figures used).

---

### Step 8 — Confidence Interval (Statistically Grounded)

**Formula:**
```
Standard Error of Median = 1.253 × std / √n

Margin = 1.645 × Standard Error   (90% confidence interval)
Margin = min(Margin, 0.40 × Median)  ← cap at 40% of median

CI Lower = max(0, Median − Margin)
CI Upper = Median + Margin
```

**Why 1.253?** The standard error of a median is approximately 1.253 times the standard error of the mean for normally distributed data. This makes the confidence interval statistically proper.

**Confidence Label based on sample size:**

| Sample Size | Confidence Label | Meaning |
|---|---|---|
| ≥ 50 records | High | Reliable estimate |
| 20 – 49 records | Medium | Reasonable but verify |
| < 20 records | Low | Use with caution |

**Plain English Example:**

| n | Std Dev | Median | Margin | CI Range | Label |
|---|---|---|---|---|---|
| 100 | 2.5 LPA | 7.0 LPA | ±0.41 | 6.59 – 7.41 | High |
| 25 | 2.5 LPA | 7.0 LPA | ±0.82 | 6.18 – 7.82 | Medium |
| 8 | 2.5 LPA | 7.0 LPA | ±1.45 | 5.55 – 8.45 | Low |

> Smaller samples → wider interval → engine is honest about uncertainty.

---

## 4. Weights and Parameters — What They Mean and Why

| Parameter | Value | Why This Value |
|---|---|---|
| `lambda_val` default | **0.1** | Moderate decay. 6-month-old data still has 55% influence — appropriate for job markets that change quarterly but not weekly. Configurable per use case. |
| IQR multiplier | **2.5×** | Salary distributions are right-skewed. Standard 1.5× removes too many legitimate high earners. 2.5× catches only true outliers (test entries, CXO mix-ins). |
| SE of median constant | **1.253** | Statistically derived — ratio of standard error of median vs mean for normal distributions. Makes the confidence interval formula mathematically correct. |
| CI z-score | **1.645** | Corresponds to 90% confidence interval. Chosen over 95% (z=1.96) because salary data is never perfectly normal — being slightly less conservative is realistic. |
| CI margin cap | **40% of median** | Prevents absurdly wide ranges for very small, noisy datasets. Even with 3 samples, the CI won't span ₹0 to ₹20 LPA. |
| Location factor cap | **0.5 – 2.0** | Real-world cap: no Indian city pays less than half or more than double the national median for the same role. Protects against garbage local data. |
| Min sample for outlier IQR | **4 records** | Need at least 4 points to compute a meaningful Q1/Q3. Below this, outlier removal is skipped. |
| Experience band `+1` tolerance | **+1 year** | A job posting saying "0–3 years" is still a fresher/junior role. The +1 tolerance includes these without expanding the filter too aggressively. |

---

## 5. Functions — What They Do and How They Are Called

```
calculate_salary_metrics()           ← Main entry point (you call this)
    │
    ├── _validate_dataframe()        → Check required columns, fix typos, convert types
    ├── _filter_domain()             → Find rows for target domain (Job_Type or title fallback)
    ├── _filter_employment_type()    → Keep full-time only (removes contract/part-time)
    ├── _filter_experience_band()    → Segment by fresher/junior/mid with fallback expansion
    ├── _remove_salary_outliers()    → IQR-based outlier removal (2.5× multiplier)
    ├── _apply_time_decay()          → Add _weight column using exponential decay formula
    ├── _weighted_percentile()       → Compute P10/P25/P50/P75/P90 using weights
    │       (called 5 times, once per percentile)
    ├── _calculate_location_factor() → Domain-specific local vs national median ratio
    ├── _calculate_confidence_interval() → SE-based CI with sample-size-aware label
    └── _interpret_salary()          → Plain English label for the median value
```

| Function | Role |
|---|---|
| `__init__()` | Sets lambda decay rate, validates it's between 0 and 1 |
| `_validate_dataframe()` | Checks required columns, auto-fixes column typo, converts to numeric |
| `_filter_domain()` | Exact Job_Type match first, title text search fallback |
| `_filter_employment_type()` | Removes part-time/contract to prevent salary deflation |
| `_filter_experience_band()` | Segments by career stage using both Min and Max experience |
| `_remove_salary_outliers()` | IQR-based cleaning with 2.5× multiplier and safety fallback |
| `_apply_time_decay()` | Computes and attaches `_weight` column to each row |
| `_weighted_percentile()` | Core statistical function — computes any weighted percentile |
| `_calculate_location_factor()` | Computes city premium/discount using domain-specific medians |
| `_calculate_confidence_interval()` | Produces statistically proper CI with confidence label |
| `calculate_salary_metrics()` | **Master function** — runs all 10 steps, assembles final output |
| `_interpret_salary()` | Converts median to emoji-labeled plain English for UI |

---

## 6. Output — What Does the Engine Return?

### Sample Output

```json
{
    "Domain": "Data Analyst",
    "Experience_Band": "fresher",
    "Location": "Bangalore",
    "Location_Factor": 1.287,
    "Sample_Size": 63,

    "Market_Range": {
        "Entry_10th":  3.8,
        "Low_25th":    5.2,
        "Median_50th": 6.8,
        "High_75th":   9.1,
        "Top_90th":    12.5
    },

    "Raw_Salary_Band": {
        "Typical_Min": 4.5,
        "Typical_Max": 10.0
    },

    "Location_Adjusted_Median": 8.75,

    "Confidence_Interval": {
        "Min": 7.94,
        "Max": 9.56,
        "Confidence": "High",
        "Sample_Size": 63
    },

    "Interpretation": "✅ Market-standard fresher salary"
}
```

### How to Read This Output

| Field | What it Tells the User |
|---|---|
| `Market_Range.Entry_10th` | Bottom 10% of earners — "floor" salary |
| `Market_Range.Median_50th` | The true middle — half earn more, half earn less |
| `Market_Range.Top_90th` | Top 10% earners — what high performers make |
| `Raw_Salary_Band.Typical_Min/Max` | Range actually advertised in job postings (P25–P75 of posted ranges) |
| `Location_Adjusted_Median` | Median adjusted for your city — **the most actionable number** |
| `Confidence_Interval` | The statistical range we are 90% confident the true median falls within |
| `Location_Factor` | How much your city pays vs national (1.287 = Bangalore pays 28.7% above national) |

### Salary Interpretation Labels (for `"fresher"` band)

| Adjusted Median | Label |
|---|---|
| ≥ ₹10 LPA | 🔥 Above-market entry salary — high-value domain |
| ₹6 – ₹9.9 LPA | ✅ Market-standard fresher salary |
| ₹4 – ₹5.9 LPA | ⚠️ Below-average — negotiate or upskill first |
| < ₹4 LPA | 🚨 Very low — verify data or consider alternatives |

---

## 7. How Robust Are the Formulas and Parameters?

### What Makes Them Solid ✅

| Feature | Why It's Good |
|---|---|
| **Weighted percentile instead of weighted mean** | Mean is destroyed by outliers even after IQR removal. Median (P50) is inherently outlier-resistant. Using weighted percentiles gives the most accurate picture of what a typical person earns. |
| **IQR with 2.5× multiplier** | Correctly handles the right-skewed nature of salary data without over-removing legitimate high earners. |
| **Time decay is configurable (λ parameter)** | Different markets (stable vs fast-moving) need different decay rates. The engine doesn't force one-size-fits-all. |
| **Domain-specific location factor** | Local median compared against SAME domain's national median — not all-jobs average. This is the statistically correct approach. |
| **Statistically grounded CI using SE formula** | CI width automatically adjusts with sample size. Small samples get wider, honest intervals. Previous fixed ±15% was scientifically incorrect. |
| **Full percentile distribution (P10–P90)** | Users see the full range, not just one number. This sets correct expectations — not everyone gets the P75 salary. |
| **Employment type filter** | Contract/freelance jobs genuinely pay less. Removing them gives the salary picture for stable full-time employment, which is what most job seekers want. |
| **Column typo auto-fix** | `TItle_Cleaned` → `Title_Cleaned` auto-rename prevents silent failure from a common data quality issue in the dataset. |
| **Never modifies caller's data** | `df.copy()` in `_validate_dataframe()` ensures the original DataFrame is never changed — critical for pipeline safety when same DataFrame is used by multiple engines. |

---

## 8. Advantages of the Current Implementation

- **Full distribution output** — P10 through P90 gives users a realistic picture of salary spread, not just an average that nobody actually earns.
- **Recency-aware** — time decay ensures salary offers from 18 months ago don't anchor estimates in an outdated market.
- **Location intelligence** — domain-specific city adjustment means "Data Analyst in Jaipur" gives a meaningfully different (and more accurate) result than national averages.
- **Honest uncertainty reporting** — confidence intervals widen with small samples, preventing false precision.
- **Flexible experience band input** — accepts both string labels (`"fresher"`) and tuples (`(0, 3)`) so it works seamlessly whether called from a UI or from another engine in the pipeline.
- **Graceful degradation** — every filtering step has a fallback so the engine returns something useful rather than crashing, even with sparse data.
- **Employment type correction** — prevents contract job salaries from misleading full-time job seekers.

---

## 9. Disadvantages and How to Improve Them

| Limitation | Problem | Suggested Fix |
|---|---|---|
| **`Avg_Salary` assumed to be in LPA** | The engine assumes all salary values are in the same unit (LPA). If the dataset has a mix of monthly and annual figures, results will be completely wrong. There is no unit validation. | Add a unit detection step: if `Avg_Salary` median is > 100, assume monthly (×12 / 100000 to convert to LPA). Add a `salary_unit` column to dataset or validate distribution before calculating. |
| **`TYPICAL_SEEKER_SKILLS = 7` hardcoded in Competition Engine feeds into this engine's domain filter** | The domain filtering logic `_filter_domain()` is copy-pasted from `CompetitionLevelCalculator` — identical code in two places. Any bug fix in one won't automatically apply to the other. | Extract `_filter_domain()` into a shared utility module (e.g., `engine_utils.py`) and import it in both engines. DRY principle — Don't Repeat Yourself. |
| **`_interpret_salary()` thresholds are hardcoded for freshers** | The ₹6 LPA / ₹10 LPA boundaries were set manually. These may not reflect 2026 market realities, especially post-inflation. For non-fresher bands, the function falls back to a plain text with no label. | Compute thresholds dynamically from dataset: "above market" = above P75 of all fresher salaries in dataset. This way thresholds auto-update as market changes. Extend labels for junior/mid bands too. |
| **Location factor minimum 3 records is too low** | With just 3 records for "Data Analyst in Jaipur", the local median is statistically meaningless. A factor computed from 3 records could be 1.8× just by chance. | Increase minimum to at least 10 records. If below threshold, report that location-specific data is unavailable rather than silently using national data with no warning to the user. |
| **No salary trend over time** | The engine gives a snapshot of current salary — it doesn't show whether salaries are going up or down. A fresher in a domain where salaries are declining needs different advice than one in a growing domain. | Add a `salary_trend` output: compute P50 for last 30 days vs 30–60 days ago (same as trend logic in `MarketDemandEngine`) and report direction + percentage change. |
| **`Raw_Salary_Band` uses simple quantiles, not weighted** | `raw_min = band_df['Min_Salary'].quantile(0.25)` ignores the time decay weights computed in Step 6. Inconsistency — some outputs are weighted, some aren't. | Apply the same `_weighted_percentile()` function to `Min_Salary` and `Max_Salary` columns as well, using the `_weight` column already computed. |
| **Confidence label thresholds (50/20) are arbitrary** | "High confidence if n ≥ 50, Medium if ≥ 20" was chosen manually without statistical justification. | Tie confidence labels to the CI width relative to median: if `(CI_Max - CI_Min) / Median < 0.15` → High, `< 0.30` → Medium, else → Low. This is more meaningful than raw sample count. |

### Formula Improvement Suggestions

```python
# Current: fixed 2.5× IQR multiplier for all domains
lower = Q1 - 2.5 * IQR
upper = Q3 + 2.5 * IQR

# Improved: adaptive multiplier based on skewness of salary distribution
# Highly skewed domains (like ML/AI) need wider upper bound
skewness = df['Avg_Salary'].skew()
upper_multiplier = 2.5 + max(0, skewness * 0.3)  # up to ~3.5× for skewed domains
lower_multiplier = 2.5  # keep lower bound strict
lower = Q1 - lower_multiplier * IQR
upper = Q3 + upper_multiplier * IQR
```

```python
# Current: lambda is fixed per engine instance
# e.g., AverageSalaryRangeCalculator(lambda_val=0.1)

# Improved: auto-select lambda based on domain volatility
# If domain's trend score (from MarketDemandEngine) > 7 → use lambda=0.2 (fast decay)
# If domain's trend score < 4 → use lambda=0.05 (slow decay)
# This would require cross-engine communication, suggesting a DataContext object
# shared between engines to pass domain-level metadata.
```

```python
# Current: location factor uses simple median comparison
factor = local_median / national_median

# Improved: use weighted median (with time decay) for BOTH local and national
# to avoid location factor being distorted by old high-salary data in one city
local_weighted_median   = _weighted_percentile(local_domain['Avg_Salary'],  local_weights,  0.5)
national_weighted_median = _weighted_percentile(domain_df['Avg_Salary'], national_weights, 0.5)
factor = local_weighted_median / national_weighted_median
```

---

*End of Engine 3 Documentation*

---

---

# Engine 4 — `JobMarketVelocityCalculator` (Job Market Velocity Engine)

**File:** `job_market_velocity_calculator.py`  
**Class:** `JobMarketVelocityCalculator`

---

## 1. Introduction — What is this Engine and What Does it Do?

The previous engines tell you **what the market looks like right now**. This engine tells you something different and more powerful:

> **"Is this market speeding up, slowing down, or flatlining — and is YOUR city keeping up with the national trend?"**

Think of two domains — both have 200 job postings this month. But:
- Domain A had 50 → 100 → 150 → 200 postings over 4 months. It is **accelerating**.
- Domain B had 300 → 250 → 220 → 200 postings over 4 months. It is **cooling down fast**.

Both look the same today. But Domain A is a better bet for the future.

**`JobMarketVelocityCalculator` captures this momentum.** It divides the last 4 months into 4 equal 30-day windows and studies how job postings have moved across those windows to answer:

1. **How fast is this domain growing/shrinking nationally?** (National Velocity)
2. **How fast is it growing in your specific city?** (Local Velocity)
3. **Is your city keeping up with the national trend, or falling behind?** (Location Intelligence)
4. **Are new companies entering this domain?** (Market Signal — strong early-growth indicator)
5. **Is the growth accelerating or decelerating?** (Acceleration — is momentum building or fading?)

> Think of it like a speedometer — not just your current speed, but whether you are accelerating (foot on gas) or decelerating (foot on brake), and whether the highway ahead is busier than your local road.

---

## 2. Data Fields Required by This Engine

### Required (at minimum one date column must exist)

| Column Name | What it Means | Required? |
|---|---|---|
| `Scraped_At_Cleaned` | Date when job was collected by scraper | ✅ Primary date column |
| `Posted_Date` | Original date job was posted on portal | ✅ Used if available (preferred over scrape date) |

> If neither date column exists, all listings are treated as current and velocity cannot be measured meaningfully.

### Strongly Recommended Columns

| Column Name | What it Means | Fallback if Missing |
|---|---|---|
| `Job_Type` | Domain/category of the job | Falls to title text search |
| `Title_Cleaned` or `TItle_Cleaned` | Job title text | Falls to description search |
| `Location` | City/region of the job | Local velocity cannot be computed |
| `No of job opening cleaned ` | Actual number of open positions | 1 opening assumed per listing |
| `Company_Cleaned` | Company name | New company entrant count = 0 |
| `Min_Experience` | Minimum years of experience | Experience filter skipped |
| `Description_Cleaned` | Full job description text | Description fallback unavailable |

### Inputs Passed at Runtime

| Parameter | What it Means | Default |
|---|---|---|
| `domain_keywords` | List of keywords for the domain (e.g., `["Data Scientist", "ML Engineer"]`) | Required |
| `target_location` | City to analyze locally (e.g., `"Bengaluru"`) | Required |
| `experience_band` | Tuple of `(min_exp, max_exp)` years | `(0, 5)` |
| `nearby_cities` | List of adjacent cities to include in local search (set in `__init__`) | `[]` |
| `use_real_date` | `True` = use today's date as reference; `False` = use max date in data | `True` |

---

## 3. Core Logic — How Does the Engine Calculate Velocity?

The engine works in **3 major stages** — building a time series, extracting metrics from it, then classifying and interpreting the results.

---

### Stage 1 — Building the 4-Window Time Series

The engine creates **4 consecutive 30-day buckets** going backwards from today:

```
Today
 │
 ├── Window "Current" : last 30 days          (most recent)
 ├── Window "T-2"     : 30–60 days ago
 ├── Window "T-3"     : 60–90 days ago
 └── Window "T-4"     : 90–120 days ago       (oldest)
```

For each window, it counts:
- **If `No of job opening cleaned` exists:** Sum of actual openings (1 listing with 50 openings = 50, not 1)
- **Otherwise:** Count of job listings in that window

**Plain English Example:**

| Window | Period | Job Postings |
|---|---|---|
| T-4 | 90–120 days ago | 45 |
| T-3 | 60–90 days ago | 62 |
| T-2 | 30–60 days ago | 89 |
| Current | Last 30 days | 134 |

This series — `[45, 62, 89, 134]` — is the foundation for all velocity calculations.

---

### Stage 2 — Extracting 4 Velocity Metrics

From the time series `[45, 62, 89, 134]`, the engine computes 4 distinct metrics:

---

#### Metric 1 — Recent Growth % (Short-term momentum)

**Formula:**
```
Recent Growth % = ((Current - Previous) / Previous) × 100
```

Measures how this month compares to last month.

**Edge cases handled:**
- Previous = 0 AND Current = 0 → Growth = 0%
- Previous = 0 AND Current > 0 → Growth = 100% (capped) + `is_emerging = True` flag
- Result is clipped between **−200% and +200%** to prevent outlier explosions

**Example:**
```
Previous period = 89 jobs
Current period  = 134 jobs
Recent Growth   = ((134 - 89) / 89) × 100 = +50.6%
```

---

#### Metric 2 — Trend Slope % (Long-term direction)

**Formula:**
```
x          = [0, 1, 2, 3]  (period indices)
counts     = [45, 62, 89, 134]
slope      = coefficient from linear regression (np.polyfit degree=1)
mean_count = average of counts

Trend Slope % = (slope / mean_count) × 100
```

This fits a straight line through all 4 data points and measures how steeply it rises or falls, expressed as a percentage of the mean count.

**Why normalize by mean?** So that a slope of +10 jobs/month means the same thing whether the domain averages 20 jobs/month (50% growth rate) or 1000 jobs/month (1% growth rate).

**Example:**
```
counts = [45, 62, 89, 134]
polyfit slope = +29.4 jobs per period
mean_count    = 82.5
Trend Slope % = (29.4 / 82.5) × 100 = +35.6% per period
```

**Interpretation:** The domain is growing at roughly 35.6% per 30-day window on trend.

---

#### Metric 3 — Acceleration (Is momentum building or fading?)

**Formula:**
```
Step 1: growth_rates = diff(counts) / counts[:-1]
        → how much % did each period grow vs the one before it?

Step 2: acceleration = mean(diff(growth_rates)) × 100
        → are those growth rates themselves increasing or decreasing?
```

This is the **second derivative** — the rate of change of the rate of change.

**Plain English Example:**

| Period | Count | Growth Rate |
|---|---|---|
| T-4 → T-3 | 45 → 62 | +37.8% |
| T-3 → T-2 | 62 → 89 | +43.5% |
| T-2 → Current | 89 → 134 | +50.6% |

Growth rates: `[37.8%, 43.5%, 50.6%]`  
Changes in growth rate: `[+5.7%, +7.1%]`  
Acceleration = mean(`[5.7, 7.1]`) = **+6.4% → Accelerating**

| Acceleration Value | Meaning |
|---|---|
| > +5% | Growth is **accelerating** — momentum building |
| Between −5% and +5% | Growth rate is **steady** |
| < −5% | Growth is **decelerating** — pace slowing down |

---

#### Metric 4 — Volatility % (How stable is the trend?)

**Formula:**
```
Volatility % = (std_dev of counts / mean of counts) × 100
```

This is the **Coefficient of Variation (CV)** — it measures how much the job count bounces around from period to period, regardless of the absolute level.

**Plain English Example:**

| Domain | Counts | Volatility |
|---|---|---|
| Steady domain | [80, 82, 79, 83] | ~2% — very stable |
| Bouncy domain | [20, 90, 30, 100] | ~65% — very volatile |

High volatility means the domain has seasonal spikes or inconsistent hiring — harder to rely on for career planning.

---

### Stage 3 — Velocity Status Classification (6 Tiers)

Based on `Recent Growth %` and `is_emerging` flag:

| Growth % | Status | Signal | Description |
|---|---|---|---|
| Previous = 0, Current > 0 | 🌱 Emerging | `🌱` | New domain appearing in market |
| Within ±5% | ⚖️ Stable | `⚖️` | No significant momentum either way |
| +5% to +30% | 📈 Growing | `📈` | Positive momentum — gradually expanding |
| > +30% | 🔥 Hot | `🔥` | Strong hiring surge |
| −5% to −30% | 📉 Slowing | `📉` | Mild decline — monitor for sustained contraction |
| < −30% | 🧊 Cooling Fast | `🧊` | Sharp decline — hiring has slowed significantly |
| < 5 total samples | ⚪ Insufficient Data | `⚪` | Not enough data for reliable velocity |

**Acceleration modifier** is appended to description:
- Acceleration > +5% → adds: *"Growth is accelerating — momentum building."*
- Acceleration < −5% → adds: *"Growth is decelerating — pace slowing down."*

**Why ±5% noise threshold?** Small fluctuations in scraped data (e.g., 48 vs 50 jobs) are noise, not signal. The 5% buffer prevents the engine from reporting "Slowing" when there's just statistical noise.

---

### Stage 4 — Location Intelligence

Two parallel time series are built — one national, one local — and compared:

#### Local Market Share
```
Current Share % = (local_current_count / national_current_count) × 100
Previous Share % = (local_previous_count / national_previous_count) × 100
Share Change % = Current Share % − Previous Share %
```

**Is local growing share or losing share to other cities?**

#### Velocity Gap (Relocation Signal)
```
National Velocity = mean(pct_change across national windows) × 100
Local Velocity    = mean(pct_change across local windows) × 100
Velocity Gap      = National Velocity − Local Velocity
```

| Velocity Gap | Relocation Signal |
|---|---|
| > +15% | 🚀 National significantly outpacing local — relocation may accelerate opportunities |
| +5% to +15% | 📦 Mild advantage to relocating — metros hiring faster |
| < −5% | 🏠 Local market growing faster than national — strong local opportunity |
| Between −5% and +5% | ⚖️ Local and national markets moving similarly |

---

### Stage 5 — New Company Entrants Signal

Companies newly hiring in a domain in the last 30 days that were NOT hiring in the 30 days before that.

```
recent_companies = set of companies hiring in last 30 days
older_companies  = set of companies that hired in 30–60 days ago
new_entrants     = recent_companies − older_companies  (set difference)
```

**Why this matters:** When new companies start entering a domain, it is one of the earliest signals of genuine market growth — before job posting volume even shows it clearly. A domain where 15 new companies just started posting jobs is a stronger signal than one where the same 5 companies are posting more.

---

## 4. Constants and Parameters — What They Mean and Why

| Constant / Parameter | Value | Why This Value |
|---|---|---|
| `WINDOW_DAYS` | **30** | One calendar month per window — natural hiring cycle. Most companies hire on monthly budget cycles. |
| `N_WINDOWS` | **4** | 4 windows = 4 months of history. Long enough to detect trends, short enough to stay relevant. Going back 6+ months risks including pre-layoff data that no longer reflects the market. |
| `MIN_SAMPLE_PER_PERIOD` | **5** | Below 5 listings per period, velocity cannot be statistically meaningful — too much noise. Returns "Insufficient Data" status. |
| `NOISE_THRESHOLD_PCT` | **5.0%** | Growth/decline within ±5% is treated as noise, not signal. Prevents false positives from minor data fluctuations. |
| Growth cap | **±200%** | Prevents outlier explosions. If a domain had 1 job last month and 10 this month (+900%), it doesn't mean the domain is 9× better. Capped at 200% to keep scores meaningful. |
| Acceleration threshold | **±5%** | Below 5% change in growth rate is considered steady momentum, not a true acceleration signal. |
| Velocity gap threshold | **15% / 5%** | 15% gap = strong relocation signal. 5% = mild signal. Values below both = negligible difference between local and national. |
| Location min sample | **5** *(via `MIN_SAMPLE_PER_PERIOD`)* | If fewer than 5 local listings exist, local velocity is unreliable. |

---

## 5. Functions — What They Do and How They Are Called

```
calculate_velocity()                ← Main entry point (you call this)
    │
    ├── _get_reference_date()       → Decide "today" — real datetime.now() or max(data date)
    ├── _filter_by_domain()         → Find rows matching domain keywords (3-strategy fallback)
    │       └── _apply_experience_filter()  → Narrow to experience band
    │
    ├── _build_time_series()        → Build 4-window count series (national)
    ├── _build_time_series()        → Build 4-window count series (local)
    │
    ├── _calculate_velocity_metrics()  → Extract growth%, slope%, acceleration, volatility
    │       (called twice — once for national, once for local)
    │
    ├── _classify_velocity_status()    → Assign status label + signal emoji
    │       (called twice — national and local)
    │
    ├── _calculate_location_metrics()  → Compute market share, velocity gap, relocation signal
    │
    └── [Inline] New company entrant count
```

| Function | Role |
|---|---|
| `__init__()` | Sets nearby cities list, real vs historical date mode |
| `_get_reference_date()` | Returns today's date OR max date in dataset (for historical replay) |
| `_filter_by_domain()` | 3-priority domain matching: Job_Type → Title regex → Description fallback |
| `_apply_experience_filter()` | Narrows data to specified experience band |
| `_build_time_series()` | Builds the 4-window job count DataFrame |
| `_calculate_velocity_metrics()` | Computes all 4 metrics: recent growth, slope, acceleration, volatility |
| `_classify_velocity_status()` | Maps metrics to 6-tier status labels with noise tolerance |
| `_calculate_location_metrics()` | Market share analysis and relocation signal computation |
| `calculate_velocity()` | **Master function** — orchestrates all steps, returns full report |

---

## 6. Output — What Does the Engine Return?

### Sample Output

```json
{
    "Domain": ["Data Scientist"],
    "Location": "Bengaluru",
    "Experience_Band": [0, 5],
    "Reference_Date": "2026-03-16",

    "National_Velocity": {
        "Status": {
            "status": "Hot",
            "signal": "🔥",
            "description": "Strong hiring surge — companies actively expanding. Growth is accelerating — momentum building."
        },
        "Recent_Growth_Pct": 50.6,
        "Trend_Slope_Pct": 35.6,
        "Acceleration": 6.4,
        "Volatility_Pct": 38.2,
        "Period_Counts": [45, 62, 89, 134],
        "Is_Emerging": false
    },

    "Local_Velocity": {
        "Status": {
            "status": "Growing",
            "signal": "📈",
            "description": "Positive momentum — market is gradually expanding."
        },
        "Recent_Growth_Pct": 18.3,
        "Trend_Slope_Pct": 14.2,
        "Acceleration": 1.2,
        "Period_Counts": [18, 22, 27, 32]
    },

    "Location_Intelligence": {
        "local_openings_30d": 32,
        "national_openings_30d": 134,
        "local_market_share_pct": 23.9,
        "share_change_pct": -2.1,
        "velocity_gap_pct": 21.3,
        "relocation_signal": "🚀 National market significantly outpacing local — relocation may accelerate opportunities.",
        "nearby_cities_included": []
    },

    "Market_Signals": {
        "New_Companies_Entering": 7,
        "Data_Freshness_Days": 0
    },

    "Time_Series": [
        {"period": "T-4", "start": "2025-11-16", "end": "2025-12-16", "count": 45, "listing_ct": 45},
        {"period": "T-3", "start": "2025-12-16", "end": "2026-01-15", "count": 62, "listing_ct": 62},
        {"period": "T-2", "start": "2026-01-15", "end": "2026-02-14", "count": 89, "listing_ct": 89},
        {"period": "Current", "start": "2026-02-14", "end": "2026-03-16", "count": 134, "listing_ct": 134}
    ]
}
```

### How to Read This Output

| Field | What it Tells the User |
|---|---|
| `National_Velocity.Status` | The big picture — is this domain hot, growing, stable, or declining nationally? |
| `National_Velocity.Acceleration` | Is the growth itself speeding up or slowing down? (+6.4 = momentum building) |
| `National_Velocity.Volatility_Pct` | How consistent is the hiring? High volatility = unreliable/seasonal market |
| `Local_Velocity.Status` | Same picture but for your specific city |
| `Location_Intelligence.velocity_gap_pct` | How far behind your city is vs the national trend |
| `Location_Intelligence.relocation_signal` | Direct advice: should you consider moving cities? |
| `Market_Signals.New_Companies_Entering` | How many fresh employers just entered this domain — early growth indicator |
| `Time_Series` | Raw period-by-period counts — can be used to draw a trend chart in the dashboard |

---

## 7. How Robust Are the Formulas and Constants?

### What Makes Them Solid ✅

| Feature | Why It's Good |
|---|---|
| **4-window time series instead of 2-point comparison** | Two-point comparison (this month vs last month) is easily fooled by a single anomalous month. 4 windows reveal the actual trend shape. |
| **Linear regression for slope** | Instead of just comparing endpoints, regression uses all 4 data points — more resistant to noise in any single window. |
| **Acceleration (2nd derivative)** | Detects whether a growing trend is gaining or losing momentum — something that neither slope nor recent growth alone can reveal. |
| **Noise threshold of ±5%** | Prevents the engine from reporting "Slowing" when there's just normal week-to-week variation in scraping volume. |
| **Emerging domain special case** | Properly handles a domain that had 0 postings last month and 15 this month — instead of reporting "+∞% growth", it flags it as "Emerging" with a special signal. |
| **Growth cap at ±200%** | Prevents small-number amplification: going from 1 to 4 jobs is not "+300% growth" in a meaningful sense. |
| **Word boundary regex for title matching** | `\b` boundary prevents "Machine Learning" from matching "no machine learning background required" — a real false positive in naive implementations. |
| **3-strategy domain filter with priority order** | Job_Type → Title regex → Description is a graceful degradation — noisiest strategy (description) only used as last resort, and only for the primary keyword. |
| **`use_real_date` toggle** | Allows the engine to be replayed against historical data for testing — using `max(date)` as the reference point instead of today. |
| **New company entrant detection** | Set-difference logic is an elegant, low-cost leading indicator of genuine market growth. |

---

## 8. Advantages of the Current Implementation

- **Momentum-aware** — unlike all other engines that give static snapshots, this engine shows the market's direction of travel, which is often more important than the current level.
- **Acceleration detection** — knows not just "growing" but "growing faster every month" vs "growing but slowing down" — a crucial distinction for career timing decisions.
- **Local vs national comparison built-in** — gives city-specific advice rather than just national averages, with an explicit relocation signal.
- **Nearby cities expansion** — `nearby_cities` parameter means "Jaipur" can also pick up jobs in Sanganer/Amer, solving the sparse local data problem for tier-2 cities.
- **`Time_Series` in output** — raw period counts are included so the frontend dashboard can directly draw a trend chart without any additional computation.
- **New company entrant signal** — detects genuine market growth early, before job volume metrics catch up.
- **Historical replay mode** — `use_real_date=False` makes the engine testable against past data without changing system time.
- **Word-boundary title matching** — much more precise than simple `str.contains()` used by the other engines.

---

## 9. Disadvantages and How to Improve Them

| Limitation | Problem | Suggested Fix |
|---|---|---|
| **Fixed 30-day window is too coarse** | Hiring has weekly patterns — some industries post heavily on Mondays, others mid-month. A 30-day bucket misses intra-month velocity patterns and can be gamed by when scraping happened. | Add an option for weekly windows (7-day) for domains with dense data, and a 14-day option as a middle ground. Window size could be auto-selected based on total listing count. |
| **`_date` column dependency in new company detection** | The new company entrant code at lines 411–417 checks `if '_date' in domain_df` — but `_date` is only added inside `_build_time_series()`, not on the `domain_df` directly. This is a **silent bug** — `new_companies` will always be 0 even if company data exists. | Move the `_date` computation step before the company entrant block, or refactor `_build_time_series()` to return the annotated DataFrame alongside the summary. |
| **Local series fallback assigns count=0 silently** | Line `national_series.assign(count=0)` silently substitutes a zero-count local series when no `Location` column exists or no local data is found. The output will show "Stable" local velocity (0 growth from 0→0) which looks like real data. | Return an explicit `null` or `"Local_Velocity": null` with a reason string when local data is truly unavailable, so the UI can display "Local data unavailable" instead of misleading stable metrics. |
| **Linear regression slope is sensitive to outliers** | `np.polyfit` (ordinary least squares) is pulled heavily by a single outlier window. One month with a scraping anomaly (e.g., 2× the normal data collected) will skew the slope significantly. | Use **Theil-Sen estimator** (`scipy.stats.theilslopes`) instead — it is the median of all pairwise slopes and is extremely robust to outliers. It is designed exactly for noisy time series like scraped job data. |
| **Volatility uses raw CoV, not normalized** | A domain with `[1, 2, 1, 2]` counts and another with `[100, 200, 100, 200]` get the same CoV (~47%) even though the absolute stability is completely different in hiring terms. | Add an absolute count check: if mean count < 10, label volatility as "Unreliable — low volume" regardless of CoV value. High CoV is only meaningful when base volume is sufficient. |
| **`nearby_cities` join uses OR regex on location string** | `loc_pattern = '|'.join(location_list)` — if `nearby_cities = ["Amer", "Sanganer"]`, it will also match "Amsterdam" and "San Francisco" because the regex has no word boundaries. | Add `\b` word boundaries around each city in the pattern: `r'\b' + city + r'\b'` for each city in the list. |
| **No seasonality correction** | Indian job market has strong seasonal patterns — massive hiring push in Oct–Dec (campus season), slowdown in May–Jun. A domain showing "Cooling Fast" in June might just be seasonal. | Add a **year-over-year comparison** option: compare this month vs same month last year, in addition to month-over-month. This requires 13+ months of historical data. |
| **`Data_Freshness_Days` always 0 in real-time mode** | When `use_real_date=True`, the field `Data_Freshness_Days` is hardcoded to 0. But the actual data could be 15 days stale if scraping ran 2 weeks ago. | Compute `Data_Freshness_Days` as `(pd.Timestamp.now() - max_scrape_date_in_data).days` regardless of `use_real_date` mode. This tells users how fresh the underlying data actually is. |

### Formula Improvement Suggestions

```python
# Current: linear regression slope (sensitive to outliers)
slope = float(np.polyfit(x, counts, 1)[0])

# Improved: Theil-Sen slope (robust to single outlier windows)
from scipy.stats import theilslopes
result = theilslopes(counts, x)
slope = result.slope  # Median of all pairwise slopes — outlier resistant
```

```python
# Current: fixed 4 windows of 30 days each
N_WINDOWS  = 4
WINDOW_DAYS = 30

# Improved: auto-scale windows based on data density
total_listings = len(domain_df)
if total_listings > 500:
    WINDOW_DAYS = 14   # Weekly windows for dense domains
elif total_listings > 100:
    WINDOW_DAYS = 30   # Monthly (current default)
else:
    WINDOW_DAYS = 60   # Bi-monthly for sparse domains
N_WINDOWS = 4          # Always 4 windows regardless of size
# This way the engine always sees 4 comparable periods, but at the right granularity
```

```python
# Current: acceleration as mean of second differences
accel = float(np.diff(growth_rates).mean()) * 100

# Improved: weight recent acceleration more than older acceleration
# A domain that was flat for 3 months but just started accelerating last month
# should get a higher acceleration score than one that peaked 3 months ago
weights = np.array([0.2, 0.8])  # For 2 acceleration points from 3 growth rates
if len(growth_rates) > 1:
    accel_values = np.diff(growth_rates)
    accel = float(np.average(accel_values, weights=weights[-len(accel_values):])) * 100
```

---

*End of Engine 4 Documentation*

---

---

# Engine 5 — `SaturationRiskIndicator` (Saturation Risk Engine)

**File:** `saturation_risk_indicator.py`  
**Class:** `SaturationRiskIndicator`

---

## 1. Introduction — What is this Engine and What Does it Do?

You might have heard someone say: *"Don't go into Web Development — it's too crowded."*

But how do you actually measure "too crowded"? Just counting job applicants is not enough. A domain could have many applicants but also many openings — that's fine. Or it could have few applicants but salaries are falling and companies keep raising the experience bar — that's a warning sign even if application counts look okay.

**`SaturationRiskIndicator` answers one critical question:**

> *"Is this domain becoming too crowded to enter, and is it getting WORSE over time?"*

It measures saturation not from one angle, but from **5 independent signals** — each one capturing a different way a job market can become oversupplied:

1. **Supply vs Demand** — How many people are chasing how many seats right now?
2. **Trend Slope** — Are job postings growing or shrinking month over month?
3. **Experience Barrier** — Are companies raising the entry bar, effectively locking out freshers?
4. **Salary Compression** — Are salaries being squeezed into a narrow band? (When employers have too many candidates, they stop offering competitive pay — this is the economic signal of oversupply.)
5. **Skill Inflation** — Are companies demanding more and more skills over time? (When supply exceeds demand, employers get picky and keep adding requirements.)

Each signal gets a score from **0.0 to 1.0** (0 = no saturation, 1 = fully saturated), then all five are combined with weights to produce a single **Saturation Risk Score**.

> Think of it like a doctor checking 5 vital signs before diagnosing a patient. One bad vital sign doesn't mean the patient is sick — but three or four bad signs together paint a clear picture.

---

## 2. Data Fields Required by This Engine

### Required

| Column Name | What it Means | Required? |
|---|---|---|
| `Job_Type` | Domain/category of the job | ✅ Primary domain filter |
| `Min_Experience` | Minimum experience required | ✅ Used in barrier + filter |
| `Max_Experience` | Maximum experience accepted | ✅ Used in domain filter |

### Strongly Recommended (each powers a specific factor)

| Column Name | Powers Which Factor | Fallback if Missing |
|---|---|---|
| `No of applicant applied cleaned` | Factor 1 — Supply/Demand | Estimated as `listing_count × 15` |
| `No of job opening cleaned ` | Factor 1 — Supply/Demand | 1 opening per listing assumed |
| `Posted_Date` or `Scraped_At_Cleaned` | Factor 2 — Trend Slope | Slope score = 0.5 (neutral) |
| `Min_Salary`, `Max_Salary` | Factor 4 — Salary Compression | Falls back to `Avg_Salary` std |
| `Avg_Salary` | Factor 4 — Compression fallback | Score = 0.5 if fully missing |
| `Skill_Count` | Factor 5 — Skill Inflation | Score = 0.5 (neutral) |

### Inputs Passed at Runtime

| Parameter | What it Means | Default |
|---|---|---|
| `target_domain` | Domain to analyze (e.g., `"Data Scientist"`) | Required |
| `weights` | Custom weights dict (set in `__init__`) | Default weights |

---

## 3. Core Logic — How Does the Engine Calculate Saturation?

The engine computes **5 independent factor scores**, each on a 0.0–1.0 scale, then combines them into a single weighted composite score.

---

### Factor 1 — Supply/Demand Score (Weight: 35%)

**What it measures:** The raw competitive pressure — how many applicants are chasing each opening?

**Formula (when actual data exists):**
```
domain_ratio   = total_applicants / total_openings
f1_score       = fraction of all domains with a lower ratio than this domain
               = percentile rank of this domain in the market
```

**Formula (when applicant/opening data is missing):**
```
domain_ratio = listing_count × 15   (conservative market estimate)
f1_score     = min(1.0, domain_ratio / MAX_SD_RATIO)
             = min(1.0, domain_ratio / 50)
```

**Plain English Example:**

Suppose we have 10 domains in the market. Their applicant/opening ratios are:
`[5, 8, 12, 15, 20, 25, 30, 40, 55, 80]`

"Data Science" has a ratio of 30. How many domains have a **lower** ratio than 30?
→ 6 out of 10 → f1_score = **0.60**

This means "Data Science" is more saturated than 60% of all domains.

**Why percentile ranking instead of fixed thresholds?**
A ratio of 30:1 might be "High" in one dataset and "Medium" in another depending on the overall market. Percentile ranking is self-normalizing — it always measures saturation relative to the current state of the entire market.

**Outlier handling:** Viral job postings (one listing attracting 50,000+ applicants) are clipped at the 95th percentile before summing, so one unusual posting doesn't inflate the whole domain's ratio.

---

### Factor 2 — Trend Slope Score (Weight: 25%)

**What it measures:** Is this domain growing or shrinking? A declining domain is more saturated than a growing one, even if current supply/demand looks acceptable.

**Formula:**
```
Step 1: Group job postings by month → monthly counts time series

Step 2: Fit a straight line (Linear Regression) through all months
        slope = jobs_per_month change (positive = growing, negative = shrinking)

Step 3: Normalize slope as % of mean monthly count
        normalized_slope = slope / mean_monthly_count

Step 4: Map to saturation score using a Sigmoid function
        f2_score = 1 / (1 + e^(5 × normalized_slope))

Step 5: Adjust by R² reliability
        f2_score = f2_score × reliability_weight + 0.5 × (1 − reliability_weight)
        where: reliability_weight = min(1.0, R² × 2)
```

**Why Sigmoid instead of direct mapping?**

| normalized_slope | Sigmoid output | Interpretation |
|---|---|---|
| +1.0 (strong growth) | ~0.007 → near 0 | Very low saturation risk from trend |
| +0.5 | ~0.075 | Low risk |
| 0.0 (flat) | 0.50 | Neutral |
| −0.5 | ~0.924 | High risk |
| −1.0 (strong decline) | ~0.993 → near 1 | Very high saturation from trend |

The sigmoid gives a smooth, continuous score rather than sharp step jumps. A slope of -0.6 and -0.7 give meaningfully different scores (not both just "High").

**R² Reliability Adjustment:**
If the linear fit is poor (R² < 0.3), the trend is unreliable — maybe the data is too noisy or too sparse. In that case, the score is pulled toward neutral (0.5) proportionally:

```
If R² = 0.0 → reliability_weight = 0 → score = 0.5 (fully neutral)
If R² = 0.5 → reliability_weight = 1 → score = full sigmoid value
If R² = 1.0 → reliability_weight = 1 → perfect trend, full weight
```

**Plain English Example:**

| Domain | Slope | R² | Reliability Weight | Final f2_score |
|---|---|---|---|---|
| Data Science | +20 jobs/month | 0.85 | 1.0 | ~0.10 (growing → low risk) |
| Web Dev | −10 jobs/month | 0.70 | 1.0 | ~0.88 (declining → high risk) |
| Blockchain | −5 jobs/month | 0.15 | 0.30 | 0.65 pulled toward 0.5 → 0.55 (unreliable) |

---

### Factor 3 — Experience Barrier Score (Weight: 15%)

**What it measures:** How hard is it for a fresher to enter this domain? High median experience requirement + rising trend = employers crowding out entry-level candidates.

**Formula (base score):**
```
median_exp = median(Min_Experience) for domain
f3_score   = fraction of all domains with lower median experience requirement
           = percentile rank of this domain's experience bar across all domains
```

**Experience Inflation Detection (split-half trend analysis):**
```
Sort all domain listings by date
old_half = first 50% of listings by date
new_half = last 50% of listings by date

old_median_exp = median(Min_Experience of old_half)
new_median_exp = median(Min_Experience of new_half)

if new_median > old_median + 0.5 years → trend = "Rising"   → f3_score += 0.10
if new_median < old_median − 0.5 years → trend = "Falling"  → f3_score −= 0.10
else                                   → trend = "Stable"
```

**Why 0.5 year threshold?** Half a year of experience difference is the smallest meaningful shift in job requirements. Less than this is likely rounding or data noise.

**Plain English Example:**

If "Data Science" median Min_Experience = 2 years, and across all domains the median experience ranges from 0 to 8 years, with 70% of domains requiring less than 2 years:
→ Base f3_score = **0.70**

If over time this domain went from requiring 1.5 years (old postings) to 2.3 years (new postings):
→ new > old + 0.5 → Rising trend → f3_score = 0.70 + 0.10 = **0.80**

**Additional output:** `fresher_pct` — what percentage of domain jobs are open to true freshers (Min_Experience ≤ 1 year). Below 20% triggers an alert.

---

### Factor 4 — Salary Compression Score (Weight: 15%)

**What it measures:** When employers have too many candidates (oversupply), they stop offering competitive, spread-out salaries. Instead they offer a narrow, compressed band — "take it or leave it." Compressed salaries are therefore an indirect economic indicator of market saturation.

**Formula (primary — per-row gap calculation):**
```
For each job posting:
    gap         = Max_Salary − Min_Salary
    midpoint    = (Max_Salary + Min_Salary) / 2
    compression = gap / midpoint    ← normalized by salary level

domain_compression = median(compression across all domain postings)

f4_score = fraction of all domains with a HIGHER compression ratio than this domain
```

**Why per-row gap, not `mean(Max) - mean(Min)`?**

The old approach of `mean(Max) - mean(Min)` computes the gap between two averages. If one posting offers ₹3–15 LPA and another offers ₹6–8 LPA, the row-level gaps are very different (₹12 vs ₹2 LPA), but both contribute equally to the averages. Per-row calculation correctly captures the actual spread each employer is offering.

**Fallback (when Min/Max Salary missing):**
```
cv = std(Avg_Salary) / mean(Avg_Salary)   ← Coefficient of Variation
f4_score = max(0.0, 1 − cv × 2)
```
Low CV = tightly clustered salaries = compressed = high saturation signal.

**Plain English Example:**

| Domain | Typical Posting | Gap | Midpoint | Compression |
|---|---|---|---|---|
| DevOps | ₹8–18 LPA | 10 | 13 | 0.77 (healthy spread) |
| Data Entry | ₹3–4 LPA | 1 | 3.5 | 0.29 (compressed) |

If 80% of all domains have a compression ratio higher than "Data Entry":
→ f4_score = **0.80** (very compressed → high saturation signal)

**Interpretation labels:**
- f4_score > 0.6 → `"Compressed"` (employer's market)
- f4_score > 0.3 → `"Normal"`
- f4_score ≤ 0.3 → `"Healthy spread"` (candidate's market)

---

### Factor 5 — Skill Inflation Score (Weight: 10%)

**What it measures:** When there are more candidates than jobs, employers become picky — they keep adding skill requirements because they can. Rising skill demand over time is therefore a leading indicator of market oversupply.

**Formula (base score):**
```
domain_median_skills = median(Skill_Count) for domain

f5_score = fraction of all domains with a lower median skill count
         = percentile rank of this domain's skill demand
```

**Skill Inflation Trend (split-half analysis — same method as Factor 3):**
```
old_skills = median(Skill_Count of older half of listings)
new_skills = median(Skill_Count of newer half of listings)

if new_skills > old_skills + 1 → trend = "Inflating"  → f5_score += 0.10
if new_skills < old_skills − 1 → trend = "Deflating"  → f5_score −= 0.05
else                           → trend = "Stable"
```

**Why +1 skill threshold?** One additional required skill is the smallest meaningful shift in job requirements that goes beyond column noise or rounding in the dataset.

---

### Final Composite Score

```
Saturation Score = f1 × 0.35
                 + f2 × 0.25
                 + f3 × 0.15
                 + f4 × 0.15
                 + f5 × 0.10
```

All factor scores are 0.0–1.0, so the final score is also 0.0–1.0.

---

## 4. Weights — What They Mean and Why

| Weight | Factor | Value | Justification |
|---|---|---|---|
| `supply_demand` | Factor 1 | **0.35** | The most direct, real-time signal of market crowding. More applicants per opening = harder to get hired. Deserves highest weight because it reflects actual present-day competition. |
| `trend_slope` | Factor 2 | **0.25** | Second most important. A declining domain becomes saturated even before supply/demand ratios worsen — slope is a forward-looking signal. |
| `experience_barrier` | Factor 3 | **0.15** | Important but structural — experience requirements change slowly. Rising barrier means freshers are being locked out, which is a key concern for the target user base. |
| `salary_compression` | Factor 4 | **0.15** | Important economic signal, but can be noisy when salary data is missing or inconsistent. Equal weight to experience barrier. |
| `skill_inflation` | Factor 5 | **0.10** | Lowest weight — a newer, more indirect signal. Skill count data can be incomplete in scraped datasets. Still worth including as a supporting signal. |

**Key constraint:** All weights must sum to 1.0 (±0.02 tolerance). Validated at startup.

---

## 5. Functions — What They Do and How They Are Called

```
get_saturation_risk()                    ← Main entry point (you call this)
    │
    ├── _filter_domain()                 → Get domain rows (experience_band = 0–10, all levels)
    │
    ├── _factor_supply_demand()          → Factor 1: applicant/opening percentile
    ├── _calculate_slope()               → Compute monthly slope + R² for Factor 2
    │       └── _factor_trend()          → Extract slope score from slope_data dict
    ├── _factor_experience_barrier()     → Factor 3: median exp + rising trend check
    ├── _factor_salary_compression()     → Factor 4: per-row compression ratio
    ├── _factor_skill_inflation()        → Factor 5: skill count percentile + trend
    │
    ├── [Inline weighted composite]      → Combine all 5 factors with weights
    │
    ├── _classify_saturation()           → Map score + slope to 5-tier risk label + color
    └── _generate_alerts()               → Build plain-English alert list for UI display
```

| Function | Role |
|---|---|
| `__init__()` | Sets and validates custom or default weights |
| `_validate_weights()` | Ensures weights sum to 1.0 ± 0.02 |
| `_filter_domain()` | Exact Job_Type match with experience band filter |
| `_factor_supply_demand()` | Computes applicant/opening ratio, clips outliers, normalizes by market percentile |
| `_calculate_slope()` | Monthly time series, linear regression, R² reliability check |
| `_factor_trend()` | Thin wrapper — extracts score from slope_data dict |
| `_factor_experience_barrier()` | Median experience percentile + split-half trend + fresher % |
| `_factor_salary_compression()` | Per-row gap/midpoint compression, market-relative, fallback to CV |
| `_factor_skill_inflation()` | Median skill count percentile + split-half inflation trend |
| `get_saturation_risk()` | **Master function** — runs all 5 factors, combines, classifies, generates alerts |
| `_classify_saturation()` | Maps composite score + slope to 5-tier color-coded risk label |
| `_generate_alerts()` | Produces actionable plain-English alert list for each triggered signal |

---

## 6. Output — What Does the Engine Return?

### Sample Output

```json
{
    "Domain": "Data Scientist",
    "Sample_Size": 184,
    "Saturation_Score": 0.612,
    "Risk_Level": "Moderate — Declining",
    "Color_Code": "Yellow",

    "Factor_Breakdown": {
        "Supply_Demand": {
            "score": 0.72,
            "ratio": 38.4,
            "total_openings": 210,
            "data_quality": "Actual"
        },
        "Trend_Slope": {
            "score": 0.61,
            "slope": -3.2,
            "norm_slope": -0.18,
            "r_squared": 0.62,
            "reliable": true,
            "months_analyzed": 8
        },
        "Experience_Barrier": {
            "score": 0.58,
            "median_exp": 2.0,
            "exp_trend": "Rising",
            "fresher_pct": 24.3
        },
        "Salary_Compression": {
            "score": 0.51,
            "compression_ratio": 0.48,
            "median_gap_lpa": 3.2,
            "interpretation": "Normal"
        },
        "Skill_Inflation": {
            "score": 0.43,
            "median_skills": 7.0,
            "skill_trend": "Inflating",
            "market_percentile": 43.0
        }
    },

    "Alerts": [
        "🚨 Very high applicant/opening ratio (38:1). Expect intense competition for every role.",
        "📉 Job postings are declining month-over-month. Market may be contracting.",
        "📈 Experience requirements are rising — entry barrier increasing for freshers.",
        "📚 Skill requirements are increasing over time — market becoming harder to enter."
    ],

    "Signals": {
        "Demand_Trend": "Declining",
        "Trend_Reliable": true,
        "Experience_Barrier": "Normal",
        "Experience_Trend": "Rising",
        "Salary_State": "Normal",
        "Skill_Inflation": "Inflating",
        "Fresher_Pct": 24.3
    }
}
```

### Risk Level Classification

| Saturation Score | Risk Level | Color | Meaning |
|---|---|---|---|
| < 0.25 | Safe Zone | 🟢 Green | Low competition, growing market |
| 0.25 – 0.39 (growing slope) | Low Risk — Growing | 🟡 Light Green | Entry-friendly, positive momentum |
| 0.25 – 0.39 (flat/declining) | Low Risk — Watch | 🟡 Light Green | Low risk but no growth signal |
| 0.40 – 0.59 (unreliable trend) | Moderate Risk | 🟡 Yellow | Mixed signals, data unclear |
| 0.40 – 0.59 (stabilizing slope) | Moderate — Stabilizing | 🟡 Yellow | Recovering from saturation |
| 0.40 – 0.59 (declining slope) | Moderate — Declining | 🟡 Yellow | Getting worse, watch closely |
| 0.60 – 0.74 | High Saturation | 🟠 Orange | Very competitive market |
| ≥ 0.75 | Critically Saturated | 🔴 Red | Avoid or pivot to adjacent roles |

---

## 7. How Robust Are the Formulas and Weights?

### What Makes Them Solid ✅

| Feature | Why It's Good |
|---|---|
| **5 independent signals** | No single metric can fool the engine. A domain might look fine on supply/demand but still score high due to salary compression + skill inflation + rising experience bar — all three indicate the same underlying problem from different angles. |
| **Percentile-based normalization for F1, F3, F5** | Scores are always relative to current market conditions. What counts as "high" saturation automatically adjusts as the overall market changes. |
| **R² reliability adjustment for trend slope** | The trend score is automatically neutralized when the linear fit is poor — prevents false signals from sparse or noisy historical data. |
| **Sigmoid for trend score** | Smooth, continuous output instead of binary "growing/declining". Small differences in slope produce meaningful score differences. |
| **Per-row salary compression** | Correctly measures the spread each employer is actually offering, not a misleading difference-of-means. |
| **Split-half temporal trend analysis for F3 and F5** | Detects rising experience and skill requirements over time — an important early warning signal that simpler snapshots would miss. |
| **95th percentile clipping for applicants** | Viral postings (one listing with 100,000 applicants) cannot distort the domain's supply/demand ratio. |
| **`_generate_alerts()`** | Each triggered condition produces a specific, actionable sentence — not just a score — making the output directly usable in a user-facing UI. |

---

## 8. Advantages of the Current Implementation

- **Multi-angle saturation diagnosis** — using 5 economically meaningful signals rather than just one metric (applicant count) that most tools rely on.
- **Temporal trend detection within factors** — both experience barrier and skill inflation check whether things are getting *worse over time*, not just bad right now. This is a forward-looking design.
- **R²-weighted trend credibility** — the engine self-reports reliability. A trend based on 3 months of data is appropriately discounted vs one based on 12 months.
- **Color-coded output ready for UI** — `Color_Code` and `Risk_Level` strings can be directly consumed by the dashboard without transformation.
- **Actionable alerts** — `_generate_alerts()` produces human-readable messages, not just numbers. Each alert explains both the signal and its implication.
- **Salary compression as economic signal** — this is a sophisticated, indirect indicator of oversupply that most simple saturation tools completely miss.
- **Configurable weights** — a user who only has partial data (e.g., no applicant data) can reduce the `supply_demand` weight and increase others to get a more balanced score given their data availability.

---

## 9. Disadvantages and How to Improve Them

| Limitation | Problem | Suggested Fix |
|---|---|---|
| **`_filter_domain()` returns `None` silently** | The function has only one `return` statement at the end of the `if 'Job_Type'` block. If `Job_Type` column is missing, the function falls through without a `return`, implicitly returning `None`. Line 358 in `get_saturation_risk()` then calls `.empty` on `None`, crashing with `AttributeError`. | Add `return pd.DataFrame()` at the end of `_filter_domain()` as a guaranteed fallback. Also add a title-text fallback strategy like the other engines have. |
| **`_factor_trend()` is a useless wrapper** | `_factor_trend()` simply does `return slope_data["score"]` — a one-line function that adds no logic. This creates the false impression of a full factor calculation when the real work is in `_calculate_slope()`. | Either merge `_factor_trend()` directly into `get_saturation_risk()` (remove the wrapper) or make it do something meaningful, such as applying the R² reliability check within `_factor_trend()` itself rather than inside `_calculate_slope()`. |
| **Split-half trend analysis is sensitive to dataset age** | Both F3 and F5 split the dataset into "older half" and "newer half" by date. But if all data is from the same 2-week scraping window, "older half" and "newer half" differ by days — making the trend detection meaningless. | Add a minimum date range check: only run split-half analysis if `max_date - min_date >= 60 days`. Otherwise return `trend = "Insufficient_History"`. |
| **Supply/Demand estimation `listing_count × 15` is arbitrary** | When actual applicant data is missing, the engine estimates `domain_ratio = listing_count × 15`. This `15` is a hardcoded guess with no data backing. For a domain with 3 listings, the estimated ratio is 45 — which could trigger a "Critically Saturated" label entirely from a made-up number. | Compute this multiplier empirically: when actual data IS available for some domains, take the median of `(actual_applicants / listing_count)` across those domains and use that as the multiplier for domains where data is missing. Cache this computed multiplier. |
| **`MAX_SD_RATIO = 50` fallback is never explained** | When market-wide normalization fails, `f1_score = min(1.0, domain_ratio / 50)` uses 50 as a ceiling. This means a domain with ratio 25 gets f1_score = 0.5 exactly. But 50 was chosen arbitrarily — it has no statistical grounding for Indian job market data. | Compute this ceiling dynamically: use the 95th percentile of all observed supply/demand ratios across all domains as the saturation ceiling. Update it every time new data is processed. |
| **No location filter in saturation analysis** | `get_saturation_risk()` does not accept a `location` parameter. A domain could be saturated nationally but undersupplied in a specific city. The score is always a national-level signal. | Add an optional `location` parameter with the same minimum sample fallback logic used in the other engines. |
| **Salary compression fallback is inverted** | When Min/Max Salary are missing and the engine falls back to `Avg_Salary` std: `f4_score = max(0.0, 1 - cv * 2)`. A high CV (wide salary spread) gives a LOW score — meaning "low saturation". But a high CV in `Avg_Salary` could also mean the dataset contains a mix of fresher and senior roles — wide spread from poor filtering, not genuine healthy spread. | When using the CV fallback, first ensure the data has been properly filtered to the relevant experience band before computing `Avg_Salary` std. |
| **Alerts have no priority ordering** | `_generate_alerts()` appends alerts in the order factors are checked. The most important alert (e.g., critically high supply/demand ratio) may not appear first. | Sort alerts by severity before returning. Define a severity rank for each alert type and sort descending. This ensures the most actionable warning appears at the top in the UI. |

### Formula Improvement Suggestions

```python
# Current: Sigmoid centered at 0 with fixed steepness of 5
f2_score = 1 / (1 + np.exp(5 * normalized_slope))

# Improved: Make steepness adaptive to R²
# If R² is high (reliable trend), use steeper sigmoid (sharper distinction)
# If R² is low (noisy trend), use flatter sigmoid (less decisive)
steepness = 5 * min(1.0, r_squared * 1.5)  # scales from 0 to 7.5
f2_score = 1 / (1 + np.exp(steepness * normalized_slope))
# This way, a reliable strong downtrend gets a very high score,
# while an unreliable mild downtrend gets a gentler score — without the hard R² blend.
```

```python
# Current: per-row compression normalized by midpoint
valid['_compression'] = valid['_gap'] / valid['_mid'].replace(0, np.nan)

# Improved: Weight recent postings more in computing domain_compression
# (same time-decay idea as AverageSalaryRangeCalculator)
# Recent compression matters more than 2-year-old compression
valid['_date'] = pd.to_datetime(valid.get('Scraped_At_Cleaned'), errors='coerce')
max_date = valid['_date'].max()
valid['_months_old'] = ((max_date - valid['_date']).dt.days / 30).clip(lower=0).fillna(6)
valid['_weight'] = np.exp(-0.1 * valid['_months_old'])
domain_compression = np.average(valid['_compression'].dropna(), 
                                 weights=valid.loc[valid['_compression'].notna(), '_weight'])
```

```python
# Current: flat 0.10 penalty for rising experience trend
if new_median > old_median + 0.5:
    f3_score = min(1.0, f3_score + 0.1)

# Improved: scale penalty proportional to how much the bar rose
# A 0.6-year rise gets a small penalty; a 3-year rise gets a large one
rise = new_median - old_median
penalty = min(0.25, rise * 0.08)   # max 0.25 penalty cap
f3_score = min(1.0, f3_score + penalty)
```

---

*End of Engine 5 Documentation*

---


---

# Engine 6 — `DomainStabilityEngine` (Domain Stability Engine)

**File:** `domain_stability_engine.py`  
**Class:** `DomainStabilityEngine`

---

## 1. Introduction — What is this Engine and What Does it Do?

Every other engine in this pipeline answers short-term questions: *How many jobs right now? How fast is it growing this month? How saturated is it today?*

This engine asks a fundamentally different question:

> *"If I invest 1–2 years of my life learning this domain, will it still be a viable career when I come out the other side?"*

**`DomainStabilityEngine` measures long-term career safety.** It is built for someone standing at a crossroads — a fresher choosing their first domain, or a professional deciding whether to upskill. Short-term demand spikes mean nothing if the domain is structurally declining or will be automated away in 4 years.

It measures stability from **5 independent dimensions**:

1. **Trend Stability** — Is the long-term demand trajectory going up, down, or flat? (Uses months of data, not days)
2. **Volatility** — Is hiring consistent month-to-month, or does it spike and crash unpredictably?
3. **AI Resistance** — How likely is this role to be automated? Analyzed from actual skill requirements in job postings, not just gut-feel guesses.
4. **Salary Stability** — Are salaries growing, stagnant, or shrinking? A shrinking salary signals employer power — which means oversupply or disruption.
5. **Supply Health** — Is there a healthy, sustainable balance between candidates and openings? (Too many OR too few is bad)

The output is a **Stability Score (0.0–1.0)** and a **12-month projection** showing where the domain is headed.

> Think of it like evaluating a city before deciding to buy a house there. You wouldn't just check today's property price — you'd check the city's economic trend, how stable employment is, whether AI or automation is going to replace the main local industry, whether salaries are growing, and whether it's attracting or losing talent. That's exactly what this engine does for job domains.

---

## 2. Data Fields Required by This Engine

### Minimum Required

| Column Name | What it Means | Required? |
|---|---|---|
| `Job_Type` | Domain/category of the job | ✅ Primary domain filter |
| `Posted_Date` or `Scraped_At_Cleaned` | Date of job posting (either works) | ✅ Needed for all time-series factors |

> The engine needs at least **3 months** of data to compute a trend. With fewer than 3 months, it returns an error.

### Strongly Recommended Columns

| Column Name | Powers Which Factor | Fallback if Missing |
|---|---|---|
| `Title_Cleaned` (or `TItle_Cleaned`) | Domain filter fallback | Engine may miss domain matches |
| `No of job opening cleaned ` | Trend, Volatility — actual openings | 1 opening per listing assumed |
| `Min_Experience`, `Max_Experience` | Domain filter accuracy | Filter skipped |
| `Combined_Skills` | AI Risk — Source 1 (skill composition) | Falls to domain lookup or structural |
| `Skill_Count` | AI Risk — Source 3 (structural proxy) | Structural risk defaults to 0.4 |
| `Avg_Salary` or `Min_Salary` | Salary Stability factor | Score defaults to 0.5 (neutral) |
| `No of applicant applied cleaned` | Supply Health factor | Score defaults to 0.5 (neutral) |

### Inputs Passed at Runtime

| Parameter | What it Means | Default |
|---|---|---|
| `target_domain` | Domain to analyze (e.g., `"Data Scientist"`) | Required |
| `weights` | Custom weight dict (set in `__init__`) | Default weights |

---

## 3. Core Logic — How Does the Engine Calculate Stability?

The engine builds a **monthly time series** of job counts first, then derives 5 factor scores from it and from the raw data.

---

### Pre-step — Building the Monthly Time Series

Before any factor is calculated, the engine builds two time series:

**Job Count Series:**
```
For each month in the dataset:
    count = sum of actual openings (or listing count if no openings column)

Special handling:
    → Current (incomplete) month is TRIMMED from the series
    → Why: If today is March 16th, March only has 16 days of data
           but looks like a "low count" month — misleading
```

**Salary Series:**
```
For each month:
    monthly_median_salary = median(Avg_Salary or Min_Salary)
```

---

### Factor 1 — Trend Stability Score (Weight: 30%)

**What it measures:** Is the long-term job demand going up, down, or staying flat? Uses all available months of data to fit a trend line and projects 12 months forward.

**Formula:**
```
Step 1: Fit linear regression on monthly job counts
        slope = jobs added (or lost) per month

Step 2: Normalize slope
        norm_slope = slope / mean_monthly_count

Step 3: Sigmoid mapping → trend_score
        trend_score = 1 / (1 + e^(−norm_slope × 10))

Step 4: R² reliability adjustment
        reliability = min(1.0, R² × 2)
        trend_score = trend_score × reliability + 0.5 × (1 − reliability)

Step 5: 12-month projection
        If ≥ 6 months of data:
            projected_count = model.predict(current_month + 12)
            projection_12m_pct = (projected_12m − current) / current × 100
        Else:
            projection_12m_pct = norm_slope × 12 × 100  (simple estimate)
```

**Direction labels with noise tolerance (±2% monthly = "Stable"):**

| Normalized Slope | Direction Label |
|---|---|
| abs(norm_slope) < 0.02 | Stable |
| 0.02 – 0.05 | Mild Growth |
| > 0.05 | Strong Growth |
| −0.02 to −0.05 | Mild Decline |
| < −0.05 | Strong Decline |

**Sigmoid behavior for trend score:**

| norm_slope | trend_score | Interpretation |
|---|---|---|
| +0.5 (strong growth) | ~0.993 → near 1.0 | Very stable trend |
| +0.1 | ~0.731 | Moderately stable |
| 0.0 (flat) | 0.500 | Neutral |
| −0.1 | ~0.269 | Mildly unstable |
| −0.5 (strong decline) | ~0.007 → near 0.0 | Very unstable trend |

> **Important difference from `SaturationRiskIndicator`:** This engine uses `exp(−slope × 10)` — positive slope gives HIGH score (stable). The saturation engine uses `exp(+slope × 5)` — positive slope gives LOW score (low saturation). The sigmoid is intentionally inverted between the two engines because they measure opposite things.

---

### Factor 2 — Volatility Score (Weight: 20%)

**What it measures:** How consistent is monthly hiring? A domain where jobs appear in bursts and then disappear is unreliable for career planning, even if the long-term trend is flat.

**Formula (Detrended Coefficient of Variation):**
```
Step 1: Fit linear regression on monthly counts to get the trend line
Step 2: residuals = actual_counts − trend_line_values
Step 3: cv (detrended) = std(residuals) / mean(monthly_counts)
Step 4: volatility_score = clip(cv, 0, 1.5) / 1.5
Step 5: stability_contribution = 1 − volatility_score
```

**Why detrended CV, not plain CV?**

Plain CV measures total variation — but a domain that is steadily growing by 20 jobs/month will show high plain CV just because of the growth, not because of noise. Detrended CV removes the trend first and measures only the irregular noise around it.

**Plain English Example:**

| Domain | Monthly Counts | Plain CV | Detrended CV | Meaning |
|---|---|---|---|---|
| Steady grower | [50, 70, 90, 110] | High (due to growth) | ~0.01 | Actually very stable |
| Volatile flat | [50, 90, 40, 100] | ~0.40 | ~0.40 | Genuinely volatile |

**Volatility interpretation labels:**

| Volatility Score | Stability Score | Label |
|---|---|---|
| < 0.20 | > 0.80 | Very stable — consistent monthly demand |
| 0.20 – 0.40 | 0.60 – 0.80 | Mildly volatile — normal seasonal variation |
| 0.40 – 0.60 | 0.40 – 0.60 | Moderately volatile — noticeable hiring cycles |
| > 0.60 | < 0.40 | Highly volatile — unpredictable hiring patterns |

---

### Factor 3 — AI Resistance Score (Weight: 25%)

**What it measures:** How likely is this role to be partially or fully automated in the next 3–10 years? This is the most unique factor in this engine — it directly addresses the structural career risk of AI disruption.

AI risk is computed from **3 sources in priority order:**

---

#### Source 1 — Skill Composition Analysis (from actual job postings)

The engine scans all skill keywords that appear in `Combined_Skills` across the domain's job postings and looks up each skill's automation risk from the `SKILL_AUTOMATION_RISK` dictionary.

**Formula:**
```
For each skill keyword in SKILL_AUTOMATION_RISK:
    count = how many times this keyword appears in all domain job postings
    weighted_risk += risk_value × count
    total_weight  += count

skill_based_risk = weighted_risk / total_weight
```

**Plain English Example:**

A "Data Analyst" domain's job postings mention: `excel` (40 times), `python` (25 times), `sql` (30 times), `machine learning` (10 times).

| Skill | Count | Risk Value | Contribution |
|---|---|---|---|
| excel | 40 | 0.65 | 26.0 |
| python | 25 | 0.20 | 5.0 |
| basic sql | 30 | 0.55 | 16.5 |
| machine learning | 10 | 0.12 | 1.2 |
| **Total** | **105** | — | **48.7** |

`skill_based_risk = 48.7 / 105 = 0.464` → 46.4% AI risk

---

#### Source 2 — Domain Lookup (from `DOMAIN_BASE_RISK` dictionary)

If the target domain name matches a known domain (partial or full string match):

```python
for known_domain, risk in DOMAIN_BASE_RISK.items():
    if known_domain in domain_lower or domain_lower in known_domain:
        domain_risk = risk
        break
```

**Sample risk values:**

| Domain | AI Risk | Reason |
|---|---|---|
| `data entry` | 88% | Fully automatable — repetitive, codifiable |
| `data analyst` | 35% | High Excel/SQL use, but judgment required |
| `ml engineer` | 10% | Builds the automation — low self-replacement risk |
| `cybersecurity` | 8% | Adversarial, creative — hard to automate |
| `web developer` | 30% | Templated work increasingly AI-assisted |

---

#### Source 3 — Structural Risk Proxy (from `Skill_Count`)

A role that requires many diverse skills is harder to automate — automation works best on narrow, repetitive tasks.

**Formula:**
```
structural_risk = max(0.05, 0.7 − (median_skill_count × 0.04))
```

| Median Skills Required | Structural Risk |
|---|---|
| 5 skills | 0.50 (medium risk) |
| 10 skills | 0.30 (lower risk) |
| 15 skills | 0.10 (low risk) |
| 17+ skills | 0.05 (minimum floor) |

---

#### Combining All 3 Sources

| Sources Available | Formula |
|---|---|
| All 3 (skill + domain + structural) | `0.50 × skill_risk + 0.35 × domain_risk + 0.15 × structural_risk` |
| Skill + structural only | `0.60 × skill_risk + 0.40 × structural_risk` |
| Domain + structural only | `0.65 × domain_risk + 0.35 × structural_risk` |
| Structural only | `structural_risk` |

Final risk is clipped between 0.03 and 0.95 — no domain is ever 0% or 100% risk.

**AI Resistance Score** (used in the composite) = `1 − final_risk`

**AI Risk Labels:**

| Risk % | Label |
|---|---|
| < 15% | 🟢 Very Low — Highly creative/strategic role |
| 15–30% | 🟡 Low — Some automatable tasks but core is safe |
| 30–50% | 🟠 Moderate — Significant automation risk in 5–10 years |
| 50–70% | 🔴 High — Many tasks automatable now or soon |
| > 70% | 🚨 Very High — Role likely disrupted within 3–5 years |

---

### Factor 4 — Salary Stability Score (Weight: 15%)

**What it measures:** Is the domain's salary growing, stagnant, or declining? Declining salaries are a structural warning sign — they indicate employer power is increasing, which happens when there is oversupply or when the role is becoming commoditized.

**Formula:**
```
Build monthly median salary series
Fit linear regression on monthly median salaries
monthly_slope_pct = (slope / base_salary) × 100
annual_pct        = monthly_slope_pct × 12
```

**Score mapping (fixed thresholds):**

| Annual Salary Growth | Score | Interpretation |
|---|---|---|
| > +15%/yr | 0.9 | Domain in high demand — salaries rising fast |
| +5% to +15%/yr | 0.7 | Healthy salary growth |
| 0% to +5%/yr | 0.5 | Stagnant but positive — neutral |
| −5% to 0%/yr | 0.3 | Mildly declining — watch |
| < −5%/yr | 0.1 | Salary compression — strong instability signal |

**Outlier handling:** IQR method (1.5×) applied to monthly salary values before regression, preventing one unusual high-salary month from skewing the slope.

---

### Factor 5 — Supply Health Score (Weight: 10%)

**What it measures:** Is there a healthy, sustainable ratio of candidates to openings? This factor is different from the `SaturationRiskIndicator` — it uses **absolute thresholds** rather than percentile ranking, because for stability assessment, there are universal healthy zones (too low or too high are both warning signs).

**Formula:**
```
ratio = total_applicants / total_openings
```

**Score mapping (absolute thresholds):**

| Ratio | Score | Interpretation |
|---|---|---|
| < 5:1 | 0.30 | Under-interest — domain may be dying or unknown |
| 5:1 – 30:1 | 0.80 | Healthy competition — sustainable market |
| 30:1 – 60:1 | 0.60 | Elevated but manageable |
| 60:1 – 100:1 | 0.35 | High saturation — unstable for newcomers |
| > 100:1 | 0.15 | Extreme saturation |

**Why is too-low also penalized?** A domain with only 3 applicants per opening is not "easy to get into" — it signals that nobody wants the job, which usually means the domain is fading or poorly compensated. A healthy market needs enough candidate interest to stay vibrant.

---

### Final Composite Score

```
Stability Score = trend_score   × 0.30
               + vol_score      × 0.20
               + ai_score       × 0.25
               + sal_stab_score × 0.15
               + supply_score   × 0.10
```

Score is clipped to `[0.0, 1.0]`.

---

## 4. Weights — What They Mean and Why

| Weight | Factor | Value | Justification |
|---|---|---|---|
| `trend_stability` | Factor 1 | **0.30** | Highest weight — long-term demand trajectory is the most fundamental indicator of career safety. A domain that is reliably growing will absorb more people over time. |
| `ai_resistance` | Factor 3 | **0.25** | Second highest — AI disruption is the defining career risk of the 2020s–2030s. A domain with 70%+ automation risk is a long-term bet against the trend regardless of other signals. |
| `volatility` | Factor 2 | **0.20** | Third — career planning requires predictability. A domain that bounces violently month-to-month makes financial planning, job searching, and retention all harder. |
| `salary_stability` | Factor 4 | **0.15** | Fourth — salary trends are a lagging signal of fundamental supply/demand shifts. Important but responds slowly, so lower weight. |
| `supply_health` | Factor 5 | **0.10** | Lowest — supply/demand ratio is already captured partly by Trend and Saturation engines. Here it serves as a final sanity check on whether the market is attracting enough interest to remain healthy. |

---

## 5. Functions — What They Do and How They Are Called

```
calculate_stability_score()          ← Main entry point (you call this)
    │
    ├── _filter_domain()             → Job_Type exact match, then title word-boundary
    ├── _build_monthly_series()      → Monthly job count series (trims current month)
    ├── _build_salary_series()       → Monthly median salary series
    │
    ├── _calculate_trend_metrics()   → Sigmoid trend score + R² + 12M projection
    ├── _calculate_volatility_score() → Detrended CV → stability contribution
    ├── _calculate_ai_risk()         → 3-source AI automation risk (skill + domain + structural)
    ├── _calculate_salary_stability() → Salary regression slope → annual growth %
    ├── _calculate_supply_health()   → Absolute ratio → score mapping
    │
    ├── [Inline weighted composite]  → Combine all 5 factors
    ├── _classify_stability()        → Map score + direction → 5-tier label + color
    └── _generate_alerts()           → Plain-English alert list for each triggered signal
```

| Function | Role |
|---|---|
| `__init__()` | Sets and validates weights, sets up logger |
| `_validate_weights()` | Ensures weights sum to 1.0 ± 0.02 |
| `_filter_domain()` | Job_Type exact match first, title word-boundary fallback, auto-fixes column typo |
| `_build_monthly_series()` | Groups by month, uses actual openings, trims incomplete current month |
| `_build_salary_series()` | Monthly median of `Avg_Salary` or `Min_Salary` |
| `_calculate_trend_metrics()` | Linear regression + normalized slope + sigmoid + R² blend + 12M projection |
| `_calculate_volatility_score()` | Detrended CV (removes trend before measuring noise), maps to stability |
| `_calculate_ai_risk()` | 3-source AI risk: skill-weighted → domain lookup → structural proxy, adaptive blending |
| `_label_ai_risk()` | Converts risk % to emoji-labeled 5-tier string |
| `_calculate_salary_stability()` | Monthly salary regression → annual growth % → fixed threshold score |
| `_calculate_supply_health()` | Absolute ratio thresholds — both low AND high are penalized |
| `calculate_stability_score()` | **Master function** — orchestrates all steps, builds full output |
| `_classify_stability()` | Maps composite score + trend direction to 5-tier color-coded label |
| `_generate_alerts()` | Actionable plain-English alerts for each triggered condition |

---

## 6. Output — What Does the Engine Return?

### Sample Output

```json
{
    "Domain": "Data Scientist",
    "Sample_Size": 184,
    "Months_Analyzed": 9,
    "Stability_Score": 0.712,
    "Status": "📈 Growing Stable",
    "Color_Code": "Light Green",

    "Factor_Breakdown": {
        "Trend_Stability": {
            "slope_normalized": 0.067,
            "r_squared": 0.74,
            "trend_score": 0.843,
            "direction": "Strong Growth",
            "projection_12m_pct": 38.2,
            "reliable": true,
            "months_analyzed": 9
        },
        "Volatility": {
            "score": 0.712,
            "cv": 0.217,
            "volatility_raw": 0.288,
            "interpretation": "Mildly volatile — normal seasonal variation"
        },
        "AI_Resistance": {
            "score": 0.820,
            "risk_pct": 18.0,
            "risk_label": "🟡 Low — Some automatable tasks but core is safe",
            "source": "skill_composition + domain_lookup + structural",
            "skill_based_risk": 0.162,
            "domain_base_risk": 0.180
        },
        "Salary_Stability": {
            "score": 0.7,
            "annual_pct": 8.4,
            "interpretation": "Salaries growing at 8.4%/yr"
        },
        "Supply_Health": {
            "score": 0.80,
            "ratio": 22.4,
            "interpretation": "22 applicants per opening — Healthy"
        }
    },

    "Alerts": [
        "✅ No major stability concerns detected."
    ],

    "Summary": {
        "Trend_Direction": "Strong Growth",
        "Trend_Reliable": true,
        "AI_Risk_Pct": 18.0,
        "AI_Risk_Label": "🟡 Low — Some automatable tasks but core is safe",
        "Volatility_Level": "Mildly volatile — normal seasonal variation",
        "Salary_Trend": "Salaries growing at 8.4%/yr",
        "12M_Projection_Pct": 38.2
    }
}
```

### Stability Classification

| Stability Score | Status | Color |
|---|---|---|
| ≥ 0.80 | 🟢 Highly Stable | Green |
| 0.65 – 0.79 (+ growth direction) | 📈 Growing Stable | Light Green |
| 0.65 – 0.79 (other) | 🟡 Mostly Stable | Light Green |
| 0.50 – 0.64 | ⚖️ Moderate Stability | Yellow |
| 0.35 – 0.49 (+ decline direction) | 📉 Declining | Orange |
| 0.35 – 0.49 (other) | 🟠 At Risk | Orange |
| < 0.35 | 🔴 High Risk — Avoid Long-Term Bet | Red |

---

## 7. How Robust Are the Formulas and Constants?

### What Makes Them Solid ✅

| Feature | Why It's Good |
|---|---|
| **Incomplete month trimming** | A critical data quality fix that most time-series analyses miss. Without this, the current month always appears as a "low count" month because it only has data for part of the month — causing false "declining" trend signals. |
| **Detrended CV for volatility** | Measuring noise *after* removing the trend is the statistically correct way to separate genuine volatility from growth. Plain CV conflates the two. |
| **3-source AI risk with adaptive blending** | Uses skill-composition data from actual job postings as the primary source — much more accurate than relying only on a fixed domain lookup table. The fallback chain means it always produces a value even with minimal data. |
| **Skill-count structural proxy** | A domain requiring 15 diverse skills is genuinely harder to automate than one requiring 3. This is a data-driven proxy for role complexity. |
| **Supply health penalizes BOTH extremes** | A ratio of 2:1 gets a low score (0.3), not a high one. This correctly identifies dying or obscure domains that look "easy to enter" but are actually shrinking. |
| **12-month projection output** | Gives a concrete, forward-looking number ("+38.2% in 12 months") rather than just a current-state score — directly actionable for career planning. |
| **R² reliability blend** | Consistent across engines — unreliable trends are automatically neutralized rather than producing false precision. |
| **Word-boundary regex in domain filter** | `re.escape()` is used before applying the pattern — prevents regex injection if domain name contains special characters like `C++`. |

---

## 8. Advantages of the Current Implementation

- **Only engine with AI disruption analysis** — directly addresses the most important long-term career risk that no other engine in the pipeline covers.
- **3-source AI risk fusion** — skill-composition analysis from actual postings is far more accurate than simple domain-level lookup tables used in most tools.
- **Detrended volatility** — correctly separates growth-driven variation from genuine instability.
- **12-month forward projection** — gives users a concrete number to act on, not just a label.
- **Incomplete month trimming** — a subtle but important data quality fix that prevents the current partial month from misleading the trend.
- **Supply health dual-sided scoring** — correctly flags dying domains as unstable, not "easy to enter."
- **Configurable weights** — a policy-maker focused on automation risk could weight `ai_resistance` at 0.50 without changing any code.
- **`re.escape()` in domain filter** — production-safe regex pattern construction.

---

## 9. Disadvantages and How to Improve Them

| Limitation | Problem | Suggested Fix |
|---|---|---|
| **`SKILL_AUTOMATION_RISK` and `DOMAIN_BASE_RISK` are fully hardcoded** | These risk values were manually chosen based on Oxford/McKinsey research from a particular point in time. AI automation is moving fast — "frontend" risk was probably 0.15 in 2018 and is realistically 0.50+ in 2026. Hardcoded values become dangerously stale. | Connect to an external, periodically-updated automation risk dataset (e.g., OECD automation risk scores, or retrain from GPT-4/Claude job displacement research). Alternatively, store these in a config JSON file that can be updated without code changes. |
| **Skill-based AI risk uses simple `str.count()` keyword matching** | `all_skills_text.count('python')` will count every occurrence of "python" in the combined skills text — including "python scripting", "python 3.10", "core python" etc. This inflates the count for some skills and underweights others. | Tokenize the skills text properly using comma/semicolon splitting (since `Combined_Skills` is likely a comma-separated list), then do exact token matching rather than substring counting. |
| **Salary stability uses fixed threshold score mapping** | The score jumps from 0.3 to 0.5 to 0.7 to 0.9 in fixed steps. A domain growing at 4.9%/yr gets 0.5, while one at 5.1%/yr gets 0.7 — a 0.2% real difference causes a 0.2 score jump. This is a cliff-edge scoring problem. | Replace fixed thresholds with a continuous sigmoid or piecewise-linear function: `score = clip(0.1 + annual_pct * 0.04, 0.1, 0.9)` — smooth and monotonic. |
| **Domain filter minimum threshold is `MIN_MONTHS × 3 = 9` records** | This is unusually strict — most other engines use 5 as the minimum. Domains with 8 job listings will fail the Job_Type filter and fall through to the noisy title regex search, which is less accurate. | Set minimum threshold independently per filter strategy: Job_Type needs at least 9 records (for trend reliability), but title fallback should still work with 5+. |
| **`_build_salary_series()` prefers `Avg_Salary` over `Min_Salary`** | `Avg_Salary` is often a computed field that may itself be inaccurate. `Min_Salary` is a raw scraped value and more reliable. The priority order in the loop should be reversed. | Change loop order to `['Min_Salary', 'Avg_Salary']` so raw scraped data takes priority over computed averages. |
| **AI risk source blending weights are hardcoded** | The combination `0.50 × skill_risk + 0.35 × domain_risk + 0.15 × structural_risk` was chosen manually. When skill-composition data is available from 500+ postings it is very reliable; when available from only 15 postings it is noisy. Both situations use the same weight. | Scale the `skill_based_risk` weight proportionally to the number of skill keywords matched: more data → higher weight for skill_based, less data → higher weight for domain_risk as the more reliable baseline. |
| **No historical validation of AI risk predictions** | The engine produces AI risk values (e.g., "Data Entry = 88% risk") but there is no mechanism to validate whether these predictions match actual hiring patterns over time — e.g., did Data Entry job postings actually decline as predicted? | Add a backtesting function that compares AI risk labels from 12–24 months ago against actual trend_direction observed since then. Domains predicted as "Very High Risk" should show "Strong Decline" trend if the risk scores are valid. |

### Formula Improvement Suggestions

```python
# Current: fixed score steps for salary stability
if annual_pct > 15:    score = 0.9
elif annual_pct > 5:   score = 0.7
elif annual_pct > 0:   score = 0.5
elif annual_pct > -5:  score = 0.3
else:                  score = 0.1

# Improved: continuous sigmoid — no cliff edges
# Designed so that:
# +20% → ~0.88, +5% → ~0.67, 0% → 0.50, -5% → ~0.33, -20% → ~0.12
score = 1 / (1 + np.exp(-0.08 * annual_pct))
score = round(float(np.clip(score, 0.1, 0.9)), 3)
```

```python
# Current: skill AI risk uses simple substring count
count = all_skills_text.count(skill_kw)

# Improved: tokenized exact matching on comma-separated skills
skill_tokens = set(
    s.strip().lower()
    for s in all_skills_text.split(',')
    if s.strip()
)
# For single-word skills, exact token match:
count = sum(1 for token in skill_tokens if skill_kw == token)
# For multi-word skills (e.g., "machine learning"), phrase match:
count = sum(1 for token in skill_tokens if skill_kw in token)
```

```python
# Current: static AI risk source blending
final_risk = 0.5 * skill_based_risk + 0.35 * domain_risk + 0.15 * structural_risk

# Improved: confidence-weighted blending
# More skill data = more confidence in skill_based_risk
skill_confidence = min(1.0, total_weight / 100)  # total_weight from skill count loop
skill_weight   = 0.30 + 0.25 * skill_confidence  # ranges from 0.30 to 0.55
domain_weight  = 0.35 * (1 - skill_confidence * 0.5)  # shrinks as skill data improves
struct_weight  = 1.0 - skill_weight - domain_weight

final_risk = (skill_weight * skill_based_risk 
            + domain_weight * domain_risk 
            + struct_weight * structural_risk)
```

---

*End of Engine 6 Documentation*

---

---

# Engine 7 — `SalaryGrowthEngine` (Salary Growth Projection Engine)

**File:** `salary_growth_engine.py`  
**Class:** `SalaryGrowthEngine`

---

## 1. Introduction — What is this Engine and What Does it Do?

`AverageSalaryRangeCalculator` (Engine 3) tells you what a fresher earns *today*. That is a snapshot.

This engine asks a completely different question:

> *"If I start at ₹5 LPA today as a fresher, what will I realistically earn at Year 1, Year 2, Year 3 — and how does that change depending on whether I job-switch, upskill aggressively, or just coast along?"*

**`SalaryGrowthEngine` is a career earnings simulator.** It takes your starting salary and projects it forward across multiple realistic life scenarios — Conservative, Expected, Optimistic, and Aggressive — using two independent data signals:

1. **Cross-Sectional Signal** — Right now, freshers in "Data Science" earn ₹5 LPA and people with 2 years earn ₹9 LPA. That gap tells us how much salary typically grows with experience in this domain. This is like a ladder — we can see all the rungs at once by looking at different experience levels today.

2. **Time-Series Signal** — Are the salaries being posted today *higher or lower* than what was posted 6 months ago? This captures actual market inflation — whether the domain is getting more or less competitive from an employer's perspective.

Both signals are blended to build 4 scenarios with clear economic logic behind each one.

> Think of it like a financial advisor giving you four investment projections: "If markets do poorly (Conservative), if they perform as expected (Expected), if you invest wisely (Optimistic), or if everything goes perfectly (Aggressive) — here is your money at Year 1, 2, 3." This engine does the same thing for your career salary.

---

## 2. Data Fields Required by This Engine

### Minimum Required

| Column Name | What it Means | Required? |
|---|---|---|
| `Min_Experience` | Minimum experience required by the job | ✅ For experience band segmentation |
| At least one salary column | `Avg_Salary`, `Min_Salary`, or `Max_Salary` | ✅ Core calculation data |

### Strongly Recommended Columns

| Column Name | What it Means | Fallback if Missing |
|---|---|---|
| `Job_Type` | Domain/category of job | Falls back to title search |
| `Title_Cleaned` (or `TItle_Cleaned`) | Job title text | Domain matching may miss records |
| `Avg_Salary` | Average salary (pre-computed in pipeline) | Computed from `(Min+Max)/2` |
| `Min_Salary` | Minimum posted salary | Used if `Avg_Salary` missing |
| `Max_Salary` | Maximum posted salary | Used if `Avg_Salary` missing |
| `Posted_Date` or `Scraped_At_Cleaned` | Date of job posting | Time-series signal unavailable |
| `Employment Type` | Full-time / Contract / Part-time | All types included |
| `Location` | City/region of the job | Location factor = 1.0 |

### Salary Priority Waterfall

The engine builds a unified `Salary_Mid` column using this priority:
```
1. Avg_Salary                      ← most accurate (already cleaned)
2. (Min_Salary + Max_Salary) / 2   ← computed midpoint
3. Min_Salary alone                ← last resort lower bound
4. Max_Salary alone                ← last resort upper bound
```

### Inputs Passed at Runtime

| Parameter | What it Means | Default |
|---|---|---|
| `target_domain` | Domain to analyze (e.g., `"Data Scientist"`) | Required |
| `projection_years` | How many years to project (1–10) | `3` (set in `__init__`) |
| `target_location` | City for location-adjusted projections | `None` (national) |

---

## 3. Core Logic — How Does the Engine Calculate Salary Growth?

The engine uses **two independent signals** and combines them into **4 scenario projections**.

---

### Signal 1 — Cross-Sectional Growth (The Experience Ladder)

**What it measures:** By looking at what different experience levels earn *right now*, we can infer the salary growth rate that comes with gaining experience.

**The 4 experience bands and their midpoints:**

| Band | Experience Range | Midpoint Used | Why This Midpoint |
|---|---|---|---|
| fresher | 0 – 1 yr | 0.5 yr | Middle of the band |
| junior | 1 – 3 yr | 2.0 yr | Middle of the band |
| mid | 3 – 6 yr | 4.5 yr | Middle of the band |
| senior | 6 – 12 yr | 9.0 yr | Middle of the band |

**For each band (minimum 5 samples required):**
```
band_median  = median(Salary_Mid for jobs requiring min_exp in this band)
band_p25     = 25th percentile
band_p75     = 75th percentile
```

**CAGR between consecutive bands:**
```
CAGR = (end_salary / start_salary)^(1 / years_between_midpoints) − 1
```

**Plain English Example:**

| Band | Median Salary | Midpoint Years |
|---|---|---|
| fresher | ₹5.0 LPA | 0.5 yr |
| junior | ₹8.5 LPA | 2.0 yr |
| mid | ₹14.0 LPA | 4.5 yr |

```
fresher → junior CAGR:
    t = 2.0 − 0.5 = 1.5 years
    CAGR = (8.5 / 5.0)^(1/1.5) − 1 = (1.70)^(0.667) − 1 = 0.440 → 44.0%/yr

junior → mid CAGR:
    t = 4.5 − 2.0 = 2.5 years
    CAGR = (14.0 / 8.5)^(1/2.5) − 1 = (1.647)^(0.40) − 1 = 0.244 → 24.4%/yr
```

This tells you: the biggest jump happens from fresher to junior — that first 1.5 years of experience is the most valuable in terms of salary growth.

**CAGR guard rails (`_safe_cagr`):**
- `start_val ≤ 0` → returns 0.0
- `end_val ≤ 0` → returns 0.0
- `periods ≤ 0` → returns 0.0
- Result clipped between **−50% and +100%** — anything outside is a data error

---

### Signal 2 — Time-Series Growth (Market Inflation)

**What it measures:** Are employers paying more or less for the same role over the past months? This is the actual **market salary inflation** — separate from what you earn with more experience.

**Formula (Weighted Linear Regression on monthly median salaries):**
```
Monthly series: median salary per month from job postings

Weighted regression:
    x = [0, 1, 2, ..., n_months]
    y = median salary per month
    w = number of job postings that month (months with more data get more weight)

monthly_slope     = regression coefficient (₹ change per month)
base_salary       = predicted salary at month 0 (intercept)
monthly_slope_pct = (monthly_slope / base_salary) × 100
annualized_pct    = monthly_slope_pct × 12
```

**Why weighted regression?** A month with 80 job postings is a much more reliable salary estimate than a month with 3 postings. Weighting by count prevents rare sparse months from pulling the slope.

**Weighted R²:**
```
ss_res = Σ w × (actual − predicted)²
ss_tot = Σ w × (actual − weighted_mean)²
R²     = 1 − (ss_res / ss_tot)
```

**Plain English Example:**

| Month | Median Salary | Job Count |
|---|---|---|
| Jan | ₹5.2 LPA | 45 |
| Feb | ₹5.5 LPA | 38 |
| Mar | ₹5.8 LPA | 52 |
| Apr | ₹6.1 LPA | 41 |

Slope ≈ +₹0.30 LPA/month → annualized = +7.2%/yr → market is inflating at 7.2%/year

This means even if you stay in the same job, market salaries are rising — so you should expect at least 7.2% hike per year just from market forces.

---

### Scenario Building — 4 Career Paths

The engine combines both signals to project 4 distinct salary trajectories from the fresher starting salary:

**Base CAGR** = `fresher_to_junior` CAGR from cross-sectional data (or first available segment)  
**Market Inflation** = annualized time-series slope (only used if R² ≥ 0.3)

| Scenario | Rate Formula | What It Represents |
|---|---|---|
| Conservative | `max(0, base_cagr × 0.6 + market_inflation × 0.5)` | Slow growth — no job switches, minimal upskilling, same company |
| Expected | `base_cagr + market_inflation` | Market-average progression — standard annual raises |
| Optimistic | `base_cagr × 1.3 + market_inflation` | Above-average — one job switch or strong upskilling |
| Aggressive | `base_cagr × 1.7 + market_inflation` | Top performer — multiple switches, high-demand skills, perfect execution |

**Final projection per scenario per year:**
```
salary_at_year_N = fresher_salary × (1 + rate)^N
```

**Rate sanity bounds:** All scenario rates are clipped between **−30% and +150%** before projection.

**Plain English Example (base_cagr = 0.25, market_inflation = 0.05, starting ₹5 LPA):**

| Scenario | Rate | Year 1 | Year 2 | Year 3 |
|---|---|---|---|---|
| Conservative | 20% | ₹6.0 | ₹7.2 | ₹8.6 |
| Expected | 30% | ₹6.5 | ₹8.5 | ₹11.0 |
| Optimistic | 37.5% | ₹6.9 | ₹9.5 | ₹13.0 |
| Aggressive | 47.5% | ₹7.4 | ₹10.9 | ₹16.1 |

---

### Location Adjustment

If `target_location` is provided:

```
local_median    = median(Salary_Mid) for domain in that city
national_median = median(Salary_Mid) for domain nationally

location_factor = local_median / national_median
location_factor = clip(location_factor, 0.7, 1.5)

adjusted_base_cagr = base_cagr × location_factor
```

**Assumption:** Cities with higher current salaries also tend to have faster salary growth curves. This is a simplification — see Disadvantages section.

**Sanity cap:** Location factor cannot multiply base CAGR by more than 1.5× or reduce it below 0.7× — prevents bad local data from producing absurd projections.

---

## 4. Constants and Parameters — What They Mean and Why

| Constant / Parameter | Value | Why This Value |
|---|---|---|
| `MIN_SAMPLES_PER_BAND` | **5** | Minimum data points for a reliable median per experience band. Below this, the band is skipped with a warning. |
| `default_projection_years` | **3** | 3 years is the typical "planning horizon" for a fresh graduate — far enough to be useful, close enough to be reliable. Configurable 1–10. |
| Fresher band midpoint | **0.5 yr** | Middle of the 0–1 year range. Used for CAGR denominator calculation. |
| Junior band midpoint | **2.0 yr** | Middle of the 1–3 year range. |
| Mid band midpoint | **4.5 yr** | Middle of the 3–6 year range. |
| Senior band midpoint | **9.0 yr** | Middle of the 6–12 year range. |
| CAGR floor | **−50%** | No real salary scenario drops by more than half per year — below this is a data error. |
| CAGR ceiling | **+100%** | No real salary doubles in one year from market forces alone — above this is a data error. |
| Scenario rate floor | **−30%** | Prevents projection from going negative in worst-case scenario. |
| Scenario rate ceiling | **+150%** | Extreme but theoretically possible in emerging domains. |
| Location factor cap | **0.7 – 1.5** | City premium/discount can be at most 50% above or 30% below national — wider than salary calculator (0.5–2.0) because this applies to growth *rate*, which is more sensitive. |
| IQR outlier multiplier | **2.5×** | Same as Engine 3 — handles right-skewed salary distributions without removing legitimate high earners. |
| Confidence thresholds | **50 / 20** | ≥50 fresher samples = High confidence, ≥20 = Medium, else Low. |
| Conservative multiplier | **0.6×** | A person who makes no extra effort realistically sees 60% of the theoretical CAGR — raises are not automatic. |
| Optimistic multiplier | **1.3×** | One job switch or strong upskilling adds roughly 30% to the base growth rate in the Indian market. |
| Aggressive multiplier | **1.7×** | Multiple switches + high-demand skills + performance can push growth to 1.7× base CAGR for top performers. |

---

## 5. Functions — What They Do and How They Are Called

```
project_growth()                     ← Main entry point (you call this)
    │
    ├── _filter_domain()             → Job_Type exact, title word-boundary fallback
    ├── _preprocess_salary()         → Build Salary_Mid, remove outliers, filter full-time
    │
    ├── _cross_sectional_growth()    → Band medians + CAGR between bands
    │       └── _safe_cagr()         → CAGR with division guards + sanity clip
    │
    ├── _time_series_growth()        → Monthly median salary trend (weighted regression)
    │
    ├── [Inline] Base CAGR selection → fresher→junior first, fallback to any segment
    ├── [Inline] Fresher salary base → band median or P25 fallback
    │
    ├── _location_adjustment()       → local/national median ratio → growth rate multiplier
    │
    ├── _build_scenarios()           → 4 scenarios: Conservative / Expected / Optimistic / Aggressive
    │       └── Uses base_cagr + market_inflation for each scenario rate
    │
    └── _interpret_growth()          → Plain-English summary string for UI display
```

| Function | Role |
|---|---|
| `__init__()` | Sets default projection years, validates range 1–10 |
| `_validate_weights()` | Validates custom scenario weight sums (currently not called — see Disadvantages) |
| `_filter_domain()` | Safe copy, typo fix, Job_Type exact, title regex fallback |
| `_preprocess_salary()` | Builds `Salary_Mid`, IQR outlier removal, full-time filter |
| `_cross_sectional_growth()` | Segments data by experience band, computes medians + CAGRs |
| `_safe_cagr()` | CAGR formula with complete guard rails — never divides by zero or returns NaN |
| `_time_series_growth()` | Monthly salary regression with sample-count weighting |
| `_location_adjustment()` | Computes local vs national median ratio as growth rate multiplier |
| `_build_scenarios()` | Blends CAGR + market inflation into 4 career path scenarios |
| `project_growth()` | **Master function** — orchestrates all steps, returns full projection report |
| `_interpret_growth()` | Plain-English interpretation of base CAGR + market inflation signal |

---

## 6. Output — What Does the Engine Return?

### Sample Output

```json
{
    "Domain": "Data Scientist",
    "Location": "Bengaluru",
    "Projection_Years": 3,

    "Data_Quality": {
        "Confidence": "High",
        "Fresher_Sample_Size": 67,
        "Time_Series_Signal": true,
        "TS_Reliable": true
    },

    "Baseline": {
        "Fresher_Median_LPA": 5.2,
        "Location_Factor": 1.287,
        "Base_CAGR_Pct": 28.7
    },

    "Market_Inflation": {
        "Annualized_Pct": 6.4,
        "Trend_R2": 0.71,
        "Months_Analyzed": 9
    },

    "Experience_Ladder": {
        "fresher": {"median": 520000, "p25": 400000, "p75": 650000, "n": 67, "exp_midpoint_yr": 0.5},
        "junior":  {"median": 880000, "p25": 720000, "p75": 1100000, "n": 84, "exp_midpoint_yr": 2.0},
        "mid":     {"median": 1500000, "p25": 1200000, "p75": 1900000, "n": 53, "exp_midpoint_yr": 4.5}
    },

    "CAGR_By_Segment": {
        "fresher_to_junior": 44.1,
        "junior_to_mid":     24.3
    },

    "Scenarios": {
        "Conservative": {
            "Annual_CAGR": "19.5%",
            "Yearly_Salary_LPA": {"Year_1": 6.21, "Year_2": 7.42, "Year_3": 8.87},
            "Final_Salary_LPA": 8.87,
            "Total_Growth_Pct": 70.6,
            "Description": "Slow growth path — minimal skill upgrades, same company"
        },
        "Expected": {
            "Annual_CAGR": "35.1%",
            "Yearly_Salary_LPA": {"Year_1": 7.03, "Year_2": 9.50, "Year_3": 12.83},
            "Final_Salary_LPA": 12.83,
            "Total_Growth_Pct": 146.7,
            "Description": "Market-average progression with standard raises"
        },
        "Optimistic": {
            "Annual_CAGR": "43.8%",
            "Yearly_Salary_LPA": {"Year_1": 7.48, "Year_2": 10.75, "Year_3": 15.46},
            "Final_Salary_LPA": 15.46,
            "Total_Growth_Pct": 197.3,
            "Description": "Above-average growth — 1 job switch or strong upskilling"
        },
        "Aggressive": {
            "Annual_CAGR": "55.5%",
            "Yearly_Salary_LPA": {"Year_1": 8.09, "Year_2": 12.58, "Year_3": 19.56},
            "Final_Salary_LPA": 19.56,
            "Total_Growth_Pct": 275.6,
            "Description": "Top performer path — multiple switches, high-demand skills"
        }
    },

    "Interpretation": "📈 Strong growth path — above-market salary acceleration expected. Market is also inflating at 6.4%/yr — good timing to enter."
}
```

### How to Read This Output

| Field | What it Tells the User |
|---|---|
| `Baseline.Fresher_Median_LPA` | Your realistic starting salary in this domain |
| `Baseline.Base_CAGR_Pct` | The underlying growth rate driving all projections |
| `Market_Inflation.Annualized_Pct` | How much market salaries are rising independently of your experience |
| `Experience_Ladder` | What each experience level earns right now — the full salary ladder |
| `CAGR_By_Segment` | The growth rate between each experience step |
| `Scenarios.Conservative.Yearly_Salary_LPA` | Year-by-year salary if you take a passive career path |
| `Scenarios.Aggressive.Yearly_Salary_LPA` | Year-by-year salary at peak performance |
| `Data_Quality.Confidence` | How much to trust these projections based on sample size |

---

## 7. How Robust Are the Formulas and Constants?

### What Makes Them Solid ✅

| Feature | Why It's Good |
|---|---|
| **Two independent signals** | Cross-sectional (experience ladder) and time-series (market inflation) capture different things. One is structural, one is temporal. Using both is more robust than either alone. |
| **Weighted time-series regression** | Months with more job postings drive the regression more than sparse months. A 3-posting month in February doesn't derail the salary trend estimate. |
| **Weighted R²** | The reliability check is computed consistently with the same weights as the regression — not just plain R² on unweighted data. |
| **`_safe_cagr()` with complete guard rails** | Zero or negative start/end values, zero periods — all handled explicitly. No silent NaN or division-by-zero can propagate into projections. |
| **Cross-sectional midpoints** | Using the midpoint of each experience band (e.g., 4.5yr for mid-level) gives a more accurate CAGR denominator than using band boundaries. |
| **Salary priority waterfall** | The `Salary_Mid` construction prefers the most reliable data source and gracefully falls back through multiple options — the engine never fails just because one salary column is missing. |
| **Scenario rate clipping** | Extreme growth rates (−30% to +150%) are caught before projections are computed — prevents financial projections from producing impossible numbers. |
| **Fresher salary fallback to P25** | If the fresher band has fewer than 5 samples, the engine falls back to the 25th percentile of all domain salaries — a conservative, defensible baseline. |

---

## 8. Advantages of the Current Implementation

- **Two-signal design** — separates "how much does experience pay" (structural) from "is the market paying more this year" (temporal). Both matter independently for career planning.
- **4 clearly differentiated scenarios** — each has explicit economic logic and a plain-English description, not just arbitrary multipliers.
- **Year-by-year breakdown** — each scenario shows salary at every year, not just the final number. This lets users plan financial milestones concretely.
- **CAGR per segment** — shows not just the starting salary but how quickly it grows at each career stage. The `fresher_to_junior` CAGR is often the most important number — the engine surfaces it prominently.
- **Market inflation blended into scenarios** — a market rising at 7%/year is correctly added to all scenario rates, not ignored.
- **Location-adjusted projections** — city-specific growth rate adjustment gives a more relevant number than national averages.
- **Data quality transparency** — `Confidence` level and `Time_Series_Signal` availability are explicit in the output — users know when to trust the numbers less.

---

## 9. Disadvantages and How to Improve Them

| Limitation | Problem | Suggested Fix |
|---|---|---|
| **`_validate_weights()` is defined but never called** | The method exists in the class but is not called anywhere — neither in `__init__()` nor in `_build_scenarios()`. This means if someone passes invalid scenario weights, there is no validation and silent errors occur. | Call `_validate_weights()` in `__init__()` if the weights parameter is passed, OR remove the method entirely since scenario multipliers are currently hardcoded (not user-configurable weights). |
| **Cross-sectional growth assumes market is in equilibrium** | The experience ladder (fresher = ₹5, junior = ₹8.5) assumes that today's junior salaries represent what today's freshers will earn in 1.5 years. But if the market is changing fast (e.g., ML salaries rising 30%/yr), today's junior salary is already outdated — it reflects what juniors hired 2 years ago negotiated. | Correct for market inflation: `projected_junior_salary = current_junior_median × (1 + market_inflation_rate)^1.5` before computing CAGR. This makes the cross-sectional ladder inflation-adjusted. |
| **Location adjustment applies to growth RATE, not starting salary** | `base_cagr *= loc_factor` — this multiplies the growth rate by the location factor. But a fresher in Bangalore starts at a higher absolute salary AND grows faster. The current implementation only captures the growth rate boost, not the higher starting point. The fresher salary baseline remains national. | Apply location factor to `fresher_median` too: `fresher_median_adjusted = fresher_median × loc_factor`. Then use the adjusted baseline for projections. |
| **`_location_adjustment()` checks `Avg_Salary` column on the full `df`** | Line 299: `if 'Location' not in domain_df.columns or 'Avg_Salary' not in df.columns:` — it checks `Avg_Salary` on the raw full `df`, but the salary calculation uses `Salary_Mid` on the preprocessed `domain_df`. If `Avg_Salary` is missing but `Min_Salary`/`Max_Salary` exist, the location adjustment silently returns 1.0 even though salary data is available. | Change the check to use `'Salary_Mid' in domain_df.columns` — since `Salary_Mid` is always created in `_preprocess_salary()`, this check will be reliable. |
| **Scenario multipliers are hardcoded (0.6, 1.3, 1.7)** | These reflect assumptions about Indian tech market job-switch premiums. But they could be wrong for other markets, or could change over time. A person in a government IT role has very different job-switch dynamics than someone in a startup. | Make multipliers configurable per domain type — a `scenario_config` dict passed to `project_growth()`. Alternatively, derive multipliers from data: compute P25, P50, P75 of actual CAGR values across job switchers in the dataset if such data is available. |
| **Time-series signal requires 10+ records and 3+ months** | These thresholds are separate from the cross-sectional minimum (5 samples). A domain with 8 records total will have a time-series signal unavailable — but the cross-sectional signal might still work. The output clearly shows `Time_Series_Signal: false`, but the user has no explanation of what this means practically. | Add an explanation field: `"Time_Series_Note": "Not enough monthly data — projections use experience ladder only. Market inflation component is estimated as 0%."` |
| **Salary is assumed to be in a single unit (LPA)** | The engine divides by 100,000 to convert to LPA (`fresher_median / 100000`). If any salary values in the dataset are monthly or in different units, the output will be completely wrong with no warning. | Add a unit detection heuristic: if `Salary_Mid.median() < 1000`, values are likely already in LPA. If `> 100000`, they are likely in rupees annually. Add a `salary_unit` detection step with explicit conversion and a warning. |

### Formula Improvement Suggestions

```python
# Current: location factor only applied to growth RATE
base_cagr *= loc_factor  # Only rate is adjusted

# Improved: apply to BOTH starting salary and growth rate
fresher_median_adjusted = fresher_median * loc_factor  # Higher base in Bangalore
adjusted_base_cagr = base_cagr * min(loc_factor, 1.2)  # Cap rate boost at 1.2x
# (Salaries in Bangalore start higher but don't necessarily GROW proportionally faster)
```

```python
# Current: cross-sectional CAGR uses today's junior salary directly
cagr = _safe_cagr(fresher_median, junior_median, years_between)

# Improved: inflation-adjust junior salary to account for market rise during that time
inflation_rate = ts_data.get("annualized_pct", 0) / 100  # from time-series signal
time_gap = junior_midpoint - fresher_midpoint  # e.g., 1.5 years
inflation_adjusted_junior = junior_median * (1 + inflation_rate) ** time_gap
cagr = _safe_cagr(fresher_median, inflation_adjusted_junior, time_gap)
# This makes the experience ladder forward-looking, not just a snapshot
```

```python
# Current: Conservative scenario has a floor at 0%
"rate": max(0.0, base_cagr * 0.6 + market_inflation * 0.5)

# Improved: allow negative Conservative scenario when market is genuinely declining
# A market with -10%/yr inflation and declining domain should show salary decline
# in the conservative case — important honest signal for career decisions
inflation = ts_data.get("annualized_pct", 0) / 100
if inflation < -0.05 and ts_data.get("reliable", False):
    conservative_rate = base_cagr * 0.6 + inflation  # Can go negative
else:
    conservative_rate = max(0.0, base_cagr * 0.6 + inflation * 0.5)
```

---

*End of Engine 7 Documentation*

---

---

# Engine 8 — `AIReplacementRiskEngine` (AI Replacement Risk Engine)

**File:** `ai_replacement_risk_engine.py`  
**Class:** `AIReplacementRiskEngine`

---

## 1. Introduction — What is this Engine and What Does it Do?

`DomainStabilityEngine` (Engine 6) included an AI risk component — but it was a supporting sub-score inside a larger stability calculation. This engine makes AI replacement risk its **entire focus**.

The question it answers is:

> *"Is my job going to be taken over by AI — not in a vague sense, but specifically based on what companies in this domain are actually asking people to do day-to-day?"*

Most AI risk tools rely on academic frameworks — lists of occupations rated by researchers. This engine does something fundamentally different: it **reads actual job descriptions** from real postings in the dataset and asks four distinct questions about what the work actually involves:

1. **Routine Exposure** — How much of this job is repetitive, manual, volume-based work that follows a fixed pattern? (Most automatable)
2. **Codified Knowledge** — How much of this job follows SOPs, compliance checklists, fixed rules and scripts? (AI executes rules better than humans)
3. **Creativity Gap** — How absent are strategic, judgment-heavy, ambiguous, human-connection tasks? (AI's weakest area)
4. **Skill-Level Automation Risk** — What specific skills does this domain require, and how automatable are those particular skills?
5. **Human Factor Protection** — Does this role require physical presence, leadership, client relationships, or high-stakes judgment? (Hardest to automate)

It also detects a **risk trend over time** — are job descriptions getting more routine (bad) or more creative and strategic (good)?

> Think of it like a security scan on a software system. Instead of guessing if it's vulnerable, you actually test it — checking for specific known vulnerabilities (routine tasks, rule-based procedures) and known protective factors (creativity requirements, human judgment, physical presence). This engine runs that scan on job descriptions.

---

## 2. Data Fields Required by This Engine

### Strongly Required (engine cannot produce meaningful results without these)

| Column Name | What it Means | Required? |
|---|---|---|
| `Description_Cleaned` | Cleaned full text of the job description | ✅ Core — all 3 task-nature scores depend on this |
| `Job_Type` | Domain/category of the job | ✅ Primary domain filter |

### Recommended Columns

| Column Name | What it Means | Fallback if Missing |
|---|---|---|
| `Title_Cleaned` (or `TItle_Cleaned`) | Job title text | Domain filter may miss records |
| `Star_Skills` | Must-have skills from posting | Falls back to `Combined_Skills` |
| `Combined_Skills` | All skills listed in posting | Falls back to `Normal_Skills` |
| `Normal_Skills` | Standard skills column | Falls back to `Skill_Count` proxy |
| `Skill_Count` | Number of skills required | Used as structural proxy if no skill text |
| `Posted_Date` or `Scraped_At_Cleaned` | Date of posting | Risk trend analysis unavailable |
| `Min_Experience` | Min years experience required | Experience filter skipped |

### Inputs Passed at Runtime

| Parameter | What it Means | Default |
|---|---|---|
| `target_domain` | Domain to analyze (e.g., `"Data Scientist"`) | Required |
| `experience_band` | Optional tuple `(min_exp, max_exp)` | `None` (all levels) |
| `weights` | Custom factor weights (set in `__init__`) | Default weights |

---

## 3. Core Logic — How Does the Engine Calculate AI Risk?

The engine has **two separate execution paths** — the old `calculate_ai_risk()` method and a collection of newer, more sophisticated methods. This is a critical architectural point covered fully in Section 9.

---

### Factor 1 — Routine Exposure Score

**What it measures:** What fraction of job postings in this domain mention tasks that are repetitive, manual, volume-based — the kind of work that is easiest to automate.

**Method used in `_analyze_task_nature()` (old path):**
```python
routine_kw = 'manual|repetitive|entry|maintenance|standard|daily reports|cleaning'
routine_score = domain_df['Description_Cleaned'].str.contains(routine_kw, case=False).mean()
```

**Method used in `_safe_keyword_score()` (new/better path — 40+ keywords with word boundaries):**
```
pattern = \b(?:keyword1|keyword2|...)\b  ← word-boundary regex
score   = fraction of JDs containing any routine keyword
```

**Full keyword list includes:** `data entry`, `manual entry`, `copy paste`, `data cleaning`, `daily report`, `repetitive`, `maintenance`, `standard procedure`, `template`, `batch processing`, `rule based`, `checklist`, `monitoring`, `high volume`, `bulk`, `pipeline execution`, `scheduled`, `automated workflow`, `logging`, `tracking`, `updating records`

**Plain English Example:**

If 60 out of 100 "Data Analyst" job descriptions mention words like "daily report", "data cleaning", or "maintenance":
→ routine_score = **0.60** → 60% of this domain's JDs signal highly automatable work

---

### Factor 2 — Codified Knowledge Score

**What it measures:** How much of this job follows fixed rules, SOPs, compliance scripts, or predefined procedures — tasks where the "right answer" is already written down somewhere and AI just needs to follow it.

**Keywords used:** `standard operating procedure`, `sop`, `fixed protocol`, `compliance`, `regulatory`, `audit`, `policy enforcement`, `script`, `template`, `predefined`, `rule engine`, `decision tree`, `flowchart`, `playbook`, `fill in`, `complete form`, `submit report`, `generate invoice`, `ticket resolution`, `level 1 support`, `faq`

**Score:** Fraction of JDs containing any codified knowledge keyword.

---

### Factor 3 — Creativity Gap Score (Inverted Creative Score)

**What it measures:** How absent is creative, judgment-heavy, strategic, human-facing work from job descriptions in this domain?

**Formula:**
```
creative_presence = fraction of JDs mentioning creative keywords
creativity_gap    = 1 − creative_presence
```

A domain where 80% of JDs mention strategic/creative tasks → creativity_gap = **0.20** (low risk)  
A domain where only 10% of JDs mention such tasks → creativity_gap = **0.90** (high risk)

**Keywords used:** `strategic`, `strategy`, `vision`, `roadmap`, `innovation`, `novel approach`, `original`, `creative solution`, `ambiguous`, `complex problem`, `trade-off`, `judgment`, `critical thinking`, `ethical`, `nuanced`, `empathy`, `negotiation`, `stakeholder`, `client relationship`, `mentoring`, `coaching`, `cultural`, `emotional intelligence`, `research`, `hypothesis`, `experiment`, `discover`, `architect`, `design from scratch`, `exploratory`

---

### Factor 4 — Skill Automation Risk Score (`_analyze_skill_risk`)

**What it measures:** Based on the specific skills listed in job postings, how automatable is the technical work in this domain? Skills are structured data — more reliable than free-text description keyword matching.

**Skill priority order:**
```
Star_Skills (must-have) → Combined_Skills → Normal_Skills → Skill_Count proxy
```

**Formula (frequency-weighted average):**
```
For each known skill found in domain's skill text:
    frequency = count of occurrences using word-boundary regex
    weighted_risk += SKILL_AI_RISK[skill] × frequency
    total_freq    += frequency

weighted_risk_avg = weighted_risk / total_freq
skill_score       = 1 − weighted_risk_avg   ← Higher = more AI-resistant
```

**Plain English Example:**

"Frontend Developer" domain's skills: `react` (30×), `html css` (45×), `javascript` (28×), `python` (5×)

| Skill | Frequency | Risk | Contribution |
|---|---|---|---|
| html css | 45 | 0.55 | 24.75 |
| react | 30 | 0.30 | 9.00 |
| javascript | 28 | 0.32 | 8.96 |
| python | 5 | 0.30 | 1.50 |
| **Total** | **108** | — | **44.21** |

`weighted_risk = 44.21 / 108 = 0.409` → 40.9% skill-level risk  
`skill_score = 1 − 0.409 = 0.591` → moderately AI-resistant

**Output also includes:**
- `top_risky_skills` — skills with risk ≥ 0.50 (up to 5)
- `top_safe_skills` — skills with risk ≤ 0.20 (up to 5)
- `skills_analyzed` — how many known skills were found

**Fallback when no known skills found:**
```
proxy_risk = max(0.05, 0.70 − (median_skill_count × 0.04))
```
More skills required = lower automation risk (requires breadth).

---

### Factor 5 — Human Factor Protection

**What it measures:** How much physical presence, leadership, client interaction, and high-stakes judgment is required? These are the strongest natural barriers to automation.

**Old path (used in `calculate_ai_risk()`):**
```python
human_factor_kw = 'physical|hardware|onsite|leadership|mentoring|client facing'
human_presence = JDs_containing_any_keyword / total_JDs
final_risk = risk_score × (1 − human_presence × 0.3)  ← multiplicative reduction
```

**New method (`_compute_human_factor_protection()`):**
```
human_score = fraction of JDs containing human-factor keywords
protection  = clip(human_score × 0.15, 0.0, 0.15)  ← max 15% additive reduction
final_risk  = base_risk − protection
```

**Why additive is better than multiplicative:**

| Approach | High-risk domain (base=0.80) | Low-risk domain (base=0.20) | Problem |
|---|---|---|---|
| Multiplicative: `risk × (1 − 0.3)` | 0.80 × 0.70 = **0.56** (-0.24) | 0.20 × 0.70 = **0.14** (-0.06) | High-risk domains get MORE benefit from human factor — backward logic |
| Additive: `risk − 0.15` | 0.80 − 0.15 = **0.65** (-0.15) | 0.20 − 0.15 = **0.05** (-0.15) | Equal absolute protection regardless of base risk — correct |

---

### Risk Trend Detection (`_analyze_risk_trend`)

**What it measures:** Is the domain's AI risk **increasing or decreasing over time**? By comparing older job postings to newer ones, we can tell whether employers are shifting toward more routine work (bad) or more creative/strategic work (good).

**Method (split-half temporal analysis):**
```
Sort all JDs by date
old_half = first 50% of JDs chronologically
new_half = last 50% of JDs chronologically

old_routine  = routine keyword fraction in old_half
new_routine  = routine keyword fraction in new_half
old_creative = creative keyword fraction in old_half
new_creative = creative keyword fraction in new_half

routine_delta  = new_routine  − old_routine    ← positive = getting worse
creative_delta = new_creative − old_creative   ← positive = getting better
direction_score = creative_delta − routine_delta
```

| Direction Score | Trend Label |
|---|---|
| > +0.05 | "Evolving Safely — Role becoming more strategic over time" |
| −0.05 to +0.05 | "Stable — No significant shift in task nature" |
| < −0.05 | "Increasing Automation Risk — Role becoming more routine over time" |

**Minimum 20 JDs required** for split-half trend analysis (10 per half for meaningful comparison).

---

### Final Score Composition (from `calculate_ai_risk()`)

```
risk_score = (routine_p      × weight_routine)
           + (codified_p     × weight_codified)
           + (low_creative_p × weight_creativity_gap)

final_risk = risk_score × (1 − human_factor_presence × 0.3)
```

**Important: Skill automation and risk trend are NOT used in `calculate_ai_risk()`** — see Section 9.

---

## 4. Weights — What They Mean and Why

| Weight | Factor | Value | Justification |
|---|---|---|---|
| `routine_exposure` | Factor 1 | **0.30** | Single largest driver of automation — repetitive, volume tasks are the first to be replaced. Reduced from a previous 0.70 to avoid over-dominance. |
| `codified_knowledge` | Factor 2 | **0.20** | Rule-following is something AI does exceptionally well. SOP execution, compliance checks, invoice generation — all automatable now. |
| `creativity_gap` | Factor 3 | **0.20** | Creativity and judgment are AI's hardest challenges. Domains that lack creative signal in JDs are far more vulnerable than those rich in it. Increased from a lower value — this is the key differentiator. |
| `skill_automation` | Factor 4 | **0.20** | Skills are structured, reliable signals. Added as a fourth dimension alongside task-nature analysis. |
| `human_factor` | Factor 5 | **0.10** | Physical presence and human relationships are strong protections, but only apply to a minority of tech roles. Lowest weight accordingly. |

---

## 5. Functions — What They Do and How They Are Called

### Defined Functions vs Actually Called Functions

```
calculate_ai_risk()                ← The ONLY public method (main entry point)
    │
    ├── _filter_domain()           → Domain rows (Job_Type or title fallback)
    ├── _analyze_task_nature()     → OLD: 7-keyword simple str.contains() for 3 scores
    └── [Inline human factor]      → OLD: 6-keyword regex, multiplicative risk reduction
                                      ← STOPS HERE — returns result

─── The following methods are DEFINED but NEVER CALLED by calculate_ai_risk() ───

    _safe_keyword_score()          → Better: word-boundary regex, 40+ keywords, NaN tracking
    _analyze_skill_risk()          → Better: frequency-weighted skill risk, risky/safe skill lists
    _analyze_risk_trend()          → Better: temporal split-half trend detection
    _compute_human_factor_protection() → Better: additive protection (not multiplicative)
    _classify_risk()               → Better: 5-tier labels (not 3-tier)
    _generate_advice()             → Better: specific factor-targeted advice (not single message)
```

| Function | Role | Called? |
|---|---|---|
| `__init__()` | Sets and validates weights | ✅ |
| `_validate_weights()` | Ensures weights sum to 1.0 ± 0.02 | ✅ |
| `_filter_domain()` | Job_Type exact + title fallback + experience filter | ✅ |
| `_analyze_task_nature()` | 3 scores from simple keyword matching (old path) | ✅ |
| `calculate_ai_risk()` | **Master function** — old implementation | ✅ |
| `_safe_keyword_score()` | Better keyword matching with word boundaries + NaN tracking | ❌ Never called |
| `_analyze_skill_risk()` | Frequency-weighted skill-level AI risk | ❌ Never called |
| `_analyze_risk_trend()` | Temporal JD trend analysis (is risk growing over time?) | ❌ Never called |
| `_compute_human_factor_protection()` | Additive human factor protection (correct formula) | ❌ Never called |
| `_classify_risk()` | 5-tier risk classification with descriptions | ❌ Never called |
| `_generate_advice()` | Factor-specific actionable advice list | ❌ Never called |

---

## 6. Output — What Does the Engine Return?

### Current Output (from `calculate_ai_risk()`)

```json
{
    "Domain": "Data Scientist",
    "AI_Risk_Score": 0.31,
    "Risk_Category": "AI-Augmented (Requires AI Synergy)",
    "Vulnerability_Breakdown": {
        "Routine_Exposure": "22%",
        "Rule_Based_Exposure": "18%",
        "Creativity_Gap": "45%"
    },
    "Actionable_Advice": "Stay updated with AI tools to enhance productivity."
}
```

### What the Output WOULD Look Like if All Methods Were Used

```json
{
    "Domain": "Data Scientist",
    "AI_Risk_Score": 0.28,
    "Risk_Category": "🟡 Low Risk — AI-Augmented",
    "Risk_Description": "Some automatable tasks — master AI tools to amplify output",

    "Vulnerability_Breakdown": {
        "Routine_Exposure_Pct": 22,
        "Codified_Knowledge_Pct": 18,
        "Creativity_Gap_Pct": 45,
        "Skill_Weighted_Risk_Pct": 19.4,
        "Human_Factor_Pct": 31
    },

    "Skill_Analysis": {
        "score": 0.806,
        "weighted_risk_pct": 19.4,
        "top_risky_skills": ["basic sql", "tableau"],
        "top_safe_skills": ["machine learning", "deep learning", "nlp"],
        "skills_analyzed": 8,
        "source": "Combined_Skills"
    },

    "Risk_Trend": {
        "trend": "Evolving Safely — Role becoming more strategic over time",
        "direction_score": 0.082,
        "routine_delta": -0.031,
        "creative_delta": 0.051
    },

    "Actionable_Advice": [
        "✅ AI-resistant skills in demand: machine learning, deep learning, nlp. Deepen these.",
        "⚠️  High-automation skills dominating: basic sql, tableau. Pair with system design.",
        "🚀 Strong position — stay current with AI tooling to amplify productivity."
    ]
}
```

### Risk Category Labels

| Risk Score | Category (old — 3 tier) | Category (new — 5 tier, unused) |
|---|---|---|
| < 0.30 | AI-Resilient (Human-Centric) | 🟢 AI-Resilient |
| 0.30 – 0.60 | AI-Augmented (Requires AI Synergy) | 🟡 Low Risk / 🟠 Moderate Risk |
| > 0.60 | High Exposure (Vulnerable to Automation) | 🔴 High Risk / 🚨 Critical Risk |

---

## 7. How Robust Are the Formulas and Constants?

### What Makes the DEFINED (but unused) Methods Solid ✅

| Feature | Why It's Good |
|---|---|
| **`_safe_keyword_score()` word-boundary regex** | `\b` boundaries prevent `'art'` matching `'artificial'`, `'repetitive'` matching `'unrepetitive'`. Far more precise than plain `str.contains()`. |
| **40+ keywords per dimension** | The `ROUTINE_KEYWORDS`, `CODIFIED_KEYWORDS`, `CREATIVE_KEYWORDS`, `HUMAN_FACTOR_KEYWORDS` lists are comprehensive, covering many real-world JD patterns. |
| **Frequency-weighted skill risk** | Skills mentioned 50 times in domain JDs are more representative than skills mentioned once. Weighting by frequency gives a more accurate domain-level risk. |
| **Risk trend detection** | Knowing that "Frontend Developer" JDs are becoming more routine over time is more actionable than a static risk score alone. |
| **Additive human factor protection** | Mathematically correct — equal absolute protection regardless of base risk level. |
| **5-tier risk classification** | Finer resolution than 3-tier — "Moderate Risk" and "High Risk" lead to completely different advice strategies. |
| **Factor-specific advice** | `_generate_advice()` identifies which specific factor is the dominant risk driver and gives targeted, actionable guidance — not a single generic sentence. |

### What Makes the ACTIVE Code (`calculate_ai_risk()`) Weak ⚠️

| Issue | Impact |
|---|---|
| **7-keyword simple regex for routine** | `'manual|repetitive|entry|...'` has no word boundaries — can match partial words. Also massively under-covers real JD language. |
| **3-tier classification** | "AI-Augmented" covers a score range of 0.30–0.60 — this is a 30-point wide bucket that groups very different risk levels together. |
| **Single generic advice string** | `"Stay updated with AI tools"` is the same advice for every domain with risk < 0.5. This provides no actionable guidance. |
| **Multiplicative human factor** | `risk × (1 − human_presence × 0.3)` gives more absolute benefit to high-risk domains — backwards. |
| **Skill risk and trend completely ignored** | 4 well-designed methods (`_analyze_skill_risk`, `_analyze_risk_trend`, `_classify_risk`, `_generate_advice`) are fully implemented but produce zero effect on the output. |

---

## 8. Advantages of the Current Implementation

- **Concept is sound** — reading actual job descriptions to assess automation risk is fundamentally better than relying on static occupation tables from academic research.
- **Well-designed keyword banks** — the 4 keyword lists (`ROUTINE_KEYWORDS`, `CODIFIED_KEYWORDS`, `CREATIVE_KEYWORDS`, `HUMAN_FACTOR_KEYWORDS`) are thoughtfully constructed with 40+ terms each covering diverse JD writing styles.
- **`SKILL_AI_RISK` dictionary is well-calibrated** — distinguishes between `data entry (0.92)`, `python (0.30)`, and `llm fine-tuning (0.06)` with sensible relative values across 4 tiers.
- **Skill priority chain** (`Star_Skills` → `Combined_Skills` → `Normal_Skills`) correctly prefers must-have skills over all skills.
- **Risk trend direction** — detecting whether a domain is evolving toward more creative or more routine work over time is a genuinely forward-looking signal not found in other engines.
- **Factor-specific advice structure in `_generate_advice()`** — when connected, this will give the most actionable output of any engine in the pipeline.

---

## 9. Disadvantages and How to Improve Them

### Critical Issue: Architecture Disconnect

This is the most important problem in this engine — **the well-designed methods are completely disconnected from the output**.

`calculate_ai_risk()` was written first (old implementation). Then `_safe_keyword_score()`, `_analyze_skill_risk()`, `_analyze_risk_trend()`, `_compute_human_factor_protection()`, `_classify_risk()`, and `_generate_advice()` were written as improvements — but `calculate_ai_risk()` was **never updated** to call them. The result is that the engine produces a primitive 3-factor output when a comprehensive 5-factor analysis is ready and waiting.

**The fix is straightforward — rewrite `calculate_ai_risk()` to use the new methods:**

```python
def calculate_ai_risk(self, df: pd.DataFrame, 
                       target_domain: str,
                       experience_band: tuple = None) -> dict:

    # 1. Filter domain
    domain_df = self._filter_domain(df, target_domain, experience_band)
    if domain_df.empty:
        return {"error": f"No data found for domain: '{target_domain}'"}

    if len(domain_df) < self.MIN_SAMPLES:
        return {"error": f"Insufficient data: {len(domain_df)} records."}

    # 2. Task-nature analysis (using BETTER _safe_keyword_score, not old inline regex)
    routine_score,   n_routine   = self._safe_keyword_score(
        domain_df.get('Description_Cleaned', pd.Series()), self.ROUTINE_KEYWORDS)
    codified_score,  n_codified  = self._safe_keyword_score(
        domain_df.get('Description_Cleaned', pd.Series()), self.CODIFIED_KEYWORDS)
    creative_score,  n_creative  = self._safe_keyword_score(
        domain_df.get('Description_Cleaned', pd.Series()), self.CREATIVE_KEYWORDS)
    human_score,     n_human     = self._safe_keyword_score(
        domain_df.get('Description_Cleaned', pd.Series()), self.HUMAN_FACTOR_KEYWORDS)

    creativity_gap = 1 - creative_score

    # 3. Skill-level risk (NEW — was never called before)
    skill_data = self._analyze_skill_risk(domain_df)

    # 4. Base risk score
    base_risk = (
        routine_score   * self.weights["routine_exposure"]   +
        codified_score  * self.weights["codified_knowledge"] +
        creativity_gap  * self.weights["creativity_gap"]     +
        (1 - skill_data["score"]) * self.weights["skill_automation"]
    )

    # 5. Human factor — ADDITIVE protection (correct formula, was never called before)
    protection = self._compute_human_factor_protection(human_score)
    final_risk = float(np.clip(base_risk - protection, 0.03, 0.95))

    # 6. Risk trend (NEW — was never called before)
    trend_data = self._analyze_risk_trend(domain_df)

    # 7. Classification (5-tier, was never called before)
    category, description = self._classify_risk(final_risk)

    # 8. Advice (factor-specific, was never called before)
    task_dict = {
        "routine": routine_score, "codified": codified_score,
        "creativity_gap": creativity_gap, "human_factor": human_score
    }
    advice = self._generate_advice(task_dict, skill_data, final_risk)

    return {
        "Domain":          target_domain,
        "Sample_Size":     len(domain_df),
        "AI_Risk_Score":   round(final_risk, 3),
        "Risk_Category":   category,
        "Risk_Description": description,
        "Vulnerability_Breakdown": {
            "Routine_Exposure_Pct":    round(routine_score * 100, 1),
            "Codified_Knowledge_Pct":  round(codified_score * 100, 1),
            "Creativity_Gap_Pct":      round(creativity_gap * 100, 1),
            "Human_Factor_Pct":        round(human_score * 100, 1),
            "Skill_Weighted_Risk_Pct": skill_data.get("weighted_risk_pct", None)
        },
        "Skill_Analysis":  skill_data,
        "Risk_Trend":      trend_data,
        "Actionable_Advice": advice
    }
```

---

### Other Limitations

| Limitation | Problem | Suggested Fix |
|---|---|---|
| **`_analyze_task_nature()` uses old 7-keyword inline regex** | Called by current `calculate_ai_risk()`. Has no word boundaries — `'manual'` matches `'unmanual'`, `'entry'` matches `'re-entry'`. Also uses only 7 keywords vs 40+ in the keyword banks. | Once `calculate_ai_risk()` is rewritten to use `_safe_keyword_score()`, `_analyze_task_nature()` should be deprecated and removed. |
| **Keyword banks rely on exact phrasing** | A JD saying "ad hoc repetitive tasks" will match "repetitive" but one saying "high-frequency manual operations" won't match "manual" if phrased differently. | Add synonym expansion — for each core keyword, include 2–3 semantic variants. For "repetitive": also add "recurring", "regular cadence", "high-frequency". |
| **Split-half temporal trend needs 20+ records** | With 15 or fewer JDs, `_analyze_risk_trend()` returns `"Insufficient data"`. For niche domains this threshold will often not be met. | Lower to 10 records minimum (5 per half), add a `"low_confidence": true` flag when between 10 and 20. |
| **`SKILL_AI_RISK` has 34 entries covering only common tech skills** | A domain like "DevRel Engineer" or "MLOps Architect" will find zero matches in `SKILL_AI_RISK` and fall back to the `Skill_Count` proxy — a much weaker signal. | Expand the dictionary to 100+ skills. Alternatively, use a tiered lookup: exact match first, then category-level match (e.g., all BI tools default to 0.50 risk if specific tool not found). |
| **No domain-level baseline validation** | The engine's scores for known domains (e.g., "Data Entry" should be ~0.85 risk, "AI Research" should be ~0.05) are never validated against ground truth. Silent miscalibrations could go undetected. | Add a `validate_known_domains(df)` utility function that runs the engine on a set of "anchor" domains with known expected risk levels and reports calibration drift. |
| **`Description_Cleaned` is accessed without checking column existence** | In `calculate_ai_risk()` line 349: `domain_df['Description_Cleaned'].str.contains(...)` — if `Description_Cleaned` column is missing, this raises a `KeyError` crash rather than returning a graceful neutral score. | Wrap in: `if 'Description_Cleaned' not in domain_df.columns: return neutral_result`. The new `_safe_keyword_score()` already handles this — another reason to use it. |

### Formula Improvement Suggestion

```python
# Current: simple fraction of JDs containing keyword
score = matches.mean()  # 1 if any keyword appears anywhere in JD

# Improved: keyword density — reward JDs that mention many keywords
# A JD with 5 routine signals is more automatable than one with 1 mention
keyword_counts = valid.apply(
    lambda text: sum(1 for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b',
                                                        text, re.IGNORECASE))
)
max_possible = len(keywords)
density_score = (keyword_counts / max_possible).clip(upper=1.0).mean()
# Blend: 70% presence, 30% density — rewards thoroughness without over-weighting
score = 0.7 * matches.mean() + 0.3 * density_score
```

---

*End of Engine 8 Documentation*

---

---

# Engine 9 — `SkillTransferabilityEngine` (Skill Transferability Engine)

**File:** `skill_transferability_engine.py`  
**Class:** `SkillTransferabilityEngine`

---

## 1. Introduction — What is this Engine and What Does it Do?

Almost every developer, analyst, or engineer eventually asks: *"Should I switch from Web Development to Data Science? How hard would it really be?"*

Most tools answer this vaguely — "some skills transfer" or "it's a big shift." This engine gives a precise, data-driven answer:

> *"Here is exactly what % of your current skills carry over, what % of the destination's requirements you already meet, which specific skills you need to learn first, how long it will take, and whether you'll get a pay raise or cut."*

**`SkillTransferabilityEngine` is a career switch calculator.** Given two domains — a source (where you are) and a target (where you want to go) — it analyzes actual job posting skill requirements for both and produces a complete switching roadmap.

It is also the **only bidirectional engine in the pipeline** — it not only tells you "Web Dev → Data Science is 35% transferable" but also checks whether "Data Science → Web Dev" might actually be easier, and tells you that too.

The engine measures four distinct things:

1. **Coverage Ratio** — "What % of the target domain's requirements do you already meet?" (Can you do the job on day 1?)
2. **Portability Ratio** — "What % of your current skills are useful in the new domain?" (Is your learning investment protected?)
3. **Priority Skill Gap** — "Which specific skills should you learn first — ranked by how important they are in the destination?"
4. **Reskilling Time Estimate** — "Realistically, how many months will this take at 10 hrs/week?"

Plus a **salary impact check** ("will you take a pay cut?") and a **bidirectional comparison** ("is the reverse switch easier?").

> Think of it like a GPS navigation tool for career switching. It doesn't just tell you the destination is far — it gives you the exact route, shows which roads you already know (bridge skills), lists the new roads to learn (priority gaps), estimates the travel time, and even checks if there's a better route in the opposite direction.

---

## 2. Data Fields Required by This Engine

### Required

| Column Name | What it Means | Required? |
|---|---|---|
| `Job_Type` | Domain/category of the job | ✅ Primary domain filter |
| At least one skill column | `Star_Skills`, `Combined_Skills`, or `Normal_Skills` | ✅ Core — no skills = no analysis |

### Strongly Recommended

| Column Name | What it Means | Fallback if Missing |
|---|---|---|
| `Star_Skills` | Must-have / critical skills (gets 2× weight) | Skipped, falls to Combined_Skills |
| `Combined_Skills` | All skills mentioned in posting (standard weight) | Skipped, falls to Normal_Skills |
| `Normal_Skills` | Nice-to-have skills (0.7× weight) | Engine returns error if all 3 missing |
| `Title_Cleaned` (or `TItle_Cleaned`) | Job title text | Domain filter may miss records |
| `Min_Experience` | Minimum experience required | Experience filter skipped |
| `Avg_Salary` | Average salary | Salary impact section unavailable |
| `Skill_Count` | Number of skills required per posting | Domain complexity comparison unavailable |

### Inputs Passed at Runtime

| Parameter | What it Means | Default |
|---|---|---|
| `source_domain` | Domain you are coming FROM (e.g., `"Web Developer"`) | Required |
| `target_domain` | Domain you want to go TO (e.g., `"Data Scientist"`) | Required |
| `experience_band` | Tuple `(min_exp, max_exp)` to filter relevant job level | `(0, 5)` |

---

## 3. Core Logic — How Does the Engine Calculate Transferability?

The engine has **4 core analytical steps** plus 3 supplementary steps.

---

### Step 1 — Building Weighted Skill Profiles

For both source and target domains, the engine builds a **skill importance profile** — a dictionary where each skill has an importance score based on how frequently and prominently it appears across job postings.

**Skill column weights:**

| Column | Weight | Why |
|---|---|---|
| `Star_Skills` | **2.0×** | Must-have skills — companies will reject without these |
| `Combined_Skills` | **1.0×** | Standard requirement — baseline expectation |
| `Normal_Skills` | **0.7×** | Nice-to-have — helpful but not critical |

**Formula:**
```
For each posting, for each skill column:
    split skills by comma → individual skill tokens
    skill_weighted_count[skill] += column_weight

After processing all postings:
    skill_importance[skill] = skill_weighted_count[skill] / total_postings

Generic skills (excel, teamwork, etc.) → multiplied by 0.2 (downweighted)
Skills with importance < 0.01 → removed (noise filter)
```

**Plain English Example (50 job postings for "Data Scientist"):**

| Skill | Star appearances | Combined appearances | Weighted Count | Importance |
|---|---|---|---|---|
| python | 40 (×2.0=80) | 48 (×1.0=48) | 128 | 2.56 |
| machine learning | 35 (×2.0=70) | 42 (×1.0=42) | 112 | 2.24 |
| sql | 20 (×2.0=40) | 38 (×1.0=38) | 78 | 1.56 |
| excel | — | 30 (×1.0=30) | 30 × 0.2 = 6 | 0.12 *(downweighted)* |

**Why downweight generic skills?** Skills like "excel", "communication", "teamwork" appear in almost every domain — they provide zero signal about what makes Data Science specifically different from Web Development. Keeping them at full weight would artificially inflate overlap scores between completely unrelated domains.

---

### Step 2 — Three Overlap Metrics

This is the mathematical heart of the engine. Given source and target skill profiles, three distinct overlap measures are computed:

---

#### Metric A — Coverage Ratio
```
Coverage = |common_skills| / |target_skills|
```
"What percentage of the target's skill requirements do you already have?"

This answers: *"Can you do the new job?"* — the most important question for a career switcher on day 1.

---

#### Metric B — Portability Ratio
```
Portability = |common_skills| / |source_skills|
```
"What percentage of your current skills are useful in the target domain?"

This answers: *"Is my past learning investment protected?"* — important for decision-making confidence.

---

#### Metric C — Weighted Coverage (most important)
```
weighted_coverage = Σ target_importance[skill]  for skill in common_skills
max_possible      = Σ target_importance[skill]  for all target skills

normalized_weighted = weighted_coverage / max_possible
```
"Are the skills you already have the HIGH-IMPORTANCE ones in the target, or just the low-importance ones?"

**Why this matters:** You could have 70% coverage by count but only cover the easy, low-importance skills. Or you could have 40% coverage but those 40% are the most critical skills. Weighted coverage captures this quality dimension.

**Plain English Example:**

Suppose "Web Developer → Data Science":
- You have: Python, SQL, JavaScript
- Target needs: Python (importance 2.56), ML (2.24), SQL (1.56), Deep Learning (1.80), Tableau (0.8), JavaScript (0.4)

Coverage by count = 2 out of 6 = **33%**

But your 2 matching skills (Python + SQL) have combined importance = 2.56 + 1.56 = 4.12  
Max possible = 2.56 + 2.24 + 1.56 + 1.80 + 0.8 + 0.4 = 9.36  
Weighted coverage = 4.12 / 9.36 = **44%** — better than raw count suggests

---

#### Composite Transferability Score
```
Composite = 0.60 × normalized_weighted + 0.40 × portability_ratio
```

**Why 60% weighted coverage and 40% portability?**
- Coverage (do you meet target requirements?) matters more for the hiring side — employers care about fit.
- Portability (does your investment transfer?) matters for the learner's motivation — but is secondary.

---

### Step 3 — Skill Gap Analysis

Identifies three categories of skills for the switch:

```
Priority Gaps   = target_skills − source_skills    ← you need to learn these
Bridge Skills   = source_skills ∩ target_skills    ← you already have these
Obsolete Skills = source_skills − target_skills    ← these won't help in the new domain
```

**Priority gaps are ranked by target importance** — you learn the highest-impact skills first, not in random order.

**Reskilling time estimation:**
```
For each of the top 10 priority gap skills:
    base_weeks      = SKILL_COMPLEXITY[skill]  (or DEFAULT_WEEKS=6 if unknown)
    adjusted_weeks  = base_weeks × (1 + target_importance)
    total_weeks    += adjusted_weeks

estimated_months = total_weeks / 4.3   (4.3 weeks per month)
assumed pace     = 10 hours/week
```

**Why multiply by `(1 + importance)`?** High-importance skills need to be learned more deeply — not just surface-level familiarity. If Python has importance 2.56, it needs `base_weeks × 3.56` — you need mastery, not just basics.

**Sample `SKILL_COMPLEXITY` values (weeks to learn):**

| Skill | Weeks | Skill | Weeks |
|---|---|---|---|
| sql | 3 | python | 4 |
| docker | 3 | react | 8 |
| aws | 8 | java | 10 |
| system design | 12 | tensorflow | 12 |
| nlp | 14 | machine learning | 16 |
| deep learning | 20 | data science | 20 |

---

### Step 4 — Bidirectional Analysis

The engine computes the overlap metrics **in both directions**:
- Forward: `source → target` (e.g., Web Dev → Data Science)
- Reverse: `target → source` (e.g., Data Science → Web Dev)

Then compares composite scores:

```
if |forward − reverse| < 0.05:
    "Both directions similarly feasible"
elif reverse > forward:
    "Reverse path is X% easier — consider building target skills first, then switching"
else:
    "Forward path is the more natural direction"
```

**Why this matters:** Sometimes the smarter career move is to go Data Science → Web Dev first (easier switch, builds a hybrid profile) and then switch. Or the reverse might be so much harder that it confirms the forward direction is correct. This insight is unique to this engine.

---

### Supplementary Step — Salary Impact

```
source_median = IQR-cleaned median(Avg_Salary) for source domain
target_median = IQR-cleaned median(Avg_Salary) for target domain
delta_pct     = (target_median − source_median) / source_median × 100
```

| Delta % | Signal |
|---|---|
| > +10% | 📈 Salary upgrade |
| −10% to +10% | ⚖️ Similar compensation |
| < −10% | 📉 Salary cut — factor into timing |

---

### Classification — 5 Tiers

| Composite Score | Label | Difficulty |
|---|---|---|
| ≥ 0.65 | 🟢 High Transferability | Easy Switch |
| 0.45 – 0.64 | 🟡 Moderate Transferability | Moderate Effort |
| 0.25 – 0.44 | 🟠 Low Transferability | Significant Reskilling |
| < 0.25 | 🔴 Very Low Transferability | Near Full Restart |

**Time modifier** appended to label:
- ≤ 2 months → "Quick transition"
- 2–6 months → "Medium transition"
- 6–12 months → "Long transition"
- > 12 months → "Extended transition"

**Coverage warning** added if coverage < 30%:
> *"⚠️ You currently cover only X% of target requirements. Expect steep learning curve even after transition."*

---

## 4. Constants and Parameters — What They Mean and Why

| Constant / Parameter | Value | Justification |
|---|---|---|
| `Star_Skills` weight | **2.0×** | Must-have skills are binary gatekeepers — missing them means automatic rejection. Doubling their weight reflects this outsized importance. |
| `Combined_Skills` weight | **1.0×** | Standard expectation — baseline for all calculations. |
| `Normal_Skills` weight | **0.7×** | Nice-to-have. Still relevant but shouldn't dominate the profile. |
| Generic skills downweight | **0.2×** | Skills like "communication" appear in 90%+ of all domains — keeping them at full weight would create artificial overlap between unrelated fields. 0.2× retains a small signal while preventing domination. |
| Importance filter threshold | **0.01** | Removes noise — skills mentioned in fewer than 1% of postings have negligible domain signal. |
| Composite split | **60% weighted coverage + 40% portability** | Coverage = "can you do the job" is what employers care about. Portability = "does your learning transfer" is what learners care about. Coverage slightly more important. |
| `adjusted_weeks = base_weeks × (1 + importance)` | Variable | High-importance skills need deeper mastery. A skill with importance 2.0 needs 3× the base learning time — you can't be superficial with a must-have skill. |
| `DEFAULT_WEEKS` | **6** | Conservative default for unknown skills — 6 weeks is a reasonable estimate for a moderately complex tech skill at 10 hrs/week. |
| Learning pace assumption | **10 hrs/week** | Realistic for a working professional who is studying on the side. Aggressive but achievable. |
| Months conversion | **÷ 4.3** | 4.3 weeks per month (52 weeks / 12 months). More accurate than ÷ 4. |
| Bidirectional threshold | **±0.05** | Differences smaller than 5% composite score are effectively equal — within margin of data noise. |
| Coverage warning threshold | **< 0.30** | Below 30% coverage, the learner will struggle significantly even after acquiring gap skills — the base is too thin. |
| IQR salary outlier | **1.5×** | Standard IQR multiplier here (vs 2.5× in salary engines) — acceptable because salary impact is a supplementary metric, not the primary calculation. |

---

## 5. Functions — What They Do and How They Are Called

```
calculate_transferability()             ← Main entry point (you call this)
    │
    ├── _filter_domain()                → Source domain rows (Job_Type + experience filter)
    ├── _filter_domain()                → Target domain rows (called twice)
    │
    ├── _extract_skill_profile()        → Weighted skill importance dict for each domain
    │       (called twice — source and target)
    │
    ├── _calculate_overlap_metrics()    → Coverage, portability, weighted coverage, composite
    │       (called twice — forward and reverse direction)
    │
    ├── _analyze_skill_gap()            → Priority gaps ranked by target importance + time estimate
    ├── _classify_transferability()     → 5-tier label + time modifier + coverage warning
    ├── _calculate_salary_impact()      → Source vs target median salary comparison
    └── _bidirectional_note()           → Forward vs reverse composite comparison + advice
```

| Function | Role |
|---|---|
| `__init__()` | Sets up logger (no weights to validate — this engine has no configurable weights) |
| `_filter_domain()` | Job_Type exact + experience filter + title fallback, safe copy |
| `_extract_skill_profile()` | Builds weighted skill importance dict from all skill columns |
| `_calculate_overlap_metrics()` | Computes coverage, portability, weighted coverage, composite |
| `_analyze_skill_gap()` | Priority gaps ranked by target importance, bridge skills, obsoletes, time estimate |
| `_classify_transferability()` | 5-tier classification using composite + coverage + time |
| `_calculate_salary_impact()` | IQR-cleaned median salary comparison with signal label |
| `_bidirectional_note()` | Compares forward vs reverse composite, gives strategic switch advice |
| `calculate_transferability()` | **Master function** — runs full bidirectional analysis |

---

## 6. Output — What Does the Engine Return?

### Sample Output

```json
{
    "Path": "Web Developer → Data Scientist",
    "Experience_Band": [0, 5],

    "Transferability": {
        "Composite_Score": 0.41,
        "Coverage_Ratio": 0.33,
        "Portability_Ratio": 0.52,
        "Label": "🟠 Low Transferability",
        "Difficulty": "Significant Reskilling",
        "Time_Estimate": "Long transition (~9.2 months)",
        "Coverage_Warning": "⚠️  You currently cover only 33% of target requirements. Expect steep learning curve even after transition."
    },

    "Skill_Gap": {
        "Priority_Skills_To_Learn": [
            {"skill": "machine learning", "importance": 2.24, "weeks": 16},
            {"skill": "deep learning",    "importance": 1.80, "weeks": 20},
            {"skill": "tensorflow",       "importance": 1.42, "weeks": 12},
            {"skill": "nlp",              "importance": 1.21, "weeks": 14},
            {"skill": "spark",            "importance": 0.95, "weeks": 8}
        ],
        "Bridge_Skills": [
            {"skill": "python",           "target_importance": 2.56},
            {"skill": "sql",              "target_importance": 1.56}
        ],
        "Skills_Becoming_Obsolete": ["react", "node.js", "css"],
        "Total_Gap_Skills": 11,
        "Total_Bridge_Skills": 3,
        "Estimated_Months": 9.2,
        "Learning_Hrs_Assumed": 10
    },

    "Domain_Complexity": {
        "Source_Median_Skills": 7.0,
        "Target_Median_Skills": 9.5,
        "Complexity_Jump": 2.5
    },

    "Salary_Impact": {
        "Available": true,
        "Source_Median": 6.8,
        "Target_Median": 9.2,
        "Delta_Pct": 35.3,
        "Signal": "📈 Salary upgrade: +35.3% median compensation gain"
    },

    "Bidirectional_Note": "💡 The reverse path (Data Scientist → Web Developer) is 18% easier. Consider building Data Science skills first, then switching.",

    "Sample_Sizes": {
        "Source_Listings": 142,
        "Target_Listings": 184
    }
}
```

### How to Read This Output

| Field | What it Tells the User |
|---|---|
| `Transferability.Coverage_Ratio` | What % of target requirements you already meet — your day-1 readiness |
| `Transferability.Portability_Ratio` | What % of your current skills carry over — protection of past investment |
| `Transferability.Composite_Score` | Overall switch difficulty — the headline number |
| `Skill_Gap.Priority_Skills_To_Learn` | **Your personalized learning roadmap** — ranked by what matters most in the target |
| `Skill_Gap.Bridge_Skills` | Skills you already have that are valuable in the new domain — your competitive advantages |
| `Skill_Gap.Skills_Becoming_Obsolete` | Skills that won't transfer — helps set realistic expectations |
| `Skill_Gap.Estimated_Months` | Realistic timeline at 10 hrs/week — concrete planning number |
| `Salary_Impact.Delta_Pct` | Will you earn more or less after switching? |
| `Bidirectional_Note` | Is the reverse path easier? Strategic insight unique to this engine |

---

## 7. How Robust Are the Formulas and Constants?

### What Makes Them Solid ✅

| Feature | Why It's Good |
|---|---|
| **Two overlap ratios (not one)** | Previous implementations only computed portability — "how much of source transfers." This missed the crucial question of coverage — "can you actually do the new job." Both are needed; they measure different things. |
| **Weighted coverage by target importance** | Not all shared skills are equal. Sharing a high-importance skill (Python in Data Science) is worth far more than sharing a low-importance one. Weighted coverage correctly captures this quality dimension. |
| **Generic skills downweighted** | "Excel" and "communication" appear in almost every domain. Without downweighting, two completely unrelated domains would show 30%+ artificial overlap just from generic skills. 0.2× keeps a tiny signal while removing the distortion. |
| **Star_Skills double weight** | Must-have skills are not just "more important" — they are gatekeepers. Without them, you don't pass the initial filter. 2× weight reflects this binary nature. |
| **Reskilling time scaled by importance** | `adjusted_weeks = base_weeks × (1 + importance)` — a must-have skill (importance ~2.0) requires 3× the learning depth of a nice-to-have mention. This produces realistic time estimates. |
| **Bidirectional analysis** | Checks whether the reverse switch is easier — a genuinely actionable insight that requires no extra data, just running the overlap calculation twice. |
| **Coverage warning at 30% threshold** | Low composite score might still hide the fact that you only cover 20% of requirements — you'd struggle even after learning gap skills. The explicit warning prevents false confidence. |
| **Gap skills ranked by target importance** | Teaching the most impactful skills first is how professional learning roadmaps are built. Random or alphabetical ordering would be far less useful. |

---

## 8. Advantages of the Current Implementation

- **Dual overlap metrics** — coverage and portability together give a complete picture that neither alone can provide.
- **Importance-weighted skill profiles** — not just "do you have the skill" but "how central is that skill to the domain."
- **Personalized learning roadmap** — priority gaps ranked by target importance is directly actionable without any post-processing.
- **Time estimate with learning pace assumption** — "9.2 months at 10 hrs/week" is far more useful than "you need to learn 11 skills."
- **Bridge skills identification** — explicitly showing what you already have and its value in the target is a motivational anchor — it shows why the switch is worth attempting.
- **Salary impact built-in** — directly answers the financial question that every career switcher asks first.
- **Bidirectional insight** — unique among all engines — provides strategic career path advice, not just a difficulty rating.
- **Fully self-contained** — no external weights to configure, no complex initialization. One function call returns the complete analysis.

---

## 9. Disadvantages and How to Improve Them

| Limitation | Problem | Suggested Fix |
|---|---|---|
| **Title fallback uses simple `str.contains()` without word boundaries** | `_filter_domain()` Priority 2 uses `df[title_col].str.contains(target_domain, case=False)` — no `\b` boundaries. Searching for "Data Science" could match "Applied Data Science Platform Engineer" — a completely different role. | Add `re.escape()` + `\b` boundaries: `r'\b' + re.escape(target_domain) + r'\b'` — consistent with how other engines handle this. |
| **Skill matching is pure set intersection — no semantic matching** | `common_skills = source_skills & target_skills` is an exact string match. `"machine learning"` and `"ml"` are treated as completely different skills. `"python"` and `"python 3"` don't overlap. This under-estimates real transferability. | Build a skill synonym dictionary mapping abbreviations and variants to canonical names: `{"ml": "machine learning", "python 3": "python", "dl": "deep learning"}`. Normalize all extracted skills through this map before computing overlap. |
| **Reskilling time only estimates top 10 gap skills** | `for skill, importance in gap_ranked[:10]` — if there are 20+ gap skills, the time estimate only accounts for the top 10. The output could say "9 months" when the full picture is 18 months. | Change to `gap_ranked[:15]` or compute for all gap skills with diminishing weight: `adjusted_weeks × max(0.5, 1 - rank * 0.05)` — later skills are learned in parallel or superficially, so their marginal time contribution decreases. |
| **`SKILL_COMPLEXITY` covers only 20 skills** | Any skill not in the dictionary defaults to `DEFAULT_WEEKS = 6`. A gap skill like "Terraform" or "FastAPI" or "LangChain" would all get 6 weeks regardless of actual complexity. | Expand the dictionary to 80+ skills covering current tech landscape. Add a complexity tier system: if skill not found, categorize by skill type (framework=6w, infrastructure=8w, ML library=12w, cloud platform=8w) rather than a flat 6w default. |
| **Salary impact uses simple median without experience adjustment** | `safe_median(source_df)` computes median over all experience levels in the band. If the source domain has mostly senior listings and target has mostly fresher listings in the dataset, the comparison is unfair — it's not comparing like-for-like. | Filter both source and target salary medians to the same experience sub-band (e.g., only 1–3 year exp rows) before comparison. This ensures a fair like-for-like salary delta. |
| **Generic skill list is hardcoded and small (13 items)** | `GENERIC_SKILLS` contains 13 entries. Many more generic skills exist: "agile", "git", "scrum", "jira", "confluence", "verbal communication", "written communication". These would inflate cross-domain overlap scores. | Compute generic skills dynamically from the dataset: skills that appear in more than 60% of ALL domain profiles are "generic" and should be downweighted. This is a true TF-IDF-style approach — domain frequency as the inverse document frequency (IDF) component. |
| **No user's actual skill input** | The engine compares two domains from the dataset — it doesn't know YOUR personal skill list. Someone with 3 years of React experience and Python basics has a very different transfer profile than a Python expert with no JavaScript. | Add a `user_skills: list` optional parameter to `calculate_transferability()`. If provided, build the source_profile from the user's actual skills rather than from dataset averages. This would make the output truly personalized (similar to what `CompetitionLevelCalculator` does). |
| **`Complexity_Jump` crashes if only one domain has `Skill_Count`** | Line 454: `round(tgt_complexity - src_complexity, 1)` — if `tgt_complexity` is a float but `src_complexity` is `None` (because source domain has no `Skill_Count` column), this raises a `TypeError`. The `if src_complexity and tgt_complexity` guard is correct but only runs *after* the arithmetic is attempted in the dict literal. | The `Complexity_Jump` should be computed before the return dict is built: `complexity_jump = round(tgt_complexity - src_complexity, 1) if src_complexity and tgt_complexity else None`. Then reference the pre-computed variable in the dict. |

### Formula Improvement Suggestions

```python
# Current: composite = 60% weighted_coverage + 40% portability
composite = 0.60 * normalized_weighted + 0.40 * portability

# Improved: make the split dynamic based on gap size
# If the gap is very large (many skills to learn), coverage matters MORE
# If the gap is small (few skills), portability matters MORE
gap_ratio = min(1.0, total_gap_skills / max(len(target_skills), 1))
coverage_weight   = 0.50 + gap_ratio * 0.20   # scales from 0.50 to 0.70
portability_weight = 1.0 - coverage_weight
composite = coverage_weight * normalized_weighted + portability_weight * portability
```

```python
# Current: reskilling time uses flat importance multiplier
adjusted_weeks = weeks * (1 + importance)

# Improved: cap the importance multiplier — a skill with importance 5.0
# doesn't take 6× the weeks to learn. Real learning has diminishing marginal effort.
importance_multiplier = 1 + min(importance, 2.0) * 0.4  # max 1.8× base weeks
adjusted_weeks = weeks * importance_multiplier
```

```python
# Current: generic skills always get exactly 0.2× weight
skill_importance[generic] *= 0.2

# Improved: dynamic TF-IDF-style downweighting
# Skills appearing in X% of all domains get weight proportional to their rarity
# Compute domain_frequency = fraction of domains that list this skill
# idf_weight = max(0.1, 1 - domain_frequency)  ← rare skill = weight near 1.0
#                                                ← ubiquitous skill = weight near 0.1
# Apply per-skill rather than a fixed 0.2× for all generics
for skill in skill_importance:
    domain_freq = global_skill_frequencies.get(skill, 0.5)
    idf_weight = max(0.1, 1.0 - domain_freq)
    skill_importance[skill] *= idf_weight
```

---

*End of Engine 9 Documentation*

---

---

# Engine 10 — `HiddenBlockerDetector` (Hidden Blocker Detector)

**File:** `hidden_blocker_detector.py`  
**Class:** `HiddenBlockerDetector`

---

## 1. Introduction — What is this Engine and What Does it Do?

Every other engine in the pipeline measures market-level signals — demand, competition, salary, growth, AI risk. But none of them answer a specific question that freshers and career switchers ask constantly:

> *"I know this domain looks good on paper — but why do I keep getting rejected? What is actually blocking me from getting in that nobody told me about?"*

The answer is almost always one of a set of **hidden blockers** — requirements buried in job descriptions that act as invisible filters. A company posts "0–2 years experience" but then in the JD body says "must have GitHub with 500+ contributions" or "CGPA 7.5 minimum" or "service bond of 2 years." These are never in the job title. They only appear when you read carefully — and most applicants don't.

**`HiddenBlockerDetector` systematically scans job descriptions and experience data to surface these invisible barriers.**

It detects **14 distinct blocker types** across 6 categories:

| Category | Blockers Detected |
|---|---|
| Experience Barrier | Experience inflation, Senior-dominated domain |
| Portfolio Barrier | Portfolio dependency, GitHub explicitly required |
| Academic Barrier | CGPA filter, Premium institute preference, PG degree required |
| Technical Depth Barrier | Math-heavy role, DSA-intensive, System design expected |
| Logistics Barrier | Relocation mandatory, Service bond/commitment |
| Market Barrier | Applicant surge (extreme competition) |
| Technical Barrier | Niche proprietary tool lock (SAP, Salesforce, etc.) |

It also detects **blocker combinations** — when multiple blockers co-occur, their combined effect is worse than each individually. For example, "Experience inflation + Applicant surge" is a "Double Entry Lock" that is far harder to overcome than either alone.

> Think of it like a pre-flight checklist for a pilot. Before takeoff, you systematically check every critical system — not just the ones you remember. This engine runs a structured scan of every known entry barrier for a domain so nothing is missed.

---

## 2. Data Fields Required by This Engine

### Required

| Column Name | What it Means | Required? |
|---|---|---|
| `Job_Type` | Domain/category of the job | ✅ Primary domain filter |

### Strongly Recommended (each powers specific detectors)

| Column Name | Powers Which Blockers | Fallback if Missing |
|---|---|---|
| `Min_Experience` | Experience inflation, Senior-dominated | Experience blockers not detected |
| `Description_Cleaned` | ALL 11 keyword-based blockers | Entire description blocker category returns empty |
| `No of applicant applied cleaned` | Applicant surge market blocker | Market blocker not detected |
| `No of job opening cleaned ` | Applicant surge (ratio denominator) | 1 opening per listing assumed |
| `Title_Cleaned` (or `TItle_Cleaned`) | Domain filter fallback | Domain filter may miss records |

### Inputs Passed at Runtime

| Parameter | What it Means | Default |
|---|---|---|
| `target_domain` | Domain to scan (e.g., `"Data Scientist"`) | Required |
| `experience_band` | Tuple `(min_exp, max_exp)` for fresher/junior focus | `(0, 3)` |
| `custom_weights` | Override blocker severity weights (set in `__init__`) | Default weights |

---

## 3. Core Logic — How Does the Engine Detect Blockers?

The engine runs **three independent detector modules** plus a post-processing stage.

---

### Detector 1 — Experience Blockers (`_detect_experience_blockers`)

Detects two experience-related barriers using **market-relative thresholds** — not hardcoded cutoffs.

---

#### Blocker A: Experience Inflation

**What it detects:** This domain has very few jobs genuinely open to freshers (0–1 year experience) compared to the overall market.

**Formula:**
```
fresher_pct       = fraction of domain postings with Min_Experience ≤ 1 year × 100
market_threshold  = P25 of fresher_pct across ALL domains in dataset
                    (i.e., bottom 25% of market is the baseline)

Triggers if: fresher_pct < market_threshold

Severity gap = (market_threshold − fresher_pct) / market_threshold
Severity     = gap × blocker_weight (0.90)
```

**Plain English Example:**

Across all domains, the P25 market baseline for fresher-friendly postings is 28%. "Data Analyst" only has 12% of postings accepting 0–1 year exp.

```
gap = (28 − 12) / 28 = 0.571
severity = 0.571 × 0.90 = 0.514
evidence = "Only 12.0% of postings accept 0-1yr exp (market avg: 28.0%)"
```

**Why P25 as threshold?** The bottom 25% of all domains represents the market's normal floor for fresher accessibility. A domain below this floor is genuinely hostile to freshers, not just moderately selective.

---

#### Blocker B: Senior-Dominated

**What it detects:** More than half the domain's job postings require 3+ years of experience — freshers are structurally outcompeted by experienced candidates applying to the same postings.

```
senior_pct       = fraction with Min_Experience ≥ 3 years × 100
senior_threshold = baselines.get('senior_pct_p75', 50.0)
                   (fallback: 50% if no market baseline available)

Triggers if: senior_pct > senior_threshold

Severity = (senior_pct / 100) × blocker_weight (0.80)
```

---

### Detector 2 — Description Blockers (`_detect_description_blockers`)

Scans the `Description_Cleaned` text of all job postings in the domain for **11 blocker types** using word-boundary regex matching. Each blocker has its own keyword list and trigger threshold.

**Core scoring function (`_safe_keyword_pct`):**
```
valid = descriptions.dropna()
pattern = \b(?:keyword1|keyword2|...)\b   ← word-boundary regex for all keywords
pct = fraction of valid descriptions containing any keyword × 100
```

**Per-blocker thresholds** (triggers if `pct ≥ threshold`):

| Blocker | Threshold | Rationale |
|---|---|---|
| `portfolio_dependency` | 40% | Common in creative/dev roles — triggers when majority of JDs mention it |
| `github_required` | 35% | Significant signal once 1 in 3 JDs explicitly require it |
| `math_heavy` | 35% | Mathematical theory is a real capability barrier — trigger at 1 in 3 |
| `dsa_intensive` | 35% | DSA preparation takes months — trigger at meaningful signal level |
| `system_design_required` | 25% | Even 1 in 4 JDs mentioning this is significant for entry-level |
| `cgpa_filter` | 20% | Even 1 in 5 is a real blocker — credentials can't be easily changed |
| `premium_degree` | 15% | College tier is completely immutable — very low threshold justified |
| `pg_required` | 20% | Advanced degree takes years — even 1 in 5 mentions is a serious barrier |
| `relocation_mandatory` | 20% | High life-impact even if rare in job descriptions |
| `bond_agreement` | 15% | Contractual commitment — low threshold because impact is severe |
| `niche_tool_lock` | 25% | Proprietary tools take months to certify in |

**Severity formula (normalized distance above threshold):**
```
normalized = min(1.0, (pct − threshold) / threshold + 0.3)
severity   = normalized × blocker_weight

At threshold exactly:     normalized = 0.0 + 0.3 = 0.30 → "mild trigger"
At 2× the threshold:      normalized = 1.0 + 0.3 → clipped to 1.0 → "maximum"
```

The `+0.3` ensures that even a barely-triggered blocker has a meaningful minimum severity of `0.3 × weight` — it's not treated as zero just because it barely crossed the threshold.

**Plain English Example:**

`dsa_intensive` has threshold = 35%, weight = 0.75.

- Domain has 55% of JDs mentioning DSA keywords:
  ```
  normalized = min(1.0, (55-35)/35 + 0.3) = min(1.0, 0.571+0.3) = 0.871
  severity   = 0.871 × 0.75 = 0.653
  evidence   = "55.0% of job descriptions mention this requirement (threshold: 35%)"
  ```

- Domain has 36% (just above threshold):
  ```
  normalized = min(1.0, (36-35)/35 + 0.3) = min(1.0, 0.029+0.3) = 0.329
  severity   = 0.329 × 0.75 = 0.247  ← mild but real signal
  ```

---

### Detector 3 — Market Blockers (`_detect_market_blockers`)

Detects the **applicant surge** blocker using market-relative P75 threshold.

```
domain_ratio     = clipped_applicants.sum() / max(openings.sum(), 1)
surge_threshold  = baselines['applicant_ratio_p75']
                   (P75 of all domain applicant/opening ratios in dataset)

Triggers if: domain_ratio > surge_threshold

normalized = min(1.0, (ratio − threshold) / threshold + 0.3)
severity   = normalized × 0.85
```

**Outlier clipping:** Applicant counts clipped at 95th percentile before summing — prevents one viral job posting from falsely triggering the blocker for an otherwise normal domain.

---

### Post-Processing — Market Baselines

Before any detector runs, `_compute_market_baselines()` scans the **entire dataset** to compute adaptive thresholds:

| Baseline | How Computed | Used By |
|---|---|---|
| `fresher_pct_p25` | P25 of fresher% across all domains | Experience inflation threshold |
| `fresher_pct_p50` | P50 (median) of fresher% | Reference point |
| `applicant_ratio_p75` | P75 of applicant/opening ratio across all domains | Applicant surge threshold |
| `applicant_ratio_p90` | P90 of applicant/opening ratio | Extreme surge reference |

**Why this matters:** A domain with 18:1 applicant ratio might be perfectly normal in a competitive market, or it might be at the 80th percentile. Without market-wide baselines, a hardcoded threshold of "20:1 = surge" would give wrong signals in different datasets.

---

### Post-Processing — Blocker Interaction Analysis

When multiple blockers are detected together, their compound effect is worse than each individually. Six interaction rules are checked:

| Interaction | Blocker Combo | Label | Penalty |
|---|---|---|---|
| 1 | experience_inflation + applicant_surge | 🚨 Double Entry Lock | +0.15 |
| 2 | math_heavy + dsa_intensive + system_design_required | 🔬 Full Technical Gauntlet | +0.20 |
| 3 | cgpa_filter + premium_degree | 🎓 Double Credential Lock | +0.15 |
| 4 | portfolio_dependency + github_required | 💻 Full Proof-of-Work Required | +0.10 |
| 5 | experience_inflation + pg_required | 📚 Experience + Education Lock | +0.20 |
| 6 | bond_agreement + relocation_mandatory | ⛓️ Commitment Lock | +0.10 |

Interaction detection uses **set subset check**: `rule["combo"].issubset(detected_blocker_ids)` — only triggers if ALL blockers in the combo are present.

---

### Final Score — Diminishing Returns Combination

The final risk score combines all blocker severities using a **diminishing returns formula**:

```
Sort severities descending: [s1, s2, s3, ...]

combined = s1×0.8⁰ + s2×0.8¹ + s3×0.8² + s4×0.8³ + ...
         = s1×1.0 + s2×0.8 + s3×0.64 + s4×0.512 + ...

combined = min(1.0, combined + interaction_penalty)
```

**Why diminishing returns?** If a domain has 8 blockers, the 8th blocker doesn't make it infinitely hard — the maximum possible difficulty is still bounded at 1.0. Each additional blocker contributes progressively less because you're already dealing with a very hard situation. The 0.8 decay factor means the 5th blocker contributes only `0.8⁴ = 41%` of what the first blocker contributed.

**Risk Labels:**

| Combined Score | Label | Color |
|---|---|---|
| < 0.20 | 🟢 Low Barrier | Green |
| 0.20 – 0.39 | 🟡 Moderate Barrier | Yellow |
| 0.40 – 0.59 | 🟠 High Barrier | Orange |
| 0.60 – 0.79 | 🔴 Very High Barrier | Red |
| ≥ 0.80 | 🚨 Extreme Barrier — Expect Rejections | Dark Red |

---

## 4. Blocker Weights — What They Mean and Why

| Blocker | Weight | Justification |
|---|---|---|
| `experience_inflation` | **0.90** | Highest weight — lack of fresher-level openings is the single largest structural barrier. You can't overcome what doesn't exist. |
| `applicant_surge` | **0.85** | Near-highest — extreme competition multiplies the effect of every other barrier. |
| `bond_agreement` | **0.85** | Very high — contractual commitment is irreversible once signed. Risk compounds over time. |
| `portfolio_dependency` | **0.80** | High — portfolio takes weeks/months to build. Can't be faked or rushed. |
| `senior_dominated` | **0.80** | High — structural seniority bias means freshers compete against experienced candidates for same roles. |
| `pg_required` | **0.75** | A degree takes years — even if rare in JDs, when it appears it's a hard barrier. |
| `dsa_intensive` | **0.75** | DSA mastery requires 3–6 months of dedicated practice minimum. |
| `github_required` | **0.75** | Active GitHub takes time to build — not fixable overnight. |
| `cgpa_filter` | **0.70** | CGPA is past and immutable — candidate cannot change it. Only workarounds possible. |
| `math_heavy` | **0.70** | Theoretical math takes dedicated study over months. |
| `system_design_required` | **0.70** | System design knowledge requires real project or study experience. |
| `niche_tool_lock` | **0.65** | Certifications available but time-consuming and sometimes costly. |
| `premium_degree` | **0.65** | College tier is completely immutable — cannot be changed. But product startups often ignore it. |
| `relocation_mandatory` | **0.60** | Lowest — relocation is a personal decision, not a capability gap. Manageable with planning. |

---

## 5. Functions — What They Do and How They Are Called

```
scan_for_blockers()                        ← Main entry point (you call this)
    │
    ├── _filter_domain()                   → Domain rows with experience band filter
    ├── _compute_market_baselines()        → P25/P75 adaptive thresholds from full dataset
    │
    ├── _detect_experience_blockers()      → Experience inflation + senior-dominated
    │       └── [inline] market-relative severity calculation
    │
    ├── _detect_description_blockers()     → 11 keyword-based blockers in one pass
    │       └── _safe_keyword_pct()        → Word-boundary keyword scan, returns (%, n_valid)
    │
    ├── _detect_market_blockers()          → Applicant surge with P75 market threshold
    │
    ├── _analyze_blocker_interactions()    → 6 interaction rules, set-subset detection
    └── _normalize_risk_score()            → Diminishing returns combination + interaction penalty
```

| Function | Role |
|---|---|
| `__init__()` | Sets up logger, applies optional custom weight overrides per blocker |
| `_filter_domain()` | Job_Type exact + experience filter + title word-boundary fallback |
| `_safe_keyword_pct()` | NaN-safe word-boundary keyword scan, returns `(match_%, n_valid)` |
| `_compute_market_baselines()` | Scans full dataset to build P25/P75 adaptive thresholds |
| `_detect_experience_blockers()` | Market-relative experience inflation + seniority bias detection |
| `_detect_description_blockers()` | One-pass scan of 11 description-based blockers with per-blocker thresholds |
| `_detect_market_blockers()` | Applicant surge detection with viral outlier clipping |
| `_analyze_blocker_interactions()` | Set-subset combo detection for 6 compound blocker patterns |
| `_normalize_risk_score()` | Diminishing returns combination with interaction penalty and 5-tier labeling |
| `scan_for_blockers()` | **Master function** — runs all detectors, assembles full report |

---

## 6. Output — What Does the Engine Return?

### Sample Output

```json
{
    "Domain": "Data Scientist",
    "Experience_Band": [0, 3],
    "Sample_Size": 184,

    "Overall_Risk": {
        "score": 0.71,
        "label": "🔴 Very High Barrier",
        "color": "Red"
    },

    "Detected_Blockers": [
        {
            "blocker_id": "dsa_intensive",
            "category": "Technical Depth Barrier",
            "severity": 0.653,
            "evidence": "55.0% of job descriptions mention this requirement (threshold: 35%)",
            "message": "Strong DSA/competitive programming expected in interviews"
        },
        {
            "blocker_id": "experience_inflation",
            "category": "Experience Barrier",
            "severity": 0.514,
            "evidence": "Only 12.0% of postings accept 0-1yr exp (market avg: 28.0%)",
            "message": "Entry-level roles scarce — prior experience effectively required"
        },
        {
            "blocker_id": "applicant_surge",
            "category": "Market Barrier",
            "severity": 0.489,
            "evidence": "68 applicants per opening (market P75: 42)",
            "message": "Extremely high applicant-to-opening ratio"
        },
        {
            "blocker_id": "math_heavy",
            "category": "Technical Depth Barrier",
            "severity": 0.318,
            "evidence": "38.0% of job descriptions mention this requirement (threshold: 35%)",
            "message": "Heavy theoretical math (statistics, calculus, linear algebra) expected"
        }
    ],

    "Blocker_Interactions": [
        {
            "label": "🚨 Double Entry Lock",
            "message": "Scarce fresher roles + massive competition. Breaking in requires exceptional differentiation.",
            "penalty": 0.15
        },
        {
            "label": "🔬 Full Technical Gauntlet",
            "message": "3-layer technical interview expected: math theory + DSA + system design.",
            "penalty": 0.20
        }
    ],

    "Priority_Actions": [
        {"blocker": "dsa_intensive",       "action": "Solve 150+ LeetCode problems (focus on medium). Practice arrays, trees, DP patterns."},
        {"blocker": "experience_inflation", "action": "Target internships, freelance projects, or open-source to build verifiable experience before applying."},
        {"blocker": "applicant_surge",      "action": "Apply within 24 hours of posting. Use referrals. Customize every application."},
        {"blocker": "math_heavy",           "action": "Complete Khan Academy Statistics + Linear Algebra before applying. Practice ML theory questions."}
    ],

    "Blocker_Summary": {
        "Total_Blockers": 4,
        "Categories_Affected": ["Technical Depth Barrier", "Experience Barrier", "Market Barrier"],
        "Highest_Severity": "dsa_intensive"
    }
}
```

### How to Read This Output

| Field | What it Tells the User |
|---|---|
| `Overall_Risk.score` | Single headline difficulty number |
| `Detected_Blockers` | Every specific wall — ranked by severity (worst first) |
| `Detected_Blockers[n].evidence` | **The exact number that triggered it** — not vague, concrete |
| `Detected_Blockers[n].resolution` | What to do about THIS specific blocker |
| `Blocker_Interactions` | When multiple blockers compound — the "double trouble" warnings |
| `Priority_Actions` | **Top 4 actionable steps ranked by severity** — the do-this-first list |

---

## 7. How Robust Are the Formulas and Constants?

### What Makes Them Solid ✅

| Feature | Why It's Good |
|---|---|
| **Market-relative thresholds via baselines** | Experience inflation and applicant surge thresholds adapt to the actual dataset — not fixed numbers that become irrelevant as the job market changes. |
| **Diminishing returns combination** | Prevents "8 mild blockers = infinite difficulty". Each additional blocker contributes progressively less. Bounded at 1.0. More realistic than simple addition. |
| **Interaction penalties are additive to combined score** | Compound blockers add penalty ON TOP of the already-combined score — capturing the real compounding effect. |
| **Per-blocker trigger thresholds (not uniform)** | Bond/relocation trigger at 15% because even rare mentions are high-impact. GitHub triggers at 35% because it's a common standard. Context-sensitive calibration. |
| **Severity normalized distance formula** | `(pct − threshold) / threshold + 0.3` — a barely-triggered blocker gets a meaningful minimum severity (0.3×weight), while heavily triggered ones approach maximum. No binary on/off. |
| **95th percentile clipping for applicants** | Prevents one viral posting from falsely triggering market blocker for an otherwise normal domain. |
| **Word-boundary regex in `_safe_keyword_pct`** | `\b` boundaries prevent "bond" matching "bond trading" or "algorithm" matching "algorithmic". Critical for description text which is noisy. |
| **Interaction detection via set subset** | `rule["combo"].issubset(detected_blocker_ids)` is mathematically exact — only fires when all required blockers are present. |
| **Custom weight override** | Users can reduce the weight of `relocation_mandatory` to 0.2 if they're willing to relocate, making the engine personalized to their specific situation. |
| **`_safe_keyword_pct` returns `n_valid`** | Engine skips a blocker if fewer than 3 valid descriptions exist — prevents false triggering from a handful of noisy records. |

---

## 8. Advantages of the Current Implementation

- **The only engine that reads job descriptions for hidden requirements** — captures information invisible to all other engines that work on structured columns.
- **14 specific, named blockers with individual resolutions** — not a generic "domain is hard" score but a specific "your CGPA might be filtered" with concrete action steps.
- **Interaction patterns** — the compound effect analysis is unique. A "Full Technical Gauntlet" warning (math + DSA + system design) is far more useful than three separate moderate-severity flags.
- **Market-adaptive thresholds** — baselines prevent the engine from producing wrong signals in different market conditions or different datasets.
- **Evidence strings** — every detected blocker includes the exact number that triggered it ("55% of JDs mention DSA"). This builds user trust — they can verify the finding.
- **Priority Actions ranked by severity** — the top 4 actions are sorted from most critical to least. The user knows exactly where to start.
- **Customizable weights** — recruiters, counselors, or users with specific constraints (willing to relocate, already have PG degree) can adjust weights at init time.

---

## 9. Disadvantages and How to Improve Them

| Limitation | Problem | Suggested Fix |
|---|---|---|
| **`senior_pct_p75` baseline never computed** | `_detect_experience_blockers()` line: `senior_threshold = baselines.get('senior_pct_p75', 50.0)`. But `_compute_market_baselines()` only computes `fresher_pct_p25` and `fresher_pct_p50` — it never computes `senior_pct_p75`. So the senior-dominated blocker always uses the hardcoded fallback of 50%. The market-adaptive design is broken for this specific blocker. | Add `senior_pcts` computation to `_compute_market_baselines()` alongside `fresher_pcts`: `senior_pct = (d['Min_Experience'] >= 3).mean() * 100` per domain, then `baselines['senior_pct_p75'] = np.percentile(senior_pcts, 75)`. |
| **Description-based blockers silently skip when `Description_Cleaned` is missing** | `_detect_description_blockers()` returns `[]` immediately if column not present. The output shows 0 description blockers — which looks like a clean bill of health when really the data is just missing. No warning in the output. | Add a `data_warnings` field to the output: `"Data_Warnings": ["Description_Cleaned column missing — 11 description-based blockers could not be evaluated."]`. This prevents users from misinterpreting "no blockers" as "no problems." |
| **Keyword thresholds are still hardcoded inside `_detect_description_blockers()`** | The `thresholds` dict inside the function has hardcoded values (40%, 35%, 20% etc.). These made sense for a specific market snapshot but aren't adaptive to dataset characteristics. A dataset of only niche startups might see 70% of JDs mentioning GitHub — making 35% too low. | Move these thresholds to a class-level constant `BLOCKER_THRESHOLDS` (similar to how `BLOCKER_DEFINITIONS` is structured). Better yet, make each threshold market-adaptive: compute P50 of each keyword's occurrence frequency across all domains and use that as the threshold. |
| **`_compute_market_baselines()` scans the entire dataset on every call** | `scan_for_blockers()` calls `_compute_market_baselines(df, ...)` every time it runs — even if the same `df` is used for multiple domain scans in a row. This is an O(n × domains) operation repeated unnecessarily. | Cache the baselines: `if not hasattr(self, '_baselines_cache'): self._baselines_cache = self._compute_market_baselines(df, experience_band)`. Add a `reset_cache()` method for when data changes. |
| **`applicant_surge` blocker missing from `BLOCKER_KEYWORDS`** | The `BLOCKER_KEYWORDS` dict has 11 entries — but `applicant_surge` is not among them (it's detected structurally from data, not from JD text). The `_detect_description_blockers()` loop skips any blocker not in `BLOCKER_KEYWORDS`. This is correct behavior but creates a subtle inconsistency — `applicant_surge` is in `BLOCKER_DEFINITIONS` but not in `BLOCKER_KEYWORDS`, which could confuse future developers maintaining this code. | Add a code comment above `BLOCKER_KEYWORDS` explicitly stating: `# Note: 'experience_inflation', 'senior_dominated', 'applicant_surge' are detected from structured data columns, not from keyword scan. They are intentionally absent from this dict.` |
| **Custom weight override mutates the class-level `BLOCKER_DEFINITIONS` dict** | In `__init__()`: `self.BLOCKER_DEFINITIONS[key]["weight"] = val`. This modifies the class-level dictionary directly — not an instance copy. If two instances of `HiddenBlockerDetector` are created with different custom weights, the second one's weights will overwrite the first instance's weights on the shared class dict. | In `__init__()`, make an instance-level deep copy: `self.BLOCKER_DEFINITIONS = {k: dict(v) for k, v in self.__class__.BLOCKER_DEFINITIONS.items()}` before applying custom weights. |
| **Interaction analysis only checks 6 predefined combos** | The 6 interaction rules cover the most common compound barriers. But there could be emerging combinations — e.g., `niche_tool_lock + pg_required` = a very narrow candidate profile. Unlisted combinations produce no interaction signal. | Make interaction rules data-driven: if any 3+ blockers from different categories are active simultaneously, generate a generic "Multi-dimensional barrier — comprehensive preparation required" warning, even if no specific rule matches. |

### Formula Improvement Suggestions

```python
# Current: diminishing returns with fixed 0.8 decay
combined += s * (0.8 ** i)

# Improved: make decay rate configurable and context-aware
# If first blocker is very severe (>0.7), decay faster — additional blockers matter less
# If first blocker is mild (<0.3), decay slower — additional blockers accumulate more meaningfully
first_severity = severities[0] if severities else 0
decay = 0.75 if first_severity > 0.7 else 0.85
combined = sum(s * (decay ** i) for i, s in enumerate(severities))
```

```python
# Current: severity at threshold = 0.3 × weight (fixed floor)
normalized = min(1.0, (pct - threshold) / threshold + 0.3)

# Improved: make the floor proportional to how impactful the blocker is
# High-weight blockers (bond=0.85) deserve a higher floor than low-weight (relocation=0.60)
weight = defn["weight"]
floor  = 0.2 + weight * 0.15   # ranges from 0.29 to 0.33
normalized = min(1.0, (pct - threshold) / threshold + floor)
# This means even a barely-triggered bond blocker starts at 0.30×0.85=0.255 severity
# while a barely-triggered relocation blocker starts at 0.29×0.60=0.174 severity
```

```python
# Current: market baselines computed from full df for all domains
# (runs once per scan_for_blockers call but still expensive)

# Improved: cache baselines as instance state, invalidate when df hash changes
import hashlib

def _get_df_hash(self, df):
    return hashlib.md5(pd.util.hash_pandas_object(df).values).hexdigest()[:8]

def scan_for_blockers(self, df, target_domain, experience_band=(0, 3)):
    df_hash = self._get_df_hash(df)
    cache_key = f"{df_hash}_{experience_band}"
    if not hasattr(self, '_baseline_cache') or self._cache_key != cache_key:
        self._baseline_cache = self._compute_market_baselines(df, experience_band)
        self._cache_key = cache_key
    baselines = self._baseline_cache
    # ... rest of method
```

---

*End of Engine 10 Documentation*

---
---

# Engine 11 — `PrerequisiteEngine` (Prerequisite & Learning Path Engine)

**File:** `prequisite_engine.py`  
**Class:** `PrerequisiteEngine`

---

## 1. Introduction — What is this Engine and What Does it Do?

Every other engine in the pipeline tells you about the market — what it pays, how competitive it is, how risky it is. This engine turns inward and asks a completely personal question:

> *"Given MY specific skills today, what exactly do I need to learn to be job-ready for this domain — and in what ORDER should I learn it?"*

The word "order" is the critical difference from a simple skill gap list. You can't learn Deep Learning before you know Python. You can't learn Machine Learning before you know Statistics. You can't learn Kubernetes before you know Docker. Skills have dependencies — just like software packages. Installing a package before its dependency is available causes a crash. Trying to learn an advanced topic before its foundations are solid causes confusion and wasted time.

**`PrerequisiteEngine` solves the sequencing problem.** It maintains a hand-crafted **Skill Dependency Tree** of 80+ skills covering all major tech domains, and for any domain + user skill combination it computes:

1. **Domain Complexity** — How deep is the prerequisite chain? How broad is the skill surface? Combined into a single complexity index.
2. **User Readiness Score** — Given your current skills, what fraction of the domain's requirements do you already cover? (Weighted by importance, not just count)
3. **Missing Skills — Ranked by Priority** — Which skills are most important in the target domain that you don't have?
4. **Learning Path with Topological Ordering** — The exact sequence to learn all needed skills, ensuring every prerequisite appears before its dependent skill.
5. **Can Start Now** — Which skills on the path can you begin today, without needing to learn anything else first?

> Think of it like a university curriculum designer. A good curriculum doesn't just list courses — it sequences them so that every course builds on what came before. This engine does the same for your personal career learning plan, using actual job posting data to determine what the market values.

---

## 2. Data Fields Required by This Engine

### Required

| Column Name | What it Means | Required? |
|---|---|---|
| `Job_Type` | Domain/category of the job | ✅ Primary domain filter |
| At least one skill column | `Star_Skills`, `Combined_Skills`, or `Normal_Skills` | ✅ Core — skills determine the learning path |

### Recommended

| Column Name | What it Means | Fallback if Missing |
|---|---|---|
| `Star_Skills` | Must-have skills (2× weight in profile) | Skipped |
| `Combined_Skills` | All skills (1× weight) | Skipped |
| `Normal_Skills` | Nice-to-have skills (0.6× weight) | Skipped |
| `Title_Cleaned` (or `TItle_Cleaned`) | Job title for domain fallback | Domain filter may miss records |
| `Min_Experience` | Min experience required | Experience filter skipped |
| `Education_Cleaned` | Education requirements | Education signal not generated |
| `PG_Degree`, `UG_Degree` | Degree columns | Degree signal not generated |

### Inputs Passed at Runtime

| Parameter | What it Means | Default |
|---|---|---|
| `target_domain` | Domain to analyze (e.g., `"Data Science"`) | Required |
| `user_skills` | List of skills you currently have (e.g., `["Python", "SQL"]`) | Required |
| `experience_band` | Tuple `(min_exp, max_exp)` | `(0, 3)` |
| `custom_skill_tree` | Additional skill dependencies to extend the tree (set in `__init__`) | `None` |

---

## 3. Core Logic — How Does the Engine Build the Learning Path?

The engine has 6 distinct analytical steps, each building on the previous.

---

### Step 1 — The Skill Dependency Tree (SKILL_TREE)

The `SKILL_TREE` is the engine's knowledge base — a hand-crafted dictionary where each skill maps to its prerequisites:

```
skill → [list of skills you must know BEFORE this]
```

**Selected dependencies (showing the chain structure):**

```
logic → programming basics → python → machine learning
                                   ↗
basic math → calculus → statistics
           → probability ↗
           → linear algebra ↗

programming basics → python → data analysis ← sql ← logic
                             → pandas
                             → numpy ← linear algebra
```

**Depth example — how deep is `deep learning`?**
```
deep learning requires: machine learning, linear algebra, calculus
machine learning requires: statistics, python, linear algebra
statistics requires: calculus, probability
calculus requires: basic math
probability requires: basic math
basic math: no prerequisites (depth = 0)

Max depth of deep learning = 4 levels deep
```

**Cycle detection at initialization:**

The tree is validated for cycles when the engine is created using DFS (Depth-First Search):
```python
def has_cycle(node, visited, rec_stack):
    visited.add(node)
    rec_stack.add(node)
    for prereq in skill_tree[node]:
        if prereq not in visited:
            if has_cycle(prereq, visited, rec_stack):
                return True   # Found cycle
        elif prereq in rec_stack:
            return True       # Found cycle back to current path
    rec_stack.discard(node)
    return False
```

If `custom_skill_tree` is passed with a circular dependency (e.g., A requires B, B requires A), the engine raises a `ValueError` immediately at `__init__()` — not at runtime when it would be much harder to debug.

---

### Step 2 — Skill Normalization (`_normalize_user_skills`)

User inputs are messy — "Python3", "ReactJS", "k8s", "ML" all need to be standardized before they can be matched against the skill tree or domain profiles.

**Alias dictionary (24 mappings):**

| User Input | Normalized To |
|---|---|
| `python3`, `python 3`, `py` | `python` |
| `js` | `javascript` |
| `react.js`, `reactjs` | `react` |
| `node`, `nodejs` | `node.js` |
| `ml` | `machine learning` |
| `dl` | `deep learning` |
| `tf` | `tensorflow` |
| `sklearn`, `scikit learn` | `scikit-learn` |
| `postgres` | `postgresql` |
| `mongo` | `mongodb` |
| `k8s` | `kubernetes` |
| `ts` | `typescript` |
| `vue` | `vue.js` |
| `spring` | `spring boot` |
| `fast api` | `fastapi` |
| `cv` | `computer vision` |

Additional normalization: all inputs are lowercased and multiple spaces collapsed.

---

### Step 3 — Domain Skill Profile (`_extract_domain_skills`)

Builds an importance-weighted skill profile from the domain's job postings — exactly like the SkillTransferabilityEngine but with a slightly different weight for `Normal_Skills` (0.6 here vs 0.7 there).

```
skill_importance[skill] = weighted_count / total_postings
```

Skills with importance < 0.02 (appear in fewer than 2% of postings) are filtered out as noise.

**Skill parsing handles two storage formats:**

```
Format A (Python list literal): "['python', 'machine learning', 'sql']"
→ uses ast.literal_eval() for safe evaluation

Format B (plain CSV): "python, machine learning, sql"
→ splits by comma, strips stray quotes/brackets
```

Both formats are gracefully handled in `_parse_skills_string()`.

---

### Step 4 — Domain Complexity Analysis

Rather than just counting skills or finding the deepest one, the engine computes a **Complexity Index** that combines two dimensions:

```
depth_values    = [_get_max_depth(skill) for skill in required_skills]
max_depth       = max(depth_values)
avg_depth       = mean(depth_values)
skill_count     = number of required skills

breadth_component = min(skill_count / 15, 4.0)
complexity_index  = (max_depth × 0.6) + (breadth_component × 0.4)
```

**Why both dimensions?**

| Scenario | Max Depth | Skill Count | What it means |
|---|---|---|---|
| Domain A: 5 skills, all depth 4 | 4 | 5 | Deep theoretical foundation, narrow scope |
| Domain B: 50 skills, all depth 1 | 1 | 50 | Broad surface, no deep theory |
| Domain C: 15 skills, depth 3–4 | 4 | 15 | Both deep AND broad — hardest |

Plain depth alone would rate Domain A and C equally. Plain breadth alone would rate B and C equally. The combined index correctly identifies C as hardest.

**Complexity index thresholds:**

| Index | Classification | Barrier Level |
|---|---|---|
| < 1.0 | 🟢 Direct Entry — minimal prerequisites | Very Low |
| 1.0 – 1.9 | 🟡 Basic Foundation — 1–2 months prep | Low |
| 2.0 – 2.9 | 🟠 Intermediate Foundation — 3–6 months prep | Medium |
| 3.0 – 3.9 | 🔴 Deep Foundation — 6–12 months structured learning | High |
| ≥ 4.0 | 🚨 Expert Prerequisites — 12+ months before job-ready | Very High |

---

### Step 5 — User Readiness Score

Measures how well the user's current skills cover the domain's requirements — using importance weighting, not just count.

```
weighted_coverage = Σ target_importance[skill] for skill in (user_skills ∩ required)
max_possible      = Σ target_importance[skill] for all required skills

count_ratio       = len(user_skills ∩ required) / len(required)

composite = 0.60 × weighted_coverage + 0.40 × count_ratio
```

**Why weighted coverage matters more than count ratio:**

You could have 3 out of 10 required skills but those 3 are Python, SQL, and Machine Learning — the highest-importance ones. You'd have low count_ratio (30%) but high weighted_coverage (say, 65%). The composite score at 60/40 correctly reflects that you're more prepared than 30% suggests.

**5-tier readiness labels:**

| Composite | Status |
|---|---|
| ≥ 0.75 | 🟢 Strong Ready — minor gaps only |
| 0.55 – 0.74 | 🟡 Mostly Ready — a few key skills to add |
| 0.35 – 0.54 | 🟠 Partially Ready — meaningful upskilling needed |
| 0.15 – 0.34 | 🔴 Early Stage — significant learning ahead |
| < 0.15 | ⚪ Starting Fresh — build from foundations |

---

### Step 6 — Learning Path with Topological Ordering

This is the most sophisticated part of the engine. It doesn't just list missing skills — it sequences them correctly.

**Algorithm:**

```
Step A: Find ALL prerequisites recursively for each missing skill
        using _get_full_prereq_chain()

Step B: to_learn = all_needed_skills − user_skills_normalized

Step C: Topological sort using DFS
        → Skills with no prerequisites (in to_learn) come first
        → Skills whose all prerequisites are in to_learn come later
        → Produces an ordered list where no skill appears before its dependency

Step D: Simulate progressive acquisition
        acquired = set(user_skills_normalized)  ← starts with what you have
        for each skill in topological order:
            can_start_now  = all prereqs already in user_skills_normalized
            prereq_ready   = all prereqs in acquired (user has OR will learn them earlier in path)
            acquired.add(skill)  ← mark as learned for subsequent skills
```

**The `acquired` simulation is the critical fix.** Without it, `prereq_ready` would always be False for skills that depend on other skills in the learning path — because the user hasn't learned those yet. The simulation walks through the path in order, marking each skill as "acquired" so downstream skills correctly see their prerequisites as ready.

**Plain English Example:**

User knows: `python`, `sql`  
Target domain needs: `machine learning`, `deep learning`, `tensorflow`

Prerequisite chains:
- `machine learning` needs: `statistics`, `linear algebra` (user missing both)
- `deep learning` needs: `machine learning`, `linear algebra`, `calculus`
- `tensorflow` needs: `deep learning`, `python` (python ✅ already known)

Topological order (correct sequence):
```
1. basic math        (can_start_now: ✅ — no prerequisites)
2. calculus          (can_start_now: ✅ — only needs basic math)
3. probability       (can_start_now: ✅ — only needs basic math)
4. linear algebra    (can_start_now: ✅ — only needs basic math)
5. statistics        (prereq_ready after step 3-4, can_start_now: ❌ — needs calc+prob)
6. machine learning  (prereq_ready after step 5, can_start_now: ❌)
7. deep learning     (prereq_ready after step 6, can_start_now: ❌)
8. tensorflow        (prereq_ready after step 7, can_start_now: ❌)
```

The `can_start_now` flag correctly marks steps 1–4 as immediately actionable — the user can begin these today without learning anything else first.

---

## 4. Constants and Parameters — What They Mean and Why

| Constant / Parameter | Value | Justification |
|---|---|---|
| `Star_Skills` weight | **2.0×** | Must-have skills — missing them = rejection. Same logic as Transferability and Stability engines. |
| `Combined_Skills` weight | **1.0×** | Standard. |
| `Normal_Skills` weight | **0.6×** | Slightly lower than SkillTransferabilityEngine's 0.7× — prerequisites analysis cares more about must-haves. |
| Importance threshold | **0.02** | Skills in fewer than 2% of postings are irrelevant noise — stricter than the 1% threshold in other engines because this engine produces a concrete learning plan. |
| Complexity depth weight | **0.6** | Depth is more important than breadth for entry difficulty — a domain requiring 4 levels of sequential learning is harder to enter than one with 60 independent shallow skills. |
| Complexity breadth component | **min(skill_count/15, 4.0)** | Normalizes breadth to a 0–4 scale. 15 skills = 1.0, 30 skills = 2.0, 60+ skills = 4.0 (capped). |
| Readiness composite split | **60% weighted + 40% count** | Having the *right* skills matters more than having *many* skills. Same rationale as SkillTransferabilityEngine. |
| `DEFAULT_WEEKS` | **5** | Conservative default for skills not in `LEARNING_WEEKS`. 5 weeks at 10 hrs/week = 50 hours, reasonable for a moderate new skill. |
| Learning pace | **10 hrs/week** | Realistic for a working professional studying on the side. Consistent with all other time-estimate engines. |
| Months conversion | **÷ 4.3** | 52 weeks / 12 months = 4.333. More accurate than ÷ 4. |
| Missing skills cap for path | **Top 15** | Learning path is built for top 15 missing skills. Beyond that, the path becomes unwieldy — a user should focus on the most impactful 15 first. |
| Priority actions shown | **Top 10** | `Missing_Skills_Prioritized` returns top 10 by importance. Enough to plan without overwhelming. |

---

## 5. Functions — What They Do and How They Are Called

```
analyze_prerequisites()                   ← Main entry point (you call this)
    │
    ├── _filter_domain()                  → Domain rows with experience filter
    ├── _extract_domain_skills()          → Weighted skill importance profile
    │       └── _parse_skills_string()    → Handles list-literal AND CSV formats
    ├── _normalize_user_skills()          → Alias resolution + lowercase normalization
    ├── _analyze_domain_complexity()      → Complexity index (depth × 0.6 + breadth × 0.4)
    │       └── _get_max_depth()          → Recursive depth with cycle guard (immutable visited)
    ├── _calculate_readiness()            → Importance-weighted coverage + count ratio composite
    ├── [Inline] missing_skills list      → Required − user_skills, ranked by importance
    ├── _build_learning_path()            → Topological sort + progressive acquisition simulation
    │       └── _get_full_prereq_chain()  → Full recursive prereq chain for a skill
    │       └── _get_max_depth()          → Depth per skill for path output
    └── _generate_summary()              → Plain-English one-paragraph verdict
```

| Function | Role |
|---|---|
| `__init__()` | Copies SKILL_TREE to instance, merges custom tree, validates for cycles at startup |
| `_validate_tree()` | DFS cycle detection — raises ValueError immediately if cycle found |
| `_filter_domain()` | Job_Type exact + experience filter + title word-boundary fallback |
| `_parse_skills_string()` | Dual-format parser: `ast.literal_eval` for list literals, comma-split for CSV |
| `_extract_domain_skills()` | Weighted skill importance dict, 2% noise filter |
| `_normalize_user_skills()` | 24-alias dictionary + lowercase/whitespace normalization → Set |
| `_get_max_depth()` | Recursive max depth with immutable `visited` set to prevent cross-branch contamination |
| `_get_full_prereq_chain()` | Full recursive prerequisite chain in topological order |
| `_build_learning_path()` | All-steps: collect chains, topological sort, simulate acquisition, mark can_start_now |
| `_analyze_domain_complexity()` | Complexity index, deepest skills, 5-tier classification |
| `_calculate_readiness()` | Weighted + count composite readiness, 5-tier status label |
| `analyze_prerequisites()` | **Master function** — all 10 steps, full output assembly |
| `_generate_summary()` | Context-aware one-paragraph plain-English verdict |

---

## 6. Output — What Does the Engine Return?

### Sample Output

```json
{
    "Domain": "Data Science",
    "Experience_Band": [0, 3],
    "Sample_Size": 184,

    "Domain_Complexity": {
        "max_depth": 4,
        "avg_depth": 2.8,
        "skill_count": 18,
        "complexity_index": 3.28,
        "classification": "🔴 Deep Foundation — 6-12 months structured learning",
        "barrier_level": "High",
        "deepest_skills": [
            {"skill": "deep learning", "depth": 4},
            {"skill": "machine learning", "depth": 3},
            {"skill": "nlp", "depth": 5}
        ]
    },

    "Your_Readiness": {
        "composite_score": 0.48,
        "weighted_coverage": 0.52,
        "count_ratio": 0.40,
        "matched_skills": 6,
        "total_required": 15,
        "status": "🟠 Partially Ready — meaningful upskilling needed",
        "Skills_You_Have": ["python", "sql", "statistics"],
        "Skills_You_Gave": ["python", "sql", "statistics"]
    },

    "Missing_Skills_Prioritized": [
        {"skill": "machine learning", "importance": 2.14},
        {"skill": "deep learning",    "importance": 1.82},
        {"skill": "data visualization","importance": 1.41},
        {"skill": "tensorflow",        "importance": 1.20},
        {"skill": "feature engineering","importance": 0.98}
    ],

    "Learning_Path": {
        "Ordered_Steps": [
            {"skill": "linear algebra",   "weeks_to_learn": 6,  "prerequisites": ["basic math"],           "prereq_ready": true,  "can_start_now": true,  "depth": 1},
            {"skill": "machine learning", "weeks_to_learn": 14, "prerequisites": ["statistics","python","linear algebra"], "prereq_ready": true, "can_start_now": false, "depth": 3},
            {"skill": "pandas",           "weeks_to_learn": 5,  "prerequisites": ["python"],                "prereq_ready": true,  "can_start_now": true,  "depth": 1},
            {"skill": "deep learning",    "weeks_to_learn": 18, "prerequisites": ["machine learning","linear algebra","calculus"], "prereq_ready": true, "can_start_now": false, "depth": 4}
        ],
        "Can_Start_Now": [
            {"skill": "linear algebra", "weeks_to_learn": 6, ...},
            {"skill": "pandas",         "weeks_to_learn": 5, ...}
        ],
        "Total_Skills_Needed": 7,
        "Estimated_Months": 11.4,
        "Time_Assumption": "10 hrs/week dedicated learning"
    },

    "Education_Signal": "⚠️  35% of postings prefer PG degree — consider if relevant.",

    "Quick_Summary": "🟠 Moderate gap but achievable. ~11.4 months to job-ready. Begin immediately with: linear algebra, pandas."
}
```

### Key Output Fields Explained

| Field | What it Tells the User |
|---|---|
| `Domain_Complexity.complexity_index` | How fundamentally hard is this domain to enter — regardless of your skills |
| `Domain_Complexity.deepest_skills` | The hardest-to-reach skills — what requires the most foundational learning |
| `Your_Readiness.composite_score` | How ready you are RIGHT NOW based on current skills |
| `Your_Readiness.Skills_You_Have` | Which of your skills actually matter in this domain |
| `Missing_Skills_Prioritized` | What to learn, ranked by how much the market cares about each |
| `Learning_Path.Can_Start_Now` | **The most actionable output** — what you can start TODAY |
| `Learning_Path.Ordered_Steps` | The full sequence — every skill in the right order |
| `Learning_Path.Estimated_Months` | Realistic timeline at 10 hrs/week |
| `Quick_Summary` | One-paragraph verdict ready to display directly to user |

---

## 7. How Robust Are the Formulas and Constants?

### What Makes Them Solid ✅

| Feature | Why It's Good |
|---|---|
| **Cycle detection at `__init__()`** | Catches malformed custom skill trees immediately at startup — not midway through a learning path calculation. Prevents infinite recursion. |
| **Immutable visited set in `_get_max_depth()`** | `visited = visited \| {skill_lower}` creates a new set instead of mutating. This prevents cross-branch contamination in recursive calls — a subtle but critical correctness fix for tree traversal. |
| **Progressive acquisition simulation** | `acquired` set grows as the path is walked — each skill is marked as learned, unlocking downstream `prereq_ready` flags. Without this, most skills would incorrectly show `prereq_ready: False`. |
| **Dual `can_start_now` vs `prereq_ready` distinction** | `can_start_now` = user has all prereqs TODAY. `prereq_ready` = prereqs will be covered by earlier path steps. Both signals serve different purposes. |
| **Dual-format skill parser** | `ast.literal_eval` for Python list literals, comma-split for plain CSV. Real datasets contain both formats — handling both prevents silent data loss. |
| **Complexity index = depth + breadth** | Neither dimension alone captures domain difficulty. Combines both with 60/40 weighting. |
| **2% minimum importance threshold** | Stricter than other engines' 1% — appropriate here because a learning plan that includes skills appearing in only 1 in 100 postings is wasteful. |
| **Custom skill tree via `__init__`** | Domain-specific skills not in the core tree can be added without modifying class code — extensible design. |

---

## 8. Advantages of the Current Implementation

- **Topologically sorted learning path** — the only engine that respects skill dependencies in its output. A list of "skills to learn" without ordering is almost useless.
- **Progressive acquisition simulation** — correctly marks what's ready at each step of the journey, not just what's ready today.
- **`can_start_now` flag** — immediately actionable output. The user doesn't need to read the whole path — just look at Can_Start_Now and begin.
- **Dual-format skill parser** — handles real-world CSV messiness gracefully without any data loss.
- **Alias normalization** — "ReactJS", "React.js", "react" all become "react". Prevents the most common source of false mismatches between user input and domain profile.
- **Complexity index combining depth + breadth** — correctly distinguishes between hard-to-enter domains (deep prerequisites) and broad-but-shallow domains (many independent skills).
- **Education signal from dataset** — uses actual PG/UG degree data from postings, not a hardcoded assumption.
- **Custom skill tree extensibility** — future domains, emerging frameworks, or organization-specific skills can be added at runtime without code changes.

---

## 9. Disadvantages and How to Improve Them

| Limitation | Problem | Suggested Fix |
|---|---|---|
| **`Skills_You_Gave` typo in output key** | In `analyze_prerequisites()` line 601: `"Skills_You_Gave": list(user_skills_normalized)`. This is clearly a typo — it should be `"Skills_You_Gave_As_Input"` or `"All_Your_Skills"`. More importantly, `user_skills_normalized` contains ALL normalized user skills, not just the ones relevant to this domain. The key name `"Skills_You_Gave"` is misleading. | Rename to `"All_Skills_You_Provided"` and keep it as informational context. The actually useful key — skills matching the domain — is already in `"Skills_You_Have"`. |
| **`Education_Cleaned` column checked but `PG_Degree`/`UG_Degree` columns used** | Line 583: `if 'Education_Cleaned' in domain_df.columns:` — checks one column. Lines 584–585 then use `PG_Degree` and `UG_Degree` columns. If `Education_Cleaned` exists but `PG_Degree` does not, both `pg_pct` and `ug_pct` will be 0 and the signal silently produces nothing. | Check directly for `'PG_Degree' in domain_df.columns` and `'UG_Degree' in domain_df.columns` — not the unrelated `Education_Cleaned` column. The outer condition should be `if 'PG_Degree' in domain_df.columns or 'UG_Degree' in domain_df.columns:`. |
| **SKILL_TREE covers ~80 skills; many modern skills are missing** | LangChain, FastAPI, Streamlit, Airflow, Hugging Face, dbt, Databricks, Next.js, GraphQL, Rust, Go — all missing from the tree. For a domain like "LLM Engineer" or "Data Engineer", the learning path will be incomplete because the tree has no entries for these skills. | Add a `"unresolved_skills"` field to the output listing target-domain skills that appear in job postings but aren't in the skill tree. This alerts the user that the path may be incomplete. Expand tree in versions with new frameworks. |
| **Topological sort in `_build_learning_path()` uses a nested function with mutable closure** | The inner `get_order()` function references `ordered` and `temp_visited` from the outer scope. This works correctly for Python closures but is harder to test in isolation and adds cognitive complexity. | Extract to a standalone `_topological_sort(skills_to_learn)` method. This improves testability, reusability, and makes the flow in `_build_learning_path()` clearer. |
| **Learning time does not account for parallel learning** | `total_weeks = sum(step["weeks_to_learn"] for step in learning_path)` assumes all skills are learned sequentially. In reality, a learner can study linear algebra while also starting Python foundations — parallel learning reduces total calendar time significantly. | Add a `parallel_estimate_months` alongside `total_months`: find independent tracks in the topological graph (skills with no shared prerequisites) and assume they can be learned in parallel. This gives a more realistic "calendar time" vs "total learning hours" distinction. |
| **Alias dictionary has 24 entries — many common variations missing** | `"Vue.js"` is handled but not `"vuejs"`. `"Angular.js"` is not aliased to `"angular"`. `"scipy"` is not aliased to `"statistics"`. Input `"PostgreSQL"` would normalize to `"postgresql"` via lowercasing — fine, but `"Postgres SQL"` (two words) would not. | Expand the ALIASES dictionary to 60+ entries. Add a fuzzy matching fallback for inputs that aren't exact aliases: if `cleaned_skill` is not in ALIASES and not in SKILL_TREE, try `difflib.get_close_matches(cleaned_skill, skill_tree.keys(), n=1, cutoff=0.85)` to catch near-matches. |
| **The `_get_full_prereq_chain()` mutable `visited` set is shared across sibling calls** | `visited.add(skill_lower)` mutates the passed set. If skill A requires [B, C], and B requires D, the recursion on B adds D to visited. When C is then processed, if C also requires D, D is already in visited and gets skipped — even though D should appear in C's chain independently. For tree structures this is technically fine (D would be added via B anyway), but it prevents correct detection of all dependency paths in DAGs. | Use the same immutable pattern as `_get_max_depth()`: `visited = visited \| {skill_lower}` — create a new set for each branch rather than mutating the shared one. This ensures each branch gets a complete, independent view of the chain. |

### Formula Improvement Suggestions

```python
# Current: simple sequential time estimate
total_weeks  = sum(step["weeks_to_learn"] for step in learning_path)
total_months = total_weeks / 4.3

# Improved: parallel time estimate
# Group skills by their prerequisite depth level
# Skills at the same depth level can be studied in parallel
from collections import defaultdict

depth_groups = defaultdict(list)
for step in learning_path:
    depth_groups[step["depth"]].append(step["weeks_to_learn"])

# Each depth level's time = max(weeks in that level) — parallel learners
parallel_weeks = sum(max(weeks_list) for weeks_list in depth_groups.values())
parallel_months = round(parallel_weeks / 4.3, 1)

# Output both: sequential for worst-case, parallel for realistic
"Estimated_Months_Sequential": total_months,
"Estimated_Months_Parallel":   parallel_months,
"Note": f"Parallel estimate assumes studying {len(depth_groups)} skill groups concurrently"
```

```python
# Current: complexity breadth capped at skill_count/15, max 4.0
breadth_component = min(skill_count / 15, 4.0)

# Improved: distinguish between skill breadth and required skill diversity
# A domain needing 20 Python variants is NOT more complex than one needing 20 different tools
# Count skills from different categories instead
categories_needed = len({
    category for skill in required_skills
    for category, skills in SKILL_CATEGORIES.items()  # a category→skills dict
    if skill in skills
})
breadth_component = min(categories_needed / 4, 4.0)  # 4 categories = full breadth score
```

```python
# Current: readiness composite = 60% weighted + 40% count (fixed)
composite = 0.6 * weighted_coverage + 0.4 * count_ratio

# Improved: adjust split based on domain complexity
# In a complex domain (high depth), WHICH skills you have matters more than HOW MANY
# because the deep skills are bottlenecks
complexity_idx = domain_complexity.get("complexity_index", 2.0)
weighted_share = min(0.80, 0.50 + complexity_idx * 0.05)  # scales from 0.55 to 0.80
count_share    = 1.0 - weighted_share
composite      = weighted_share * weighted_coverage + count_share * count_ratio
```

---

*End of Engine 11 Documentation*

---
---

# Engine 12 — `ProjectComplexityEvaluator` (Project Complexity Evaluator)

**File:** `project_complexity_evaluator.py`  
**Class:** `ProjectComplexityEvaluator`

---

## 1. Introduction — What is this Engine and What Does it Do?

Every fresher and career switcher builds projects for their portfolio. But almost none of them know the answer to one critical question:

> *"Is my project complex enough to impress a recruiter for THIS specific domain? Or am I submitting a beginner-level TODO app for a role that expects a production-grade ML pipeline?"*

The gap between "project exists on GitHub" and "project meets market expectations" is often invisible — until you get rejected after 50 applications.

**`ProjectComplexityEvaluator` bridges this gap.** It analyzes job descriptions from the target domain to extract what level of project complexity companies actually expect, then lets users measure their own projects against that market benchmark — dimension by dimension.

It works in two modes:

**Mode 1 — Market Benchmark Only:**  
*"What kind of projects does a Data Scientist role actually expect?"*  
→ Returns a market complexity score, label, confidence, and a concrete example project.

**Mode 2 — User Project vs Market (Gap Analysis):**  
*"My project has 4 features, uses 5 techs, 1 integration, and is deployed on AWS — how does it compare?"*  
→ Returns gap per dimension, specific improvement actions ranked by priority, and an overall status.

The engine measures project complexity across **4 dimensions**:

1. **Feature Depth** — How complex are the core features? (CRUD vs real-time vs ML-powered)
2. **Tech Stack Breadth** — How diverse and advanced is the technology used?
3. **Integration Depth** — How many external systems and APIs are connected?
4. **Deployment Level** — How production-ready is the deployment? (localhost → Kubernetes)

> Think of it like a restaurant inspector checking against a required hygiene standard. The inspector doesn't just say "clean or not clean" — they check temperature logs, food handling, storage, sanitation — each dimension against a specific standard. Then they tell you exactly which areas failed and by how much. This engine does the same for your portfolio project.

---

## 2. Data Fields Required by This Engine

### Required

| Column Name | What it Means | Required? |
|---|---|---|
| `Job_Type` | Domain/category of the job | ✅ Primary domain filter |
| `Description_Cleaned` | Full job description text | ✅ Core — all 3 description-based signals depend on this |

### Recommended

| Column Name | What it Means | Fallback if Missing |
|---|---|---|
| `Title_Cleaned` (or `TItle_Cleaned`) | Job title for fallback filter | Domain filter may miss records |
| `Min_Experience` | Minimum experience required | Experience filter skipped |
| `Skill_Count` | Number of skills required | Signal 4 (skill breadth) not computed |
| `No of applicant applied cleaned` | Applicant count | Competition modifier = 0 |
| `No of job opening cleaned ` | Opening count | Competition modifier = 0 |

### Inputs Passed at Runtime

| Parameter | What it Means | Default |
|---|---|---|
| `target_domain` | Domain to benchmark (e.g., `"Data Scientist"`) | Required |
| `experience_band` | Tuple `(min_exp, max_exp)` | `(0, 3)` |
| `user_project_stats` | Dict describing user's project (see below) | `None` (benchmark only) |
| `weights` | Custom dimension weights (set in `__init__`) | Default weights |

### User Project Stats Format (for Gap Analysis)

```python
user_project_stats = {
    "features":     4,          # Number of distinct features (int, 1-20)
    "tech_count":   5,          # Number of technologies used (int, 1-20)
    "integrations": 1,          # Number of external APIs/services (int, 0-10)
    "deployment":   "cloud_basic"  # One of: none/local/free_hosting/cloud_basic/cloud_full/production
}
```

All 4 keys are required. The engine validates input and returns specific error messages for wrong key names, invalid deployment strings, or negative numbers.

---

## 3. Core Logic — How Does the Engine Calculate Market Complexity?

### Market Benchmark — 5 Signals Combined

The market score is derived from job descriptions using **5 signals**:

---

#### Signal 1 — Feature Complexity (from JD keywords)

Scans `Description_Cleaned` for keywords that indicate what level of features are expected in candidates' work:

**Keyword tiers:**

| Tier | Sample Keywords | Weight in Signal |
|---|---|---|
| Basic | `crud`, `todo`, `login`, `registration`, `simple dashboard`, `calculator` | 15% |
| Intermediate | `authentication`, `oauth`, `payment`, `real-time`, `recommendation`, `multi-user`, `notification system`, `file upload` | 35% |
| Advanced | `machine learning model`, `nlp pipeline`, `streaming data`, `event-driven`, `distributed`, `predictive model`, `ab testing` | 50% |

**Formula:**
```
feature_score = (basic_pct×0.15 + inter_pct×0.35 + adv_pct×0.50) / 10
feature_score = min(10.0, feature_score × 2)    ← scale to 0-10
```

**Why advanced gets 50% weight?** Advanced features represent a genuine capability barrier — a domain where 30% of JDs mention ML models or distributed systems is fundamentally different from one where they mention CRUD. The signal needs to be amplified, not averaged equally.

---

#### Signal 2 — Integration Depth (from JD keywords)

Scans for how many external systems and services are mentioned:

| Tier | Sample Keywords | Weight |
|---|---|---|
| Basic | `rest api`, `json`, `sqlite`, `http request`, `fetch api` | 10% |
| Intermediate | `payment gateway`, `aws s3`, `redis cache`, `message queue`, `oauth provider`, `stripe`, `elasticsearch` | 40% |
| Advanced | `microservices`, `kafka`, `rabbitmq`, `graphql`, `grpc`, `websocket`, `event sourcing`, `cqrs`, `api gateway` | 50% |

**Formula:**
```
int_score = (basic_pct×0.10 + inter_pct×0.40 + adv_pct×0.50) / 10
int_score = min(10.0, int_score × 2)
```

---

#### Signal 3 — Deployment Complexity (from JD keywords)

Scans for deployment and infrastructure expectations:

| Tier | Sample Keywords | Weight |
|---|---|---|
| Basic | `heroku`, `netlify`, `vercel`, `github pages`, `render` | 10% |
| Intermediate | `aws ec2`, `docker`, `docker compose`, `nginx`, `ssl`, `digital ocean` | 35% |
| Advanced | `kubernetes`, `k8s`, `ci/cd`, `github actions`, `terraform`, `helm`, `load balancer`, `monitoring`, `canary release` | 55% |

**Formula:**
```
dep_score = (basic_pct×0.10 + inter_pct×0.35 + adv_pct×0.55) / 10
dep_score = min(10.0, dep_score × 2)
```

---

#### Signal 4 — Skill Breadth (from Skill_Count column)

```
skill_score = min(10.0, (median_skill_count / 20) × 10)
```

Normalizes median skill count against a ceiling of 20 skills → 0–10 score.

---

#### Signal 5 — Competition Modifier

High-competition domains raise the bar — projects need to stand out more.

```
ratio = total_applicants / total_openings

if ratio > 100: competition_modifier = +1.5
elif ratio > 50: competition_modifier = +0.75
elif ratio > 25: competition_modifier = +0.25
else:           competition_modifier =  0.0
```

This modifier is **added after** the base score is computed — it can push the final score above what description keywords alone indicate.

---

#### Composite Market Score

```
base_score = (feature_score × 0.35) + (integration_score × 0.25)
           + (deployment_score × 0.25) + (skill_score × 0.15)
           [only averages over signals that are actually available]

final_score = min(10.0, base_score + competition_modifier)
```

**Market complexity labels (5-tier):**

| Score | Label | Tier |
|---|---|---|
| < 2.5 | 🟢 Basic / CRUD Level | basic |
| 2.5 – 4.4 | 🟡 Simple-Intermediate | simple_intermediate |
| 4.5 – 6.4 | 🟠 Medium Complexity | medium |
| 6.5 – 7.9 | 🔴 Advanced / Production-Ready | advanced |
| ≥ 8.0 | 🚨 Expert-Level / Scalable Systems | expert |

---

### User Project Scoring (`calculate_project_score`)

When `user_project_stats` is provided, the engine scores the user's project on the same 0–10 scale:

```
feature_score     = min(10.0, features / 2.0)          ← 20 features = perfect 10
tech_score        = min(10.0, tech_count / 2.0)        ← 20 techs = perfect 10
integration_score = min(10.0, integrations / 1.0)      ← 10 integrations = perfect 10
deploy_score      = DEPLOYMENT_SCORES[deployment]      ← named tier → fixed score

user_composite = (feature_score    × 0.35)
               + (tech_score       × 0.20)
               + (integration_score × 0.25)
               + (deploy_score     × 0.20)
```

**Deployment Score Mapping (replaces simple 1/2/3 integers):**

| Deployment Level | Score | Examples |
|---|---|---|
| `none` | 0.0 | Not deployed |
| `local` | 1.0 | Localhost only |
| `free_hosting` | 3.0 | Vercel, Netlify, Heroku, Render |
| `cloud_basic` | 5.5 | AWS EC2, Docker, DigitalOcean |
| `cloud_full` | 7.5 | Docker + CI/CD + custom domain |
| `production` | 10.0 | Kubernetes, auto-scaling, monitoring |

---

### Gap Analysis (`_analyze_gap`)

Computes the per-dimension gap between user score and market expectation:

```
For each dimension (features, tech_stack, integrations, deployment):
    dim_gap = market_dim_score - user_dim_score
    if dim_gap > 1.5:  ← threshold: only flag meaningful gaps
        add to suggestions with specific action
```

Suggestions are **sorted by gap size** — the biggest gap gets the top recommendation.

**Smart deployment suggestion:** Instead of one generic message, the engine checks your current deployment tier and gives the **specific next step**:

| Current Deployment | Next Step |
|---|---|
| `none` | Deploy to Vercel/Netlify (free, 1 day effort) |
| `local` | Deploy to Vercel/Netlify or Render (free, 1 day effort) |
| `free_hosting` | Add Docker + deploy to cloud VM (AWS EC2 free tier) |
| `cloud_basic` | Add CI/CD pipeline with GitHub Actions |
| `cloud_full` | Add monitoring (Prometheus/Grafana) and auto-scaling |

**Gap status labels:**

| Gap | Status |
|---|---|
| ≤ 0 | ✅ Market Ready |
| 0 – 1.5 | 🟡 Minor Gap |
| 1.5 – 3.5 | 🟠 Moderate Gap |
| > 3.5 | 🔴 Significant Gap |

---

### Domain Archetypes — Concrete Project Examples

For 7 known domains, the engine returns a concrete example project at each complexity tier:

| Domain | Simple | Medium | Advanced |
|---|---|---|---|
| Data Scientist | Single dataset EDA notebook | End-to-end ML pipeline with evaluation dashboard | Production ML system with real-time inference, A/B testing |
| ML Engineer | Trained model in Jupyter | Dockerized FastAPI serving + basic monitoring | MLOps: automated training, MLflow versioning, drift detection |
| Web Developer | Static site or basic CRUD | Full-stack app with auth, DB, cloud deployed | Scalable SaaS with microservices, payments, multi-tenancy |
| Backend Developer | REST API with CRUD + SQLite | Production API with PostgreSQL, Redis, Docker | Distributed event-driven system with auto-scaling |
| Frontend Developer | Static HTML/CSS or basic React | React SPA with state management, API, deployed | Server-side rendering, design system, testing suite |
| DevOps Engineer | Basic bash + manual deploy | Docker + CI/CD with GitHub Actions | Full IaC with Terraform, Kubernetes, Prometheus/Grafana |
| Cybersecurity | Basic scanner or CTF writeup | Security audit tool with SIEM integration | Full pen-testing framework or SIEM with ML anomaly detection |

---

### Target Specifications — Data-Driven Recommendations

Instead of generic "build better projects" advice, the engine computes data-driven specifications based on the market score:

```
minimum_features  = 2 + int(score / 2)        ← score=6 → 5 features minimum
recommended_techs = 3 + int(score / 2)        ← score=6 → 6 techs
integrations      = max(1, int(score / 3))    ← score=6 → 2 integrations
deployment_target = tier based on score thresholds
data_complexity   = text description based on score
```

---

## 4. Weights — What They Mean and Why

### Market Benchmark Signal Weights

| Signal | Weight | Justification |
|---|---|---|
| `feature_complexity` | **35%** | What your project does is the primary signal of capability. Feature complexity is what interviewers directly quiz you on. |
| `integration_depth` | **25%** | Real-world software integrates external systems — this distinguishes toy projects from production-aware work. |
| `deployment_complexity` | **25%** | A project that's never deployed is half a project. Production deployment signals engineering maturity. |
| `skill_breadth` | **15%** | Skill count is a weaker, indirect signal. Description keywords carry more market information than a bare count. |

### User Project Scoring Weights

| Dimension | Weight | Justification |
|---|---|---|
| `feature_depth` | **35%** | Features are what interviewers ask about. The depth of what you built matters most. |
| `integration_depth` | **25%** | External integrations show real-world software development experience. |
| `deployment_level` | **20%** | Deployment demonstrates end-to-end ownership — critical differentiator between junior and senior project quality. |
| `tech_stack` | **20%** | Technology breadth matters but less than what you built with it. A diverse stack with shallow features is not impressive. |

### Within-Signal Tier Weights (Feature/Integration/Deployment)

| Tier | Weight | Why |
|---|---|---|
| Advanced | **50%** | Advanced signals are the true differentiators — rare enough to be meaningful. |
| Intermediate | **35–40%** | Expected baseline in most domains — important but not rare. |
| Basic | **10–15%** | Table stakes — expected of everyone; low market signal value. |

---

## 5. Functions — What They Do and How They Are Called

```
evaluate_portfolio_readiness()        ← Main entry point (you call this)
    │
    ├── _filter_domain()              → Domain rows with experience filter
    │
    ├── _extract_market_complexity()  → 5-signal market benchmark score
    │       └── _safe_keyword_pct()   → NaN-safe word-boundary keyword scan
    │       └── _label_complexity()   → 5-tier label + tier string
    │
    ├── _get_domain_archetype()       → Concrete example project for domain + tier
    │
    ├── calculate_project_score()     → User project 0-10 score (if stats provided)
    │       └── _validate_user_project_stats() → Check required keys + valid values
    │       └── _label_complexity()   → Label user score with same 5-tier system
    │
    ├── _analyze_gap()                → Per-dimension gaps + ranked improvement actions
    │       (only called if user_project_stats provided)
    │
    ├── _derive_target_specs()        → Data-driven minimum specs from market score
    └── _quick_verdict()              → Plain-English one-line status for UI
```

| Function | Role |
|---|---|
| `__init__()` | Sets and validates weights |
| `_validate_weights()` | Ensures weights sum to 1.0 ± 0.02 |
| `_filter_domain()` | Job_Type exact + experience filter + title word-boundary fallback |
| `_safe_keyword_pct()` | NaN-safe word-boundary keyword scan, returns 0–100 percentage |
| `_extract_market_complexity()` | 5-signal composite with competition modifier |
| `_label_complexity()` | 5-tier label + tier key for both market and user scores |
| `_validate_user_project_stats()` | Explicit validation with detailed error messages |
| `calculate_project_score()` | Normalizes 4 user inputs to 0–10, computes weighted composite |
| `_analyze_gap()` | Per-dimension gap with >1.5 threshold filter + smart deployment suggestions |
| `_get_domain_archetype()` | Partial string match to 7 known domain archetypes |
| `_derive_target_specs()` | Data-driven minimums computed from market score |
| `_quick_verdict()` | One-line plain-English status for UI display |
| `evaluate_portfolio_readiness()` | **Master function** — orchestrates all steps |

---

## 6. Output — What Does the Engine Return?

### Sample Output (with user project stats)

```json
{
    "Domain": "Data Scientist",
    "Experience_Band": [0, 3],
    "Sample_Size": 184,

    "Market_Benchmark": {
        "Score": 6.82,
        "Label": "🔴 Advanced / Production-Ready",
        "Confidence": "High",
        "Signals": {
            "feature_complexity":    6.40,
            "integration_depth":     7.20,
            "deployment_complexity": 5.80,
            "skill_breadth":         6.50,
            "competition_ratio":     68.4
        },
        "Example_Project": "End-to-end ML pipeline: data collection → feature engineering → model → evaluation dashboard"
    },

    "User_Project": {
        "composite_score": 4.85,
        "label": "🟠 Medium Complexity",
        "tier": "medium",
        "dimension_scores": {
            "features":     2.00,
            "tech_stack":   2.50,
            "integrations": 1.00,
            "deployment":   5.50
        }
    },

    "Gap_Analysis": {
        "overall_gap": 1.97,
        "status": "🟠 Moderate Gap",
        "status_detail": "Gap of 2.0 points. Need meaningful project upgrades across 2 dimensions.",
        "dimension_gaps": {
            "features": 4.40,
            "integrations": 6.20
        },
        "improvement_actions": [
            {
                "dimension": "Integration Depth",
                "gap": 6.20,
                "action": "Integrate a third-party API (payment, auth, email, or analytics service)."
            },
            {
                "dimension": "Feature Depth",
                "gap": 4.40,
                "action": "Add a complex feature: real-time updates, recommendation engine, or multi-user collaboration."
            }
        ],
        "priority_action": "Integrate a third-party API (payment, auth, email, or analytics service)."
    },

    "Target_Specifications": {
        "minimum_features": 5,
        "recommended_techs": 6,
        "integrations": 2,
        "deployment_target": "cloud_full",
        "data_complexity": "Multiple sources with API integration"
    },

    "Quick_Verdict": "🟠 Moderate Gap — Gap of 2.0 points. Need meaningful upgrades across 2 dimensions. Next: Integrate a third-party API."
}
```

### How to Read This Output

| Field | What it Tells the User |
|---|---|
| `Market_Benchmark.Score` | The market's minimum expectation — your project needs to beat this |
| `Market_Benchmark.Example_Project` | A concrete real-world example of what the market expects |
| `Market_Benchmark.Signals` | What specific aspects companies are looking for |
| `User_Project.composite_score` | Your project's score on the same 0–10 scale |
| `Gap_Analysis.dimension_gaps` | Which specific dimensions are pulling you down |
| `Gap_Analysis.improvement_actions` | **Ranked specific actions** — biggest gap first |
| `Gap_Analysis.priority_action` | Single most impactful thing to do next |
| `Target_Specifications` | Data-driven minimums — concrete targets to hit |
| `Quick_Verdict` | One-line summary ready for UI display |

---

## 7. How Robust Are the Formulas and Constants?

### What Makes Them Solid ✅

| Feature | Why It's Good |
|---|---|
| **Multi-signal market score** | 5 independent signals — description features, integrations, deployment, skill count, competition — far more accurate than any single proxy. |
| **Tier-weighted keyword scoring** | Advanced keywords get 50% weight. This correctly amplifies the rare, high-signal terms that distinguish elite projects from standard ones. |
| **Competition modifier** | A domain with 100:1 applicant/opening ratio genuinely requires stronger differentiation. The modifier captures this market reality. |
| **Named deployment tiers (not raw numbers)** | `"cloud_basic"` maps to `5.5`. No more user confusion about what "3" means. Explicit named tiers prevent input errors. |
| **Input validation with clear error messages** | `_validate_user_project_stats()` tells you exactly which key is missing and what format it expects. No silent zeros from typos. |
| **1.5-point gap threshold** | Only dimensions with gap > 1.5 are flagged. This prevents noise — a tiny 0.3-point gap doesn't need its own improvement action. |
| **Smart deployment suggestions** | Context-aware next step based on current deployment level, not a generic message. |
| **`_derive_target_specs()` — data-driven minimums** | Minimum features, techs, integrations computed from market score with formulas — not hardcoded numbers that become stale. |
| **Domain archetype examples** | 7 specific domains with 3 tiers each = 21 concrete project examples. These are more useful than abstract score labels. |

---

## 8. Advantages of the Current Implementation

- **Dual-mode output** — works both as a standalone "what does the market expect" tool AND as a "how does MY project compare" tool, without needing both.
- **5-signal market benchmark** — reads JD text, skill counts, and competition together for a much richer market picture than any single signal.
- **Concrete domain-specific archetypes** — "End-to-end ML pipeline with evaluation dashboard" is actionable. "Medium complexity" alone is not.
- **Per-dimension gap analysis** — tells you not just that you're behind, but exactly which dimension is dragging your score down most.
- **Priority-ranked improvement actions** — sorted by gap size so the user knows exactly where to focus first.
- **Data-driven target specs** — `minimum_features`, `recommended_techs`, `integrations`, `deployment_target` are computed from the market score, not hardcoded.
- **Input validation** — the evaluator never silently accepts wrong inputs. Clear error messages prevent misuse.
- **Competition modifier** — the only engine in the pipeline that adjusts its benchmark upward when the domain is especially crowded.

---

## 9. Disadvantages and How to Improve Them

| Limitation | Problem | Suggested Fix |
|---|---|---|
| **Market signal normalization math is inconsistent** | The feature/integration/deployment scores are computed as `(weighted_pct_sum) / 10` then `× 2`. This means: if all 3 tiers score 100% (hypothetical max), the result is `(15+35+50)/10 × 2 = 20.0` — then clipped to 10. But in practice, a domain where 50% of JDs mention advanced features gets `50×0.50 = 25 / 10 × 2 = 5.0` — which seems low for 50% advanced mention rate. The `÷10 then ×2` chain obscures the intended scale. | Simplify to a single-step formula with an explicit 0–10 scale: `score = (basic_pct×0.15 + inter_pct×0.35 + adv_pct×0.50) / 10`. Drop the `×2` multiplier and instead adjust tier weights so the result naturally spans 0–10 without artificial scaling. |
| **User project stat inputs are too coarse** | `"features": 4` — but what counts as a feature? Is pagination 1 feature? Is dark mode 1 feature? Is an OAuth login flow 1 feature? The schema is ambiguous and users will self-report inconsistently. | Either provide a feature checklist (e.g., "count these specific items") or replace the raw count with tiered inputs: `"feature_tier": "basic" | "intermediate" | "advanced"` — mirroring the market benchmark's own tier system. |
| **Gap analysis uses market signal scores as proxies for dimension expectations** | `market_dims["features"] = market_signals.get("feature_complexity", market_score)` — falls back to the composite `market_score` for dimensions where the signal is missing. A score of 7.0 for the full composite becomes the feature expectation AND the integration expectation if either signal is absent. This inflates the apparent gap. | Compute dimension-specific market expectations from the job postings directly — run `calculate_project_score()` on inferred stats from the market signals rather than reusing the composite as a per-dimension proxy. |
| **`_get_domain_archetype()` uses partial string matching without word boundaries** | `if known_domain in domain_lower or domain_lower in known_domain:` — searching for "data scientist" inside "data scientist manager" and vice versa. The check `domain_lower in known_domain` would match "data" in "data scientist" if the user types just "data". | Use exact match first: `if known_domain == domain_lower`. Then partial match as fallback with a minimum word overlap check to prevent false positives. |
| **No project description / URL input for richer evaluation** | The engine only accepts 4 numeric/string stats. A user cannot paste a GitHub README or project URL for analysis. If they could, the engine could infer feature complexity, integrations, and deployment from the text — removing the need for manual self-reporting. | Add an optional `project_description: str` parameter. If provided, apply the same `_safe_keyword_pct()` scanning against `COMPLEXITY_KEYWORDS` to auto-score all 4 dimensions — making the user project assessment as rich as the market benchmark. |
| **Competition modifier uses hardcoded thresholds (25, 50, 100)** | The `+0.25`, `+0.75`, `+1.5` modifier amounts and the ratio thresholds were manually chosen. In different market conditions these could be miscalibrated. | Use the same market-relative approach as `HiddenBlockerDetector` — compute the P75 of all domain competition ratios from the full dataset and use that as the modifier threshold rather than a fixed number. |
| **`_derive_target_specs()` uses simple linear formulas** | `minimum_features = 2 + int(score / 2)` — a score of 6.9 and 6.1 both give `minimum_features = 5`. The rounding makes the spec insensitive to meaningful differences in the score. | Use `round()` instead of `int()` for smoother transitions, and add a domain-type modifier: technical domains (ML, DevOps) should have higher feature requirements than display domains (Frontend). |

### Formula Improvement Suggestions

```python
# Current: confusing ÷10 then ×2 normalization
feature_score = (basic_pct * 0.15 + inter_pct * 0.35 + adv_pct * 0.50) / 10
feature_score = min(10.0, feature_score * 2)

# Improved: single-step, self-documenting formula
# Design: 100% advanced mentions → score 10. 100% basic → score 1.5. 100% intermediate → 3.5
# Scale: treat pct as 0-1 (not 0-100) and map to 0-10
feature_score = min(10.0,
    (basic_pct/100 * 1.5) +     # max contribution: 1.5
    (inter_pct/100 * 3.5) +     # max contribution: 3.5
    (adv_pct/100  * 5.0)        # max contribution: 5.0
)
# Total max = 10.0 naturally. No hidden ×2 needed.
```

```python
# Current: user features input is a raw count
feature_score = min(10.0, stats["features"] / 2.0)

# Improved: accept tiered input matching the market benchmark system
# user_project_stats = {"feature_tier": "intermediate", ...}
TIER_SCORES = {"basic": 2.5, "intermediate": 5.5, "advanced": 8.5, "expert": 10.0}
feature_score = TIER_SCORES.get(stats.get("feature_tier", "basic"), 2.5)
# This makes user scoring directly comparable to market scoring (both use the same tier system)
```

```python
# Current: competition modifier uses hardcoded thresholds
if ratio > 100: modifier = 1.5
elif ratio > 50: modifier = 0.75
elif ratio > 25: modifier = 0.25

# Improved: market-relative modifier using the same baseline approach as other engines
p75_ratio = baselines.get("applicant_ratio_p75", 50.0)
p90_ratio = baselines.get("applicant_ratio_p90", 100.0)

if ratio > p90_ratio:
    modifier = 1.5
elif ratio > p75_ratio:
    modifier = 0.75
elif ratio > p75_ratio * 0.5:
    modifier = 0.25
else:
    modifier = 0.0
```

---

*End of Engine 12 Documentation*

---

---

# Engine 13 — `InterviewDifficultyEngine` (Interview Difficulty Engine)

**File:** `interview_difficulty_engine.py`  
**Class:** `InterviewDifficultyEngine`

---

## 1. Introduction — What is this Engine and What Does it Do?

Most job seekers prepare for interviews in a general, domain-agnostic way — "practice LeetCode, study system design, brush up on your frameworks." But interview preparation is not one-size-fits-all. A **Data Scientist** interview is fundamentally different from a **Backend Engineer** interview, which is different again from a **Frontend Developer** interview.

- A Data Scientist interview is 65% domain knowledge (statistics, ML theory) and only 15% DSA
- A Software Engineer interview is 50% DSA, 30% domain, and 20% system design
- A DevOps Engineer interview barely tests DSA (25%) but heavily tests system design (35%)

Preparing for the wrong things wastes weeks.

**`InterviewDifficultyEngine` answers two critical questions:**

> 1. *"How hard are the interviews for THIS specific domain — and what specifically makes them hard?"*
> 2. *"Given that difficulty profile, exactly how should I prepare — in what order, for how many weeks?"*

It does this by reading actual job descriptions for the target domain and measuring three independent "interview pillars":

- **Pillar α (Alpha) — DSA / Algorithmic Difficulty** — What level of data structures and algorithms are being signaled in job descriptions and requirements?
- **Pillar β (Beta) — Domain Knowledge Depth** — How deep is the technical domain knowledge expected? Surface tools vs. internals vs. OS/GPU-level expertise?
- **Pillar γ (Gamma) — System Design Complexity** — Is system design part of the interview? At what level — basic API design or globally-distributed systems?

Each domain has its own custom blend of these three pillars. The blend is what makes the difficulty score meaningful — not just the raw intensity of any single pillar.

> Think of it like a personal trainer designing a fitness program. A marathon runner and a powerlifter both train hard — but the composition of cardio vs. strength training is completely different. This engine tells you the exact composition of your interview's "fitness demands" and designs a preparation plan to match.

---

## 2. Data Fields Required by This Engine

### Required

| Column Name | What it Means | Required? |
|---|---|---|
| `Job_Type` | Domain/category of the job | ✅ Primary domain filter |
| `Description_Cleaned` | Full cleaned job description | ✅ All 3 pillars scored from this |

### Recommended

| Column Name | What it Means | Fallback if Missing |
|---|---|---|
| `Title_Cleaned` (or `TItle_Cleaned`) | Job title text | Domain filter may miss records |
| `Min_Experience` | Minimum years required | Experience filter skipped |
| `Star_Skills` | Must-have skills | DSA skill boost not applied |
| `Skill_Count` | Number of skills | Used as fallback for domain knowledge if no descriptions |

### Inputs Passed at Runtime

| Parameter | What it Means | Default |
|---|---|---|
| `target_domain` | Domain to analyze (e.g., `"Data Scientist"`) | Required |
| `experience_band` | Tuple `(min_exp, max_exp)` | `(0, 5)` |
| `custom_weights` | Override domain weight profiles in `DOMAIN_WEIGHTS` | `None` |

---

## 3. Core Logic — The Three-Pillar Framework

### Step 1 — Resolve Domain Weight Profile

Every domain has a pre-configured weight profile that defines how much each interview pillar matters:

```
α (DSA weight)     — How much of this domain's interview is algorithmic?
β (Domain weight)  — How much is deep technical/domain knowledge?
γ (System Design)  — How much is architecture and system design?

All three must sum to 1.0
```

**Selected domain profiles:**

| Domain | α DSA | β Domain | γ System Design | Why |
|---|---|---|---|---|
| Software Engineer | 50% | 30% | 20% | SWE interviews are heavily DSA-driven at most companies |
| Data Scientist | 15% | 65% | 20% | Mostly ML theory, statistics, pandas — DSA rarely tested |
| Data Analyst | 10% | 70% | 20% | Heaviest domain weight — SQL, statistics, viz tools |
| ML Engineer | 25% | 45% | 30% | More system design than DS (model serving), less DSA |
| Frontend Developer | 35% | 55% | 10% | Deep JS/React knowledge dominates, system design minimal |
| DevOps Engineer | 25% | 40% | 35% | Highest system design weight — infrastructure design matters |
| React Developer | 30% | 60% | 10% | Even less DSA than frontend, more React internals |
| Cybersecurity | 20% | 60% | 20% | Heavy domain knowledge — protocols, attack vectors, tools |

**Weight resolution order:**

```
1. Exact match on domain name (case-insensitive)
   "Data Scientist" → "data scientist" → exact profile found ✅

2. Partial/fuzzy word overlap match
   "Senior ML Engineer" → matches "ml engineer" (word overlap: "ml", "engineer")

3. Category inference from keywords
   "LLM Fine-tuning Engineer" → contains "ml" keyword → inferred as ml_category
   Inferred weights: α=0.20, β=0.50, γ=0.30

4. Default fallback
   Completely unknown domain → α=0.35, β=0.40, γ=0.25
```

The `weight_source` field in the output tells you which resolution level was used — so users know how reliable the weight profile is.

---

### Step 2 — Pillar α: DSA Score

**What it measures:** How algorithmically demanding are the interviews for this domain, based on what companies actually mention in job descriptions?

**Keyword tiers:**

| Tier | Sample Keywords |
|---|---|
| Easy | arrays, strings, hashing, basic sorting, stack, queue, linked list, two pointers |
| Medium | dynamic programming, binary search, backtracking, BFS/DFS, sliding window, heap, trie, segment tree |
| Hard | advanced dp, network flow, computational geometry, suffix array, NP-hard, approximation algorithm |
| Direct Hard | competitive programming, ICPC, codeforces, leetcode hard, topcoder |
| Direct Easy | basic coding, beginner friendly, no dsa required |

**Formula:**
```
easy_p   = fraction of JDs mentioning easy DSA keywords
med_p    = fraction of JDs mentioning medium DSA keywords
hard_p   = fraction of JDs mentioning hard DSA keywords

Direct signal adjustments:
  if direct_hard > 20% of JDs: hard_p += 0.30, med_p += 0.15
  if direct_easy > 20% of JDs: hard_p -= 0.20, easy_p += 0.20

dsa_score = easy_p × 0.15 + med_p × 0.35 + hard_p × 0.50
```

**Why Hard gets 50% weight?** Hard DSA problems are not just "harder versions" of medium — they represent a qualitatively different preparation requirement. A candidate who can solve hard problems can solve everything below. The scoring correctly amplifies this signal.

**Star_Skills boost:**
```
if 'dsa' or 'data structures' or 'algorithms' or 'leetcode' in Star_Skills:
    dsa_score = min(1.0, dsa_score + 0.10)
```
When companies list DSA as a must-have skill, it confirms the signal from descriptions.

**Plain English Example:**

"Backend Engineer" JDs: 15% mention medium DSA (DP, trees), 25% mention hard DSA (advanced graph, network flow), 20% mention competitive programming.

```
hard_p boosted by direct_hard: 0.25 + 0.30 = 0.55
dsa_score = (0.05×0.15) + (0.15×0.35) + (0.55×0.50) = 0.007 + 0.053 + 0.275 = 0.335
```

---

### Step 3 — Pillar β: Domain Knowledge Score

**What it measures:** How deep is the technical domain expertise expected — surface tool knowledge vs. framework internals vs. OS/memory/GPU-level?

**Keyword tiers:**

| Tier | Sample Keywords | Weight |
|---|---|---|
| Surface | html, css, basic sql, git, json, rest, basic python, excel, tableau | 15% |
| Intermediate | react hooks, state management, ORM, indexing, query optimization, docker, CI/CD, design patterns, SOLID | 40% |
| Deep | compiler, OS internals, memory management, concurrency, multithreading, JVM, kernel, network protocol, GPU programming, CUDA, transformer architecture, custom loss function | 45% |

**Formula:**
```
domain_score = surface_p × 0.15 + intermediate_p × 0.40 + deep_p × 0.45
```

**Skill_Count blending (when available):**
```
skill_signal = min(1.0, median_skill_count / 20)
domain_score = 0.70 × keyword_score + 0.30 × skill_signal
```

**Fallback when no descriptions:**
```
domain_score = min(1.0, median_skill_count / 20)   ← pure skill count proxy
```

---

### Step 4 — Pillar γ: System Design Score

**What it measures:** Is system design part of the interview process, and at what level of complexity?

**Keyword tiers:**

| Tier | Sample Keywords | Weight |
|---|---|---|
| Basic | rest api, crud, database design, mvc, basic architecture, monolithic | 10% |
| Intermediate | microservices, scalable, distributed system, caching, load balancer, message queue, kafka, api gateway | 35% |
| Advanced | system design interview, HLD, LLD, design at scale, millions of users, globally distributed, consensus algorithm, CAP theorem, event sourcing | 55% |

**Formula:**
```
sys_score = basic_p × 0.10 + intermediate_p × 0.35 + advanced_p × 0.55
```

**Key design decision:** `"cloud"` mention was deliberately **excluded** from the basic tier. A job posting mentioning AWS does not imply a system design interview round — it just means they use cloud. This avoids a common false positive where cloud-heavy domains get inflated system design scores.

**Tier labels:**

| Condition | Tier |
|---|---|
| advanced_pct > 25% | Advanced — HLD/LLD rounds expected |
| intermediate_pct > 30% | Intermediate — microservices & scalability questions |
| basic_pct > 20% | Basic — API design and DB schema questions |
| else | Minimal — system design unlikely in interview |

---

### Step 5 — Composite Difficulty Index

```
raw_index = α × dsa_score + β × domain_score + γ × sys_score
raw_index = clip(raw_index, 0.0, 1.0)
difficulty_10 = raw_index × 10
```

**Difficulty Labels (5-tier):**

| Score | Label |
|---|---|
| ≥ 8.0 | 🔴 Extremely Difficult |
| 6.5 – 7.9 | 🟠 Hard |
| 5.0 – 6.4 | 🟡 Moderate |
| 3.0 – 4.9 | 🟢 Manageable |
| < 3.0 | ⚪ Accessible |

---

### Step 6 — Interview Structure Estimation

Translates the pillar scores into a **concrete round-by-round interview structure**:

```
Round 1: Online Assessment (always)
         → Easy-Medium DSA if dsa_score < 0.40, else Medium-Hard

Round 2: Technical Interview (if domain_score > 0.50)
         → Probability: High

Round 3: Coding Round (if α ≥ 0.35)
         → Focus: Medium-Hard if hard_pct > 15%, else Easy-Medium
         → Probability: High if α > 0.40, else Medium

Round 4: System Design (if γ ≥ 0.20 AND sys_score > 0.25)
         → Focus: tier label from sys_score
         → Probability: High if γ > 0.30, else Medium

Round Final: HR / Behavioral (always)
```

---

### Step 7 — Preparation Plan

Three preparation tracks, each with a priority score and time estimate:

```
Track priority = weight × pillar_score × 10   ← highest impact first

DSA Track (if α > 0.10):
    dsa_intensity > 0.60 → 300+ LeetCode, focus DP/graphs, 12 weeks
    dsa_intensity > 0.35 → 150-200 LeetCode, focus Medium, 8 weeks
    else                 → 75-100 LeetCode Easy-Medium, 4 weeks

Domain Track (if β > 0.10):
    deep_pct > 20%         → OS/memory/concurrency internals, read source code, 10 weeks
    domain_intensity > 0.40 → 2-3 non-trivial projects + patterns, 8 weeks
    else                   → Core tutorials + 1 full project, 5 weeks

System Design Track (if γ ≥ 0.15 AND sys_score > 0.15):
    sys_intensity > 0.55 → Grokking SD, 10+ systems from scratch, 10 weeks
    sys_intensity > 0.30 → Microservices/caching/LB, 5-6 common systems, 6 weeks
    else                 → REST API + basic DB schema, 3 weeks

Total weeks = max(individual track weeks)   ← parallel preparation, not sequential
```

**Why `max()` not `sum()`?** The preparation tracks can be pursued simultaneously. DSA practice and system design study don't need to be sequential. The longest single track determines the total timeline, not the sum of all tracks.

---

## 4. Weights — What They Mean and Why

### Within-Pillar Tier Weights (same logic across all 3 pillars)

| Tier | Weight | Justification |
|---|---|---|
| Hard / Deep / Advanced | **50–55%** | These represent qualitatively harder interview requirements. A domain with hard DSA or advanced system design is dramatically different from one with medium/basic. High weight amplifies the signal. |
| Medium / Intermediate | **35–40%** | Expected baseline at most companies. Important but not rare. |
| Easy / Surface / Basic | **10–15%** | Table stakes — almost every domain mentions basic things. Low signal value. |

### Domain Weight Profile Rationale

| α (DSA) | Higher for: SWE, Backend — companies treat DSA as a proxy for general problem-solving |
|---|---|
| β (Domain) | Higher for: Data, Frontend, Security — roles where wrong domain knowledge is immediately visible on the job |
| γ (System Design) | Higher for: DevOps, ML Engineer, SRE — roles where architectural decisions are core responsibilities |

---

## 5. Functions — What They Do and How They Are Called

```
calculate_interview_difficulty()          ← Main entry point (you call this)
    │
    ├── _filter_domain()                  → Domain rows with experience filter
    ├── _resolve_weights()                → Exact → fuzzy → category inference → default
    │
    ├── _calculate_dsa_score()            → 5-tier DSA keyword scan + direct signal adjustments
    ├── _calculate_domain_score()         → 3-tier depth keyword scan + skill count blend
    ├── _calculate_system_design_score()  → 3-tier system design keyword scan + tier label
    │
    ├── [Inline composite]                → weighted sum of 3 pillar scores × 10
    ├── [Inline label]                    → 5-tier difficulty label
    │
    ├── _estimate_interview_structure()   → Round-by-round structure from scores + weights
    └── _generate_preparation_plan()      → 3 prioritized tracks + total weeks (max, not sum)
```

| Function | Role |
|---|---|
| `__init__()` | Applies custom weights, validates ALL domain profiles sum to 1.0 |
| `_validate_all_weights()` | Loops through every domain profile — raises error if any don't sum to 1.0 |
| `_filter_domain()` | Job_Type exact + experience filter + title word-boundary fallback |
| `_resolve_weights()` | 4-level weight resolution: exact → fuzzy word overlap → category inference → default |
| `_calculate_dsa_score()` | 5-tier DSA keyword analysis with direct override signals and Star_Skills boost |
| `_calculate_domain_score()` | 3-tier depth analysis with 70/30 blend of keywords and skill count |
| `_calculate_system_design_score()` | 3-tier system design analysis — cloud deliberately excluded from basic tier |
| `_estimate_interview_structure()` | Concrete round-by-round structure with focus, duration, probability |
| `_generate_preparation_plan()` | Priority-ranked tracks with specific LeetCode counts and week estimates |
| `calculate_interview_difficulty()` | **Master function** — orchestrates all steps, builds full output |

---

## 6. Output — What Does the Engine Return?

### Sample Output

```json
{
    "Domain": "Data Scientist",
    "Experience_Band": [0, 5],
    "Sample_Size": 184,
    "Weight_Profile": "exact",

    "Difficulty": {
        "Index": 5.8,
        "Label": "🟡 Moderate",
        "Raw_Score": 0.580
    },

    "Pillar_Scores": {
        "DSA": {
            "Score":      0.280,
            "Weight":     "15%",
            "Weighted":   0.42,
            "Easy_Pct":   18.2,
            "Medium_Pct": 24.5,
            "Hard_Pct":   8.1,
            "Confidence": "High"
        },
        "Domain_Knowledge": {
            "Score":       0.620,
            "Weight":      "65%",
            "Weighted":    4.03,
            "Surface_Pct": 41.2,
            "Deep_Pct":    22.8,
            "Source":      "keyword_analysis"
        },
        "System_Design": {
            "Score":        0.410,
            "Weight":       "20%",
            "Weighted":     0.82,
            "Tier":         "Intermediate — microservices & scalability questions",
            "Advanced_Pct": 18.3,
            "Confidence":   "High"
        }
    },

    "Interview_Structure": {
        "rounds": [
            {"round": 1, "type": "Online Assessment / Screening",
             "focus": "DSA problems (Easy-Medium level)", "duration": "60-90 min", "probability": "Very High"},
            {"round": 2, "type": "Technical Interview",
             "focus": "Domain depth: 22.8% of JDs mention advanced topics", "duration": "45-60 min", "probability": "High"},
            {"round": 3, "type": "System Design",
             "focus": "Intermediate — microservices & scalability questions", "duration": "45-60 min", "probability": "Medium"},
            {"round": 4, "type": "HR / Behavioral",
             "focus": "Culture fit, projects, career goals", "duration": "30-45 min", "probability": "Very High"}
        ],
        "total_rounds": 4,
        "approx_hours": 4.0,
        "intensity": "Moderate"
    },

    "Preparation_Plan": {
        "Tracks": [
            {
                "track": "Domain Knowledge",
                "priority": 4.0,
                "weight_pct": "65%",
                "intensity": "6.2/10",
                "recommendation": "Build 2-3 non-trivial projects. Study design patterns, testing, and production practices.",
                "weeks_needed": 8
            },
            {
                "track": "System Design",
                "priority": 0.82,
                "weight_pct": "20%",
                "intensity": "4.1/10",
                "recommendation": "Learn microservices, caching, load balancing. Practice designing 5-6 common systems.",
                "weeks_needed": 6
            },
            {
                "track": "DSA / Problem Solving",
                "priority": 0.42,
                "weight_pct": "15%",
                "intensity": "2.8/10",
                "recommendation": "Solve 75-100 LeetCode Easy-Medium. Focus on arrays, strings, hashing, basic sorting.",
                "weeks_needed": 4
            }
        ],
        "Total_Weeks_Needed": 8,
        "Time_Assumption": "10-15 hrs/week"
    }
}
```

### How to Read This Output

| Field | What it Tells the User |
|---|---|
| `Difficulty.Index` | Single headline difficulty number — the overall interview hardness |
| `Weight_Profile` | Whether "exact", "fuzzy", "inferred", or "default" weights were used — reliability indicator |
| `Pillar_Scores.*.Weighted` | How much each pillar contributes to the final score — where the difficulty comes from |
| `Pillar_Scores.DSA.Hard_Pct` | What % of JDs mention hard DSA topics — directly tells you if you need hard LeetCode |
| `Pillar_Scores.Domain_Knowledge.Deep_Pct` | What % of JDs mention deep domain internals — signals if you need OS/memory/compiler knowledge |
| `Interview_Structure.rounds` | The actual rounds you'll likely face — with focus, duration, and probability |
| `Preparation_Plan.Tracks` | **Priority-ranked preparation plan** — highest impact track first |
| `Preparation_Plan.Total_Weeks_Needed` | Realistic timeline (max of tracks, not sum — parallel prep) |

---

## 7. How Robust Are the Formulas and Constants?

### What Makes Them Solid ✅

| Feature | Why It's Good |
|---|---|
| **Domain-specific weight profiles** | The most important design decision. Interview difficulty is not universal — a Data Scientist and a Software Engineer need completely different preparation. 25 domain profiles capture these structural differences. |
| **Hard DSA at 50% weight (within DSA pillar)** | Hard problems represent a qualitatively different requirement level. Equal weighting with medium would dramatically underestimate difficulty for FAANG-style interviews. |
| **Direct override signals** | "competitive programming" in 25% of JDs is a much stronger signal than just counting hard algorithm keywords. Direct signals bypass indirect inference and give a boost. |
| **`"cloud"` excluded from system design basic tier** | A job mentioning AWS does NOT imply system design rounds. This exclusion prevents a major false positive that inflates system design scores for cloud-heavy domains incorrectly. |
| **70/30 blend of keyword + skill count for domain score** | Keywords are the primary signal but noisy. Skill count provides a structural sanity check. 70/30 gives keywords primacy while retaining the skill count signal. |
| **4-level weight resolution** | Exact → fuzzy word overlap → category inference → default. New or unusual domain names will always get a reasonable weight profile rather than crashing or using pure defaults. |
| **`max()` not `sum()` for total prep weeks** | Preparation tracks are parallel — you can study DSA and system design simultaneously. Using max gives the correct calendar-time estimate. |
| **Track priority = weight × score** | Preparation time should be proportional to both how much the interview tests this area (weight) AND how intense that area actually is (score). The product of both gives the correct priority. |
| **Validates ALL domain weight profiles at init** | Every entry in `DOMAIN_WEIGHTS` is checked. If a custom weight is passed that doesn't sum to 1.0, it fails at startup — not during a live analysis. |

---

## 8. Advantages of the Current Implementation

- **Domain-aware difficulty** — the core innovation. The same DSA score means different things for a Data Scientist vs a Software Engineer because the weights are different.
- **Three-pillar decomposition** — shows WHERE the difficulty comes from, not just how hard it is overall. Knowing that 65% of difficulty comes from domain knowledge tells you exactly what to study.
- **Concrete interview structure prediction** — "you'll likely face 4 rounds: OA → Technical → System Design → HR" is far more actionable than "difficulty: 5.8/10."
- **Priority-ranked preparation tracks** — the highest-impact track (Domain Knowledge for Data Scientists, DSA for SWEs) appears first with a specific recommendation.
- **Direct signal detection** — "competitive programming required" in JDs is caught as a direct override, not just inferred from indirect keywords.
- **"cloud" exclusion from system design** — a subtle but important correction for cloud-heavy domains.
- **Fuzzy weight resolution** — "Senior ML Research Engineer" still gets a sensible weight profile through fuzzy and inference matching.

---

## 9. Disadvantages and How to Improve Them

| Limitation | Problem | Suggested Fix |
|---|---|---|
| **`custom_weights` mutates the class-level `DOMAIN_WEIGHTS` dict** | Line 115: `self.DOMAIN_WEIGHTS.update(custom_weights)`. This modifies the class-level dictionary, not an instance copy. Two instances with different custom weights will overwrite each other's profiles on the shared class dict. | In `__init__()`, make an instance-level deep copy first: `self.DOMAIN_WEIGHTS = {k: dict(v) for k, v in self.__class__.DOMAIN_WEIGHTS.items()}` before applying `update()`. Same bug as `HiddenBlockerDetector`. |
| **`_resolve_weights()` partial matching is directional and fragile** | `if known_domain in domain_lower or domain_lower in known_domain` — if user types `"data"`, `"data"` is `in "data scientist"` so it matches. If user types `"data engineer"` (not in DOMAIN_WEIGHTS), it partially matches `"data analyst"` via the `in` check — a completely different role. | Use word-set intersection count (already computed as `overlap`) as the primary selector, not the substring `in` check. Add a minimum overlap threshold: at least 2 shared words required for a fuzzy match to fire. |
| **Interview structure estimation uses hardcoded thresholds** | `if domain["score"] > 0.50` to add a Technical Round, `if weights['g'] >= 0.20` for System Design round. These thresholds were manually chosen without validation against real interview processes. | Connect to a small validation dataset of known interview processes (e.g., collected user feedback). Alternatively, use percentile-based triggers: if a pillar score is above P60 of all domain scores in the dataset, add that round. |
| **Total prep time = max(tracks), ignores sequencing** | `total_weeks = max(t["weeks_needed"] for t in tracks)`. This assumes all tracks can be started simultaneously. But DSA prep is actually more effective before system design (you need to think algorithmically before designing systems). A sequenced estimate would be more accurate. | Add a `sequenced_weeks` field: DSA foundation (4 weeks baseline) → domain knowledge → system design builds on both. Weighted by which tracks are present and their required weeks. |
| **Domain knowledge `deep_pct` keyword list is sparse (12 keywords)** | The "deep" tier only has 12 keywords covering a narrow set of technical depth signals. A role requiring "distributed consensus", "zero-copy I/O", "SIMD optimization", or "FPGA programming" wouldn't trigger any deep signal. | Expand the deep tier to 30+ keywords covering current technical depth signals across all major domains. Group by domain category (web deep: browser internals, V8 engine; ML deep: backprop from scratch, custom CUDA kernels). |
| **No experience-level differentiation in preparation recommendations** | The same LeetCode count recommendation ("solve 300+ LeetCode") appears regardless of whether the user is targeting a 0–1 year experience role or a 3–5 year role. Junior interviews have lower bars. | Add `experience_band` to `_generate_preparation_plan()`. Scale thresholds: for fresher bands, reduce LeetCode targets by 30–40% and remove advanced system design track if `max_exp < 3`. |
| **`_estimate_interview_structure()` approximates total hours as `total_rounds × 1.0`** | Line: `total_hours = total_rounds * 1.0`. All rounds are treated as 1 hour each, but the code already specifies different durations (60–90 min OA, 45–60 min system design). The stored duration strings aren't used for the calculation. | Sum actual durations: parse the `"duration"` string from each round dict or store durations as numbers. `total_hours = sum(round["duration_min"] for round in rounds) / 60`. |

### Formula Improvement Suggestions

```python
# Current: max() for total prep weeks (assumes full parallelism)
total_weeks = max(t["weeks_needed"] for t in tracks)

# Improved: partial sequencing — DSA first, then domain + system design in parallel
# If DSA track exists, it provides a foundation for system design
dsa_track    = next((t for t in tracks if t["track"] == "DSA / Problem Solving"), None)
domain_track = next((t for t in tracks if t["track"] == "Domain Knowledge"), None)
sys_track    = next((t for t in tracks if t["track"] == "System Design"), None)

dsa_weeks    = dsa_track["weeks_needed"]    if dsa_track    else 0
domain_weeks = domain_track["weeks_needed"] if domain_track else 0
sys_weeks    = sys_track["weeks_needed"]    if sys_track    else 0

# System design benefits from DSA foundation — but not strictly sequential
# Domain knowledge is largely parallel to DSA
sequential_weeks = dsa_weeks + max(0, sys_weeks - dsa_weeks // 2)
parallel_weeks   = max(dsa_weeks, domain_weeks, sys_weeks)  # current approach

total_weeks = round((sequential_weeks + parallel_weeks) / 2)  # realistic midpoint
```

```python
# Current: hard_pct boost from direct_hard is additive and uncapped before clip
if direct_hard > 0.20:
    hard_p = min(1.0, hard_p + 0.30)
    med_p  = min(1.0, med_p  + 0.15)

# Improved: scale boost proportionally to signal strength, not a fixed +0.30
# A domain where 50% of JDs mention competitive programming should get a larger boost
# than one where 21% barely cross the threshold
boost_multiplier = min(2.0, direct_hard / 0.20)  # 1.0× at threshold, 2.0× at 40%+ JDs
hard_p = min(1.0, hard_p + 0.20 * boost_multiplier)
med_p  = min(1.0, med_p  + 0.10 * boost_multiplier)
```

```python
# Current: track priority score
priority = round(weights['a'] * dsa_intensity * 10, 1)

# Improved: include difficulty gap between current knowledge and required level
# A user who already has strong DSA should see lower DSA priority
# (Requires user_skills input — future enhancement)
# For now, multiply by a confidence factor so low-confidence scores have lower priority
confidence_factor = {"High": 1.0, "Medium": 0.8, "Low": 0.6}.get(dsa["confidence"], 0.7)
priority = round(weights['a'] * dsa_intensity * 10 * confidence_factor, 1)
```

---

*End of Engine 13 Documentation*

---
---

# Engine 14 — `RoleEvolutionEngine` (Role Evolution Engine)

**File:** `role_evaluation_engine.py`  
**Class:** `RoleEvolutionEngine`

> **Note on file naming:** The file is named `role_evaluation_engine.py` but the class inside is `RoleEvolutionEngine`. The correct name is **Evolution** (not Evaluation) — this appears to be a filename typo.

---

## 1. Introduction — What is this Engine and What Does it Do?

Every other engine in the pipeline answers questions about the current state of the market — "what does this domain pay now?", "how competitive is it now?", "how hard are the interviews?" This engine is the only one that answers a question about the **future**:

> *"If I start as a Junior Data Scientist today, where will I realistically be in 3 years, 5 years, 10 years — and what will my salary look like at each step?"*

It also answers the career fork question that every mid-level professional eventually faces:

> *"Should I stay on the Individual Contributor (IC) track and become a Staff Engineer / Principal Scientist, or should I pivot to the Management track and become an Engineering Manager / Director?"*

**`RoleEvolutionEngine` is a career trajectory simulator.** It uses a hand-crafted **Career Transition Graph** — a directed probability graph where each role has probabilities of transitioning to possible next roles — to:

1. **Simulate the most likely career path** step by step (greedy: always pick the highest-probability next role)
2. **Show all alternative paths** at each step (branches: what else could happen?)
3. **Attach salary data** to each role from the dataset — so you see compensation at every step
4. **Identify skills to acquire** between each transition
5. **Check market availability** of each next role — is there actually demand for it?
6. **Flag IC vs Management forks** when they appear
7. **Estimate time at each role** using actual dataset experience requirements (not just guesswork)

> Think of it like a GPS route planner with multiple route options. The primary route shows the most likely path. Alternative routes show other viable options. Each waypoint shows what you'll "pay" (skills to acquire) and "earn" (salary) when you arrive. And the GPS warns you when a road is rarely travelled (niche role, low market availability).

---

## 2. Data Fields Required by This Engine

### Required

| Column Name | What it Means | Required? |
|---|---|---|
| `Job_Type` | Domain/category of the job | ✅ Primary role filter |

### Strongly Recommended

| Column Name | What it Means | Fallback if Missing |
|---|---|---|
| `Title_Cleaned` (or `TItle_Cleaned`) | Job title text | Role filter may miss records |
| `Min_Experience` | Minimum years required | Time-in-role falls back to TYPICAL_YEARS table |
| `Avg_Salary` | Average salary | Salary data shows as `None` for that role |
| `Star_Skills` | Must-have skills (preferred) | Falls to `Combined_Skills` |
| `Combined_Skills` | All skills from posting | Skills-to-acquire list will be empty |
| `No of job opening cleaned ` | Actual openings count | Market availability shows listing count only |

### Inputs Passed at Runtime

| Parameter | What it Means | Default |
|---|---|---|
| `current_role` | Starting role (e.g., `"Junior Data Scientist"`) | Required |
| `steps` | How many career steps ahead to simulate | `3` |
| `show_branches` | Include all alternative paths at each step | `True` |
| `custom_transitions` | Override or add role transitions (set in `__init__`) | `None` |

---

## 3. Core Logic — How Does the Engine Simulate Career Evolution?

### The Career Transition Graph

The engine's core knowledge base is `TRANSITION_GRAPH` — a directed probability graph:

```python
{
    "junior data scientist": {
        "mid data scientist":  0.70,   # 70% probability this is the next step
        "data analyst":        0.15,   # 15% chance of lateral move
        "ml engineer":         0.15,   # 15% chance of domain switch
    },
    ...
}
```

**Probabilities within each role must sum to exactly 1.0** — validated at `__init__()`.

**Graph structure covers 5 main tracks:**

| Track | Starting Point | IC Ceiling | Management Path |
|---|---|---|---|
| Data Science | junior data scientist | chief data scientist | data science manager → director → CDO |
| ML Engineering | junior ml engineer | ml architect | engineering manager |
| Software Engineering | junior software engineer | distinguished engineer | engineering manager → director → VP |
| Frontend / Backend | junior developer | architect | engineering manager |
| DevOps / Cloud | junior devops engineer | devops architect | engineering manager |

**Role Metadata** classifies each role by three dimensions:
- `track`: IC (Individual Contributor), MGT (Management), SPEC (Specialist)
- `level`: 1 (junior) → 6 (principal/distinguished)
- `domain`: data_science, ml_engineering, software, frontend, backend, devops, analytics

---

### Step 1 — Role Resolution (`_resolve_role`)

User input is rarely exactly right. "ML Eng", "Junior SWE", "Data Sci" all need to map to graph keys.

**Three-level resolution:**

```
Level 1: Exact match (case-insensitive)
         "Junior Data Scientist" → "junior data scientist" ✅

Level 2: Substring match (both directions)
         "Senior ML Research Engineer" → "ml engineer" is in "senior ml research engineer" ✅

Level 3: Word overlap (minimum 1 shared word)
         "data science lead" → "lead data scientist" has 2 shared words ("data", "lead") ✅

No match: returns error with list of valid roles
```

The `Match_Type` field in the output tells you which level was used — so users can see if an exact or approximate match was applied.

---

### Step 2 — Greedy Path Simulation

For `steps` iterations:

```
current = resolved_role
for each step:
    next_role = argmax(TRANSITION_GRAPH[current])  ← highest probability transition
    
    time_data   = _get_time_in_role(df, current)
    current_sal = _get_role_salary(df, current)
    next_sal    = _get_role_salary(df, next_role)
    gap_skills  = _get_role_skills(df, next_role) - _get_role_skills(df, current)
    availability = _check_market_availability(df, next_role)
    
    cumulative_prob  *= transition_probability
    cumulative_years += time_in_current_role
    
    current = next_role
```

---

### Step 3 — Time in Role Estimation (`_get_time_in_role`)

This is one of the most carefully designed functions — it uses a **3-level fallback chain**:

**Method 1 — Data-Driven (most accurate):**
```
current_median_min_exp = median(Min_Experience) for current role
next_median_min_exp    = median(Min_Experience) for next role

delta = next_median_min_exp - current_median_min_exp

Valid if: 0.5 ≤ delta ≤ 8.0   ← sanity range
```

**Why this formula?** If "Junior Data Scientist" jobs require median 0.5 years and "Mid Data Scientist" jobs require median 2.5 years, then the typical time-in-role before transitioning is approximately 2.0 years. This is a smart proxy — it uses the market's own experience requirements to infer role tenure.

**Critical fix noted in code:** `Max_Exp - Min_Exp` is the job's requirement range (e.g., "2–5 years wanted"), NOT the tenure. Previous implementations that used this were computing the wrong thing entirely.

**Method 2 — Seniority Level Fallback:**
```
TYPICAL_YEARS = {
    1: 1.5,   # Junior → Mid
    2: 2.5,   # Mid → Senior
    3: 3.0,   # Senior → Lead/Staff
    4: 3.5,   # Lead → Principal/Director
    5: 4.0,   # Principal → Distinguished/VP
}
```

**Method 3 — Industry Average:**
```
years = 2.5 (generic fallback)
confidence = "Very Low"
```

The output includes `source` and `confidence` so users know how reliable the time estimate is.

---

### Step 4 — Salary Data (`_get_role_salary`)

For each role in the path:
```
role_df = filter postings matching this role title
sal = Avg_Salary column, numeric conversion
IQR outlier removal (1.5× standard)
median_lpa = clean_median / 100000   ← converts to LPA

Returns: {median_lpa, p25_lpa, p75_lpa, sample_size}
         or None if < MIN_SAMPLES records
```

**Between-role salary delta:**
```
delta_lpa = next_salary.median_lpa - current_salary.median_lpa
delta_pct = (delta_lpa / current_salary.median_lpa) × 100

> +10%: "📈 +X% salary growth"
±10%:  "➡️  Similar compensation"
< -10%: "📉 X% — verify this transition makes sense"
```

---

### Step 5 — Skills Gap Per Transition

```
current_skills = top 10 skills from Star_Skills or Combined_Skills for current role
next_skills    = top 10 skills for next role

skills_to_gain = next_skills - current_skills    ← set difference, top 5 shown
```

Skills are extracted by frequency — most-mentioned skills across all postings for that role appear first.

---

### Step 6 — Market Availability Check

```
listings = count of postings matching this role in dataset

≥ 50 listings: ✅ Active market
15–49:         🟡 Moderate demand
5–14:          🟠 Niche role — limited openings
< 5:           🔴 Rare in current market
```

A career path that goes through a "🔴 Rare in current market" role is a red flag — the theoretical transition probability may be valid but the actual market may not support it.

---

### Step 7 — Move Type Classification

Each step is classified using role metadata:

```
IC → MGT:                "🔀 Management Pivot"
next_level > current_level: "⬆️  Promotion"
else:                       "↔️  Lateral Move"

Lateral + different domain (from _get_all_next_steps):
    "Lateral + Domain Switch"
```

---

### Step 8 — Cumulative Probability Decay

```
cumulative_prob starts at 1.0
After step 1: cumulative_prob = 0.70   (if first transition had 70% probability)
After step 2: cumulative_prob = 0.70 × 0.65 = 0.455
After step 3: cumulative_prob = 0.455 × 0.55 = 0.250
```

The engine explicitly warns about this in the output: *"Individual steps are more reliable than the full chain."* A 3-step path with 25% cumulative probability doesn't mean the path is unlikely — it means each step is individually probable but the exact sequence matters less than the direction.

---

## 4. Constants and Parameters — What They Mean and Why

| Constant / Parameter | Value | Justification |
|---|---|---|
| Transition probabilities | Sum to 1.0 per role | Probabilistic model — each role's exit distribution must be a proper probability distribution |
| `TYPICAL_YEARS` level 1 | **1.5 years** | Junior roles are often fast exits — companies expect juniors to be promoted or leave within 1–2 years |
| `TYPICAL_YEARS` level 2 | **2.5 years** | Mid-level standard tenure |
| `TYPICAL_YEARS` level 3–5 | **3.0–4.0 years** | Senior/lead roles require deeper expertise and slower advancement |
| Time delta sanity range | **0.5 – 8.0 years** | Below 0.5: suspiciously fast (data noise). Above 8: suspiciously slow (likely bad data or extreme outlier). Outside this range → fall back to typical years. |
| `MIN_SAMPLES` | **5** | Minimum postings for any role to produce reliable salary or experience data |
| Market availability thresholds | **50/15/5** | Industry heuristics for what "active" vs "niche" vs "rare" means in Indian tech job market |
| `steps` default | **3** | 3 career steps covers approximately 6–8 years — a meaningful planning horizon for most professionals |
| IQR salary outlier | **1.5×** | Standard IQR for salary cleaning — less conservative than engines with 2.5× because per-role samples are smaller |

---

## 5. Functions — What They Do and How They Are Called

```
predict_evolution_path()              ← Main entry point (you call this)
    │
    ├── _resolve_role()               → 3-level fuzzy matching to graph keys
    │
    ├── [For each step in range(steps):]
    │     ├── [Inline] argmax transition → greedy next role
    │     ├── _get_time_in_role()     → 3-level time estimate (data → seniority → average)
    │     ├── _get_role_salary()      → IQR-cleaned median salary with P25/P75
    │     ├── _get_role_skills()      → Top 10 skills by frequency
    │     ├── _check_market_availability() → Listing count + signal label
    │     └── _get_all_next_steps()   → All branches with probability + salary + move type
    │
    └── [Post-loop summary]
        ├── Total salary growth (start → end)
        └── IC vs Management fork detection
```

| Function | Role |
|---|---|
| `__init__()` | Merges custom transitions, validates ALL role probability sums = 1.0 |
| `_validate_transition_graph()` | Ensures every role's transition probabilities sum to 1.0 ± 0.02 |
| `_filter_role()` | Job_Type exact match + title word-boundary fallback |
| `_resolve_role()` | Exact → substring → word-overlap fuzzy matching |
| `_get_time_in_role()` | Min_experience delta method → seniority fallback → industry average |
| `_get_role_salary()` | IQR-cleaned median salary with P25/P75 and LPA conversion |
| `_get_role_skills()` | Top 10 skills by frequency from Star_Skills or Combined_Skills |
| `_get_all_next_steps()` | All possible next roles sorted by probability with salary and move type |
| `_check_market_availability()` | Listing count + openings count → 4-tier signal label |
| `predict_evolution_path()` | **Master function** — greedy path simulation + summary + IC/MGT fork detection |

---

## 6. Output — What Does the Engine Return?

### Sample Output

```json
{
    "Starting_Role": "Junior Data Scientist",
    "Resolved_Role": "junior data scientist",
    "Match_Type": "exact",

    "Evolution_Path": [
        {
            "step": 1,
            "from": "junior data scientist",
            "to":   "mid data scientist",
            "move_type": "⬆️  Promotion",
            "transition_probability": "70%",
            "time_in_current_role": {
                "years": 2.0, "source": "data_driven", "confidence": "High"
            },
            "cumulative_years": 2.0,
            "salary_at_next_role": {
                "median_lpa": 9.8, "p25_lpa": 7.5, "p75_lpa": 13.2, "sample_size": 84
            },
            "salary_progression": {
                "delta_lpa": 4.3, "delta_pct": 78.2,
                "signal": "📈 +78% salary growth"
            },
            "skills_to_acquire": ["tensorflow", "feature engineering", "spark", "mlflow"],
            "market_availability": {"listings": 84, "openings": 210, "signal": "✅ Active market"},
            "alternative_paths": [
                {"role": "data analyst", "probability": "15%", "move_type": "Lateral Move",
                 "salary": {"median_lpa": 6.2, ...}},
                {"role": "ml engineer", "probability": "15%", "move_type": "Lateral + Domain Switch",
                 "salary": {"median_lpa": 10.5, ...}}
            ]
        },
        {
            "step": 2,
            "from": "mid data scientist",
            "to":   "senior data scientist",
            "move_type": "⬆️  Promotion",
            "transition_probability": "55%",
            "cumulative_years": 4.5,
            "salary_at_next_role": {"median_lpa": 16.4, ...},
            "salary_progression": {"delta_pct": 67.3, "signal": "📈 +67% salary growth"},
            "skills_to_acquire": ["system design", "research", "team mentoring"],
            "alternative_paths": [
                {"role": "ml engineer",          "probability": "25%", "move_type": "Lateral + Domain Switch"},
                {"role": "data science manager", "probability": "10%", "move_type": "Pivot to Management"}
            ]
        }
    ],

    "Journey_Summary": {
        "Total_Steps": 3,
        "Total_Years": 7.5,
        "Path_Confidence": "20.4%",
        "Confidence_Note": "Confidence decays with each step. 20.4% reflects the joint probability of this exact sequence — individual steps are more reliable than the full chain.",
        "Starting_Salary": {"median_lpa": 5.5, ...},
        "Ending_Salary":   {"median_lpa": 24.2, ...},
        "Total_Salary_Growth": "+340% total compensation growth",
        "Track_Note": "🔀 Management track available at this level. IC track continues to Staff/Principal. Management track leads to Director/VP. Both are valid — choose based on your strengths."
    },

    "Data_Coverage": {
        "Roles_In_Dataset": 3,
        "Salary_Data_Available": true
    }
}
```

### How to Read This Output

| Field | What it Tells the User |
|---|---|
| `Match_Type` | Was your role exactly matched or approximated? |
| `Evolution_Path[n].transition_probability` | How likely is this specific next step |
| `Evolution_Path[n].time_in_current_role.source` | Is the tenure estimate data-driven or a fallback guess? |
| `Evolution_Path[n].salary_progression.signal` | Will you earn more or less at the next role? |
| `Evolution_Path[n].skills_to_acquire` | What to learn before making this transition |
| `Evolution_Path[n].market_availability.signal` | Is there actually demand for this next role? |
| `Evolution_Path[n].alternative_paths` | What else could you do instead of the greedy path |
| `Journey_Summary.Path_Confidence` | How probable is this exact sequence (decreases with each step) |
| `Journey_Summary.Track_Note` | IC vs Management fork warning when applicable |
| `Journey_Summary.Total_Salary_Growth` | Total compensation journey from start to end role |

---

## 7. How Robust Are the Formulas and Constants?

### What Makes Them Solid ✅

| Feature | Why It's Good |
|---|---|
| **Experience delta for time estimation** | Instead of hardcoding "junior = 2 years", the engine infers tenure from the actual gap in experience requirements between roles in the dataset. Market-adaptive and data-grounded. |
| **3-level time fallback chain** | Data-driven → seniority lookup → industry average. Graceful degradation with explicit confidence labels at each level. |
| **Cumulative probability with explicit warning** | The engine correctly computes joint probability and warns users that the full path is less reliable than individual steps. Prevents false confidence. |
| **Probability validation at init** | All role transition probabilities must sum to 1.0. Validated at startup on all roles in the graph. |
| **Market availability check** | A theoretical career path with a "🔴 Rare in current market" role is flagged immediately — theory vs practice gap exposed. |
| **IC vs Management fork detection** | Automatically detects when a management path appears in the alternatives and surfaces a dedicated note — answering the most common career decision question. |
| **Move type classification from metadata** | Uses level and track metadata, not just names, to correctly identify Promotion vs Lateral vs Management Pivot. |
| **Salary delta with direction signal** | ±10% tolerance prevents noise from triggering "pay cut" warnings on equivalent compensation. |

---

## 8. Advantages of the Current Implementation

- **Full career trajectory in one call** — salary at every step, skills to acquire, market availability, time estimates, and alternative paths — all in a single API call.
- **Probabilistic branching** — shows not just the greedy path but all realistic alternatives at each step, enabling the user to make informed choices about lateral vs upward moves.
- **IC vs Management fork detection** — the most important career decision question is automatically surfaced when it appears in the transition graph.
- **Data-driven time estimates** — tenure derived from actual market experience requirements rather than hardcoded industry guesses.
- **Market availability validation** — prevents recommending theoretical paths that have no actual demand in the job market.
- **Skill gap per transition** — at every career step, the user sees what they need to learn to make that specific transition.
- **Confidence decay warning** — the engine is honest about the decreasing reliability of longer-horizon predictions.
- **Custom transitions via `__init__`** — new roles, new paths, or company-specific hierarchies can be added without code changes.

---

## 9. Disadvantages and How to Improve Them

| Limitation | Problem | Suggested Fix |
|---|---|---|
| **`custom_transitions` mutates class-level `TRANSITION_GRAPH`** | Line 202: `self.TRANSITION_GRAPH.update(custom_transitions)` modifies the class-level dict. Two instances with different custom transitions will overwrite each other. Same bug as `HiddenBlockerDetector` and `InterviewDifficultyEngine`. | Instance-level deep copy: `self.TRANSITION_GRAPH = {k: dict(v) for k, v in self.__class__.TRANSITION_GRAPH.items()}` before applying `update()`. |
| **Greedy path only shows ONE sequence** | The greedy algorithm always picks the highest-probability next role. This gives "the most common path" but not necessarily "the best path" for the user. Someone targeting ML Engineering should see the Data Science → ML Engineer path, not Data Science → Senior Data Scientist. | Add a `target_role: str = None` parameter. If provided, use A* or Dijkstra's algorithm on the graph to find the shortest-probability path from current role to target role. |
| **`_resolve_role()` substring match is directional and fragile** | `if known_role in role_lower or role_lower in known_role` — typing `"data"` matches `"data analyst"` because `"data"` is a substring of `"data analyst"`. This is the same fragile matching issue as `InterviewDifficultyEngine`. | Enforce minimum word overlap: require at least 2 shared words for substring match, or use only the word-overlap method with a minimum threshold of 2. |
| **`_get_role_skills()` uses comma-split without `ast.literal_eval`** | `for skill in skills_str.split(',')` — if `Star_Skills` is stored as a Python list literal `"['python', 'sql']"`, the split produces `"['python'"` and `" 'sql']"` with brackets and quotes. Same dual-format issue that `PrerequisiteEngine` handles correctly. | Use `_parse_skills_string()` from `PrerequisiteEngine` (or a shared utility module) instead of raw comma-split. |
| **Transition probabilities are entirely manually set** | All 40+ role transitions and their probabilities were manually authored. There is no data validation that, for example, 70% of Junior Data Scientists actually become Mid Data Scientists vs 15% who become Data Analysts. | Validate (or derive) transition probabilities from the dataset: for roles that appear in the dataset, compute the actual distribution of experience levels and job titles to calibrate the manual graph against real data. |
| **Time estimate delta sanity range `0.5 – 8.0` is hardcoded** | If two roles genuinely have a small experience delta (e.g., some markets compress juniors and mids to only 1 year apart), the 0.5 floor might incorrectly reject valid deltas. | Make the sanity bounds configurable as class constants: `MIN_DELTA_YEARS = 0.5` and `MAX_DELTA_YEARS = 8.0`. Make them easy to tune per market. |
| **No reverse path lookup** | A user who knows where they want to END UP (e.g., "I want to be a Data Science Director in 5 years") cannot ask the engine "what path should I take?" — the engine only goes forward from a starting role. | Add `find_path_to(target_role, max_steps=5)` method that performs a backward BFS from target role through the graph to find which starting roles can reach it and through which paths. |
| **Skills-to-acquire list capped at top 5** | Line 540: `skills_to_gain = list(next_skills - current_skills)[:5]`. The top 10 skills per role are retrieved, then only the first 5 differences are shown. "First 5" is arbitrary — skill importance isn't preserved in the set difference operation. | Weight skills by frequency and sort: `sorted(next_skills - current_skills, key=lambda s: skill_frequency[s], reverse=True)[:5]`. Show the 5 most-frequently-required new skills, not the first 5 alphabetically. |

### Formula Improvement Suggestions

```python
# Current: greedy path (always pick highest probability)
next_role = max(transitions, key=transitions.get)

# Improved: user-directed path finding toward a target role
# If user wants to reach "data science manager", 
# pick transitions that increase proximity to that target
def _find_optimal_path(self, current: str, target: str, steps: int) -> List[str]:
    """BFS to find shortest path from current to target."""
    from collections import deque
    queue = deque([(current, [current])])
    visited = set()
    
    while queue:
        role, path = queue.popleft()
        if role == target:
            return path
        if role in visited or len(path) > steps:
            continue
        visited.add(role)
        for next_role in self.TRANSITION_GRAPH.get(role, {}):
            queue.append((next_role, path + [next_role]))
    return []  # No path found within steps
```

```python
# Current: time estimate uses simple median delta
delta = next_median - current_median

# Improved: use interquartile range of the delta for a confidence interval
# Report: "typically 1.5-2.5 years" rather than just "2.0 years"
current_p25 = min_exp.quantile(0.25)
current_p75 = min_exp.quantile(0.75)
next_p25    = next_exp.quantile(0.25)
next_p75    = next_exp.quantile(0.75)

delta_low  = max(0, next_p25 - current_p75)   # Fastest realistic transition
delta_high = next_p75 - current_p25             # Slowest realistic transition

return {
    "years":       round((delta_low + delta_high) / 2, 1),  # midpoint
    "years_range": f"{delta_low:.1f}–{delta_high:.1f}",    # range shown to user
    "source":      "data_driven"
}
```

```python
# Current: cumulative path probability as joint probability
cumulative_prob *= prob  # decreases to ~20% over 3 steps

# Improved: also compute "expected steps to target" using Markov chain theory
# For a Markov chain, the expected number of steps to reach a state
# can be computed from the transition matrix — gives a more intuitive metric
# than joint probability which most users misinterpret
# Add: "At current transition rates, the median career path reaches 
# Senior Data Scientist in approximately X years"
```

---

*End of Engine 14 Documentation*

---
---

# Engine 15 — `CareerPathEngine` (Career Path & Readiness Orchestrator)

**File:** `career_path_engine.py`  
**Class:** `CareerPathEngine`

---

## 1. Introduction — What is this Engine and What Does it Do?

Every engine built so far answers one specific question in depth. But a user doesn't sit down and run 14 separate analyses before deciding what to do. They ask one compound question:

> *"I want to become a Data Scientist. Given my current skills, how ready am I — and what exactly should I do next?"*

**`CareerPathEngine` is the final orchestration layer** — the conductor that calls the right sub-engines, collects their outputs, weighs them together, and produces a single, unified **Readiness Report** with one headline number and one priority action.

It is the only engine in the pipeline that accepts **other engines as constructor arguments** (dependency injection). This gives it two operating modes:

**Mode 1 — Standalone (no sub-engines injected):**  
All calculations are done internally with simplified fallback logic. Works immediately with no setup — useful for quick assessments.

**Mode 2 — Orchestrated (all sub-engines injected):**  
Delegates to the full, production-quality implementations of each engine. Each sub-engine result feeds into the composite readiness score. This is the intended production use.

The engine synthesizes **4 dimensions** into a single **Readiness Score (0–100)**:

| Dimension | Weight | Question it Answers |
|---|---|---|
| Skill Overlap | 40% | Do you already have what this domain needs? |
| Blocker Clearance | 25% | Are there hidden walls that could block even skilled candidates? |
| Interview Manageability | 20% | How hard are the interviews relative to your current level? |
| Time Manageability | 15% | Is the remaining gap achievable in a reasonable timeframe? |

And alongside the score, it produces:
- A **Learning Plan** showing how many hours/weeks/months to close the gap
- A **Project Benchmark** showing what complexity level is expected
- A **Salary Benchmark** for the target domain
- **Hidden Blocker** summary
- **Evolution Preview** showing where this role leads in 2 steps
- A **single Priority Action** — the one most impactful thing to do right now

> Think of it like a financial planning dashboard. Different modules track your savings, investments, debt, and insurance. But the dashboard shows one overall financial health score, one urgent action, and one forward projection — synthesizing everything into what actually matters for the decision at hand. This engine does the same for career readiness.

---

## 2. Data Fields Required by This Engine

This engine inherits the data requirements of all sub-engines it calls. Minimum for internal fallback mode:

| Column Name | What it Means | Required? |
|---|---|---|
| `Job_Type` | Domain/category of the job | ✅ Primary domain filter |
| At least one skill column | `Star_Skills`, `Combined_Skills`, or `Normal_Skills` | ✅ Skill overlap calculation |

### Full Data for Rich Output

| Column Name | Used For | Fallback if Missing |
|---|---|---|
| `Title_Cleaned` (or `TItle_Cleaned`) | Domain filter fallback | Filter may miss records |
| `Min_Experience` | Experience filtering + experience inflation blocker | Experience filter skipped |
| `Skill_Count` | Project benchmark fallback | Score defaults to 5.0 |
| `Avg_Salary` | Salary benchmark | `Salary_Benchmark: null` |
| `Description_Cleaned` | Interview difficulty, blocker detection | Internal estimates used |
| `No of applicant applied cleaned` | Blocker detection | Applicant surge not detected |
| `No of job opening cleaned ` | Blocker detection | Market blocker not detected |

### Inputs Passed at Runtime

| Parameter | What it Means | Default |
|---|---|---|
| `target_domain` | Domain to assess readiness for (e.g., `"Data Scientist"`) | Required |
| `user_skills` | List of user's current skills | Required |
| `prior_knowledge` | `"none"`, `"basic"`, `"intermediate"`, `"advanced"` | `"basic"` |
| `user_project_stats` | Optional dict with project info for ProjectComplexityEvaluator | `None` |
| `experience_band` | Tuple `(min_exp, max_exp)` | `(0, 3)` |

### Sub-Engine Injection (via `__init__`)

```python
engine = CareerPathEngine(
    prerequisite_engine    = PrerequisiteEngine(),
    transferability_engine = SkillTransferabilityEngine(),
    project_evaluator      = ProjectComplexityEvaluator(),
    interview_engine       = InterviewDifficultyEngine(),
    blocker_detector       = HiddenBlockerDetector(),
    evolution_engine       = RoleEvolutionEngine()
)
```

> **Note:** `prerequisite_engine` and `transferability_engine` are accepted as parameters but are **never called** in the current implementation. See Section 9.

---

## 3. Core Logic — How Does the Engine Calculate Readiness?

The `calculate_learning_readiness()` method runs **11 sequential steps**:

---

### Steps 1–2: Domain Filtering + Skill Profile Extraction

Standard domain filter (Job_Type first, title fallback), then extract weighted skill importance profile from `Star_Skills` (2.0×), `Combined_Skills` (1.0×), `Normal_Skills` (0.6×). Skills below 2% presence threshold are filtered out as noise.

---

### Step 3: Skill Overlap Calculation

**Formula:**
```
weighted_coverage = Σ importance[skill] for skill in (user_skills ∩ required)
                  / Σ importance[skill] for all required skills

count_ratio = |user_skills ∩ required| / |required|

composite = 0.60 × weighted_coverage + 0.40 × count_ratio
```

Same 60/40 split as `SkillTransferabilityEngine` and `PrerequisiteEngine` — having the **right** skills matters more than having **many** skills.

---

### Step 4: Learning Time Calculation

**Three critical fixes documented in comments:**

**Fix 1 — Only count GAP skills:**
```
gap_skills = required_skills − user_skills  ← only what you don't have
```
Previous broken versions counted ALL required skills even if user already knew them.

**Fix 2 — Prior knowledge REDUCES time (not increases):**
```
PRIOR_KNOWLEDGE_FACTORS = {
    "none":         1.30,   # 30% more time needed
    "basic":        1.00,   # Baseline
    "intermediate": 0.75,   # 25% faster
    "advanced":     0.50,   # 50% faster
}
```
Previous broken version had `"advanced": 1.5` — meaning advanced knowledge made preparation take 50% LONGER. This was a direct inversion of the correct logic and has been explicitly fixed.

**Fix 3 — Importance-weighted hours:**
```
hours_per_skill = BASE_HOURS (35) × 1.5 if importance > 0.5 else BASE_HOURS
total_hours = Σ hours_per_skill for gap skills
total_hours ×= prior_knowledge_factor

weeks  = total_hours / 10     (10 hrs/week assumed)
months = weeks / 4.3
```

High-importance gap skills (market importance > 0.5) need 1.5× more depth — you can't be superficial about skills that appear in the majority of job postings.

---

### Step 5: Project Benchmark

**Orchestrated mode:** Calls `ProjectComplexityEvaluator.evaluate_portfolio_readiness()`.

**Fallback mode (no engine injected):**
```
score = min(10.0, (median_skill_count / 20) × 10)
label = "Advanced" if score ≥ 6.5, "Medium" if ≥ 4.0, else "Basic"
```

---

### Step 6: Interview Difficulty

**Orchestrated mode:** Calls `InterviewDifficultyEngine.calculate_interview_difficulty()`.

**Fallback mode:**
```
weights = DOMAIN_WEIGHTS[target_domain]
estimated_index = α×5.0 + β×5.0 + γ×4.5   ← conservative mid-range estimate
```
The fallback conservatively estimates all pillars at moderate difficulty and labels the output as an estimate so users are not misled.

---

### Step 7: Hidden Blockers

**Orchestrated mode:** Calls `HiddenBlockerDetector.scan_for_blockers()`.

**Fallback mode:**
```
fresher_pct = fraction of domain postings with Min_Experience ≤ 1 year × 100
if fresher_pct < 30%:
    severity = ((30 − fresher_pct) / 30) × 0.90
    trigger experience_inflation blocker
```
Only the experience inflation blocker is detectable in fallback mode — all 10 description-based blockers require the full `HiddenBlockerDetector`.

---

### Step 8: Evolution Preview

**Orchestrated mode:** Calls `RoleEvolutionEngine.predict_evolution_path()` with `steps=2`.

**Standalone mode:** Returns `None` — evolution preview is completely unavailable without the engine.

---

### Step 9: Composite Readiness Score (0–100)

```
Component 1 — Skill Overlap (40%):
    overlap_component = composite_skill_score × 100

Component 2 — Blocker Clearance (25%):
    blocker_risk      = Overall_Risk.score (0–1)
    blocker_component = (1 − blocker_risk) × 100

Component 3 — Interview Manageability (20%):
    interview_index   = Difficulty.Index (0–10)
    interview_component = (10 − interview_index) / 10 × 100
    ← Lower difficulty = more manageable = higher readiness

Component 4 — Time Manageability (15%):
    months ≤ 0:   100   (no gap)
    months ≤ 3:    90   (achievable)
    months ≤ 6:    70   (manageable)
    months ≤ 12:   45   (challenging)
    else:          20   (very long haul)

Composite = 0.40×overlap + 0.25×blocker + 0.20×interview + 0.15×time
            clipped to [0, 100]
```

---

### Steps 10–11: Salary Benchmark + Priority Action

**Salary:** IQR-cleaned (1.5× standard) median of `Avg_Salary` → P25/P50/P75 in LPA.

**Priority Action selection logic (in order of precedence):**
```
1. If any blocker severity > 0.70:
   → "🚨 Address critical blocker first: [resolution]"

2. Else if composite_skill_score < 0.55 AND gap skills exist:
   → "🎯 Start with: '[top_gap_skill]'. Full prep: ~N months."

3. Else by readiness score:
   ≥ 75: "✅ Apply now — focus on interview prep and portfolio polish."
   ≥ 55: "🟡 Close remaining gaps, then apply within 1-2 months."
    else: "📚 Structured learning: ~N months to job-ready. Start today."
```

---

## 4. Readiness Score Weights — What They Mean and Why

| Component | Weight | Justification |
|---|---|---|
| Skill Overlap | **40%** | The most fundamental signal — without skill fit, everything else is irrelevant. Highest weight reflects this primacy. |
| Blocker Clearance | **25%** | Hidden blockers can reject even well-qualified candidates. Second-highest because these are often invisible and high-impact. |
| Interview Manageability | **20%** | Even perfect skills don't help if the interview process is far too hard for the current level. Critical for freshers targeting high-difficulty domains. |
| Time Manageability | **15%** | A large gap isn't disqualifying if it's achievable in 4 months. Lowest weight because time is controllable by the user. |

### Prior Knowledge Factors

| Level | Factor | Meaning |
|---|---|---|
| `none` | 1.30× | Zero background — learns everything from scratch, takes 30% longer |
| `basic` | 1.00× | Some exposure — baseline pace |
| `intermediate` | 0.75× | Foundational knowledge + some hands-on — learns 25% faster |
| `advanced` | 0.50× | Deep adjacent expertise — applies existing mental models, learns 50% faster |

---

## 5. Functions — What They Do and How They Are Called

```
calculate_learning_readiness()          ← Main entry point (you call this)
    │
    ├── _filter_domain()                → Domain rows with experience filter
    ├── _extract_required_skills()      → Weighted skill profile (2.0/1.0/0.6 weights)
    ├── _normalize_user_skills()        → Alias resolution + lowercase normalization
    │
    ├── _calculate_skill_overlap()      → 60/40 weighted + count composite
    ├── _calculate_learning_time()      → Gap-only, importance-weighted, prior-corrected
    │
    ├── _get_project_benchmark()        → ProjectComplexityEvaluator OR skill-count fallback
    ├── _get_interview_difficulty()     → InterviewDifficultyEngine OR weight-based estimate
    ├── _get_blockers()                 → HiddenBlockerDetector OR fresher-% fallback
    ├── _get_evolution_path()           → RoleEvolutionEngine OR None
    │
    ├── _compute_readiness_score()      → 4-component weighted composite 0-100
    ├── [Inline] salary benchmark       → IQR-cleaned P25/P50/P75
    └── _derive_next_action()           → Priority action from dominant weakness
```

| Function | Role |
|---|---|
| `__init__()` | Stores injected sub-engine references, sets up logger |
| `_filter_domain()` | Job_Type exact + experience filter + title word-boundary fallback |
| `_extract_required_skills()` | Weighted skill importance profile, 2% noise filter |
| `_normalize_user_skills()` | 15-alias dictionary + lowercase normalization → Set |
| `_calculate_skill_overlap()` | Importance-weighted + count composite overlap |
| `_calculate_learning_time()` | Gap-only, importance-adjusted hours, prior-factor corrected |
| `_get_project_benchmark()` | Delegates to ProjectComplexityEvaluator or skill-count fallback |
| `_get_interview_difficulty()` | Delegates to InterviewDifficultyEngine or weight-based estimate |
| `_get_blockers()` | Delegates to HiddenBlockerDetector or fresher-% only fallback |
| `_get_evolution_path()` | Delegates to RoleEvolutionEngine or returns None |
| `_compute_readiness_score()` | 4-component weighted composite, READINESS_THRESHOLDS lookup |
| `_derive_next_action()` | Blocker-first priority logic → single actionable sentence |
| `calculate_learning_readiness()` | **Master orchestration function** — 11-step pipeline |

---

## 6. Output — What Does the Engine Return?

### Sample Output (Orchestrated Mode)

```json
{
    "Target_Domain":   "Data Scientist",
    "Experience_Band": [0, 3],
    "Sample_Size":     184,

    "Readiness_Score": {
        "score": 58.3,
        "label": "🟡 Almost Ready",
        "color": "yellow",
        "components": {
            "skill_overlap_score":     64.5,
            "blocker_clearance":       72.0,
            "interview_manageability": 42.0,
            "time_manageability":      70.0
        }
    },

    "Skill_Overlap": {
        "composite_score":   0.645,
        "weighted_coverage": 0.680,
        "count_ratio":       0.600,
        "matched_count":     9,
        "required_count":    15,
        "matched_skills":    ["python", "sql", "statistics", "pandas", "numpy"],
        "status":            "🟡 Good base — a few key skills missing",
        "Prior_Knowledge_Level": "intermediate"
    },

    "Learning_Plan": {
        "gap_skills_count": 6,
        "total_hours":      245,
        "weeks_at_10hrs":   18.4,
        "months":           4.3,
        "label":            "~4.3 months at 10hrs/week",
        "top_gap_skills": [
            ["machine learning", 2.14],
            ["deep learning",    1.82],
            ["tensorflow",       1.20]
        ],
        "Prior_Knowledge_Factor": 0.75
    },

    "Project_Benchmark": {
        "Score": 6.82,
        "Label": "🔴 Advanced / Production-Ready"
    },

    "Interview_Difficulty": {
        "Index": 5.8,
        "Label": "🟡 Moderate"
    },

    "Hidden_Blockers": {
        "Count": 2,
        "Overall_Risk": "🟠 High Barrier",
        "Top_Blockers": [
            {"blocker_id": "dsa_intensive",        "severity": 0.653},
            {"blocker_id": "experience_inflation",  "severity": 0.514}
        ]
    },

    "Salary_Benchmark": {
        "median_lpa": 7.8,
        "p25_lpa":    5.5,
        "p75_lpa":    11.2
    },

    "Evolution_Preview": {
        "first_step":      "senior data scientist",
        "years_to_senior": 4.5
    },

    "Priority_Action": "🎯 Start with highest-impact gap skill: 'machine learning'. Full preparation: ~4.3 months at 10hrs/week.",

    "Data_Sources_Used": {
        "PrerequisiteEngine":         false,
        "SkillTransferabilityEngine": false,
        "ProjectComplexityEvaluator": true,
        "InterviewDifficultyEngine":  true,
        "HiddenBlockerDetector":      true,
        "RoleEvolutionEngine":        true
    }
}
```

### Readiness Score Labels

| Score | Label | Meaning |
|---|---|---|
| 80–100 | 🟢 Ready to Apply | Start applying now |
| 60–79 | 🟡 Almost Ready | Minor gaps; apply in 1–2 months |
| 40–59 | 🟠 Meaningful Gap | Focused upskilling needed |
| 20–39 | 🔴 Significant Work Ahead | Several months of structured learning |
| 0–19 | ⚪ Starting From Scratch | Build from foundations |

---

## 7. How Robust Are the Formulas and Constants?

### What Makes Them Solid ✅

| Feature | Why It's Good |
|---|---|
| **Prior knowledge inversion fix** | `"advanced": 0.50` correctly reduces time. The original broken `1.5` made advanced users take 50% LONGER — this explicit fix is critical. |
| **Gap-only learning time** | Only counts skills the user does NOT have. Previous versions incorrectly counted all required skills. |
| **Dependency injection pattern** | Sub-engines are injected, not hardcoded. Enables unit testing of `CareerPathEngine` in isolation and allows individual engines to be swapped without modifying the orchestrator. |
| **Graceful fallback chain** | Every sub-engine call is wrapped in `try-except`. If `InterviewDifficultyEngine` fails, an internal estimate is used — the overall report is still produced. |
| **`Data_Sources_Used` transparency field** | Users see exactly which engines contributed. If all are `false`, scores are based on fallbacks — users are not misled. |
| **Blocker-first priority logic** | Critical blockers (severity > 0.70) override all other priority actions — because a CGPA filter blocks even skilled candidates. Correct prioritization order. |
| **BASE_HOURS_PER_SKILL = 35** | Reduced from original 40 — "more realistic for focused learners" as noted in code comment. 35 hours at 10hrs/week = 3.5 weeks per skill — reasonable and achievable. |

---

## 8. Advantages of the Current Implementation

- **Single entry point for the entire pipeline** — one function call produces a complete career readiness report that previously required running 6 separate engines.
- **Dual-mode operation** — works standalone for quick assessments AND in full orchestration mode for production use — same API, different richness.
- **Critical prior knowledge fix** — the inversion (advanced = 0.5× not 1.5×) produces sensible time estimates that the original broken version could not.
- **Blocker-first priority logic** — ensures users aren't told to learn skills when a CGPA filter blocks them anyway.
- **4-component score with full breakdown** — users see not just the score but what is dragging it down, enabling targeted improvement.
- **Evolution preview** — gives a forward look at where the target role leads, adding career planning context to what would otherwise be a static readiness snapshot.
- **`Data_Sources_Used` field** — prevents silent degradation. Users know when they're getting fallback quality output.

---

## 9. Disadvantages and How to Improve Them

| Limitation | Problem | Suggested Fix |
|---|---|---|
| **`prereq_engine` and `transfer_engine` accepted but never called** | Both `PrerequisiteEngine` and `SkillTransferabilityEngine` are accepted in `__init__()`, stored, but zero methods call them. Their injection has no effect on any output — a misleading API contract. | Implement `_get_prerequisites()` calling `prereq_engine.analyze_prerequisites()` and `_get_transferability()` calling `transfer_engine.calculate_transferability()`. Incorporate their outputs into the readiness report or remove the unused parameters to avoid confusion. |
| **`_extract_required_skills()` uses raw comma-split** | Same dual-format bug as `RoleEvolutionEngine` — list literals `"['python', 'sql']"` produce `"['python'"` with brackets. | Use `ast.literal_eval` first (like `PrerequisiteEngine`), falling back to comma-split. Extract to shared utility module used by all engines. |
| **`interview_manageability` ignores the user's preparation level** | `(10 - interview_index) / 10 × 100` — a hard interview gives lower readiness even for an `"advanced"` user who can handle it. The prior_knowledge parameter is completely ignored in this component. | Scale interview component by prior knowledge: `adjusted_index = interview_index × (1 - prior_adjustment)` where `prior_adjustment` is +0.20 for advanced, 0 for basic, -0.15 for none. |
| **Time manageability uses step-function with cliff edges** | A 2.9-month gap scores 90 while a 3.1-month gap scores 70 — a 0.2-month real difference produces a 20-point score jump. | Replace with `time_component = max(20, 100 × e^(-months × 0.058))` — smooth exponential decay from 100 (0 months) to ~40 (12 months) with no cliff edges. |
| **Alias dictionary has 15 entries vs PrerequisiteEngine's 24** | Both engines maintain separate alias dictionaries that can drift out of sync. An alias working in one engine may silently fail in another. | Extract to shared `skill_aliases.py` module. Single source of truth — any new alias works in all engines. |
| **Inline salary benchmark ignores time decay and location** | The salary is a simple IQR-cleaned median with no time-weighting and no city adjustment. A user in Bangalore gets the same salary figure as a user in Jaipur. | Accept optional `target_location` parameter. Call `AverageSalaryRangeCalculator.calculate_salary_metrics()` via injected engine pattern when available — consistent with how other sub-engines are used. |
| **`READINESS_THRESHOLDS` lookup is a dict-of-tuples iterated linearly** | `for (low, high), (lbl, clr) in self.READINESS_THRESHOLDS.items()` — ordering of a dict is implicit and the approach is semantically fragile. | Replace with a straightforward `if/elif` chain. The tuple-dict pattern adds cognitive overhead with no benefit for only 5 tiers. |

### Formula Improvement Suggestions

```python
# Current: step-function creates cliff edges
elif months <= 3:  time_component = 90
elif months <= 6:  time_component = 70
elif months <= 12: time_component = 45
else:              time_component = 20

# Improved: smooth exponential decay — no cliff edges
import math
time_component = max(20, 100 * math.exp(-months * 0.058))
# 0 months → 100, 3 months → ~84, 6 months → ~70, 12 months → ~49, 18 months → ~33
```

```python
# Current: interview manageability ignores prior knowledge
interview_component = max(0, (10 - interview_index) / 10 * 100)

# Improved: advanced users handle harder interviews better
PRIOR_ADJUSTMENT = {"none": -0.15, "basic": 0.0, "intermediate": 0.10, "advanced": 0.20}
adjustment = PRIOR_ADJUSTMENT.get(prior_knowledge, 0.0)
effective_index = max(0, interview_index * (1 - adjustment))
interview_component = max(0, (10 - effective_index) / 10 * 100)
# For "advanced" user: difficulty 7.0 → effective 5.6 → component 44 instead of 30
```

```python
# Current: prereq_engine stored but never used
self.prereq_engine = prerequisite_engine

# Improved: call it and integrate into output and priority action
def _get_prerequisites(self, df, target_domain, user_skills, experience_band):
    if self.prereq_engine is not None:
        try:
            return self.prereq_engine.analyze_prerequisites(
                df, target_domain, user_skills, experience_band
            )
        except Exception as e:
            self.logger.warning(f"PrerequisiteEngine failed: {e}")
    return None

# In calculate_learning_readiness():
prereq_data = self._get_prerequisites(
    df, target_domain, list(user_skills_norm), experience_band
)
# Use prereq_data["Learning_Path"]["Can_Start_Now"] 
# to enhance Priority_Action with "you can start X today"
```

---

*End of Engine 15 Documentation*

---

---

# Engine 16 — `AdaptiveRealTalkEngine` (Adaptive Real Talk Engine)

**File:** `adaptive_real_talk_engine.py`  
**Class:** `AdaptiveRealTalkEngine`

---

## 1. Introduction — What is this Engine and What Does it Do?

Every engine in the pipeline produces numbers, scores, and structured data. But a user sitting at their screen at 11 PM wondering "should I pivot to Data Science?" doesn't need another score — they need someone to talk straight to them.

**`AdaptiveRealTalkEngine` is the pipeline's voice layer.** It takes the numerical outputs from all 15 engines, distills them into a **Persona** that describes the market situation in vivid human terms, then generates a completely personalized narrative — the "harsh truth," the "silver lining," the common traps, and the proven success patterns — all injected with the user's actual data.

The central insight is that the same domain means completely different things to different people:

- A **fresher** asking about Data Science needs: entry barriers, how hard the first job is to get, and exactly what to learn first
- An **intermediate professional** asking the same question needs: specialization path, salary negotiation, positioning against other candidates

And the same domain also falls into fundamentally different market archetypes:

- A domain with **high barrier + high competition** = "The Gauntlet" (needs completely different advice than…)
- A domain with **low competition + high demand** = "The Hidden Gem"

This engine uses **8 Personas** — named market archetypes — to categorize any domain into a situation type, then generates narrative content calibrated to both that persona AND the user's experience level.

> Think of it like a financial advisor who doesn't just hand you a spreadsheet. They sit down, look at your numbers, and say: "Look, the market right now is a buyer's market in your sector. Here's the honest situation, here's what most people get wrong, and here's exactly what the successful ones do differently." This engine does that for career decisions.

---

## 2. What Makes This Engine Unique in the Pipeline

All other engines in this pipeline are **data engines** — they compute metrics from job posting data. This engine is fundamentally different:

- **It has no `df: pd.DataFrame` parameter** — it receives no raw job data
- **It produces no numerical scores** — it produces narrated, human-readable advice
- **It is the only engine with personality** — 8 distinct personas with names, emoji, taglines, and archetypes
- **It adapts its tone** by experience level — the same domain, the same persona, but a "fresher" gets "encouraging but honest" while a "senior" gets "strategic and forward-looking"
- **It injects actual data into text** — the harsh truth for "The Crowded Room" says `"Competition score: 7.8/10. Your resume has approximately 6 seconds with a recruiter."` — real numbers from the user's analysis, not generic text

---

## 3. Data Fields Required by This Engine

This engine takes **engine output dicts**, not raw job data.

### Required Input

| Parameter | Source Engine | What it Contains |
|---|---|---|
| `career_path_report` | `CareerPathEngine` | Readiness score, skill overlap, learning plan, blockers, salary, evolution preview |
| `domain` | User input | Target domain name (string) |
| `experience_level` | User input | `"fresher"`, `"junior"`, `"intermediate"`, `"senior"` |

### Optional Inputs (each adds richer metrics)

| Parameter | Source Engine | Used For |
|---|---|---|
| `saturation_report` | `SaturationRiskIndicator` | Competition metric (0–10) |
| `velocity_report` | `JobMarketVelocityCalculator` | Growth signal (-1 to +1) |
| `ai_risk_report` | `AIReplacementRiskEngine` | AI replacement risk (0–1) |
| `demand_report` | `MarketDemandEngine` | Demand score (0–10) |
| `salary_report` | `AverageSalaryRangeCalculator` | Salary context |
| `transferability_report` | `SkillTransferabilityEngine` | Transferability score (0–1) |

> The engine gracefully handles missing optional inputs — each has a sensible numeric fallback so the persona classification and narrative still work even with only the `career_path_report`.

---

## 4. Core Logic — How Does the Engine Generate Real Talk?

The `generate_real_talk()` method runs **7 sequential steps**:

---

### Step 1 — Build Normalized Metrics (`build_metrics_from_engines`)

Converts raw engine outputs into a unified, normalized metrics dictionary:

| Metric | Scale | How Derived |
|---|---|---|
| `barrier_depth` | 0–5 | `(blocker_risk × 2.0) + (interview_index / 10 × 3.0)` |
| `competition` | 0–10 | From `SaturationRiskIndicator.Saturation_Score` or inferred from blocker clearance |
| `growth` | −1 to +1 | From `velocity_report.direction_score` or demand score centered at 5.0 |
| `stability` | 0–1 | **Hardcoded at 0.55** (see Section 9) |
| `demand` | 0–10 | From `MarketDemandEngine.demand_score` or default 5.0 |
| `ai_risk` | 0–1 | From `AIReplacementRiskEngine.AI_Risk_Score` or default 0.3 |
| `transferability` | 0–1 | From `SkillTransferabilityEngine.Transferability.Composite_Score` or default 0.4 |
| `readiness_score` | 0–100 | From `CareerPathEngine.Readiness_Score.score` |

**Barrier Depth formula:**
```
barrier_depth = (blocker_risk × 2.0) + (interview_index / 10 × 3.0)

blocker_risk is converted from string labels:
    "No Blockers Detected" → 0.0
    "Low Barrier"          → 0.2
    "Moderate Barrier"     → 0.4
    "High Barrier"         → 0.6
    "Very High Barrier"    → 0.8
    "Extreme Barrier"      → 1.0

Maximum barrier_depth:
    1.0 × 2.0 + 1.0 × 3.0 = 5.0   (extreme blockers + hardest interview)
```

**Growth from demand fallback:**
```
growth = (demand_score − 5.0) / 5.0
# Demand of 7.5 → growth = +0.50 (positive)
# Demand of 3.0 → growth = −0.40 (negative)
```

---

### Step 2 — Classify Persona (`_classify_persona`)

**8 personas** are evaluated against the metrics dict. Each has a lambda condition:

| Persona | Condition | Priority |
|---|---|---|
| 🤖 **THE_AI_CROSSROADS** | `ai_risk ≥ 0.60` | 1st (overrides all) |
| 🌊 **THE_SHRINKING_POOL** | `growth < −0.10 AND stability < 0.40` | 2nd |
| ⚔️ **THE_GAUNTLET** | `barrier_depth ≥ 2 AND competition ≥ 6.5` | 3rd |
| 💎 **THE_HIDDEN_GEM** | `competition < 5.0 AND demand ≥ 6.0` | 4th |
| 🪙 **THE_GOLD_RUSH** | `growth ≥ 0.40 AND stability < 0.45` | 5th |
| 🏟️ **THE_CROWDED_ROOM** | `competition ≥ 7.5 AND barrier_depth < 2` | 6th |
| 🔀 **THE_PIVOT_ZONE** | `transferability ≥ 0.55 AND barrier_depth < 2` | 7th |
| 🏔️ **THE_STEADY_CLIMB** | `growth ≥ 0.0 AND stability ≥ 0.50` | 8th (default) |

**Multiple match resolution:** If multiple conditions are true simultaneously, the priority list above determines the winner. AI Crossroads always wins if triggered — because AI displacement is the most urgent signal regardless of other market characteristics.

**Confidence scores:**
- One persona matches → confidence = **0.85** (clear signal)
- Multiple personas match → confidence = **0.65** (ambiguous market)
- No persona matches → `"THE_STEADY_CLIMB"`, confidence = **0.50** (neutral fallback)

---

### Step 3 — Experience Modifier (`_get_experience_modifier`)

**4 experience levels** produce completely different advice profiles:

| Level | Tone | Focus |
|---|---|---|
| `fresher` | "encouraging but honest" | entry barriers, learning path, first job strategy |
| `junior` | "direct and strategic" | skill gaps, project quality, interview prep |
| `intermediate` | "peer-level, strategic" | specialization, salary negotiation, positioning |
| `senior` | "strategic and forward-looking" | leadership, architecture, market positioning |

The modifier's `prefix` string is injected into every persona message: "As someone just starting out..." vs "At your experience level..." — a small change that makes the entire narrative feel addressed to the right person.

---

### Step 4 — Data-Injected Persona Content (`_build_persona_content`)

For each persona, three categories of content are generated with real data injected:

**Harsh Truth** — The uncomfortable market reality, personalized:
```python
# THE_GAUNTLET harsh truth example:
f"{exp_prefix}, {domain} is an interview gauntlet "
f"(difficulty: {interview_difficulty}/10). "
f"Your current skill overlap is {overlap_pct}% — "
f"{'strong foundation' if overlap_pct > 60 else 'significant gap to close'}."
```

**Silver Lining** — What makes this domain worthwhile despite the challenges

**Beginner Traps** — The 3 most common mistakes people make in this specific persona situation

**Success Patterns** — The 3 proven strategies that work for people who successfully enter this domain

> **Critical design choice:** None of these are static strings. Every message template has actual numbers — competition score, overlap percentage, months to ready, growth rate — pulled from the metrics dict and career path report. A user sees their situation, not generic advice.

---

### Step 5 — Urgency Signal (`_generate_urgency_signal`)

A single urgency verdict answering "Should I apply now, prep first, or reconsider entirely?"

**Decision logic (priority order):**

```
1. Critical blocker (severity > 0.70):
   → 🚨 "Resolve Blocker First" — even perfect skills don't help

2. Shrinking Pool persona:
   → ⚠️ "Reconsider Direction" — declining domain warning

3. readiness ≥ 75 AND no blockers:
   → ✅ "Apply Immediately"

4. readiness ≥ 50 AND months ≤ 4:
   → 🟡 "Apply in N Months"

5. readiness ≥ 30:
   → 🟠 "Structured Preparation Needed"

6. else:
   → 🔴 "Build Foundation First"
```

---

### Steps 6–7: Evolution Note + Salary Context

Simple string generation from `Evolution_Preview` and `Salary_Benchmark` in the career path report:

```
Evolution note: "📈 Natural next step from Data Scientist: senior data scientist (~4.5 years to senior level)"
Salary context: "💰 Market median: ₹7.8 LPA (P25: ₹5.5 | P75: ₹11.2 LPA)"
```

---

## 5. The 8 Personas — Full Reference

### ⚔️ THE_GAUNTLET
- **Condition:** `barrier_depth ≥ 2 AND competition ≥ 6.5`
- **Archetypes:** ML Engineer, Data Scientist, Quant Analyst, AI Researcher
- **Tagline:** "High barrier, high reward. Only the prepared survive."
- **Core message:** Theory-depth matters — APIs aren't enough. Premium salaries reward those who clear the bar.

### 🏟️ THE_CROWDED_ROOM
- **Condition:** `competition ≥ 7.5 AND barrier_depth < 2`
- **Archetypes:** Frontend Developer, UI/UX Designer, Manual QA, Web Developer
- **Tagline:** "Everyone is here. Standing out is the only game."
- **Core message:** You qualify but so do 1,000 others. Differentiation via niche skills and referrals is the only winning strategy.

### 🪙 THE_GOLD_RUSH
- **Condition:** `growth ≥ 0.40 AND stability < 0.45`
- **Archetypes:** GenAI Engineer, Blockchain Dev, Prompt Engineer, MLOps
- **Tagline:** "Hot now, uncertain tomorrow. First movers win."
- **Core message:** Fast growth + low stability = high upside but short shelf life. Move fast and keep foundations solid.

### 🏔️ THE_STEADY_CLIMB
- **Condition:** `growth ≥ 0.0 AND stability ≥ 0.50`
- **Archetypes:** Backend Java, DevOps, SQL Developer, Cloud Engineer
- **Tagline:** "Not glamorous. But it pays reliably and grows steadily."
- **Core message:** Reliable and underrated. Risk is complacency — job-switching is the fastest salary growth mechanism here.

### 🌊 THE_SHRINKING_POOL
- **Condition:** `growth < −0.10 AND stability < 0.40`
- **Archetypes:** Manual Tester, Flash Developer, Mainframe Programmer
- **Tagline:** "Demand declining. Strategic pivot needed before the tide goes out."
- **Core message:** Data-based warning, not guarantee. Map skills to adjacent growing domains before investing further.

### 💎 THE_HIDDEN_GEM
- **Condition:** `competition < 5.0 AND demand ≥ 6.0`
- **Archetypes:** Cybersecurity, Embedded Systems, Compiler Engineering
- **Tagline:** "Low competition, high demand. Most people don't know this exists."
- **Core message:** Hard to find, harder to enter, but once in — you face far less competition and above-market salaries.

### 🔀 THE_PIVOT_ZONE
- **Condition:** `transferability ≥ 0.55 AND barrier_depth < 2`
- **Archetypes:** Product Manager (from Dev), DevRel, Solutions Architect
- **Tagline:** "Skills transfer well here. Switchers have an edge over freshers."
- **Core message:** Don't compete as a fresher — lead with your prior domain context as differentiation.

### 🤖 THE_AI_CROSSROADS
- **Condition:** `ai_risk ≥ 0.60`
- **Archetypes:** Data Entry, Report Analyst, Basic QA Tester
- **Tagline:** "AI is actively reshaping this role. Adapt or be replaced."
- **Core message:** Not a future concern — present-tense reality. The role is transforming for those who adapt, disappearing for those who don't.

---

## 6. Functions — What They Do and How They Are Called

```
generate_real_talk()                    ← Main entry point (you call this)
    │
    ├── build_metrics_from_engines()    → Normalize all engine outputs to unified metrics dict
    ├── _classify_persona()             → Evaluate 8 conditions, apply priority, return persona + confidence
    ├── _get_experience_modifier()      → Tone + focus + prefix based on experience level
    ├── _build_persona_content()        → Data-injected harsh truth, silver lining, traps, patterns
    ├── _generate_urgency_signal()      → Single urgency verdict with color + message
    ├── [Inline] evolution_note         → Format RoleEvolutionEngine preview as string
    └── [Inline] salary_context         → Format AverageSalaryRangeCalculator output as string
```

| Function | Role |
|---|---|
| `__init__()` | Sets up logger — no weights, no validation needed (no numerical pipeline) |
| `build_metrics_from_engines()` | Converts 7 optional engine outputs into unified normalized metrics dict |
| `_classify_persona()` | Evaluates all 8 persona conditions, resolves conflicts via priority list |
| `_get_experience_modifier()` | Returns level-specific tone, focus, prefix, and urgency config |
| `_build_persona_content()` | 8 persona content templates with real data string interpolation |
| `_generate_urgency_signal()` | 6-tier urgency logic with blocker-first and shrinking pool overrides |
| `generate_real_talk()` | **Master function** — orchestrates all 7 steps, returns full narrative report |

---

## 7. Output — What Does the Engine Return?

### Sample Output

```json
{
    "domain":           "Data Scientist",
    "experience_level": "Junior (0-2 years)",

    "persona": {
        "id":         "THE_GAUNTLET",
        "name":       "The Gauntlet",
        "emoji":      "⚔️",
        "tagline":    "High barrier, high reward. Only the prepared survive.",
        "confidence": "85%",
        "archetypes": ["ML Engineer", "Data Scientist", "Quant Analyst", "AI Researcher"]
    },

    "readiness_snapshot": {
        "score":           58.3,
        "label":           "🟡 Almost Ready",
        "skill_overlap":   "68%",
        "months_to_ready": 4.3,
        "active_blockers": 2
    },

    "market_pulse": {
        "competition":   "7.2/10",
        "barrier_depth": "3.1/5",
        "ai_risk":       "18%",
        "growth_signal": "📈 Growing"
    },

    "real_talk": {
        "harsh_truth": "As a junior professional, Data Scientist is an interview gauntlet (difficulty: 5.8/10). Interviewers test theory, not just syntax — if you can't derive the math behind the library, you're out. Your current skill overlap is 68% — strong foundation.",
        "silver_lining": "Those who clear the gauntlet earn premium salaries and face far less competition. Data Scientist has 7.2/10 competition — hard to get in, but rare to be replaced once in.",
        "beginner_traps": [
            "Memorizing ML APIs without understanding the statistics underneath",
            "Spending 6 months on LeetCode easy problems — gauntlet roles need medium-hard",
            "Building Jupyter notebook projects with no deployment — looks like coursework, not engineering"
        ],
        "success_patterns": [
            "Candidates with published research or math-heavy GitHub repos bypass ATS filters",
            "Target Data Scientist roles at startups first — lower bar than FAANG, same skill building",
            "One strong open-source contribution to a major library > 10 tutorial projects"
        ]
    },

    "urgency": {
        "signal":  "🟡 Apply in 4 Months",
        "color":   "yellow",
        "message": "Readiness score: 58/100. ~4.3 months of focused upskilling bridges your current gap. Start applying while you learn — don't wait until 100% ready."
    },

    "evolution_note": "📈 Natural next step from Data Scientist: senior data scientist (~4.5 years to senior level)",

    "salary_context": "💰 Market median: ₹7.8 LPA (P25: ₹5.5 | P75: ₹11.2 LPA)",

    "priority_action": "🎯 Start with highest-impact gap skill: 'machine learning'. Full preparation: ~4.3 months at 10hrs/week."
}
```

### How to Read This Output

| Field | What it Tells the User |
|---|---|
| `persona.name + tagline` | The headline market situation in one memorable phrase |
| `persona.confidence` | How clearly this persona dominates — 85% = clear, 65% = ambiguous market |
| `readiness_snapshot` | Their current position at a glance |
| `market_pulse` | Key market metrics as human-readable strings |
| `real_talk.harsh_truth` | The honest, data-backed market reality — no sugarcoating |
| `real_talk.silver_lining` | Why this is still worth pursuing |
| `real_talk.beginner_traps` | What NOT to do — common mistakes in this specific situation |
| `real_talk.success_patterns` | What the successful entrants actually did |
| `urgency.signal` | The one-word verdict: Apply? Prep? Reconsider? |
| `priority_action` | Forwarded from `CareerPathEngine` — the single most important next step |

---

## 8. How Robust Are the Persona Conditions?

### What Makes Them Solid ✅

| Feature | Why It's Good |
|---|---|
| **Priority ordering for conflicts** | When multiple personas match, AI Crossroads wins first (most urgent), then Shrinking Pool (existential risk), then Gauntlet. Priority reflects real-world urgency correctly. |
| **Data-injected content** | No persona narrative is fully static. Every template interpolates actual user metrics — the harsh truth mentions their exact overlap percentage, their exact months-to-ready, their exact competition score. |
| **Experience-level tone differentiation** | Same persona, completely different framing. A fresher and a senior in "The Gauntlet" get different prefix, different urgency, different focus areas. |
| **Blocker-first urgency logic** | A critical blocker (severity > 0.70) overrides all other urgency signals — correct priority since blockers prevent even skilled candidates from being interviewed. |
| **Graceful fallback on missing engine data** | Every optional engine output has a sensible numeric default. `stability = 0.55`, `ai_risk = 0.3`, `growth = 0.1` — the persona classification degrades gracefully, not crashes. |
| **`blocker_risk` string → number conversion** | The `Overall_Risk` from `HiddenBlockerDetector` is a string label. The engine converts it to numeric via lookup dict rather than parsing — robust to emoji/label changes. |

---

## 9. Disadvantages and How to Improve Them

| Limitation | Problem | Suggested Fix |
|---|---|---|
| **`stability = 0.55` hardcoded** | Line 168: `metrics['stability'] = 0.55`. The comment says "Would be populated from DomainStabilityEngine when connected" — but it never is. Every domain gets the same stability score regardless of actual stability, making `THE_STEADY_CLIMB` (requires stability ≥ 0.50) and `THE_SHRINKING_POOL` (requires stability < 0.40) unable to trigger based on stability. `THE_SHRINKING_POOL` only triggers via `growth < -0.10` alone. | Accept an optional `stability_report: Dict = None` parameter in both `build_metrics_from_engines()` and `generate_real_talk()`. Extract `stability_score` from `DomainStabilityEngine` output. Add to the injection chain. |
| **Persona conditions use hardcoded numeric thresholds** | `competition ≥ 6.5` for Gauntlet, `competition ≥ 7.5` for Crowded Room, `growth ≥ 0.40` for Gold Rush — all manually chosen. These may not be well-calibrated for the Indian tech job market. A domain with 6.8/10 competition in India might be "Crowded Room" level while the same score in the US market is "Gauntlet." | Make persona thresholds configurable as a class constant dict (like `DOMAIN_WEIGHTS` in other engines). Allow market-specific calibration without code changes. |
| **`_build_persona_content()` references `metrics.get('interview_difficulty', barrier*2)`** | Line: `metrics.get('interview_difficulty', barrier*2)`. But `interview_difficulty` is never added to the `metrics` dict by `build_metrics_from_engines()`. The `barrier*2` fallback always fires — hiding this silent miss. | Add `metrics['interview_difficulty'] = career_path_report.get("Interview_Difficulty", {}).get("Index", 5.0)` in `build_metrics_from_engines()`. |
| **Urgency signal has a string interpolation bug** | Line: `"signal": "🟡 Apply in {months} Months"` — this is a regular string, NOT an f-string. The `{months}` placeholder will appear literally in the output as text instead of being replaced with the actual number. | Change to: `"signal": f"🟡 Apply in {months} Months"` — add the `f` prefix. |
| **Persona confidence is binary (0.85 or 0.65)** | All single matches get 0.85 and all multi-matches get 0.65 — there is no gradation. A domain that barely crosses one threshold and misses all others should be 0.9+ confident. A domain that crosses 5 thresholds simultaneously should be 0.5 or less. | Compute confidence as `1 / number_of_matches` for multi-match cases, clipped at a minimum of 0.40. For single-match: `0.75 + (margin_above_threshold / threshold_range × 0.15)` — rewards clear wins. |
| **Traps and patterns are static per persona** | The 3 traps and 3 patterns per persona are pre-written strings. While the harsh_truth and silver_lining inject real metrics, the traps and patterns are the same for every user in a given persona — regardless of their specific situation. | Make traps and patterns contextual: if `overlap_pct < 40`, show different traps than if `overlap_pct > 70`. If experience_level is "senior", show senior-specific patterns. This requires making `traps` and `patterns` into conditional lists rather than static strings. |
| **No cross-persona nuance** | A domain that scores 0.55 transferability (just above Pivot Zone threshold) and 7.6 competition (just above Crowded Room threshold) gets AI Crossroads if `ai_risk ≥ 0.60` — the nuance that it's ALSO a crowded room AND a pivot zone is lost. | Add a `secondary_personas` field to the output: all conditions that were true (not just the priority winner). This lets the UI surface: "Primary: Gauntlet | Also: Crowded Room" — richer situational awareness. |

### Formula Improvement Suggestions

```python
# Current: barrier_depth formula
metrics['barrier_depth'] = round(
    (blocker_risk * 2.0) + (interview_index / 10 * 3.0), 2
)  # Scale 0-5

# Improved: add competition component to barrier depth
# High competition with high interview difficulty = compounded barrier
metrics['barrier_depth'] = round(
    (blocker_risk * 1.5) +
    (interview_index / 10 * 2.5) +
    (min(metrics.get('competition', 5.0), 10) / 10 * 1.0),  # competition adds up to 1.0
    2
)  # Still scales 0-5
```

```python
# Current: hardcoded stability
metrics['stability'] = 0.55  # Always moderate stable

# Improved: derive from available signals when DomainStabilityEngine not connected
# Proxy: stable = demand is moderate, growth is moderate, ai_risk is low
stability_proxy = (
    (1 - abs(metrics.get('growth', 0.1)) * 0.5) *   # low volatility = stable
    (1 - metrics.get('ai_risk', 0.3) * 0.3)          # low ai risk = stable
)
metrics['stability'] = round(float(np.clip(stability_proxy, 0.1, 0.9)), 2)
```

```python
# Current: binary confidence
if len(scores) == 1:
    return list(scores.keys())[0], 0.85
# else:
    confidence = 0.65

# Improved: graduated confidence based on number of matching personas
n_matches = len(scores)
if n_matches == 1:
    confidence = 0.85
elif n_matches == 2:
    confidence = 0.70
elif n_matches == 3:
    confidence = 0.60
else:
    confidence = 0.50  # Very ambiguous market

# Further improvement: boost confidence for dominant primary persona
# if primary persona's metrics are far above threshold vs others
```

---

*End of Engine 16 Documentation*

---