# Lead list summary

**Client ICP:** Brightloop (fictional B2B SaaS) - mid-market US & UK  
**Input file:** `sample_leads.csv`  
**Generated:** 2026-09-28

## At a glance

| | Leads |
|---|---:|
| Rows in the original file | 500 |
| Duplicate rows merged away | 60 |
| Unique contacts | 440 |
| Rejected (see reasons below) | 11 |
| **Ranked and ready to use** | **429** |

## Tier breakdown

| Tier | Score range | What it means | Leads | Share |
|---|---|---|---:|---:|
| A | 80-100 | Strong fit: contact first | 103 | 24% |
| B | 55-79 | Good fit: worth a sequence | 182 | 42% |
| C | 0-54 | Weak fit: nurture or skip | 144 | 34% |

Cut-offs come from icp.yaml. Leads are sorted by score (highest first). Ties are broken by profile completeness (more complete first), then date added (newest first), then original row order.

## Leads with missing data

A blank field earns no points, so a low score can mean *we don't know* rather than *poor fit*. `needs_enrichment` is Yes when filling the lead's blank fields could move it up a tier.

- **185** of 429 ranked leads are blank in at least one scored field (see the `missing_fields` column).
- **93** could move up a tier if those gaps were filled: worth researching before writing them off.

| Tier now | Could move up |
|---|---:|
| A | 0 |
| B | 47 |
| C | 46 |

| Most often missing | Leads |
|---|---:|
| Annual revenue | 43 |
| Phone | 42 |
| Employees | 27 |
| Annual revenue (unreadable) | 24 |
| Industry | 22 |
| Phone (unreadable) | 21 |
| Job title | 20 |
| Country | 17 |
| Employees (unreadable) | 17 |

## Top 10 leads

| Rank | Tier | Score | Contact | Job title | Company | Country |
|---:|---|---:|---|---|---|---|
| 1 | A | 100 | Ethan Lindqvist | Director, Revenue Operations | Tidalstack | United States |
| 2 | A | 100 | Liam Zielinski | CEO | Silverbridge LLC | United Kingdom |
| 3 | A | 100 | Sean Kowalski | Director of Marketing | Northspring | United States |
| 4 | A | 100 | Isaac Sokolov | Director of Marketing | Meadowsight Logistics Corp | United States |
| 5 | A | 100 | Vera Ellery | Sales Director | Nimbusgrid Group Ltd | United States |
| 6 | A | 100 | Wes Nakamura | Director of Marketing | Bluegrid Labs Corp | United States |
| 7 | A | 100 | Hannah Brennan | Head of Marketing | Sablegrid Group LLC | United Kingdom |
| 8 | A | 100 | Wes Iyer | VP Sales | Atlasloop Health LLC | United States |
| 9 | A | 100 | Rosa Moreau | Co-Founder | Vertexnest LLC | United States |
| 10 | A | 100 | Avery Whitfield | CEO | Prismbridge Logistics | United Kingdom |

## Why leads were rejected

| Reason | Leads |
|---|---:|
| Email is missing or not a valid address | 11 |

_A lead can have more than one reason._

## Data quality fixes

How many values in each column were blank, tidied into a standard format, or unreadable (unreadable values are left blank; invalid emails are kept so you can see them).

| Column | Blank | Standardized | Unreadable |
|---|---:|---:|---:|
| Company | 10 | 183 | 0 |
| Website | 77 | 364 | 0 |
| First name | 0 | 63 | 0 |
| Last name | 0 | 60 | 0 |
| Job title | 37 | 50 | 0 |
| Email | 2 | 63 | 10 |
| Phone | 59 | 394 | 28 |
| Industry | 41 | 120 | 0 |
| Employees | 42 | 129 | 22 |
| Annual revenue | 66 | 318 | 32 |
| Country | 21 | 376 | 0 |
| State / region | 14 | 45 | 0 |
| City | 10 | 58 | 0 |
| Lead source | 25 | 111 | 0 |
| Date added | 21 | 336 | 0 |

## Scoring rules used (from icp.yaml)

| Rule | Points |
|---|---:|
| Target industry | +25 |
| Mid-market company size | +20 |
| Senior decision-maker | +20 |
| Target country | +15 |
| Company email address | +10 |
| Revenue in target range | +10 |
| Junior role | -15 |
| No phone number | -5 |

Scores are points earned divided by the maximum possible (100), shown out of 100.
