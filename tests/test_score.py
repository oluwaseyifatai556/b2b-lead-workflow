import pandas as pd

from leadflow.score import assign_tier, rank_leads, score_leads, score_row, split_disqualified


def test_score_row_explains_every_rule(config):
    row = {"industry": "SaaS", "employee_count": 120, "contact_title": "VP Sales", "email_is_free": False}
    score, why = score_row(row, config.rules, config.max_points)
    assert score == 100
    assert why == "+40 Industry (SaaS); +30 Size (120); +20 Senior (VP Sales); +10 Work email"


def test_negative_points_and_floor_at_zero(config):
    score, why = score_row({"contact_title": "Marketing Intern", "email_is_free": True}, config.rules, 100)
    assert score == 0
    assert "-30 Intern" in why


def test_no_rules_matched(config):
    assert score_row({"email_is_free": True}, config.rules, 100) == (0, "No ICP rules matched")


def test_tiers_use_thresholds(config):
    assert [assign_tier(s, config) for s in (100, 80, 79, 50, 49, 0)] == ["A", "A", "B", "B", "C", "C"]


def test_split_disqualified_lists_all_reasons(config):
    df = pd.DataFrame([
        {"source_row": 2, "email_valid": True, "company_name": "Acme"},
        {"source_row": 3, "email_valid": False, "company_name": None},
        {"source_row": 4, "email_valid": False, "company_name": "Globex"},
    ])
    kept, rejected = split_disqualified(df, config)
    assert kept["source_row"].tolist() == [2]
    assert rejected["reject_reason"].tolist() == ["Invalid email; No company", "Invalid email"]


def test_rank_orders_by_score_then_completeness_then_recency():
    from datetime import date

    df = pd.DataFrame([
        {"source_row": 2, "score": 50, "profile_completeness": 90, "created_date": date(2026, 1, 1)},
        {"source_row": 3, "score": 90, "profile_completeness": 50, "created_date": None},
        {"source_row": 4, "score": 50, "profile_completeness": 90, "created_date": date(2026, 6, 1)},
        {"source_row": 5, "score": 50, "profile_completeness": 95, "created_date": None},
    ])
    ranked = rank_leads(df)
    assert ranked["source_row"].tolist() == [3, 5, 4, 2]
    assert ranked["rank"].tolist() == [1, 2, 3, 4]


def test_score_leads_adds_columns(config):
    df = pd.DataFrame([{"industry": "Retail", "employee_count": 5, "contact_title": None, "email_is_free": True}])
    out = score_leads(df, config)
    assert out.loc[0, ["score", "tier", "score_reasons"]].tolist() == [0, "C", "No ICP rules matched"]
