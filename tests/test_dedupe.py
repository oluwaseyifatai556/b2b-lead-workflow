from leadflow.clean import clean_leads
from leadflow.dedupe import completeness, dedupe, match_keys, merge_group
from tests.conftest import raw_frame


def _person(**overrides):
    base = {"company_name": "Acme", "contact_first_name": "Jane", "contact_last_name": "Doe"}
    return {**base, **overrides}


def _dedupe(rows):
    cleaned, _ = clean_leads(raw_frame(rows))
    return dedupe(cleaned)


def test_same_email_merges():
    out = _dedupe([_person(email="jane@acme.example"), _person(email="JANE@acme.example ")])
    assert len(out) == 1
    assert out.loc[0, "source_rows"] == "2; 3"
    assert out.loc[0, "duplicates_merged"] == 1


def test_same_domain_and_name_merges_even_with_different_email():
    out = _dedupe([
        _person(email="jane@acme.example"),
        _person(website="https://www.acme.example", email="jane.doe@gmail.com"),
    ])
    assert len(out) == 1


def test_different_people_at_same_company_are_kept():
    out = _dedupe([
        _person(email="jane@acme.example"),
        _person(contact_first_name="Raj", email="raj@acme.example"),
    ])
    assert len(out) == 2


def test_same_name_at_different_companies_are_kept():
    out = _dedupe([
        _person(email="jane@acme.example"),
        _person(company_name="Globex", email="jane@globex.example"),
    ])
    assert len(out) == 2


def test_invalid_emails_do_not_match_each_other():
    out = _dedupe([
        _person(contact_first_name="A", email="unknown"),
        _person(contact_first_name="B", email="unknown"),
    ])
    assert len(out) == 2


def test_matches_chain_transitively():
    out = _dedupe([
        _person(email="jane@acme.example"),                      # A
        _person(website="acme.example", email="jd@gmail.com"),   # B ~ A by domain+name
        _person(contact_last_name="Doe ", email="jd@gmail.com"),  # C ~ B by email
    ])
    assert len(out) == 1
    assert out.loc[0, "duplicates_merged"] == 2


def test_merge_keeps_most_complete_and_fills_gaps():
    out = _dedupe([
        _person(email="jane@acme.example", phone="(415) 555-0100", country="US"),
        _person(email="jane@acme.example", phone="", country="US", industry="SaaS", city="Boston",
                contact_title="VP Sales"),
    ])
    row = out.iloc[0]
    assert row["contact_title"] == "VP Sales"  # from the more complete row
    assert row["phone"] == "+14155550100"      # filled from the other row
    assert row["source_row"] == 2


def test_valid_email_replaces_invalid_on_merge():
    merged = merge_group([
        {"source_row": 2, "email": "jane@@acme", "industry": "SaaS", "city": "Boston"},
        {"source_row": 3, "email": "jane@acme.example"},
    ])
    assert merged["email"] == "jane@acme.example"


def test_match_keys_and_completeness():
    row = {"email": "jane@acme.example", "domain": "acme.example", "full_name": "Jane Doe"}
    assert match_keys(row) == ["email:jane@acme.example", "domain+name:acme.example|jane doe"]
    assert match_keys({"email": "bad", "domain": None, "full_name": "Jane"}) == []
    assert completeness({}) == 0


def test_dedupe_is_deterministic(messy_leads):
    cleaned, _ = clean_leads(messy_leads)
    first = dedupe(cleaned)
    second = dedupe(cleaned.sample(frac=1, random_state=3).sort_values("source_row"))
    assert first.equals(second)
