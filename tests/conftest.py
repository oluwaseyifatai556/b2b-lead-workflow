import pandas as pd
import pytest

from leadflow.config import parse_config


def raw_frame(rows: list[dict]) -> pd.DataFrame:
    """Build a raw lead table the way read_leads_csv does: all strings, blanks as ''."""
    columns = [
        "company_name", "website", "contact_first_name", "contact_last_name", "contact_title",
        "email", "phone", "industry", "employee_count", "annual_revenue", "country",
        "state_region", "city", "lead_source", "created_date",
    ]
    return pd.DataFrame([{c: r.get(c, "") for c in columns} for r in rows], dtype=str)


@pytest.fixture
def config_data() -> dict:
    return {
        "client_name": "Test Client",
        "disqualifiers": [
            {"field": "email_valid", "equals": False, "reason": "Invalid email"},
            {"field": "company_name", "is_missing": True, "reason": "No company"},
        ],
        "scoring_rules": [
            {"name": "Industry", "field": "industry", "in": ["SaaS", "Software"], "points": 40},
            {"name": "Size", "field": "employee_count", "between": [50, 1000], "points": 30},
            {"name": "Senior", "field": "contact_title", "contains_any": ["VP", "Director", "CTO"], "points": 20},
            {"name": "Work email", "field": "email_is_free", "equals": False, "points": 10},
            {"name": "Intern", "field": "contact_title", "contains_any": ["Intern"], "points": -30},
        ],
        "tiers": [
            {"name": "A", "min_score": 80},
            {"name": "B", "min_score": 50},
            {"name": "C", "min_score": 0},
        ],
    }


@pytest.fixture
def config(config_data):
    return parse_config(config_data)


@pytest.fixture
def messy_leads() -> pd.DataFrame:
    return raw_frame(
        [
            # 0: great fit
            {"company_name": "ACME ANALYTICS INC.", "website": "https://www.acme.example/about",
             "contact_first_name": "jane", "contact_last_name": "DOE", "contact_title": "vp of marketing",
             "email": " Jane.Doe@Acme.example ", "phone": "(415) 555-0100", "industry": "saas",
             "employee_count": "50-200", "annual_revenue": "$12M", "country": "USA", "created_date": "2026-01-15"},
            # 1: same person as 0 by email, with an extra field filled in
            {"company_name": "Acme Analytics", "contact_first_name": "Jane", "contact_last_name": "Doe",
             "email": "jane.doe@acme.example", "city": "san francisco", "created_date": "01/15/2026"},
            # 2: same person as 0 by domain + name, personal email
            {"company_name": "Acme Analytics", "website": "acme.example", "contact_first_name": "Jane",
             "contact_last_name": "Doe", "email": "janed@gmail.com", "lead_source": "linkedin"},
            # 3: different person at the same company -> not a duplicate
            {"company_name": "Acme Analytics", "website": "acme.example", "contact_first_name": "Raj",
             "contact_last_name": "Patel", "contact_title": "Marketing Intern", "email": "raj@acme.example",
             "industry": "SaaS", "employee_count": "120", "country": "UK", "phone": "020 7946 0000"},
            # 4: invalid email -> rejected
            {"company_name": "Globex Ltd", "contact_first_name": "Ann", "contact_last_name": "Lee",
             "email": "ann.lee@@globex", "industry": "Software"},
            # 5: missing company -> rejected
            {"company_name": "  ", "contact_first_name": "Bo", "contact_last_name": "Chen",
             "email": "bo@initech.example"},
            # 6: poor fit, free email
            {"company_name": "tiny shop", "contact_first_name": "Al", "contact_last_name": "Ng",
             "contact_title": "Owner", "email": "al.ng@yahoo.com", "industry": "Retail", "employee_count": "4"},
        ]
    )
