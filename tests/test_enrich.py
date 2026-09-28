import pandas as pd
import pytest

from leadflow.clean import clean_leads
from leadflow.enrich import company_from_domain, fill_company_names
from tests.conftest import raw_frame


def _filled(rows):
    cleaned, _ = clean_leads(raw_frame(rows))
    return fill_company_names(cleaned).set_index("contact_first_name")


def _lead(first, **fields):
    return {"contact_first_name": first, "contact_last_name": "X", **fields}


def test_company_copied_from_another_lead_on_the_same_domain():
    out = _filled([
        _lead("Ann", company_name="Prismloop Labs", email="ann@prismloop.example"),
        _lead("Bo", company_name="", email="bo@prismloop.example"),
    ])
    assert out.loc["Bo", "company_name"] == "Prismloop Labs"
    assert out.loc["Bo", "company_name_source"] == "same domain"
    assert out.loc["Ann", "company_name_source"] == "original"


def test_most_common_name_on_the_domain_wins():
    out = _filled([
        _lead("A", company_name="Acme Ltd", website="acme.example", email="a@gmail.com"),
        _lead("B", company_name="Acme", website="acme.example", email="b@gmail.com"),
        _lead("C", company_name="Acme", website="acme.example", email="c@gmail.com"),
        _lead("D", company_name="", website="acme.example", email="d@gmail.com"),
    ])
    assert out.loc["D", "company_name"] == "Acme"


def test_company_inferred_from_domain_when_no_other_lead_has_it():
    out = _filled([_lead("Cy", company_name="N/A", website="https://www.orbitline-health.example")])
    assert out.loc["Cy", "company_name"] == "Orbitline Health"
    assert out.loc["Cy", "company_name_source"] == "inferred"


def test_no_company_and_no_domain_stays_missing():
    out = _filled([_lead("Di", company_name="", email="di@gmail.com")])
    assert pd.isna(out.loc["Di", "company_name"])
    assert pd.isna(out.loc["Di", "company_name_source"])


@pytest.mark.parametrize(
    ("domain", "expected"),
    [
        ("prismloop.example", "Prismloop"),
        ("orbitline-health.example", "Orbitline Health"),
        ("shop.acme.com", "Acme"),
        ("acme.co.uk", "Acme"),
        ("blue_sky.io", "Blue Sky"),
    ],
)
def test_company_from_domain(domain, expected):
    assert company_from_domain(domain) == expected
