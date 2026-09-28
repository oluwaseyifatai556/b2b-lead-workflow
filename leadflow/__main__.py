"""Command line: python -m leadflow run --input leads.csv --config icp.yaml --out output"""

from __future__ import annotations

import argparse
import sys
from datetime import date

from leadflow.clean import InputError
from leadflow.config import ConfigError
from leadflow.pipeline import run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="leadflow", description="Clean, dedupe, score and rank a B2B lead list.")
    sub = parser.add_subparsers(dest="command", required=True)
    run_cmd = sub.add_parser("run", help="Process a lead CSV")
    run_cmd.add_argument("--input", required=True, help="Path to the messy lead CSV")
    run_cmd.add_argument("--config", default="icp.yaml", help="Path to the ICP settings file (default: icp.yaml)")
    run_cmd.add_argument("--out", default="output", help="Folder for results (default: output)")
    run_cmd.add_argument("--date", type=date.fromisoformat, help="Report date, YYYY-MM-DD (default: today)")
    args = parser.parse_args(argv)

    try:
        result = run(args.input, args.config, args.out, run_date=args.date)
    except (InputError, ConfigError) as exc:
        print(f"\nProblem: {exc}", file=sys.stderr)
        return 1
    except PermissionError as exc:
        print(
            f"\nProblem: can't save '{exc.filename}'. If it's open in Excel, close it and try again.",
            file=sys.stderr,
        )
        return 1

    s = result.stats
    tiers = ", ".join(f"{t}: {n}" for t, n in result.ranked["tier"].value_counts().reindex(
        [t.name for t in result.config.tiers], fill_value=0).items())
    print(
        f"\nDone! {s['rows_in']} rows in -> {s['duplicates_removed']} duplicates merged, "
        f"{s['rejected']} rejected, {s['ranked']} ranked ({tiers})."
    )
    print(f"Results saved in: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
