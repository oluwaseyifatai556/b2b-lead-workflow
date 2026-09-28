"""Data-hygiene reference tables used by the cleaner.

These describe how messy values map to standard spellings. They are NOT targeting rules:
which industries, countries or titles a client wants lives in icp.yaml.
"""

# Incoming header spellings (lowercased, non-alphanumerics collapsed to "_") -> standard column.
HEADER_ALIASES: dict[str, str] = {
    "company": "company_name",
    "company_name": "company_name",
    "organization": "company_name",
    "account_name": "company_name",
    "website": "website",
    "url": "website",
    "company_website": "website",
    "domain": "website",
    "first_name": "contact_first_name",
    "firstname": "contact_first_name",
    "contact_first_name": "contact_first_name",
    "last_name": "contact_last_name",
    "lastname": "contact_last_name",
    "surname": "contact_last_name",
    "contact_last_name": "contact_last_name",
    "title": "contact_title",
    "job_title": "contact_title",
    "contact_title": "contact_title",
    "email": "email",
    "email_address": "email",
    "e_mail": "email",
    "phone": "phone",
    "phone_number": "phone",
    "telephone": "phone",
    "industry": "industry",
    "employees": "employee_count",
    "employee_count": "employee_count",
    "company_size": "employee_count",
    "headcount": "employee_count",
    "revenue": "annual_revenue",
    "annual_revenue": "annual_revenue",
    "country": "country",
    "state": "state_region",
    "region": "state_region",
    "state_region": "state_region",
    "county": "state_region",
    "city": "city",
    "lead_source": "lead_source",
    "source": "lead_source",
    "created_date": "created_date",
    "created": "created_date",
    "date_added": "created_date",
}

# Plain-English names for lead fields, used in reports and in the missing_fields column.
FIELD_LABELS: dict[str, str] = {
    "company_name": "Company",
    "website": "Website",
    "domain": "Website",
    "contact_first_name": "First name",
    "contact_last_name": "Last name",
    "full_name": "Contact",
    "contact_title": "Job title",
    "email": "Email",
    "email_valid": "Valid email?",
    "email_is_free": "Personal email?",
    "phone": "Phone",
    "industry": "Industry",
    "employee_count": "Employees",
    "annual_revenue": "Annual revenue",
    "country": "Country",
    "state_region": "State / region",
    "city": "City",
    "lead_source": "Lead source",
    "created_date": "Date added",
}

COUNTRY_ALIASES: dict[str, str] = {
    "us": "United States",
    "u.s.": "United States",
    "u.s.a.": "United States",
    "usa": "United States",
    "united states": "United States",
    "united states of america": "United States",
    "america": "United States",
    "uk": "United Kingdom",
    "u.k.": "United Kingdom",
    "gb": "United Kingdom",
    "great britain": "United Kingdom",
    "united kingdom": "United Kingdom",
    "england": "United Kingdom",
    "scotland": "United Kingdom",
    "wales": "United Kingdom",
    "ca": "Canada",
    "can": "Canada",
    "canada": "Canada",
    "de": "Germany",
    "deutschland": "Germany",
    "germany": "Germany",
    "au": "Australia",
    "aus": "Australia",
    "australia": "Australia",
    "in": "India",
    "ind": "India",
    "india": "India",
    "fr": "France",
    "france": "France",
    "ie": "Ireland",
    "ireland": "Ireland",
    "nl": "Netherlands",
    "netherlands": "Netherlands",
    "the netherlands": "Netherlands",
}

# International dialling codes, used to normalize phone numbers written without one.
COUNTRY_DIAL_CODES: dict[str, str] = {
    "United States": "1",
    "Canada": "1",
    "United Kingdom": "44",
    "Germany": "49",
    "Australia": "61",
    "India": "91",
    "France": "33",
    "Ireland": "353",
    "Netherlands": "31",
}

# Allowed length of the national number (digits after the country code, without a leading 0)
# per dialling code. Numbers outside the range can't be complete and are treated as unreadable.
# German numbers genuinely vary in length; 8-11 covers normal landlines and mobiles.
PHONE_NATIONAL_DIGITS: dict[str, tuple[int, int]] = {
    "1": (10, 10),    # US, Canada
    "44": (9, 10),    # UK
    "49": (8, 11),    # Germany
    "61": (9, 9),     # Australia
    "91": (10, 10),   # India
    "33": (9, 9),     # France
    "353": (7, 9),    # Ireland
    "31": (9, 9),     # Netherlands
}
# E.164 limits, used when the country code isn't one we know.
PHONE_ANY_DIGITS = (8, 15)

# Free / personal mailbox providers. A lead on one of these is not a company address.
FREE_EMAIL_DOMAINS: frozenset[str] = frozenset(
    {
        "gmail.com",
        "googlemail.com",
        "yahoo.com",
        "yahoo.co.uk",
        "hotmail.com",
        "hotmail.co.uk",
        "outlook.com",
        "live.com",
        "msn.com",
        "aol.com",
        "icloud.com",
        "me.com",
        "proton.me",
        "protonmail.com",
        "gmx.com",
        "gmx.de",
        "mail.com",
        "zoho.com",
        "yandex.com",
    }
)

# Standard spellings for industry labels (keyed by lowercase).
INDUSTRY_CANONICAL: dict[str, str] = {
    label.lower(): label
    for label in [
        "SaaS",
        "Software",
        "Fintech",
        "Cybersecurity",
        "HR Tech",
        "MarTech",
        "E-commerce",
        "Marketing Services",
        "Healthcare",
        "Manufacturing",
        "Logistics",
        "Education",
        "Retail",
        "Real Estate",
        "Nonprofit",
        "Hospitality",
    ]
}
INDUSTRY_CANONICAL.update(
    {
        "software as a service": "SaaS",
        "ecommerce": "E-commerce",
        "e commerce": "E-commerce",
        "cyber security": "Cybersecurity",
        "hrtech": "HR Tech",
        "martech": "MarTech",
        "non-profit": "Nonprofit",
        "non profit": "Nonprofit",
    }
)

LEAD_SOURCE_CANONICAL: dict[str, str] = {
    label.lower(): label
    for label in [
        "LinkedIn",
        "Website Form",
        "Webinar",
        "Referral",
        "Trade Show",
        "Cold Outreach",
        "Content Download",
    ]
}
LEAD_SOURCE_CANONICAL.update(
    {
        "linked in": "LinkedIn",
        "web form": "Website Form",
        "website": "Website Form",
        "tradeshow": "Trade Show",
        "event": "Trade Show",
        "outbound": "Cold Outreach",
        "ebook": "Content Download",
    }
)

# Words kept in a fixed case when tidying ALL-CAPS / all-lowercase text.
FIXED_CASE_WORDS: dict[str, str] = {
    w.lower(): w
    for w in [
        "VP", "SVP", "EVP", "SDR", "BDR", "CEO", "CFO", "COO", "CTO", "CMO", "CRO", "CIO", "CISO",
        "IT", "HR", "UK", "US", "USA", "B2B", "SaaS", "GmbH", "PLC", "LLC", "LLP",
        "of", "and", "the", "for",
    ]
}

COMPANY_SUFFIXES: dict[str, str] = {
    "inc": "Inc",
    "incorporated": "Inc",
    "llc": "LLC",
    "l.l.c": "LLC",
    "ltd": "Ltd",
    "limited": "Ltd",
    "corp": "Corp",
    "corporation": "Corp",
    "co": "Co",
    "plc": "PLC",
    "gmbh": "GmbH",
    "llp": "LLP",
}
