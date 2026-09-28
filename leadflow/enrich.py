"""Fill gaps using information already in the list (no outside lookups)."""

from __future__ import annotations

import re
from collections import Counter

import pandas as pd

from leadflow.clean import is_missing

# Second-level labels that sit under a country code, e.g. acme.co.uk.
_SECOND_LEVEL = {"co", "com", "org", "net", "ac", "gov", "ltd", "plc"}


def company_from_domain(domain: str) -> str:
    """'orbitline-health.example' -> 'Orbitline Health', 'acme.co.uk' -> 'Acme'."""
    labels = domain.lower().split(".")
    if len(labels) >= 3 and labels[-2] in _SECOND_LEVEL and len(labels[-1]) == 2:
        label = labels[-3]
    else:
        label = labels[-2] if len(labels) >= 2 else labels[0]
    return " ".join(word.capitalize() for word in re.split(r"[-_]+", label) if word)


def fill_company_names(df: pd.DataFrame) -> pd.DataFrame:
    """Fill a missing company name from another lead on the same domain, else infer it from the
    domain. Adds `company_name_source`: original / same domain / inferred (blank if still missing).
    """
    df = df.copy()
    names_by_domain: dict[str, Counter] = {}
    for domain, name in zip(df["domain"], df["company_name"], strict=True):
        if not is_missing(domain) and not is_missing(name):
            names_by_domain.setdefault(domain, Counter())[name] += 1

    names, sources = [], []
    for domain, name in zip(df["domain"], df["company_name"], strict=True):
        if not is_missing(name):
            names.append(name)
            sources.append("original")
        elif is_missing(domain):
            names.append(None)
            sources.append(None)
        elif domain in names_by_domain:
            # Most common spelling; Counter keeps first-seen order for ties, so this is deterministic.
            names.append(names_by_domain[domain].most_common(1)[0][0])
            sources.append("same domain")
        else:
            names.append(company_from_domain(domain))
            sources.append("inferred")
    df["company_name"] = names
    df["company_name_source"] = sources
    return df
