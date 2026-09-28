"""Orchestrate the workflow: load -> clean -> dedupe -> disqualify -> score -> rank -> write."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from leadflow.clean import InputError, clean_leads
from leadflow.config import IcpConfig, load_config
from leadflow.dedupe import dedupe
from leadflow.enrich import fill_company_names
from leadflow.report import build_summary_markdown, write_excel
from leadflow.score import rank_leads, score_leads, split_disqualified

PROFILE_COLUMNS = [
    "full_name",
    "contact_title",
    "company_name",
    "company_name_source",
    "domain",
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
    "email_is_free",
    "profile_completeness",
    "source_rows",
    "duplicates_merged",
    "contact_first_name",
    "contact_last_name",
]
RANKED_COLUMNS = ["rank", "tier", "score", "score_reasons", "needs_enrichment", "missing_fields", *PROFILE_COLUMNS]
REJECTED_COLUMNS = ["reject_reason", *PROFILE_COLUMNS]


@dataclass
class RunResult:
    ranked: pd.DataFrame
    rejected: pd.DataFrame
    quality: pd.DataFrame
    stats: dict[str, int]
    config: IcpConfig
    input_name: str
    run_date: date


def read_leads_csv(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise InputError(f"Can't find the lead file '{path}'.")
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
        except pd.errors.EmptyDataError as exc:
            raise InputError(f"The lead file '{path.name}' is empty.") from exc
    else:
        raise InputError(f"Can't read '{path.name}'. Save it from Excel as 'CSV UTF-8' and try again.")
    if df.empty:
        raise InputError(f"The lead file '{path.name}' has a header row but no leads.")
    return df


def process(
    raw: pd.DataFrame, config: IcpConfig, input_name: str = "leads.csv", run_date: date | None = None
) -> RunResult:
    cleaned, quality = clean_leads(raw)
    unique = fill_company_names(dedupe(cleaned))
    kept, rejected = split_disqualified(unique, config)
    ranked = rank_leads(score_leads(kept, config))
    rejected = rejected.sort_values("source_row", kind="mergesort")
    stats = {
        "rows_in": len(raw),
        "duplicates_removed": len(cleaned) - len(unique),
        "unique_contacts": len(unique),
        "rejected": len(rejected),
        "ranked": len(ranked),
    }
    return RunResult(
        ranked=ranked[RANKED_COLUMNS].reset_index(drop=True),
        rejected=rejected[REJECTED_COLUMNS].reset_index(drop=True),
        quality=quality,
        stats=stats,
        config=config,
        input_name=input_name,
        run_date=run_date or date.today(),
    )


def write_outputs(result: RunResult, out_dir: str | Path) -> dict[str, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = {
        "ranked_csv": out / "ranked_leads.csv",
        "rejected_csv": out / "rejected_leads.csv",
        "summary_md": out / "summary.md",
        "excel": out / "ranked_leads.xlsx",
    }
    # Excel first: it's the file most likely to be locked (open in Excel), and failing before
    # anything is written avoids leaving a folder where only some files were updated.
    write_excel(result, paths["excel"])
    # utf-8-sig so Excel opens the CSVs with accents intact.
    result.ranked.to_csv(paths["ranked_csv"], index=False, encoding="utf-8-sig")
    result.rejected.to_csv(paths["rejected_csv"], index=False, encoding="utf-8-sig")
    paths["summary_md"].write_text(build_summary_markdown(result), encoding="utf-8")
    return paths


def run(
    input_path: str | Path, config_path: str | Path, out_dir: str | Path, run_date: date | None = None
) -> RunResult:
    config = load_config(config_path)
    raw = read_leads_csv(input_path)
    result = process(raw, config, input_name=Path(input_path).name, run_date=run_date)
    write_outputs(result, out_dir)
    return result
