"""Load and validate icp.yaml. All targeting rules come from there, never from code."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from leadflow.clean import CLEAN_COLUMNS, is_missing

NUMERIC_FIELDS = {"employee_count", "annual_revenue"}
BOOLEAN_FIELDS = {"email_valid", "email_is_free"}
OPERATORS = {"equals", "in", "not_in", "contains_any", "between", "at_least", "at_most", "is_missing"}
DEFAULT_TIER_COLORS = ["C6EFCE", "FFEB9C", "E7E6E6", "F4CCCC"]


class ConfigError(ValueError):
    """icp.yaml is invalid; the message names the offending setting in plain English."""


@dataclass(frozen=True)
class Condition:
    field: str
    op: str
    value: Any

    def test(self, cell: object) -> bool:
        if self.op == "is_missing":
            return is_missing(cell) == bool(self.value)
        if is_missing(cell):
            return False
        if self.op == "equals":
            return _norm(cell) == _norm(self.value)
        if self.op == "in":
            return _norm(cell) in {_norm(v) for v in self.value}
        if self.op == "not_in":
            return _norm(cell) not in {_norm(v) for v in self.value}
        if self.op == "contains_any":
            # Whole-word match, so "CTO" doesn't match inside "Director".
            text = str(cell).lower()
            return any(re.search(rf"\b{re.escape(str(v).lower())}\b", text) for v in self.value)
        number = float(cell)  # type: ignore[arg-type]
        if self.op == "between":
            low, high = self.value
            return low <= number <= high
        if self.op == "at_least":
            return number >= self.value
        if self.op == "at_most":
            return number <= self.value
        raise AssertionError(f"unhandled operator {self.op}")


@dataclass(frozen=True)
class ScoringRule:
    name: str
    condition: Condition
    points: int


@dataclass(frozen=True)
class Disqualifier:
    name: str
    condition: Condition
    reason: str


@dataclass(frozen=True)
class Tier:
    name: str
    min_score: int
    color: str
    description: str


@dataclass(frozen=True)
class IcpConfig:
    client_name: str
    rules: list[ScoringRule]
    disqualifiers: list[Disqualifier]
    tiers: list[Tier]  # highest min_score first

    @property
    def max_points(self) -> int:
        return sum(r.points for r in self.rules if r.points > 0)


def _norm(value: object) -> object:
    if isinstance(value, str):
        return value.strip().lower()
    return value


def load_config(path: str | Path) -> IcpConfig:
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"Can't find the ICP settings file '{path}'.")
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1252", errors="replace")  # saved as "ANSI" by an older Notepad
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ConfigError(f"'{path.name}' isn't valid YAML (check indentation and colons): {exc}") from exc
    return parse_config(data)


def parse_config(data: object) -> IcpConfig:
    if not isinstance(data, dict):
        raise ConfigError("The ICP settings file is empty or not a list of settings.")
    for key in ("scoring_rules", "tiers"):
        if key not in data:
            raise ConfigError(f"The ICP settings file needs a '{key}' section.")

    rules_data = _as_list(data, "scoring_rules")
    if not rules_data:
        raise ConfigError("'scoring_rules' needs at least one rule.")
    rules = []
    for i, item in enumerate(rules_data, start=1):
        where = f"scoring rule #{i}"
        _require_mapping(item, where)
        name = str(item.get("name") or f"Rule {i}")
        points = item.get("points")
        if isinstance(points, bool) or not isinstance(points, int) or points == 0:
            raise ConfigError(f"{where} ('{name}'): 'points' must be a whole number other than 0.")
        rules.append(ScoringRule(name, _parse_condition(item, f"{where} ('{name}')"), points))
    if not any(r.points > 0 for r in rules):
        raise ConfigError("At least one scoring rule must award positive points.")

    disqualifiers = []
    for i, item in enumerate(_as_list(data, "disqualifiers"), start=1):
        where = f"disqualifier #{i}"
        _require_mapping(item, where)
        reason = item.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise ConfigError(f"{where}: add a 'reason' explaining why these leads are rejected.")
        name = str(item.get("name") or reason)
        disqualifiers.append(Disqualifier(name, _parse_condition(item, f"{where} ('{name}')"), reason.strip()))

    tiers = _parse_tiers(_as_list(data, "tiers"))
    return IcpConfig(str(data.get("client_name") or "Unnamed client"), rules, disqualifiers, tiers)


def _as_list(data: dict, key: str) -> list:
    value = data.get(key) or []
    if not isinstance(value, list):
        raise ConfigError(f"'{key}' must be a list (each item starting with '- ').")
    return value


def _require_mapping(item: object, where: str) -> None:
    if not isinstance(item, dict):
        raise ConfigError(f"{where} must be a set of 'key: value' settings.")


def _parse_condition(item: dict, where: str) -> Condition:
    field = item.get("field")
    if field not in CLEAN_COLUMNS or field == "source_row":
        allowed = ", ".join(c for c in CLEAN_COLUMNS if c != "source_row")
        raise ConfigError(f"{where}: unknown field '{field}'. Use one of: {allowed}.")
    ops = [k for k in item if k in OPERATORS]
    if len(ops) != 1:
        raise ConfigError(
            f"{where}: give exactly one test, one of: {', '.join(sorted(OPERATORS))} (found {len(ops)})."
        )
    op = ops[0]
    value = item[op]

    if op in {"in", "not_in", "contains_any"}:
        if not isinstance(value, list) or not value:
            raise ConfigError(f"{where}: '{op}' needs a non-empty list, e.g. [\"A\", \"B\"].")
    elif op == "between":
        if (
            not isinstance(value, list)
            or len(value) != 2
            or not all(_is_number(v) for v in value)
            or value[0] > value[1]
        ):
            raise ConfigError(f"{where}: 'between' needs [low, high] numbers, e.g. [50, 1000].")
    elif op in {"at_least", "at_most"} and not _is_number(value):
        raise ConfigError(f"{where}: '{op}' needs a number.")
    elif op == "is_missing" and not isinstance(value, bool):
        raise ConfigError(f"{where}: 'is_missing' must be true or false.")

    if op in {"between", "at_least", "at_most"} and field not in NUMERIC_FIELDS:
        raise ConfigError(f"{where}: '{op}' only works on number fields ({', '.join(sorted(NUMERIC_FIELDS))}).")
    if field in BOOLEAN_FIELDS and op != "equals":
        raise ConfigError(f"{where}: '{field}' is true/false, so use 'equals: true' or 'equals: false'.")
    if field in BOOLEAN_FIELDS and not isinstance(value, bool):
        raise ConfigError(f"{where}: '{field}' is true/false, so 'equals' must be true or false.")
    return Condition(field, op, value)


def _parse_tiers(items: list) -> list[Tier]:
    if not items:
        raise ConfigError("'tiers' needs at least one tier.")
    tiers = []
    for i, item in enumerate(items):
        where = f"tier #{i + 1}"
        _require_mapping(item, where)
        name = item.get("name")
        min_score = item.get("min_score")
        if not isinstance(name, str) or not name.strip():
            raise ConfigError(f"{where}: needs a 'name'.")
        if isinstance(min_score, bool) or not _is_number(min_score) or not 0 <= min_score <= 100:
            raise ConfigError(f"{where} ('{name}'): 'min_score' must be a number from 0 to 100.")
        color = str(item.get("color") or DEFAULT_TIER_COLORS[min(i, len(DEFAULT_TIER_COLORS) - 1)])
        color = color.lstrip("#").upper()
        if len(color) != 6 or any(c not in "0123456789ABCDEF" for c in color):
            raise ConfigError(f"{where} ('{name}'): 'color' must be a hex code like \"#C6EFCE\".")
        tiers.append(Tier(name.strip(), min_score, color, str(item.get("description") or "")))
    tiers.sort(key=lambda t: t.min_score, reverse=True)
    if tiers[-1].min_score != 0:
        raise ConfigError("The lowest tier must have 'min_score: 0' so every lead gets a tier.")
    if len({t.name for t in tiers}) != len(tiers):
        raise ConfigError("Tier names must be unique.")
    return tiers


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)
