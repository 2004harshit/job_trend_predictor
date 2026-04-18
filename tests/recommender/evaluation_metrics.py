# tests/recommender/evaluation_metrics.py
"""
Evaluation metrics for the Rule-Based Recommendation Engine.
Covers: Precision@K, Hit Rate, NDCG@K, Average Match %, Final Score.
"""

import math
from typing import List, Dict


# -----------------------------------------------------------------------
# CORE METRICS
# -----------------------------------------------------------------------

def precision_at_k(recommended: List[str], ground_truth: List[str], k: int = 3) -> float:
    """
    Fraction of top-K recommendations that are in the ground truth list.
    Range: 0.0 – 1.0

    Example:
        recommended   = ["Data Analyst", "QA Automation", "Web Developer"]
        ground_truth  = ["QA Automation", "Data Analyst", "Software Engineer"]
        precision@3   = 2/3 = 0.667
    """
    if k == 0:
        return 0.0
    top_k = recommended[:k]
    hits = len(set(top_k) & set(ground_truth))
    return round(hits / k, 4)


def hit_rate(recommended: List[str], ground_truth: List[str], k: int = 3) -> int:
    """
    1 if at least ONE of the top-K recommendations is in ground truth, else 0.
    Used to compute % of users with at least 1 correct recommendation.
    """
    top_k = recommended[:k]
    return 1 if len(set(top_k) & set(ground_truth)) > 0 else 0


def ndcg_at_k(recommended: List[str], ground_truth: List[str], k: int = 3) -> float:
    """
    Normalized Discounted Cumulative Gain @ K.
    Rewards correct recommendations that appear higher in the ranked list.
    Range: 0.0 – 1.0

    DCG  = sum( rel_i / log2(i+1) )   for i = 1..k
    IDCG = best possible DCG (all ground truth hits at top positions)
    NDCG = DCG / IDCG
    """
    def dcg(hits: List[int]) -> float:
        return sum(h / math.log2(i + 2) for i, h in enumerate(hits))

    top_k = recommended[:k]
    hits = [1 if item in ground_truth else 0 for item in top_k]

    ideal_hits = [1] * min(len(ground_truth), k) + [0] * max(0, k - len(ground_truth))
    ideal_hits = ideal_hits[:k]

    idcg = dcg(ideal_hits)
    if idcg == 0:
        return 0.0
    return round(dcg(hits) / idcg, 4)


def average_match_percentage(recs: List[Dict], k: int = 3) -> float:
    """
    Average match_percentage of the top-K recommendations.
    Uses the 'match_percentage' field from engine output.
    """
    top_k = recs[:k]
    if not top_k:
        return 0.0
    total = sum(r.get("match_percentage", 0) for r in top_k)
    return round(total / len(top_k), 2)


def top1_match_percentage(recs: List[Dict]) -> float:
    """Returns match_percentage of the top-1 recommendation."""
    if not recs:
        return 0.0
    return round(recs[0].get("match_percentage", 0), 2)


# -----------------------------------------------------------------------
# AGGREGATE METRICS (across all users)
# -----------------------------------------------------------------------

def aggregate_metrics(results: List[Dict]) -> Dict:
    """
    Computes aggregate metrics across all tested users.

    Each result dict should have:
        {
            "user_id": str,
            "precision@3": float,
            "hit_rate": int,
            "ndcg@3": float,
            "top1_match_pct": float,
            "avg_match_pct": float,
        }

    Returns a summary dict with averages and derived stats.
    """
    n = len(results)
    if n == 0:
        return {}

    avg_precision = round(sum(r["precision@3"] for r in results) / n, 4)
    avg_hit_rate  = round(sum(r["hit_rate"]     for r in results) / n, 4)
    avg_ndcg      = round(sum(r["ndcg@3"]       for r in results) / n, 4)
    avg_top1      = round(sum(r["top1_match_pct"] for r in results) / n, 2)
    avg_match     = round(sum(r["avg_match_pct"]  for r in results) / n, 2)

    good_users   = [r for r in results if r["precision@3"] >= 0.67]
    worst_users  = [r for r in results if r["precision@3"] == 0.0]

    return {
        "total_users":          n,
        "avg_precision@3":      avg_precision,
        "avg_hit_rate":         avg_hit_rate,
        "pct_users_good":       round(len(good_users) / n * 100, 1),   # Precision >= 0.67
        "avg_ndcg@3":           avg_ndcg,
        "avg_top1_match_pct":   avg_top1,
        "avg_match_pct":        avg_match,
        "worst_case_count":     len(worst_users),
        "worst_case_user_ids":  [r["user_id"] for r in worst_users],
    }


# -----------------------------------------------------------------------
# FINAL COMPOSITE SCORE (Phase 5 formula)
# -----------------------------------------------------------------------

def final_overall_score(
    avg_precision_at3: float,
    user_satisfaction_normalized: float,
    hit_rate_ratio: float,
) -> float:
    """
    Final Overall Score = (Precision@3 x 0.5) + (User_Satisfaction x 0.3) + (Hit_Rate x 0.2)

    Args:
        avg_precision_at3:            float in [0, 1]
        user_satisfaction_normalized: float in [0, 1]  (e.g., 4.2/5 = 0.84)
        hit_rate_ratio:               float in [0, 1]

    Returns:
        Composite score in [0, 1]
    """
    score = (
        avg_precision_at3            * 0.5
        + user_satisfaction_normalized * 0.3
        + hit_rate_ratio               * 0.2
    )
    return round(score, 4)


# -----------------------------------------------------------------------
# PRETTY PRINT HELPERS
# -----------------------------------------------------------------------

def print_metrics_table(results: List[Dict]) -> None:
    """Prints a formatted table of per-user metrics."""
    header = f"{'User':<10} {'P@3':>6} {'Hit':>5} {'NDCG@3':>8} {'Top1%':>7} {'AvgMatch%':>10}"
    print(header)
    print("-" * len(header))
    for r in results:
        print(
            f"{r['user_id']:<10} "
            f"{r['precision@3']:>6.3f} "
            f"{r['hit_rate']:>5} "
            f"{r['ndcg@3']:>8.4f} "
            f"{r['top1_match_pct']:>7.1f} "
            f"{r['avg_match_pct']:>10.1f}"
        )


def print_aggregate_summary(agg: Dict) -> None:
    """Prints aggregate summary to console."""
    print("\n" + "=" * 45)
    print("  AGGREGATE EVALUATION SUMMARY")
    print("=" * 45)
    print(f"  Total Users Tested       : {agg['total_users']}")
    print(f"  Avg Precision@3          : {agg['avg_precision@3']:.4f}")
    print(f"  Avg Hit Rate             : {agg['avg_hit_rate']:.4f}")
    print(f"  % Users with P@3 >= 0.67 : {agg['pct_users_good']:.1f}%")
    print(f"  Avg NDCG@3               : {agg['avg_ndcg@3']:.4f}")
    print(f"  Avg Top-1 Match %        : {agg['avg_top1_match_pct']:.1f}%")
    print(f"  Avg Match % (top-3)      : {agg['avg_match_pct']:.1f}%")
    print(f"  Worst-case Users (P@3=0) : {agg['worst_case_count']}")
    if agg["worst_case_user_ids"]:
        print(f"  Worst-case IDs           : {', '.join(agg['worst_case_user_ids'])}")
    print("=" * 45 + "\n")