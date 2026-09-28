"""Find duplicate contacts and merge each group into one, most-complete row.

Two leads are the same contact if their normalized email matches, OR their company domain
and full name both match. Matches chain: if A~B by email and B~C by domain+name, A, B and C
merge into one lead.
"""

from __future__ import annotations

import pandas as pd

from leadflow.clean import add_derived_columns, is_missing, is_valid_email, unreadable_set

MERGE_FIELDS = [
    "company_name",
    "domain",
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


def _usable(field: str, value: object) -> bool:
    if field == "email":
        return is_valid_email(value)
    return not is_missing(value)


def completeness(row: dict) -> int:
    """Percent of profile fields that hold a usable value."""
    filled = sum(_usable(f, row.get(f)) for f in MERGE_FIELDS)
    return round(100 * filled / len(MERGE_FIELDS))


def match_keys(row: dict) -> list[str]:
    keys = []
    if is_valid_email(row.get("email")):
        keys.append("email:" + row["email"])
    domain, name = row.get("domain"), row.get("full_name")
    if not is_missing(domain) and not is_missing(name):
        keys.append(f"domain+name:{domain}|{str(name).lower()}")
    return keys


def _group_rows(records: list[dict]) -> list[list[int]]:
    parent = list(range(len(records)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    first_seen: dict[str, int] = {}
    for i, row in enumerate(records):
        for key in match_keys(row):
            if key in first_seen:
                a, b = find(first_seen[key]), find(i)
                if a != b:
                    parent[max(a, b)] = min(a, b)
            else:
                first_seen[key] = i

    groups: dict[int, list[int]] = {}
    for i in range(len(records)):
        groups.setdefault(find(i), []).append(i)
    return sorted(groups.values(), key=lambda g: g[0])


def merge_group(rows: list[dict]) -> dict:
    """Keep the most complete row; fill its gaps from the others (most complete first)."""
    ordered = sorted(rows, key=lambda r: (-completeness(r), r["source_row"]))
    merged = dict(ordered[0])
    for field in MERGE_FIELDS:
        if _usable(field, merged.get(field)):
            continue
        for other in ordered[1:]:
            if _usable(field, other.get(field)):
                merged[field] = other[field]
                break
    if any("unreadable_fields" in r for r in rows):
        # Still unreadable only if no copy supplied a usable value.
        unreadable = set().union(*(unreadable_set(r) for r in rows))
        merged["unreadable_fields"] = "; ".join(
            f for f in MERGE_FIELDS if f in unreadable and not _usable(f, merged.get(f))
        )
    source_rows = sorted(r["source_row"] for r in rows)
    merged["source_row"] = source_rows[0]
    merged["source_rows"] = "; ".join(str(s) for s in source_rows)
    merged["duplicates_merged"] = len(rows) - 1
    return merged


def dedupe(df: pd.DataFrame) -> pd.DataFrame:
    """Return one row per contact, with `source_rows`, `duplicates_merged` and `profile_completeness`."""
    records = df.to_dict("records")
    merged = [merge_group([records[i] for i in group]) for group in _group_rows(records)]
    out = pd.DataFrame(merged, columns=[*df.columns, "source_rows", "duplicates_merged"])
    for col in ("employee_count", "annual_revenue"):
        if col in df.columns:
            out[col] = out[col].astype(df[col].dtype)
    out = add_derived_columns(out)
    out["profile_completeness"] = [completeness(r) for r in out.to_dict("records")]
    return out.reset_index(drop=True)
