"""Apply icp.yaml: reject disqualified leads, score the rest, assign tiers and rank."""

from __future__ import annotations

import numbers
from datetime import date

import pandas as pd

from leadflow.clean import is_missing
from leadflow.config import IcpConfig, ScoringRule


def split_disqualified(df: pd.DataFrame, config: IcpConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (kept, rejected). Rejected rows carry a `reject_reason` listing every rule they hit."""
    reasons = []
    for row in df.to_dict("records"):
        hits = [d.reason for d in config.disqualifiers if d.condition.test(row.get(d.condition.field))]
        reasons.append("; ".join(hits))
    mask = pd.Series([bool(r) for r in reasons], index=df.index)
    rejected = df[mask].copy()
    rejected.insert(0, "reject_reason", [r for r in reasons if r])
    return df[~mask].copy(), rejected


def _describe(value: object) -> str:
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if isinstance(value, numbers.Integral) and abs(value) >= 1000:
        return f"{value:,}"
    return str(value)


def score_row(row: dict, rules: list[ScoringRule], max_points: int) -> tuple[int, str]:
    """Return (score 0-100, human-readable explanation of every rule that fired)."""
    raw = 0
    reasons = []
    for rule in rules:
        value = row.get(rule.condition.field)
        if rule.condition.test(value):
            raw += rule.points
            show = not is_missing(value) and not isinstance(value, bool)
            detail = f" ({_describe(value)})" if show else ""
            reasons.append(f"{rule.points:+d} {rule.name}{detail}")
    score = max(0, min(100, round(100 * raw / max_points)))
    return score, "; ".join(reasons) if reasons else "No ICP rules matched"


def score_leads(df: pd.DataFrame, config: IcpConfig) -> pd.DataFrame:
    df = df.copy()
    results = [score_row(r, config.rules, config.max_points) for r in df.to_dict("records")]
    df["score"] = [s for s, _ in results]
    df["score_reasons"] = [why for _, why in results]
    df["tier"] = [assign_tier(s, config) for s in df["score"]]
    return df


def assign_tier(score: int, config: IcpConfig) -> str:
    for tier in config.tiers:  # sorted highest threshold first
        if score >= tier.min_score:
            return tier.name
    return config.tiers[-1].name


def rank_leads(df: pd.DataFrame) -> pd.DataFrame:
    """Best first: score, then completeness, then most recent, then original file order."""
    df = df.copy()
    df["_recency"] = [-(d.toordinal()) if isinstance(d, date) else 0 for d in df["created_date"]]
    df = df.sort_values(
        ["score", "profile_completeness", "_recency", "source_row"],
        ascending=[False, False, True, True],
        kind="mergesort",
    ).drop(columns="_recency")
    df.insert(0, "rank", range(1, len(df) + 1))
    return df.reset_index(drop=True)
