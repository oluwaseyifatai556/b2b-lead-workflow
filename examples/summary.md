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
| Rejected (see reasons below) | 20 |
| **Ranked and ready to use** | **420** |

## Tier breakdown

| Tier | What it means | Leads | Share |
|---|---|---:|---:|
| A | Strong fit: contact first | 101 | 24% |
| B | Good fit: worth a sequence | 178 | 42% |
| C | Weak fit: nurture or skip | 141 | 34% |

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
| Company name is missing | 9 |

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
| Phone | 50 | 421 | 9 |
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
