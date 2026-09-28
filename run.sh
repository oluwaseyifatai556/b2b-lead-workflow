#!/usr/bin/env sh
# Lead list workflow (macOS / Linux). Usage: ./run.sh [path/to/leads.csv]
set -e
cd "$(dirname "$0")"

if [ ! -f .venv/.installed ]; then
  echo "First run: setting things up. This takes a minute and only happens once."
  python3 -m venv .venv
  .venv/bin/python -m pip install --quiet --disable-pip-version-check -r requirements.txt
  touch .venv/.installed
fi

.venv/bin/python -m leadflow run --input "${1:-data/raw/sample_leads.csv}" --config icp.yaml --out output
