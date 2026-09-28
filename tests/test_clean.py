from datetime import date

import pandas as pd
import pytest

from leadflow import clean
from tests.conftest import raw_frame


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("ACME ANALYTICS INC.", "Acme Analytics Inc"),
        ("acme analytics, inc.", "Acme Analytics Inc"),
        ("Brightpath L.L.C", "Brightpath LLC"),
        ("  Northwind   Limited ", "Northwind Ltd"),
        ("DataCo", "DataCo"),  # deliberate mixed case is kept
        ("", None),
        ("N/A", None),
    ],
)
def test_clean_company_name(raw, expected):
    assert clean.clean_company_name(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://www.acme.example/about", "acme.example"),
        ("HTTP://WWW.ACME.EXAMPLE", "acme.example"),
        ("www.acme.example/?utm_source=x", "acme.example"),
        ("acme.example:8080", "acme.example"),
        ("not a website", None),
        ("", None),
    ],
)
def test_clean_domain(raw, expected):
    assert clean.clean_domain(raw) == expected


@pytest.mark.parametrize(
    ("raw", "cleaned", "valid"),
    [
        (" Jane.Doe@Acme.example ", "jane.doe@acme.example", True),
        ("mailto:bob@x.example", "bob@x.example", True),
        ("<bob@x.example>", "bob@x.example", True),
        ("bob@@x.example", "bob@@x.example", False),
        ("bob@company", "bob@company", False),
        ("bob at gmail", "bobatgmail", False),
        ("", None, False),
    ],
)
def test_clean_and_validate_email(raw, cleaned, valid):
    assert clean.clean_email(raw) == cleaned
    assert clean.is_valid_email(clean.clean_email(raw)) is valid


def test_free_email_detection():
    assert clean.is_free_email("someone@gmail.com")
    assert not clean.is_free_email("someone@acme.example")
    assert not clean.is_free_email("broken@@gmail.com")


@pytest.mark.parametrize(
    ("raw", "country", "expected"),
    [
        ("(415) 555-0100", "United States", "+14155550100"),
        ("1-415-555-0100", "United States", "+14155550100"),
        ("415-555-0100 x12", "United States", "+14155550100"),
        ("020 7946 0000", "United Kingdom", "+442079460000"),
        ("+44 (0)20 7946 0000", "United Kingdom", "+442079460000"),
        ("0049 30 1234 5678", "Germany", "+493012345678"),
        ("+33 1 23 45 67 89", "France", "+33123456789"),
        ("+61 2 9876 5432", "Australia", "+61298765432"),
        ("+91 98765 43210", "India", "+919876543210"),
        ("+1 416 555 0199", "Canada", "+14165550199"),
        ("4155550100", None, "4155550100"),  # unknown country: keep the digits
        ("123", "United States", None),
        ("n/a", "United States", None),
    ],
)
def test_clean_phone(raw, country, expected):
    assert clean.clean_phone(raw, country) == expected


@pytest.mark.parametrize(
    ("raw", "country"),
    [
        ("+1-525-8369", "Canada"),        # audit example: 7 digits after +1, needs 10
        ("525-8369", "Canada"),
        ("+49 694 6703", "Germany"),      # 7 national digits, needs 8-11
        ("0049 301 2345", "Germany"),
        ("+33 948 1206", "France"),       # needs 9
        ("+61 555 1234", "Australia"),    # needs 9
        ("+91-622-7961", "India"),        # needs 10
        ("+44 20 7946", "United Kingdom"),  # needs 9-10
        ("+1 415 555 01000", "United States"),  # too long
        ("+33 948 1206", None),           # country code in the number is enough to judge it
    ],
)
def test_incomplete_phone_numbers_are_unreadable(raw, country):
    assert clean.clean_phone(raw, country) is None


def test_incomplete_phones_count_as_unreadable_not_standardized():
    raw = raw_frame([
        {"company_name": "A", "contact_first_name": "a", "contact_last_name": "b", "email": "a@a.example",
         "country": "Canada", "phone": "+1-525-8369"},
        {"company_name": "B", "contact_first_name": "c", "contact_last_name": "d", "email": "c@b.example",
         "country": "Canada", "phone": "(416) 555-0199"},
    ])
    cleaned, quality = clean.clean_leads(raw)
    assert pd.isna(cleaned.loc[0, "phone"])
    phone_q = quality.set_index("field").loc["phone"]
    assert (phone_q["unreadable"], phone_q["standardized"]) == (1, 1)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("120", 120), ("50-200", 125), ("~1k", 1000), ("1,200", 1200), ("500+", 500),
     ("approx. 75", 75), ("unknown", None), ("", None)],
)
def test_parse_employee_count(raw, expected):
    assert clean.parse_employee_count(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("$2.5M", 2_500_000), ("£750K", 750_000), ("USD 4 million", 4_000_000), ("$12,000,000", 12_000_000),
     ("14.2m", 14_200_000), ("1.1B", 1_100_000_000), ("n/a", None), ("undisclosed", None)],
)
def test_parse_revenue(raw, expected):
    assert clean.parse_revenue(raw) == expected


@pytest.mark.parametrize(
    "raw", ["2026-03-12", "03/12/2026", "12 Mar 2026", "Mar 12, 2026", "2026/03/12", "2026-03-12T10:22:00"]
)
def test_parse_date_formats(raw):
    assert clean.parse_date(raw) == date(2026, 3, 12)


def test_parse_date_unreadable():
    assert clean.parse_date("sometime last spring") is None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("USA", "United States"), ("u.s.", "United States"), ("Great Britain", "United Kingdom"),
     ("uk", "United Kingdom"), ("Deutschland", "Germany"), ("narnia", "Narnia")],
)
def test_clean_country(raw, expected):
    assert clean.clean_country(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("vp of marketing", "VP of Marketing"), ("HEAD OF DEMAND GENERATION", "Head of Demand Generation"),
     ("o'donnell", "O'Donnell"), ("co-founder", "Co-Founder"), ("McKenzie", "McKenzie")],
)
def test_clean_name_casing(raw, expected):
    assert clean.clean_name(raw) == expected


def test_industry_and_source_canonical():
    assert clean.clean_industry("software as a service") == "SaaS"
    assert clean.clean_industry("E-Commerce") == "E-commerce"
    assert clean.clean_lead_source("linked in") == "LinkedIn"
    assert clean.clean_industry("underwater basket weaving") == "Underwater Basket Weaving"


def test_headers_are_standardized():
    df = pd.DataFrame({"Company Name": ["A"], "First Name": ["x"], "Last Name": ["y"], "E-mail": ["a@b.example"]})
    out = clean.standardize_headers(df)
    assert {"company_name", "contact_first_name", "contact_last_name", "email", "phone"} <= set(out.columns)


def test_missing_required_column_is_a_plain_error():
    df = pd.DataFrame({"company_name": ["A"], "email": ["a@b.example"]})
    with pytest.raises(clean.InputError, match="contact_first_name"):
        clean.standardize_headers(df)


def test_clean_leads_derives_domain_from_business_email_only():
    raw = raw_frame([
        {"company_name": "A", "contact_first_name": "a", "contact_last_name": "b", "email": "a@acme.example"},
        {"company_name": "B", "contact_first_name": "c", "contact_last_name": "d", "email": "c@gmail.com"},
    ])
    cleaned, _ = clean.clean_leads(raw)
    assert cleaned.loc[0, "domain"] == "acme.example"
    assert pd.isna(cleaned.loc[1, "domain"])


def test_clean_leads_reports_quality(messy_leads):
    cleaned, quality = clean.clean_leads(messy_leads)
    assert list(cleaned.columns) == clean.CLEAN_COLUMNS
    assert cleaned["source_row"].tolist() == [2, 3, 4, 5, 6, 7, 8]
    email_q = quality.set_index("field").loc["email"]
    assert email_q["unreadable"] == 1  # ann.lee@@globex
    assert email_q["standardized"] == 1  # " Jane.Doe@Acme.example "
