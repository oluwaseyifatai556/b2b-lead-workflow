"""Normalize messy lead values into consistent, comparable ones.

Per-value functions are pure and return None when a value is missing or unreadable.
`clean_leads` applies them to a whole table and reports what it changed.
"""

from __future__ import annotations

import math
import re
from datetime import date, datetime

import pandas as pd

from leadflow.reference import (
    COMPANY_SUFFIXES,
    COUNTRY_ALIASES,
    COUNTRY_DIAL_CODES,
    FIXED_CASE_WORDS,
    FREE_EMAIL_DOMAINS,
    HEADER_ALIASES,
    INDUSTRY_CANONICAL,
    LEAD_SOURCE_CANONICAL,
    PHONE_ANY_DIGITS,
    PHONE_NATIONAL_DIGITS,
)

INPUT_COLUMNS = [
    "company_name",
    "website",
    "contact_first_name",
    "contact_last_name",
    "contact_title",
    "email",
    "phone",
    "industry",
    "employee_count",
    "annual_revenue",
    "country",
    "state_region",
    "city",
    "lead_source",
    "created_date",
]
REQUIRED_INPUT_COLUMNS = ["company_name", "contact_first_name", "contact_last_name", "email"]

# Columns available to icp.yaml rules after cleaning.
CLEAN_COLUMNS = [
    "source_row",
    "company_name",
    "domain",
    "contact_first_name",
    "contact_last_name",
    "full_name",
    "contact_title",
    "email",
    "email_valid",
    "email_is_free",
    "phone",
    "industry",
    "employee_count",
    "annual_revenue",
    "country",
    "state_region",
    "city",
    "lead_source",
    "created_date",
]

EMAIL_RE = re.compile(r"^[a-z0-9._%+'-]+@[a-z0-9-]+(\.[a-z0-9-]+)*\.[a-z]{2,}$")
DATE_FORMATS = [
    "%Y-%m-%d",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d",
    "%m/%d/%Y",
    "%d %b %Y",
    "%d %B %Y",
    "%b %d, %Y",
    "%B %d, %Y",
]


class InputError(ValueError):
    """The input file can't be used; the message is written for a non-technical reader."""


def is_missing(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if value is pd.NA or value is pd.NaT:
        return True
    return isinstance(value, str) and value.strip() in {"", "-", "n/a", "N/A", "none", "None", "null"}


def _text(value: object) -> str | None:
    if is_missing(value):
        return None
    return re.sub(r"\s+", " ", str(value)).strip()


def smart_title(text: str) -> str:
    """Title-case text that is ALL CAPS or all lowercase; leave deliberate mixed case alone."""
    if not (text.isupper() or text.islower()):
        return text
    words = []
    for i, word in enumerate(text.split(" ")):
        fixed = FIXED_CASE_WORDS.get(word.lower())
        if fixed and not (i == 0 and fixed.islower()):
            words.append(fixed)
        else:
            words.append(word.title())  # handles "o'donnell" and "co-founder"
    return " ".join(words)


def clean_name(value: object) -> str | None:
    text = _text(value)
    if not text:
        return None
    return smart_title(text)


def clean_company_name(value: object) -> str | None:
    text = _text(value)
    if not text:
        return None
    text = smart_title(text)
    words = text.replace(",", " ").split()
    last = words[-1].rstrip(".").lower() if words else ""
    if len(words) > 1 and last in COMPANY_SUFFIXES:
        words[-1] = COMPANY_SUFFIXES[last]
    return " ".join(words)


def clean_domain(value: object) -> str | None:
    text = _text(value)
    if not text:
        return None
    text = text.lower()
    text = re.sub(r"^[a-z]+://", "", text)
    text = text.split("/")[0].split("?")[0].split(":")[0]
    text = re.sub(r"^www\d*\.", "", text).strip(".")
    return text if "." in text and " " not in text else None


def clean_email(value: object) -> str | None:
    """Lowercase and trim an email. Returns the tidied text even if it is not a valid address."""
    text = _text(value)
    if not text:
        return None
    text = text.lower().replace(" ", "")
    text = re.sub(r"^mailto:", "", text)
    return text.strip("<>;,")


def is_valid_email(email: object) -> bool:
    return isinstance(email, str) and bool(EMAIL_RE.match(email))


def email_domain(email: object) -> str | None:
    if not is_valid_email(email):
        return None
    return str(email).split("@", 1)[1]


def is_free_email(email: object) -> bool:
    return email_domain(email) in FREE_EMAIL_DOMAINS


def clean_country(value: object) -> str | None:
    text = _text(value)
    if not text:
        return None
    return COUNTRY_ALIASES.get(text.lower(), smart_title(text))


def _national_ok(code: str, national: str) -> bool:
    low, high = PHONE_NATIONAL_DIGITS[code]
    return low <= len(national) <= high


def _any_length_ok(digits: str) -> bool:
    return PHONE_ANY_DIGITS[0] <= len(digits) <= PHONE_ANY_DIGITS[1]


def clean_phone(value: object, country: str | None = None) -> str | None:
    """Return a phone number as +<country code><number>, or None if it can't be read or is
    the wrong length to be a complete number for its country."""
    text = _text(value)
    if not text:
        return None
    text = re.split(r"(?i)\s*(?:x|ext\.?|extension)\s*\d+$", text)[0]
    text = text.replace("(0)", "")
    digits = re.sub(r"\D", "", text)
    if not digits:
        return None

    if text.startswith(("+", "00")):
        if text.startswith("00"):
            digits = digits[2:]
        # The number carries its own country code; judge it by that, not the lead's country.
        for code in sorted(PHONE_NATIONAL_DIGITS, key=len, reverse=True):
            if digits.startswith(code):
                national = digits[len(code):]
                if national.startswith("0"):  # e.g. "+44 020 ..."
                    national = national[1:]
                return f"+{code}{national}" if _national_ok(code, national) else None
        return "+" + digits if _any_length_ok(digits) else None

    code = COUNTRY_DIAL_CODES.get(country) if isinstance(country, str) else None
    if code is None:
        # Country unknown: keep the digits rather than lose the number, if the length is plausible.
        return digits if _any_length_ok(digits) else None
    if digits.startswith(code) and _national_ok(code, digits[len(code):]):
        national = digits[len(code):]  # written with the country code but no "+"
    elif digits.startswith("0"):
        national = digits[1:]  # national trunk prefix
    else:
        national = digits
    return f"+{code}{national}" if _national_ok(code, national) else None


_MULTIPLIERS = {"k": 1e3, "thousand": 1e3, "m": 1e6, "mm": 1e6, "mil": 1e6, "million": 1e6,
                "b": 1e9, "bn": 1e9, "billion": 1e9}
_NUMBER_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(thousand|million|billion|mil|mm|bn|k|m|b)?\b")


def _parse_amounts(text: str) -> list[float]:
    text = text.lower().replace(",", "")
    return [float(num) * _MULTIPLIERS.get(unit or "", 1) for num, unit in _NUMBER_RE.findall(text)]


def parse_employee_count(value: object) -> int | None:
    """'50-200' -> 125 (midpoint), '~1k' -> 1000, '500+' -> 500, '1,200' -> 1200."""
    text = _text(value)
    if not text:
        return None
    amounts = _parse_amounts(text)
    if not amounts:
        return None
    count = sum(amounts[:2]) / len(amounts[:2])
    return int(round(count)) if count >= 1 else None


def parse_revenue(value: object) -> int | None:
    """'$2.5M' -> 2500000, '£750k' -> 750000, 'USD 4 million' -> 4000000. Currency is ignored."""
    text = _text(value)
    if not text:
        return None
    amounts = _parse_amounts(text)
    if not amounts:
        return None
    amount = round(sum(amounts[:2]) / len(amounts[:2]))
    return amount if amount > 0 else None


def parse_date(value: object) -> date | None:
    text = _text(value)
    if not text:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def clean_region(value: object) -> str | None:
    text = _text(value)
    if not text:
        return None
    if len(text) <= 3 and text.isalpha():
        return text.upper()
    return smart_title(text)


def _canonical(value: object, table: dict[str, str]) -> str | None:
    text = _text(value)
    if not text:
        return None
    return table.get(text.lower(), smart_title(text))


def clean_industry(value: object) -> str | None:
    return _canonical(value, INDUSTRY_CANONICAL)


def clean_lead_source(value: object) -> str | None:
    return _canonical(value, LEAD_SOURCE_CANONICAL)


def standardize_headers(df: pd.DataFrame) -> pd.DataFrame:
    """Map incoming header spellings to standard names and add any optional missing columns."""
    renamed = {}
    for col in df.columns:
        key = re.sub(r"[^a-z0-9]+", "_", str(col).strip().lower()).strip("_")
        renamed[col] = HEADER_ALIASES.get(key, key)
    df = df.rename(columns=renamed)
    df = df.loc[:, ~df.columns.duplicated()]
    missing = [c for c in REQUIRED_INPUT_COLUMNS if c not in df.columns]
    if missing:
        raise InputError(
            "The lead file is missing these required columns: "
            + ", ".join(missing)
            + ". Check the header row of your CSV."
        )
    for col in INPUT_COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df


def clean_leads(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Clean a raw lead table.

    Returns (cleaned table with CLEAN_COLUMNS, data-quality table with one row per field
    showing how many values were standardized and how many were unreadable and blanked).
    """
    raw = standardize_headers(raw.copy())
    out = pd.DataFrame(index=raw.index)
    # Spreadsheet row number of each lead (row 1 is the header).
    out["source_row"] = [i + 2 for i in range(len(raw))]
    out["company_name"] = raw["company_name"].map(clean_company_name)
    out["contact_first_name"] = raw["contact_first_name"].map(clean_name)
    out["contact_last_name"] = raw["contact_last_name"].map(clean_name)
    out["contact_title"] = raw["contact_title"].map(clean_name)
    out["email"] = raw["email"].map(clean_email)
    out["country"] = raw["country"].map(clean_country)
    out["phone"] = [clean_phone(p, c) for p, c in zip(raw["phone"], out["country"], strict=True)]
    out["industry"] = raw["industry"].map(clean_industry)
    out["employee_count"] = pd.array(raw["employee_count"].map(parse_employee_count).tolist(), dtype="Int64")
    out["annual_revenue"] = pd.array(raw["annual_revenue"].map(parse_revenue).tolist(), dtype="Int64")
    out["state_region"] = raw["state_region"].map(clean_region)
    out["city"] = raw["city"].map(clean_name)
    out["lead_source"] = raw["lead_source"].map(clean_lead_source)
    out["created_date"] = raw["created_date"].map(parse_date)
    website_domain = raw["website"].map(clean_domain)
    out["domain"] = [
        site if not is_missing(site) else (None if is_free_email(e) else email_domain(e))
        for site, e in zip(website_domain, out["email"], strict=True)
    ]
    out = add_derived_columns(out)
    out["unreadable_fields"] = _unreadable_fields(raw, out)

    quality = _quality_report(raw, out, website_domain)
    return out[[*CLEAN_COLUMNS, "unreadable_fields"]].reset_index(drop=True), quality


# Fields whose raw value can be present but unreadable, and that the same-named clean column holds.
# (Email is excluded: an invalid email is kept as text and handled by email_valid.)
_UNREADABLE_CANDIDATES = [c for c in INPUT_COLUMNS if c not in ("website", "email")]


def _unreadable_fields(raw: pd.DataFrame, clean: pd.DataFrame) -> list[str]:
    """Per row, '; '-joined fields that had a value in the file which couldn't be read."""
    flags = {
        field: ~raw[field].map(is_missing) & clean[field].map(is_missing) for field in _UNREADABLE_CANDIDATES
    }
    return ["; ".join(f for f in _UNREADABLE_CANDIDATES if flags[f].iloc[i]) for i in range(len(raw))]


def unreadable_set(row: dict) -> set[str]:
    """The set of unreadable field names recorded on a lead (empty if none or not tracked)."""
    value = row.get("unreadable_fields")
    return set() if is_missing(value) else {f for f in str(value).split("; ") if f}


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """(Re)compute columns that depend on other columns. Safe to call after merging."""
    df = df.copy()
    df["full_name"] = [
        " ".join(p for p in (f, la) if not is_missing(p)) or None
        for f, la in zip(df["contact_first_name"], df["contact_last_name"], strict=True)
    ]
    df["email_valid"] = df["email"].map(is_valid_email).astype(bool)
    df["email_is_free"] = df["email"].map(is_free_email).astype(bool)
    return df


def _quality_report(raw: pd.DataFrame, clean: pd.DataFrame, website_domain: pd.Series) -> pd.DataFrame:
    checks = {
        "company_name": clean["company_name"],
        "website": website_domain,
        "contact_first_name": clean["contact_first_name"],
        "contact_last_name": clean["contact_last_name"],
        "contact_title": clean["contact_title"],
        "email": clean["email"],
        "phone": clean["phone"],
        "industry": clean["industry"],
        "employee_count": clean["employee_count"],
        "annual_revenue": clean["annual_revenue"],
        "country": clean["country"],
        "state_region": clean["state_region"],
        "city": clean["city"],
        "lead_source": clean["lead_source"],
        "created_date": clean["created_date"],
    }
    rows = []
    for field, cleaned in checks.items():
        before = raw[field]
        present = ~before.map(is_missing)
        unreadable = present & cleaned.map(is_missing)
        if field == "email":
            unreadable = present & ~clean["email"].map(is_valid_email)
        changed = present & ~unreadable & (before.map(_text).astype(object) != cleaned.map(_display).astype(object))
        rows.append(
            {
                "field": field,
                "blank": int((~present).sum()),
                "standardized": int(changed.sum()),
                "unreadable": int(unreadable.sum()),
            }
        )
    return pd.DataFrame(rows)


def _display(value: object) -> str | None:
    if is_missing(value):
        return None
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else str(value)
    return str(value)
