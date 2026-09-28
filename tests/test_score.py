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


def _enrich_view(config, **row):
    base = {"industry": None, "employee_count": None, "contact_title": None, "email_is_free": False}
    out = score_leads(pd.DataFrame([{**base, **row}]), config)
    return out.loc[0, ["score", "tier", "missing_fields", "needs_enrichment"]].tolist()


def test_blank_field_that_could_lift_the_tier_needs_enrichment(config):
    # 30 size + 20 senior + 10 work email = 60 (B). Industry is blank; +40 would make it A.
    assert _enrich_view(config, employee_count=120, contact_title="VP Sales") == [60, "B", "Industry", True]


def test_blank_field_that_cannot_change_the_tier_is_listed_but_not_flagged(config):
    # 40 + 30 + 10 = 80 (already A). Title is blank, but filling it can't lift the tier.
    assert _enrich_view(config, industry="SaaS", employee_count=120) == [80, "A", "Job title", False]


def test_complete_lead_has_no_missing_fields(config):
    view = _enrich_view(config, industry="Retail", employee_count=5, contact_title="Owner", email_is_free=True)
    assert view == [0, "C", "", False]  # a genuine poor fit, not missing data


def test_several_missing_fields_listed_in_rule_order(config):
    assert _enrich_view(config)[2:] == ["Industry; Employees; Job title", True]


def test_filling_a_penalised_blank_counts_towards_best_case():
    from leadflow.config import parse_config

    cfg = parse_config({
        "scoring_rules": [
            {"name": "Industry", "field": "industry", "in": ["SaaS"], "points": 60},
            {"name": "No phone", "field": "phone", "is_missing": True, "points": -20},
        ],
        "tiers": [{"name": "A", "min_score": 80}, {"name": "B", "min_score": 0}],
    })
    out = score_leads(pd.DataFrame([{"industry": "SaaS", "phone": None}]), cfg)
    # (60 - 20) / 60 = 67 -> B. With a phone the penalty goes away: 60 / 60 = 100 -> A.
    assert out.loc[0, ["score", "tier", "missing_fields", "needs_enrichment"]].tolist() == [67, "B", "Phone", True]


def _phone_config():
    from leadflow.config import parse_config

    return parse_config({
        "scoring_rules": [
            {"name": "Industry", "field": "industry", "in": ["SaaS"], "points": 80},
            {"name": "No phone number", "field": "phone", "is_missing": True, "points": -20},
        ],
        "tiers": [{"name": "A", "min_score": 90}, {"name": "B", "min_score": 0}],
    })


def test_unreadable_phone_is_not_penalised_as_missing():
    cfg = _phone_config()
    blank = {"industry": "SaaS", "phone": None, "unreadable_fields": ""}
    unreadable = {"industry": "SaaS", "phone": None, "unreadable_fields": "phone"}
    assert score_row(blank, cfg.rules, cfg.max_points) == (75, "+80 Industry (SaaS); -20 No phone number")
    assert score_row(unreadable, cfg.rules, cfg.max_points) == (100, "+80 Industry (SaaS)")


def test_unreadable_phone_is_flagged_for_enrichment():
    cfg = _phone_config()
    out = score_leads(pd.DataFrame([
        {"industry": None, "phone": None, "unreadable_fields": "phone"},
        {"industry": "SaaS", "phone": None, "unreadable_fields": ""},
    ]), cfg)
    assert out["missing_fields"].tolist() == ["Industry; Phone (unreadable)", "Phone"]
    # Row 0: 0 now, 100 if industry fits -> could move B -> A. Row 1: 75 now, 100 with a phone -> B -> A.
    assert out["needs_enrichment"].tolist() == [True, True]


def test_score_leads_adds_columns(config):
    df = pd.DataFrame([{"industry": "Retail", "employee_count": 5, "contact_title": None, "email_is_free": True}])
    out = score_leads(df, config)
    assert out.loc[0, ["score", "tier", "score_reasons"]].tolist() == [0, "C", "No ICP rules matched"]
