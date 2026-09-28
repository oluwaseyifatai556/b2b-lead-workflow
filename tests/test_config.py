import copy
from pathlib import Path

import pytest

from leadflow.config import Condition, ConfigError, load_config, parse_config

ROOT = Path(__file__).resolve().parents[1]


def test_shipped_icp_yaml_is_valid():
    config = load_config(ROOT / "icp.yaml")
    assert config.rules and config.tiers
    assert config.tiers[-1].min_score == 0
    assert [t.name for t in config.tiers] == ["A", "B", "C"]


def test_parse_valid_config(config):
    assert config.client_name == "Test Client"
    assert config.max_points == 100
    assert [t.name for t in config.tiers] == ["A", "B", "C"]
    assert config.tiers[0].color == "C6EFCE"  # default color for the first tier


def _broken(config_data, mutate):
    data = copy.deepcopy(config_data)
    mutate(data)
    return data


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda d: d.pop("scoring_rules"), "scoring_rules"),
        (lambda d: d["scoring_rules"][0].update(field="favourite_colour"), "unknown field 'favourite_colour'"),
        (lambda d: d["scoring_rules"][0].update(points=0), "whole number"),
        (lambda d: d["scoring_rules"][0].update(points="lots"), "whole number"),
        (lambda d: d["scoring_rules"][0].update(equals="SaaS"), "exactly one test"),
        (lambda d: d["scoring_rules"][0].pop("in"), "exactly one test"),
        (lambda d: d["scoring_rules"][1].update(between=[1000, 50]), "low, high"),
        (lambda d: d["scoring_rules"][2].update(contains_any="VP"), "non-empty list"),
        (lambda d: d["scoring_rules"].append({"field": "industry", "at_least": 3, "points": 1}), "number fields"),
        (lambda d: d["scoring_rules"].append({"field": "email_is_free", "in": [True], "points": 1}), "true/false"),
        (lambda d: d["disqualifiers"][0].pop("reason"), "reason"),
        (lambda d: d["tiers"].pop(), "min_score: 0"),
        (lambda d: d["tiers"][0].update(min_score=150), "0 to 100"),
        (lambda d: d["tiers"][0].update(color="green"), "hex code"),
        (lambda d: d["tiers"][1].update(name="A"), "unique"),
    ],
)
def test_invalid_config_gives_plain_error(config_data, mutate, message):
    with pytest.raises(ConfigError, match=message):
        parse_config(_broken(config_data, mutate))


def test_only_negative_rules_rejected(config_data):
    data = copy.deepcopy(config_data)
    data["scoring_rules"] = [{"field": "phone", "is_missing": True, "points": -5}]
    with pytest.raises(ConfigError, match="positive points"):
        parse_config(data)


def test_missing_file(tmp_path):
    with pytest.raises(ConfigError, match="Can't find"):
        load_config(tmp_path / "nope.yaml")


def test_bad_yaml(tmp_path):
    path = tmp_path / "icp.yaml"
    path.write_text("scoring_rules: [unclosed\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="isn't valid YAML"):
        load_config(path)


def test_yaml_saved_by_notepad_with_bom_or_ansi(tmp_path, config_data):
    import yaml

    text = yaml.safe_dump({**config_data, "client_name": "Café Co"}, allow_unicode=True)
    bom = tmp_path / "bom.yaml"
    bom.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))
    ansi = tmp_path / "ansi.yaml"
    ansi.write_bytes(text.encode("cp1252"))
    assert load_config(bom).client_name == "Café Co"
    assert load_config(ansi).client_name == "Café Co"


@pytest.mark.parametrize(
    ("condition", "value", "expected"),
    [
        (Condition("industry", "in", ["SaaS"]), "saas", True),
        (Condition("industry", "in", ["SaaS"]), None, False),
        (Condition("industry", "not_in", ["SaaS"]), "Retail", True),
        (Condition("industry", "not_in", ["SaaS"]), None, False),
        (Condition("contact_title", "contains_any", ["CTO"]), "Director of Sales", False),
        (Condition("contact_title", "contains_any", ["CTO"]), "Co-founder & CTO", True),
        (Condition("contact_title", "contains_any", ["Head of"]), "Head of Growth", True),
        (Condition("employee_count", "between", [50, 1000]), 50, True),
        (Condition("employee_count", "between", [50, 1000]), 1001, False),
        (Condition("employee_count", "at_least", 10), 9, False),
        (Condition("annual_revenue", "at_most", 10), 10, True),
        (Condition("phone", "is_missing", True), None, True),
        (Condition("phone", "is_missing", False), "+1555", True),
        (Condition("email_is_free", "equals", False), False, True),
    ],
)
def test_condition_semantics(condition, value, expected):
    assert condition.test(value) is expected
