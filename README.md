# Lead List Cleaner & Ranker

**Turn a messy spreadsheet of B2B leads into a clean, ranked call list in one click.**

You give it a CSV export of leads (from LinkedIn, a trade show, a list vendor, your CRM…).
It gives you back an Excel file where:

- messy values are tidied up: names, websites, phone numbers, countries, company sizes, revenue and dates are all put into one consistent format,
- **duplicate contacts are merged**, keeping the most complete details from every copy,
- leads that can't be used (bad email, no company) are set aside **with the reason**,
- every remaining lead gets a **score out of 100** and a **tier (A / B / C)** based on your client's
  Ideal Customer Profile, **with a plain-English explanation of the score**,
- and everything is sorted best-first.

It runs on your own computer. No accounts, no subscriptions, no data sent anywhere.

> 👀 **See a finished example without installing anything:** open
> [`examples/summary.md`](examples/summary.md) or download
> [`examples/ranked_leads.xlsx`](examples/ranked_leads.xlsx).
> (All example data is made up, including the people, companies and phone numbers.)

---

## What a result looks like

From the example run (500 messy rows in):

| | Leads |
|---|---:|
| Rows in the original file | 500 |
| Duplicate rows merged away | 60 |
| Rejected (bad email or no company name) | 20 |
| **Ranked and ready to use** | **420**: 101 A, 178 B, 141 C |

And each lead comes with the reason behind its score, for example:

| Rank | Tier | Score | Contact | Why this score |
|---:|:---:|---:|---|---|
| 1 | A | 100 | Ethan Lindqvist, Director, Revenue Operations at Tidalstack | +25 Target industry (SaaS); +20 Mid-market company size (420); +20 Senior decision-maker (Director, Revenue Operations); +15 Target country (United States); +10 Company email address; +10 Revenue in target range (60,500,000) |

So when a client asks "why is this lead at the top?", you have the answer.

---

## Getting started (Windows)

### One-time setup

1. Install **Python 3** from <https://www.python.org/downloads/>.
   During installation, **tick the box "Add python.exe to PATH"**.
2. Download this project (on GitHub: green **Code** button → **Download ZIP**) and unzip it
   somewhere easy, like your Documents folder.

### Every time

- **To try it on the sample data:** double-click **`run.bat`**.
- **To run it on your own leads:** drag your CSV file **onto** `run.bat`.

The first run takes about a minute while it sets itself up. After that it takes a few seconds.
When it finishes, the Excel results open automatically.

> On a Mac? Open Terminal in the project folder and run `./run.sh` or `./run.sh path/to/leads.csv`.

---

## What you get

Everything is saved in the **`output`** folder:

| File | What it's for |
|---|---|
| **`ranked_leads.xlsx`** | The main file. Three tabs: **Ranked** (best leads first, tiers colour-coded, header row stays visible when you scroll, filters on every column), **Rejected** (with the reason), and **Summary**. |
| `ranked_leads.csv` | The same ranked list as a plain CSV, ready to import into your CRM or email tool. |
| `rejected_leads.csv` | Leads that were set aside, each with a "Why rejected" reason. Fix and re-run, or ignore. |
| `summary.md` | A one-page report: counts, tier breakdown, top 10 leads, rejection reasons and data fixes. |

⚠️ Each run **replaces** the files in `output`. Copy anything you want to keep somewhere else first.
If Excel has `ranked_leads.xlsx` open, close it before running again.

### Reading the Ranked tab

| Column | Meaning |
|---|---|
| **Tier** | **A** = strong fit, contact first · **B** = good fit, worth a sequence · **C** = weak fit, nurture or skip |
| **Score** | 0–100. How well the lead matches the client's ideal customer. |
| **Why this score** | Every rule the lead matched and the points it earned or lost. |
| **Profile complete %** | How many of the useful fields are filled in. Among leads with the same score, fuller profiles rank higher. |
| **Original row(s)** | Which row(s) of your original spreadsheet this lead came from. More than one means duplicates were merged. |
| **Personal email?** | "Yes" if the email is a Gmail/Outlook/Yahoo-style personal address. |

---

## Using your own lead file

Your CSV needs a header row. These four columns are **required**:
company name, first name, last name, email.

These are **used if present**: website, job title, phone, industry, employees, annual revenue,
country, state/region, city, lead source, date added.

Column names don't have to match exactly. "Company", "Company Name" and "Organization" all
work, and so do "First Name", "firstname" and so on. Values can be messy: `"50-200"`, `"~1k"`,
`"$2.5M"`, `"USA"`, `"U.K."`, `"(415) 555-0100"`, `"Mar 12, 2026"` are all understood.

**Tip:** In Excel, save your file as **CSV UTF-8** (File → Save As → "CSV UTF-8").

---

## Changing who counts as a good lead

All the targeting lives in one file: **`icp.yaml`**. Open it with Notepad, edit, save, and
run again. No programming needed. The file has instructions at the top.

It has three parts:

**1. Disqualifiers:** leads that get rejected outright.
```yaml
disqualifiers:
  - field: email_valid
    equals: false
    reason: "Email is missing or not a valid address"
```

**2. Scoring rules:** points for a good fit (or minus points for a bad one).
```yaml
  - name: Target country
    field: country
    in: [United States, United Kingdom]
    points: 15
```

**3. Tiers:** the score needed for each tier, and its colour in Excel.
```yaml
  - name: A
    min_score: 80
    color: "#C6EFCE"
```

**Common edits**

| I want to… | Change |
|---|---|
| Target Canada too | Add `Canada` to the list under **Target country** |
| Focus on bigger companies | Change **Mid-market company size** to `between: [200, 5000]` |
| Care more about job title than industry | Raise the `points` on **Senior decision-maker** |
| Reject anyone using a personal email | Add a disqualifier: `field: email_is_free`, `equals: true`, with a `reason` |
| Have fewer A leads | Raise A's `min_score` (e.g. to `85`) |

If you make a mistake in the file, the tool tells you which rule is wrong and why. For example:
`Problem: scoring rule #2 ('Mid-market company size'): 'between' needs [low, high] numbers, e.g. [50, 1000].`

**Scores explained:** a lead's score is the points it earned divided by the most any lead could
earn, shown out of 100. So you can add or change rules freely, and scores always stay on the same
0–100 scale.

---

## How duplicates are found

Two rows are treated as **the same person** if either:
- they have the **same email address** (ignoring capitals and spaces), or
- they have the **same company website and the same full name**. This catches someone who
  signed up once with a work email and once with a personal one.

When duplicates are found, the tool keeps the most complete row and fills its blanks from the
other copies, so you don't lose a phone number that only appeared in one of them. The
**Original row(s)** column shows which rows were combined.

Different people at the same company are never merged.

---

## FAQ

**Is my data sent anywhere?**
No. Everything runs on your computer, and nothing connects to the internet except the one-time setup.

**Why was a phone number left blank?**
It couldn't be read (for example `"123"` or `"n/a"`). The Summary shows how many values in each
column were blank, tidied, or unreadable.

**Why do some phone numbers have no `+` country code?**
The lead had no country, so the tool kept the digits as they were rather than guess.

**Revenue is in different currencies. Does that matter?**
Currency symbols are ignored, so `£3M` and `$3M` both count as 3,000,000. For a rough size
filter that's usually fine. If it matters for a client, split the list by country first.

**Does running it twice give the same result?**
Yes. The same file with the same settings always produces the same ranking.

**Something went wrong.**
The window shows a message starting with `Problem:` explaining what to fix: a missing column,
a typo in `icp.yaml`, or the Excel file being open. Fix it and run again.

---

## For developers

<details>
<summary>Project layout, commands and design notes</summary>

### Stack
Python 3.10+, pandas, PyYAML, openpyxl. Tests with pytest, lint with ruff. No network, no API keys.

### Commands
```powershell
py -3 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt

.\.venv\Scripts\python -m leadflow run --input data\raw\sample_leads.csv --config icp.yaml --out output
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m ruff check .
.\.venv\Scripts\python scripts\generate_sample_data.py      # rebuild the synthetic sample (seeded)
```
`run.bat` wraps the run command and bootstraps `.venv` on first use. Set `LEADFLOW_UNATTENDED=1`
to skip opening Excel and pausing (e.g. for Task Scheduler). `--date YYYY-MM-DD` pins the report date.

### Layout
```
leadflow/
  __main__.py    CLI (argparse); maps InputError/ConfigError/PermissionError to plain messages
  pipeline.py    read CSV → clean → dedupe → disqualify → score → rank → write
  clean.py       pure per-field normalizers + clean_leads() + data-quality counts
  reference.py   data-hygiene lookup tables (country aliases, free-mail domains, …)
  dedupe.py      union-find on match keys; merge = most complete row + gap fill
  config.py      icp.yaml loader/validator and the Condition rule engine
  score.py       disqualifiers, scoring with explanations, tiers, ranking
  report.py      summary.md and the formatted Excel workbook
scripts/generate_sample_data.py   stdlib-only, seeded synthetic messy data
tests/                            unit tests per module + end-to-end pipeline tests
examples/                         committed output of one run on the sample data
```

### Pipeline
1. **Read**: every column as text; UTF-8 (with or without BOM) or Windows-1252 fallback.
2. **Clean**: headers mapped to standard names; each value normalized by a pure function that
   returns `None` when unreadable. Invalid emails are kept (so they're visible) and flagged `email_valid=false`.
   A lead's `domain` comes from its website, or from its email if that's a business address.
3. **Dedupe**: keys are `email` (valid only) and `domain + lower(full name)`. Union-find makes
   matches transitive. The primary row is the most complete (tie → earliest row); blanks are filled from
   the others. An invalid email counts as blank, so a valid one from a duplicate wins.
4. **Disqualify**: any matching disqualifier sends the lead to `rejected_leads.csv`; all hit
   reasons are listed.
5. **Score**: sum of matching rule points ÷ sum of positive points × 100, clamped to 0–100;
   tier by descending `min_score`.
6. **Rank**: score ↓, profile completeness ↓, date added ↓, original row ↑ (stable sort, so output is deterministic).

### Rule engine (`icp.yaml`)
Tests: `equals`, `in`, `not_in`, `contains_any` (whole-word, case-insensitive), `between`,
`at_least`, `at_most`, `is_missing`. Numeric tests are only allowed on `employee_count` and
`annual_revenue`, and boolean fields only accept `equals: true|false`. The config is validated up
front, and every error names the rule and the fix.

### Parsing choices worth knowing
- Employee ranges use the midpoint (`50-200` → 125). `500+` → 500.
- Phone numbers are output as `+<country code><digits>` when the country is known, and raw digits otherwise.
- Dates accept ISO, `MM/DD/YYYY` (US order), `12 Mar 2026`, `Mar 12, 2026`, `YYYY/MM/DD`, ISO with time.
  `DD/MM/YYYY` is intentionally **not** guessed, to avoid silently swapping day and month.

### Synthetic data
`scripts/generate_sample_data.py` builds 500 rows (seed 42) from invented name parts. Company
domains use the reserved `.example` TLD. Phone numbers use ranges reserved for fiction (US
555-01xx, UK Ofcom drama numbers). About 12% of rows are duplicates (exact copies, thinner copies, or
the same person with a personal email), and about 5% have problems that get them rejected.

</details>
