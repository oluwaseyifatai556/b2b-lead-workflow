from collections import Counter

import pytest

from leadflow.clean import clean_country, clean_phone, is_missing
from scripts.generate_sample_data import generate

SEEDS = [42, 7, 2026]


def _phone_outcomes(rows):
    """Per country: Counter of 'readable' / 'unreadable' for phones that were filled in."""
    outcomes: dict[str, Counter] = {}
    for row in rows:
        if is_missing(row["phone"]):
            continue
        country = clean_country(row["country"])
        ok = clean_phone(row["phone"], country) is not None
        outcomes.setdefault(country or "(no country)", Counter())["readable" if ok else "unreadable"] += 1
    return outcomes


def test_generator_is_deterministic():
    assert generate(200, seed=42) == generate(200, seed=42)
    assert generate(200, seed=42) != generate(200, seed=43)


@pytest.mark.parametrize("seed", SEEDS)
def test_every_country_gets_realistic_phone_numbers(seed):
    for country, counts in _phone_outcomes(generate(500, seed)).items():
        total = counts.total()
        if country == "(no country)" or total < 8:
            continue
        assert counts["readable"] / total >= 0.8, f"{country}: only {counts['readable']}/{total} phones readable"


@pytest.mark.parametrize("seed", SEEDS)
def test_roughly_5_to_10_percent_of_phones_are_unreadable(seed):
    totals = sum(_phone_outcomes(generate(500, seed)).values(), Counter())
    share = totals["unreadable"] / totals.total()
    assert 0.05 <= share <= 0.10, f"{share:.1%} of phones unreadable"


def test_other_messiness_is_kept():
    rows = generate(500, seed=42)
    emails = [r["email"] for r in rows]
    assert len(set(emails)) < len(emails)  # duplicates still present
    assert any(r["company_name"].isupper() for r in rows)  # case mess
    assert any(r["employee_count"] and not r["employee_count"].isdigit() for r in rows)  # "50-200", "~1k"
    assert any(r["phone"].startswith("(") for r in rows)  # varied phone formats
