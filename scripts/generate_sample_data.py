"""Generate a synthetic, deliberately messy B2B lead CSV.

Everything here is invented: company names are random word combinations on the reserved
`.example` domain. Phone numbers have realistic lengths for their country and, where a
regulator publishes a range for fiction, use it (US/Canada 555-01xx, UK Ofcom drama numbers,
Australia (02) 5550 xxxx, France 01 99 00 xx xx). Germany and India have no such range, so
their numbers are random digits of a valid length. Personal emails use common free-mail
providers with made-up names.

About 8% of phone numbers are deliberately made unreadable (truncated or junk text). That
noise uses its own random stream, so changing it never reshuffles the rest of the data.

Usage: python scripts/generate_sample_data.py [--rows 500] [--seed 42] [--out data/raw/sample_leads.csv]
"""

from __future__ import annotations

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

COLUMNS = [
    "company_name", "website", "contact_first_name", "contact_last_name", "contact_title",
    "email", "phone", "industry", "employee_count", "annual_revenue", "country",
    "state_region", "city", "lead_source", "created_date",
]

FIRST_NAMES = [
    "Avery", "Jordan", "Priya", "Marcus", "Elena", "Tomasz", "Aisha", "Liam", "Sofia", "Kenji",
    "Grace", "Mateo", "Nadia", "Oliver", "Chloe", "Rahul", "Hannah", "Diego", "Freya", "Samuel",
    "Imani", "Lucas", "Zara", "Ethan", "Maya", "Noah", "Leila", "Isaac", "Ruby", "Omar",
    "Clara", "Felix", "Anika", "Hugo", "Iris", "Jonah", "Keira", "Leo", "Mira", "Nathan",
    "Olivia", "Pablo", "Quinn", "Rosa", "Sean", "Tara", "Umar", "Vera", "Wes", "Yara",
]
LAST_NAMES = [
    "Whitfield", "Okafor", "Lindqvist", "Moreau", "Castellano", "Brennan", "Haddad", "Kowalski",
    "Nakamura", "Ashworth", "Delgado", "Fairbanks", "Gallagher", "Holloway", "Iyer", "Jansen",
    "Kaur", "Larkin", "Mbeki", "Novak", "O'Donnell", "Pemberton", "Quintero", "Rasmussen",
    "Sokolov", "Thornbury", "Underwood", "Varga", "Wakefield", "Xu", "Yardley", "Zielinski",
    "Abernathy", "Blackwood", "Cromwell", "Dunmore", "Ellery", "Fenwick", "Garrow", "Hartley",
]
NAME_PREFIXES = [
    "Bright", "Blue", "North", "Clear", "Swift", "Silver", "Oak", "Pine", "Maple", "Iron",
    "Summit", "Harbor", "Nimbus", "Quartz", "Ember", "Lumen", "Vertex", "Cobalt", "Juniper",
    "Atlas", "Copper", "Meadow", "Orbit", "Prism", "Ridge", "Sable", "Tidal", "Umber", "Velvet",
]
NAME_STEMS = ["path", "stack", "wave", "forge", "leaf", "bridge", "point", "field", "works", "grid",
              "loop", "nest", "spring", "line", "mark", "gate", "scale", "sight"]
NAME_DESCRIPTORS = ["", "", "Analytics", "Labs", "Systems", "Software", "Health", "Logistics",
                    "Partners", "Group", "Digital", "Solutions", "Commerce"]
LEGAL_SUFFIXES = ["Inc", "LLC", "Ltd", "Corp", "", "", ""]

INDUSTRIES = {
    "SaaS": 18, "Software": 12, "Fintech": 8, "Cybersecurity": 6, "HR Tech": 4, "MarTech": 5,
    "E-commerce": 7, "Marketing Services": 6, "Healthcare": 7, "Manufacturing": 6,
    "Logistics": 5, "Education": 4, "Retail": 5, "Real Estate": 3, "Nonprofit": 2, "Hospitality": 2,
}
INDUSTRY_MESS = {
    "SaaS": ["saas", "SAAS", "Software as a Service"],
    "E-commerce": ["ecommerce", "E-Commerce", "e commerce"],
    "Cybersecurity": ["Cyber Security", "cybersecurity"],
    "HR Tech": ["hrtech", "HR tech"],
    "Nonprofit": ["Non-Profit", "non profit"],
}
TITLES = {
    "CEO": 4, "Co-Founder": 3, "Founder & CEO": 2, "Chief Marketing Officer": 3, "CMO": 2,
    "Chief Revenue Officer": 2, "CTO": 2, "VP of Marketing": 6, "VP Sales": 5,
    "Vice President, Growth": 2, "Head of Demand Generation": 4, "Head of Marketing": 5,
    "Director of Marketing": 6, "Sales Director": 4, "Director, Revenue Operations": 3,
    "Marketing Manager": 8, "Growth Marketing Manager": 4, "Sales Manager": 5,
    "Content Marketing Specialist": 4, "Account Executive": 5, "Marketing Coordinator": 4,
    "SDR": 3, "Marketing Assistant": 2, "Marketing Intern": 1, "Operations Analyst": 3,
}
COUNTRIES = {
    "United States": (48, ["USA", "US", "United States", "U.S.", "united states", "United States of America"]),
    "United Kingdom": (20, ["UK", "United Kingdom", "U.K.", "England", "Great Britain", "GB"]),
    "Canada": (8, ["Canada", "CA", "canada"]),
    "Germany": (7, ["Germany", "DE", "Deutschland"]),
    "Australia": (6, ["Australia", "AU", "Aus"]),
    "India": (5, ["India", "IN"]),
    "France": (6, ["France", "FR"]),
}
PLACES = {
    "United States": [("CA", "California", ["San Francisco", "Los Angeles", "San Diego"]),
                      ("NY", "New York", ["New York", "Brooklyn"]),
                      ("TX", "Texas", ["Austin", "Dallas", "Houston"]),
                      ("MA", "Massachusetts", ["Boston", "Cambridge"]),
                      ("IL", "Illinois", ["Chicago"]),
                      ("WA", "Washington", ["Seattle"]),
                      ("CO", "Colorado", ["Denver", "Boulder"]),
                      ("GA", "Georgia", ["Atlanta"])],
    "United Kingdom": [("", "Greater London", ["London"]), ("", "Greater Manchester", ["Manchester"]),
                       ("", "West Midlands", ["Birmingham"]), ("", "Scotland", ["Edinburgh", "Glasgow"]),
                       ("", "West Yorkshire", ["Leeds"]), ("", "Bristol", ["Bristol"])],
    "Canada": [("ON", "Ontario", ["Toronto", "Ottawa"]), ("BC", "British Columbia", ["Vancouver"]),
               ("QC", "Quebec", ["Montreal"])],
    "Germany": [("", "Berlin", ["Berlin"]), ("", "Bavaria", ["Munich"]), ("", "Hamburg", ["Hamburg"])],
    "Australia": [("NSW", "New South Wales", ["Sydney"]), ("VIC", "Victoria", ["Melbourne"])],
    "India": [("", "Karnataka", ["Bengaluru"]), ("", "Maharashtra", ["Mumbai", "Pune"])],
    "France": [("", "Île-de-France", ["Paris"]), ("", "Auvergne-Rhône-Alpes", ["Lyon"])],
}
LEAD_SOURCES = {"LinkedIn": 25, "Website Form": 20, "Webinar": 12, "Referral": 10,
                "Trade Show": 10, "Cold Outreach": 13, "Content Download": 10}
LEAD_SOURCE_MESS = {"LinkedIn": ["linkedin", "Linked In", "LINKEDIN"], "Website Form": ["web form", "website"],
                    "Trade Show": ["tradeshow", "Event"], "Cold Outreach": ["outbound"]}
FREE_MAIL = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.co.uk", "icloud.com"]
DATE_FORMATS = ["%Y-%m-%d", "%Y-%m-%d", "%m/%d/%Y", "%d %b %Y", "%b %d, %Y", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S"]


def pick(rng: random.Random, weighted: dict) -> str:
    keys = list(weighted)
    weights = [v[0] if isinstance(v, tuple) else v for v in weighted.values()]
    return rng.choices(keys, weights=weights)[0]


def make_companies(rng: random.Random, n: int) -> list[dict]:
    companies, used = [], set()
    while len(companies) < n:
        stem = rng.choice(NAME_PREFIXES) + rng.choice(NAME_STEMS)
        descriptor = rng.choice(NAME_DESCRIPTORS)
        base = f"{stem} {descriptor}".strip()
        if base in used:
            continue
        used.add(base)
        country = pick(rng, COUNTRIES)
        abbrev, region, cities = rng.choice(PLACES[country])
        size = int(rng.lognormvariate(4.6, 1.3))
        size = max(3, min(size, 20000))
        revenue = size * rng.uniform(60_000, 260_000)
        companies.append({
            "name": base,
            "suffix": rng.choice(LEGAL_SUFFIXES),
            "domain": (stem + ("-" + descriptor if descriptor and rng.random() < 0.4 else "")).lower() + ".example",
            "industry": pick(rng, INDUSTRIES),
            "employees": size,
            "revenue": revenue,
            "country": country,
            "region_abbrev": abbrev,
            "region": region,
            "city": rng.choice(cities),
        })
    return companies


def make_contacts(rng: random.Random, companies: list[dict], n: int) -> list[dict]:
    contacts, seen, emails = [], set(), set()
    start = date(2025, 1, 1)
    while len(contacts) < n:
        company = rng.choice(companies)
        first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
        if (company["domain"], first, last) in seen:
            continue
        seen.add((company["domain"], first, last))
        local_last = last.lower().replace("'", "")
        style = rng.random()
        if style < 0.08:
            email = f"{first.lower()}.{local_last}{rng.randint(1, 99)}@{rng.choice(FREE_MAIL)}"
        elif style < 0.6:
            email = f"{first.lower()}.{local_last}@{company['domain']}"
        elif style < 0.85:
            email = f"{first[0].lower()}{local_last}@{company['domain']}"
        else:
            email = f"{first.lower()}@{company['domain']}"
        if email in emails:  # two different people must never share an address
            email = f"{first.lower()}.{local_last}.{len(contacts)}@{company['domain']}"
        emails.add(email)
        contacts.append({
            **company,
            "first": first,
            "last": last,
            "title": pick(rng, TITLES),
            "email": email,
            "phone_n": rng.randint(0, 99),
            "source": pick(rng, LEAD_SOURCES),
            "created": start + timedelta(days=rng.randint(0, 600), seconds=rng.randint(0, 86399)),
        })
    return contacts


def mess_case(rng: random.Random, text: str, p: float = 0.12) -> str:
    r = rng.random()
    if r < p / 2:
        text = text.upper()
    elif r < p:
        text = text.lower()
    if rng.random() < 0.08:
        text = rng.choice(["  ", " ", ""]) + text + rng.choice(["  ", " "])
    return text


def render_company(rng: random.Random, c: dict) -> str:
    suffix = c["suffix"]
    if suffix and rng.random() < 0.5:
        suffix = rng.choice({"Inc": ["Inc.", ", Inc.", "inc", "Incorporated"], "LLC": ["L.L.C", ", LLC", "llc"],
                             "Ltd": ["Ltd.", "Limited", "LTD"], "Corp": ["Corp.", "Corporation"]}[suffix])
    name = c["name"] + ("" if not suffix else (suffix if suffix.startswith(",") else " " + suffix))
    return mess_case(rng, name)


def render_website(rng: random.Random, domain: str) -> str:
    return rng.choice([
        f"https://www.{domain}", f"http://{domain}/", f"www.{domain}", domain, f"https://{domain}/about",
        f"HTTPS://WWW.{domain.upper()}", f"https://www.{domain}/?utm_source=list",
    ])


def render_phone(rng: random.Random, c: dict) -> str:
    n = c["phone_n"]
    country = c["country"]
    if country == "United States":
        area = rng.choice(["415", "212", "512", "617", "312", "206", "303", "404"])
        return rng.choice([
            f"({area}) 555-01{n:02d}", f"{area}.555.01{n:02d}", f"+1 {area} 555 01{n:02d}",
            f"{area}55501{n:02d}", f"{area}-555-01{n:02d} x{rng.randint(10, 99)}", f"1-{area}-555-01{n:02d}",
        ])
    if country == "United Kingdom":
        return rng.choice([
            f"020 7946 0{n:03d}", f"+44 20 7946 0{n:03d}", f"+44 (0)20 7946 0{n:03d}",
            f"07700 900{n:03d}", f"+447700900{n:03d}",
        ])
    # Exactly two randint draws and one 3-way choice, as in earlier versions, so the random
    # stream (and therefore every other field in the sample) stays the same.
    a, b = rng.randint(100, 999), rng.randint(1000, 9999)
    if country == "Canada":
        area, line = ("416", "604", "514")[a % 3], f"01{n:02d}"
        formats = [f"+1 {area} 555 {line}", f"({area}) 555-{line}", f"{area}.555.{line}"]
    elif country == "Germany":
        formats = [f"+49 30 {a} {b}", f"030 {a}{b}", f"+49 (0)30 {a}{b}"]
    elif country == "France":
        pair1, pair2 = f"{b // 100:02d}", f"{b % 100:02d}"
        formats = [f"+33 1 99 00 {pair1} {pair2}", f"01 99 00 {pair1} {pair2}", f"+33 (0)1 99 00 {pair1}{pair2}"]
    elif country == "Australia":
        formats = [f"+61 2 5550 {b}", f"(02) 5550 {b}", f"02 5550 {b}"]
    else:  # India: 10-digit mobile
        num = f"9{a}{b}{n:02d}"
        formats = [f"+91 {num[:5]} {num[5:]}", f"0{num[:5]} {num[5:]}", f"+91-{num[:5]}-{num[5:]}"]
    return rng.choice(formats)


PHONE_NOISE_RATE = 0.08


def garble_phone(noise: random.Random, phone: str) -> str:
    """Make a phone number unreadable the way real lists do: cut off, or junk text."""
    r = noise.random()
    if r < 0.6:
        chars, dropped = list(phone), 0
        for i in range(len(chars) - 1, -1, -1):  # drop the last three digits
            if chars[i].isdigit() and dropped < 3:
                chars[i], dropped = "", dropped + 1
        return "".join(chars).rstrip(" -.x")
    return noise.choice(["TBD", "123", "see notes", "ask reception"])


def render_employees(rng: random.Random, n: int) -> str:
    r = rng.random()
    if r < 0.45:
        return str(n)
    if r < 0.6:
        low = max(1, round(n * 0.6, -1) or 1)
        return f"{int(low)}-{int(round(n * 1.4, -1)) or n + 10}"
    if r < 0.68 and n >= 1000:
        return f"~{n / 1000:.0f}k"
    if r < 0.76:
        return f"{n:,}"
    if r < 0.82:
        return f"{int(round(n, -1))}+"
    if r < 0.88:
        return f"approx. {n}"
    return rng.choice(["", "", "unknown"])


def render_revenue(rng: random.Random, amount: float, country: str) -> str:
    symbol = "£" if country == "United Kingdom" else ("€" if country in ("Germany", "France") else "$")
    r = rng.random()
    if amount >= 1e6:
        millions = amount / 1e6
        short = f"{millions:.1f}".rstrip("0").rstrip(".")
        if r < 0.3:
            return f"{symbol}{short}M"
        if r < 0.45:
            return f"{symbol}{int(round(amount, -5)):,}"
        if r < 0.6:
            return str(int(round(amount, -5)))
        if r < 0.7:
            return f"USD {short} million"
        if r < 0.8:
            return f"{short}m"
    elif r < 0.7:
        return f"{symbol}{amount / 1e3:.0f}K"
    return rng.choice(["", "", "n/a", "undisclosed"])


def render(rng: random.Random, noise: random.Random, c: dict, variant: str = "normal") -> dict:
    """Turn a clean contact into a messy CSV row. `noise` drives only the unreadable phones."""
    country_text = rng.choice(COUNTRIES[c["country"]][1])
    region = c["region_abbrev"] if c["region_abbrev"] and rng.random() < 0.6 else c["region"]
    industry = c["industry"]
    if industry in INDUSTRY_MESS and rng.random() < 0.4:
        industry = rng.choice(INDUSTRY_MESS[industry])
    source = c["source"]
    if source in LEAD_SOURCE_MESS and rng.random() < 0.3:
        source = rng.choice(LEAD_SOURCE_MESS[source])
    email = c["email"]
    if rng.random() < 0.1:
        email = email.upper() if rng.random() < 0.5 else email.capitalize()
    if rng.random() < 0.05:
        email = rng.choice([f" {email} ", f"mailto:{email}", f"<{email}>"])

    row = {
        "company_name": render_company(rng, c),
        "website": render_website(rng, c["domain"]) if rng.random() > 0.12 else "",
        "contact_first_name": mess_case(rng, c["first"]),
        "contact_last_name": mess_case(rng, c["last"]),
        "contact_title": mess_case(rng, c["title"]) if rng.random() > 0.05 else "",
        "email": email,
        # Five choices (as before) keeps the random stream aligned; junk values now come from garble_phone.
        "phone": render_phone(rng, c) if rng.random() > 0.1 else rng.choice(["", "", "", "n/a", "N/A"]),
        "industry": mess_case(rng, industry) if rng.random() > 0.06 else "",
        "employee_count": render_employees(rng, c["employees"]),
        "annual_revenue": render_revenue(rng, c["revenue"], c["country"]),
        "country": country_text if rng.random() > 0.04 else "",
        "state_region": mess_case(rng, region),
        "city": mess_case(rng, c["city"]),
        "lead_source": source if rng.random() > 0.05 else "",
        "created_date": c["created"].strftime(rng.choice(DATE_FORMATS)) if rng.random() > 0.04 else "",
    }

    if variant == "partial":
        # A thinner copy of the same person, e.g. from a different list export.
        for field in rng.sample(["phone", "industry", "employee_count", "annual_revenue", "contact_title",
                                 "website", "state_region", "city"], k=rng.randint(2, 5)):
            row[field] = ""
    elif variant == "other_email":
        # Same person, different email: must be matched on company domain + name.
        local = f"{c['first']}.{c['last']}".lower().replace("'", "")
        row["email"] = f"{local}{rng.randint(1, 99)}@{rng.choice(FREE_MAIL)}"
        row["website"] = render_website(rng, c["domain"])

    if row["phone"] not in ("", "n/a", "N/A") and noise.random() < PHONE_NOISE_RATE:
        row["phone"] = garble_phone(noise, row["phone"])
    return row


def break_row(rng: random.Random, row: dict) -> dict:
    """Inject problems that should get a lead rejected."""
    if rng.random() < 0.65:
        local = row["email"].strip().split("@")[0] or "contact"
        row["email"] = rng.choice([
            f"{local}@", f"{local} at gmail", f"{local}@@mail.example", f"{local}@company",
            f"{local}.example", "", "unknown",
        ])
    else:
        row["company_name"] = rng.choice(["", " ", "N/A"])
    return row


def generate(rows: int = 500, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    noise = random.Random(f"{seed}-phone-noise")
    n_dupes = round(rows * 0.12)
    n_unique = rows - n_dupes
    companies = make_companies(rng, max(20, n_unique // 2))
    contacts = make_contacts(rng, companies, n_unique)

    out = [render(rng, noise, c) for c in contacts]
    for i in rng.sample(range(len(out)), k=round(n_unique * 0.05)):
        out[i] = break_row(rng, out[i])

    dup_sources = rng.sample(contacts, k=n_dupes)
    for i, c in enumerate(dup_sources):
        r = i / n_dupes
        if r < 0.25:
            out.append(dict(out[contacts.index(c)]))  # exact copy
        elif r < 0.7:
            out.append(render(rng, noise, c, "partial"))
        else:
            out.append(render(rng, noise, c, "other_email"))
    rng.shuffle(out)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--rows", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", default=str(Path(__file__).resolve().parents[1] / "data" / "raw" / "sample_leads.csv"))
    args = parser.parse_args()

    rows = generate(args.rows, args.seed)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} synthetic leads to {out}")


if __name__ == "__main__":
    main()
