from __future__ import annotations

import argparse
import json
import random
import string
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable, Iterator, Sequence

import duckdb
import pandas as pd


@dataclass(frozen=True)
class GenerationProfile:
    customers: int
    accounts: int
    merchants: int
    transactions: int
    customer_changes: int
    patients: int
    providers: int
    visits: int
    patient_changes: int
    tickers: int
    market_years: int
    ticker_changes: int


SIZE_PROFILES = {
    "small": GenerationProfile(
        customers=1_200,
        accounts=1_900,
        merchants=300,
        transactions=35_000,
        customer_changes=1_200,
        patients=900,
        providers=90,
        visits=18_000,
        patient_changes=500,
        tickers=45,
        market_years=2,
        ticker_changes=40,
    ),
    "challenge": GenerationProfile(
        customers=4_000,
        accounts=6_800,
        merchants=950,
        transactions=180_000,
        customer_changes=6_500,
        patients=3_300,
        providers=220,
        visits=85_000,
        patient_changes=2_800,
        tickers=180,
        market_years=3,
        ticker_changes=160,
    ),
    "large": GenerationProfile(
        customers=9_000,
        accounts=15_000,
        merchants=2_200,
        transactions=520_000,
        customer_changes=16_000,
        patients=7_200,
        providers=480,
        visits=250_000,
        patient_changes=8_500,
        tickers=420,
        market_years=5,
        ticker_changes=500,
    ),
}


US_LOCALES = [
    {"state": "CA", "city": "San Francisco", "region": "West"},
    {"state": "WA", "city": "Seattle", "region": "West"},
    {"state": "CO", "city": "Denver", "region": "Mountain"},
    {"state": "TX", "city": "Austin", "region": "South"},
    {"state": "IL", "city": "Chicago", "region": "Midwest"},
    {"state": "GA", "city": "Atlanta", "region": "South"},
    {"state": "FL", "city": "Miami", "region": "South"},
    {"state": "NC", "city": "Charlotte", "region": "South"},
    {"state": "MA", "city": "Boston", "region": "Northeast"},
    {"state": "PA", "city": "Philadelphia", "region": "Northeast"},
    {"state": "NY", "city": "New York", "region": "Northeast"},
    {"state": "OH", "city": "Columbus", "region": "Midwest"},
    {"state": "AZ", "city": "Phoenix", "region": "West"},
    {"state": "MN", "city": "Minneapolis", "region": "Midwest"},
    {"state": "TN", "city": "Nashville", "region": "South"},
]

FIRST_NAMES = [
    "Ava",
    "Noah",
    "Liam",
    "Sophia",
    "Mia",
    "Olivia",
    "Lucas",
    "Emma",
    "Isabella",
    "Ethan",
    "Mateo",
    "Amelia",
    "Harper",
    "Elijah",
    "Charlotte",
    "Benjamin",
    "Sofia",
    "Daniel",
    "James",
    "Evelyn",
    "Mason",
    "Layla",
    "Logan",
    "Avery",
]

LAST_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Garcia",
    "Miller",
    "Davis",
    "Wilson",
    "Anderson",
    "Taylor",
    "Thomas",
    "Moore",
    "Martin",
    "Jackson",
    "Thompson",
    "White",
    "Lopez",
    "Lee",
    "Harris",
]

CUSTOMER_SEGMENTS = [
    "mass_market",
    "affluent",
    "high_net_worth",
    "young_professional",
    "small_business_owner",
    "retiree",
]

RISK_BANDS = ["low", "medium", "elevated", "high", "watchlist"]
MARKETING_TIERS = ["bronze", "silver", "gold", "platinum"]
ACQUISITION_CHANNELS = ["organic", "referral", "paid_search", "partner", "event"]
LIFECYCLE_STAGES = ["prospect", "active", "retained", "expansion", "at_risk"]
ACCOUNT_TYPES = ["consumer_credit", "travel_rewards", "cashback", "business_credit"]
ACCOUNT_STATUSES = ["active", "active", "active", "delinquent", "closed"]

MERCHANT_CATEGORIES = [
    ("grocery", "5411"),
    ("travel", "3000"),
    ("airlines", "4511"),
    ("dining", "5812"),
    ("electronics", "5732"),
    ("healthcare", "8099"),
    ("streaming", "4899"),
    ("gas", "5541"),
    ("retail", "5311"),
    ("home_improvement", "5200"),
    ("insurance", "6300"),
    ("transport", "4121"),
]

PROVIDER_SPECIALTIES = [
    ("Primary Care", "Clinic"),
    ("Cardiology", "Hospital"),
    ("Oncology", "Hospital"),
    ("Orthopedics", "Medical Center"),
    ("Behavioral Health", "Specialty Center"),
    ("Endocrinology", "Clinic"),
    ("Urgent Care", "Urgent Care"),
    ("Dermatology", "Clinic"),
    ("Neurology", "Hospital"),
    ("Pulmonology", "Medical Center"),
    ("Gastroenterology", "Clinic"),
]

DIAGNOSES = [
    ("E11.9", "Endocrine", "Type 2 diabetes without complications", True, "medium"),
    ("I10", "Cardiovascular", "Essential primary hypertension", True, "medium"),
    ("J06.9", "Respiratory", "Acute upper respiratory infection", False, "low"),
    ("M54.5", "Musculoskeletal", "Low back pain", False, "low"),
    ("F41.1", "Behavioral Health", "Generalized anxiety disorder", True, "medium"),
    ("E78.5", "Endocrine", "Hyperlipidemia", True, "medium"),
    ("K21.9", "Digestive", "Gastro-esophageal reflux disease", False, "low"),
    ("J45.909", "Respiratory", "Unspecified asthma", True, "medium"),
    ("N39.0", "Genitourinary", "Urinary tract infection", False, "low"),
    ("R07.9", "Cardiovascular", "Chest pain", False, "high"),
    ("S93.4", "Injury", "Sprain of ankle", False, "low"),
    ("C50.919", "Oncology", "Malignant neoplasm of breast", True, "high"),
    ("G43.909", "Neurology", "Migraine", True, "medium"),
    ("L20.9", "Dermatology", "Atopic dermatitis", True, "low"),
    ("R10.9", "Digestive", "Abdominal pain", False, "medium"),
    ("I25.10", "Cardiovascular", "Coronary artery disease", True, "high"),
    ("M17.9", "Musculoskeletal", "Osteoarthritis of knee", True, "medium"),
    ("F33.1", "Behavioral Health", "Major depressive disorder", True, "high"),
    ("Z00.00", "Preventive", "Adult general examination", False, "low"),
    ("R51.9", "Neurology", "Headache", False, "low"),
]

SECTOR_INDUSTRY = {
    "Technology": ["Software", "Semiconductors", "Cloud Infrastructure"],
    "Healthcare": ["Biotech", "Medical Devices", "Healthcare Services"],
    "Financials": ["Payments", "Insurance", "Asset Management"],
    "Consumer": ["Retail", "Travel", "Entertainment"],
    "Energy": ["Oil & Gas", "Renewables", "Utilities"],
    "Industrials": ["Logistics", "Aerospace", "Manufacturing"],
    "Communication": ["Telecom", "Media", "Digital Platforms"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic DuckDB challenge datasets.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("datasets"),
        help="Directory where the DuckDB files will be written.",
    )
    parser.add_argument(
        "--profile",
        choices=sorted(SIZE_PROFILES),
        default="challenge",
        help="Predefined dataset size profile.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed used for deterministic data generation.",
    )
    return parser.parse_args()


def random_date(rand: random.Random, start: date, end: date) -> date:
    delta_days = (end - start).days
    return start + timedelta(days=rand.randint(0, delta_days))


def random_datetime(rand: random.Random, start: datetime, end: datetime) -> datetime:
    delta_seconds = int((end - start).total_seconds())
    return start + timedelta(seconds=rand.randint(0, max(delta_seconds, 1)))


def business_days(start: date, end: date) -> Iterator[date]:
    current_day = start
    while current_day <= end:
        if current_day.weekday() < 5:
            yield current_day
        current_day += timedelta(days=1)


def postal_code(rand: random.Random) -> str:
    return f"{rand.randint(10000, 99999)}"


def phone_number(rand: random.Random) -> str:
    return f"+1-{rand.randint(200, 989)}-{rand.randint(100, 999)}-{rand.randint(1000, 9999)}"


def fake_email(first_name: str, last_name: str, suffix: int) -> str:
    local_part = f"{first_name}.{last_name}.{suffix}".lower()
    return f"{local_part}@example.com"


def choose_locale(rand: random.Random) -> dict[str, str]:
    return rand.choice(US_LOCALES)


def round_currency(amount: float) -> float:
    return round(amount + 1e-9, 2)


def insert_rows(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    columns: Sequence[str],
    rows: Iterable[Sequence[object]],
    batch_size: int = 25_000,
) -> None:
    batch: list[Sequence[object]] = []
    conn.execute("BEGIN")
    try:
        for row in rows:
            batch.append(row)
            if len(batch) >= batch_size:
                conn.append(table_name, pd.DataFrame.from_records(batch, columns=columns))
                batch.clear()
        if batch:
            conn.append(table_name, pd.DataFrame.from_records(batch, columns=columns))
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


def count_rows(conn: duckdb.DuckDBPyConnection, table_name: str) -> int:
    return conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]


def ticker_symbol(index: int) -> str:
    alphabet = string.ascii_uppercase
    value = index
    chars = []
    for _ in range(4):
        chars.append(alphabet[value % 26])
        value //= 26
    return "".join(reversed(chars))


def generate_master_customers(profile: GenerationProfile, rand: random.Random) -> list[dict[str, object]]:
    customers: list[dict[str, object]] = []
    start_birth = date(1945, 1, 1)
    end_birth = date(2004, 12, 31)
    join_start = datetime(2020, 1, 1, 8, 0, 0)
    join_end = datetime(2025, 4, 30, 17, 0, 0)
    for index in range(profile.customers):
        first_name = rand.choice(FIRST_NAMES)
        last_name = rand.choice(LAST_NAMES)
        locale = choose_locale(rand)
        annual_income = rand.randint(38_000, 240_000)
        risk_band = rand.choices(RISK_BANDS, weights=[35, 28, 20, 12, 5], k=1)[0]
        customer = {
            "customer_id": f"CUST{index + 1:06d}",
            "first_name": first_name,
            "last_name": last_name,
            "full_name": f"{first_name} {last_name}",
            "email": fake_email(first_name, last_name, index + 1),
            "phone": phone_number(rand),
            "address_line1": f"{rand.randint(100, 9899)} {last_name} Street",
            "city": locale["city"],
            "state": locale["state"],
            "postal_code": postal_code(rand),
            "country_code": "US",
            "birth_date": random_date(rand, start_birth, end_birth),
            "joined_at": random_datetime(rand, join_start, join_end),
            "segment": rand.choices(CUSTOMER_SEGMENTS, weights=[30, 20, 8, 22, 10, 10], k=1)[0],
            "risk_band": risk_band,
            "marketing_tier": rand.choices(MARKETING_TIERS, weights=[25, 35, 25, 15], k=1)[0],
            "acquisition_channel": rand.choice(ACQUISITION_CHANNELS),
            "lifecycle_stage": rand.choices(LIFECYCLE_STAGES, weights=[10, 42, 24, 12, 12], k=1)[0],
            "preferred_language": rand.choices(["en", "es", "pt", "fr"], weights=[72, 18, 6, 4], k=1)[0],
            "household_income_band": (
                "40k_75k"
                if annual_income < 75_000
                else "75k_125k"
                if annual_income < 125_000
                else "125k_200k"
                if annual_income < 200_000
                else "200k_plus"
            ),
            "annual_income": annual_income,
        }
        customers.append(customer)
    return customers


def generate_accounts(
    customers: list[dict[str, object]],
    target_count: int,
    rand: random.Random,
) -> list[dict[str, object]]:
    accounts: list[dict[str, object]] = []
    account_index = 1
    customer_pool = customers[:]
    rand.shuffle(customer_pool)
    while len(accounts) < target_count:
        customer = customer_pool[len(accounts) % len(customer_pool)]
        segment = customer["segment"]
        risk_band = customer["risk_band"]
        multiplier = 1.8 if segment == "high_net_worth" else 1.4 if segment == "affluent" else 1.0
        risk_modifier = 0.7 if risk_band in {"high", "watchlist"} else 1.0
        credit_limit = int(rand.randint(1_500, 18_000) * multiplier * risk_modifier)
        current_balance = round_currency(rand.uniform(0, credit_limit * 0.95))
        opened_at = customer["joined_at"] + timedelta(days=rand.randint(0, 900))
        accounts.append(
            {
                "account_id": f"ACC{account_index:07d}",
                "customer_id": customer["customer_id"],
                "opened_at": opened_at,
                "account_type": rand.choices(ACCOUNT_TYPES, weights=[50, 20, 20, 10], k=1)[0],
                "account_status": rand.choices(ACCOUNT_STATUSES, weights=[75, 0, 0, 15, 10], k=1)[0],
                "credit_limit": credit_limit,
                "current_balance": current_balance,
                "utilization_ratio": round(current_balance / credit_limit, 4),
                "currency_code": "USD",
                "autopay_enabled": rand.random() < 0.68,
                "card_number": f"{rand.randint(4000, 4999)}{rand.randint(1000, 9999)}{rand.randint(1000, 9999)}{rand.randint(1000, 9999)}",
                "expiry_month": rand.randint(1, 12),
                "expiry_year": rand.randint(2026, 2032),
            }
        )
        account_index += 1
    return accounts


def generate_merchants(count: int, rand: random.Random) -> list[dict[str, object]]:
    name_prefixes = [
        "Atlas",
        "Northstar",
        "Blue Harbor",
        "Granite",
        "Silverline",
        "Peak",
        "Urban",
        "Summit",
        "Nova",
        "Crescent",
        "Lighthouse",
        "Bridge",
    ]
    merchants: list[dict[str, object]] = []
    for index in range(count):
        category, mcc = rand.choice(MERCHANT_CATEGORIES)
        locale = choose_locale(rand)
        merchants.append(
            {
                "merchant_id": f"MER{index + 1:06d}",
                "merchant_name": f"{rand.choice(name_prefixes)} {category.replace('_', ' ').title()} {index + 1}",
                "merchant_category": category,
                "mcc": mcc,
                "city": locale["city"],
                "state": locale["state"],
                "country_code": "US",
                "risk_level": rand.choices(["low", "medium", "high"], weights=[55, 35, 10], k=1)[0],
            }
        )
    return merchants


def transaction_amount(rand: random.Random, merchant_category: str) -> float:
    multiplier = {
        "airlines": 7.5,
        "travel": 5.0,
        "electronics": 3.8,
        "healthcare": 4.2,
        "insurance": 6.0,
        "home_improvement": 3.4,
    }.get(merchant_category, 1.0)
    base_value = rand.gammavariate(2.0, 42.0) * multiplier
    return round_currency(min(base_value, 18_000.0))


def generate_customer_change_log(
    customers: list[dict[str, object]],
    target_count: int,
    rand: random.Random,
) -> Iterator[Sequence[object]]:
    change_start = datetime(2023, 1, 1, 9, 0, 0)
    change_end = datetime(2026, 4, 30, 18, 0, 0)
    operations = ["UPDATE", "UPDATE", "UPDATE", "DELETE"]
    for index in range(target_count):
        customer = rand.choice(customers)
        operation = rand.choice(operations)
        payload = {
            "segment": rand.choice(CUSTOMER_SEGMENTS),
            "state": rand.choice(US_LOCALES)["state"],
            "risk_band": rand.choice(RISK_BANDS),
            "email_opt_in": rand.random() < 0.72,
            "sms_opt_in": rand.random() < 0.51,
        }
        if operation == "DELETE":
            payload = {"deleted_reason": rand.choice(["fraud", "requested", "inactive"])}
        yield (
            f"CCHG{index + 1:07d}",
            customer["customer_id"],
            operation,
            random_datetime(rand, change_start, change_end),
            json.dumps(payload, sort_keys=True),
        )


def generate_transaction_rows(
    accounts: list[dict[str, object]],
    customers_by_id: dict[str, dict[str, object]],
    merchants: list[dict[str, object]],
    target_count: int,
    rand: random.Random,
) -> Iterator[Sequence[object]]:
    start = datetime(2024, 1, 1, 0, 0, 0)
    end = datetime(2026, 4, 30, 23, 59, 0)
    duplicate_indices = set(rand.sample(range(target_count), max(25, target_count // 1_200)))
    outlier_indices = set(rand.sample(range(target_count), max(10, target_count // 18_000)))
    for index in range(target_count):
        account = rand.choice(accounts)
        customer = customers_by_id[account["customer_id"]]
        merchant = rand.choice(merchants)
        posted_at = random_datetime(rand, start, end)
        transaction_kind = rand.choices(
            ["purchase", "refund", "dispute", "cash_advance"],
            weights=[90, 5, 2, 3],
            k=1,
        )[0]
        amount = transaction_amount(rand, merchant["merchant_category"])
        if index in outlier_indices:
            amount = round_currency(rand.uniform(120_000.0, 240_000.0))
        if transaction_kind in {"refund", "dispute"}:
            amount *= -1
        state = merchant["state"] if rand.random() < 0.92 else customer["state"]
        running_balance = round_currency(
            min(account["credit_limit"], max(0.0, account["current_balance"] + amount * 0.15))
        )
        row = (
            f"TXN{index + 1:09d}",
            account["account_id"],
            customer["customer_id"],
            merchant["merchant_id"],
            posted_at,
            posted_at + timedelta(hours=rand.randint(1, 72)),
            amount,
            "USD",
            transaction_kind,
            rand.choices(["card_present", "card_not_present", "wallet"], weights=[40, 45, 15], k=1)[0],
            rand.random() < 0.37,
            merchant["merchant_category"],
            "US",
            state,
            transaction_kind == "refund",
            transaction_kind == "dispute",
            rand.choices(["settled", "pending", "reversed"], weights=[86, 10, 4], k=1)[0],
            running_balance,
        )
        yield row
        if index in duplicate_indices:
            yield row


def generate_patients(
    customers: list[dict[str, object]],
    target_count: int,
    rand: random.Random,
) -> list[dict[str, object]]:
    patients: list[dict[str, object]] = []
    linked_customers = customers[:]
    rand.shuffle(linked_customers)
    created_start = datetime(2021, 1, 1, 8, 0, 0)
    created_end = datetime(2025, 4, 30, 17, 0, 0)
    for index in range(target_count):
        if index < len(linked_customers) and rand.random() < 0.82:
            customer = linked_customers[index]
            full_name = customer["full_name"]
            email = customer["email"]
            phone = customer["phone"]
            address_line1 = customer["address_line1"]
            city = customer["city"]
            state = customer["state"]
            postal = customer["postal_code"]
            birth_date = customer["birth_date"]
            linked_customer_id = customer["customer_id"]
        else:
            first_name = rand.choice(FIRST_NAMES)
            last_name = rand.choice(LAST_NAMES)
            locale = choose_locale(rand)
            full_name = f"{first_name} {last_name}"
            email = fake_email(first_name, last_name, 100_000 + index)
            phone = phone_number(rand)
            address_line1 = f"{rand.randint(100, 9899)} Care Avenue"
            city = locale["city"]
            state = locale["state"]
            postal = postal_code(rand)
            birth_date = random_date(rand, date(1940, 1, 1), date(2020, 12, 31))
            linked_customer_id = None
        patients.append(
            {
                "patient_id": f"PAT{index + 1:06d}",
                "customer_id": linked_customer_id,
                "patient_name": full_name,
                "email": email,
                "phone": phone,
                "address_line1": address_line1,
                "city": city,
                "state": state,
                "postal_code": postal,
                "insurance_member_id": f"INS{rand.randint(100000000, 999999999)}",
                "birth_date": birth_date,
                "gender": rand.choice(["F", "M", "X"]),
                "chronic_condition_count": rand.choices([0, 1, 2, 3, 4], weights=[35, 28, 18, 12, 7], k=1)[0],
                "risk_score": round(rand.uniform(0.03, 0.98), 4),
                "created_at": random_datetime(rand, created_start, created_end),
            }
        )
    return patients


def generate_providers(count: int, rand: random.Random) -> list[dict[str, object]]:
    providers: list[dict[str, object]] = []
    for index in range(count):
        specialty, facility_type = rand.choice(PROVIDER_SPECIALTIES)
        locale = choose_locale(rand)
        providers.append(
            {
                "provider_id": f"PRV{index + 1:05d}",
                "provider_name": f"{specialty} Group {index + 1}",
                "specialty": specialty,
                "facility_name": f"{locale['city']} {facility_type} {index % 13 + 1}",
                "city": locale["city"],
                "state": locale["state"],
                "region": locale["region"],
                "npi": f"{rand.randint(1000000000, 9999999999)}",
                "network_status": rand.choices(["in_network", "out_of_network"], weights=[83, 17], k=1)[0],
            }
        )
    return providers


def generate_medical_visit_rows(
    patients: list[dict[str, object]],
    providers: list[dict[str, object]],
    rand: random.Random,
    target_count: int,
) -> Iterator[Sequence[object]]:
    start = datetime(2024, 1, 1, 7, 0, 0)
    end = datetime(2026, 4, 30, 19, 0, 0)
    diagnoses = DIAGNOSES[:]
    visit_types = ["outpatient", "inpatient", "telehealth", "emergency"]
    outcomes = ["discharged", "referred", "admitted", "follow_up"]
    severity_multiplier = {"low": 0.9, "medium": 1.6, "high": 3.2}
    for index in range(target_count):
        patient = rand.choice(patients)
        provider = rand.choice(providers)
        diagnosis = rand.choice(diagnoses)
        visit_at = random_datetime(rand, start, end)
        base_claim = rand.gammavariate(2.2, 180.0) * severity_multiplier[diagnosis[4]]
        if diagnosis[1] == "Oncology":
            base_claim *= 4.2
        if provider["specialty"] in {"Cardiology", "Neurology", "Oncology"}:
            base_claim *= 1.7
        claim_amount = round_currency(min(base_claim, 42_000.0))
        paid_amount = round_currency(claim_amount * rand.uniform(0.62, 0.96))
        visit_type = rand.choices(visit_types, weights=[55, 10, 20, 15], k=1)[0]
        row = (
            f"VIS{index + 1:08d}",
            patient["patient_id"],
            provider["provider_id"],
            diagnosis[0],
            visit_at,
            claim_amount,
            paid_amount,
            visit_type,
            rand.randint(15, 240),
            provider["facility_name"].split()[1],
            provider["state"],
            rand.choices(outcomes, weights=[58, 13, 9, 20], k=1)[0],
            rand.random() < 0.34,
            rand.choice(["self_referral", "pcp_referral", "ed", "scheduled"]),
        )
        yield row


def generate_patient_change_log(
    patients: list[dict[str, object]],
    target_count: int,
    rand: random.Random,
) -> Iterator[Sequence[object]]:
    change_start = datetime(2023, 1, 1, 8, 0, 0)
    change_end = datetime(2026, 4, 30, 18, 0, 0)
    for index in range(target_count):
        patient = rand.choice(patients)
        operation = rand.choices(["UPDATE", "UPDATE", "DELETE"], weights=[78, 12, 10], k=1)[0]
        payload = {
            "state": rand.choice(US_LOCALES)["state"],
            "risk_score": round(rand.uniform(0.05, 0.99), 4),
            "chronic_condition_count": rand.randint(0, 5),
            "coverage_tier": rand.choice(["bronze", "silver", "gold", "platinum"]),
        }
        if operation == "DELETE":
            payload = {"deleted_reason": rand.choice(["coverage_end", "requested", "duplicate"]) }
        yield (
            f"PCHG{index + 1:07d}",
            patient["patient_id"],
            operation,
            random_datetime(rand, change_start, change_end),
            json.dumps(payload, sort_keys=True),
        )


def generate_tickers(count: int, rand: random.Random) -> list[dict[str, object]]:
    tickers: list[dict[str, object]] = []
    sectors = list(SECTOR_INDUSTRY)
    for index in range(count):
        sector = sectors[index % len(sectors)]
        industry = rand.choice(SECTOR_INDUSTRY[sector])
        tickers.append(
            {
                "ticker": ticker_symbol(index),
                "company_name": f"{industry} Holdings {index + 1}",
                "sector": sector,
                "industry": industry,
                "exchange": rand.choice(["NASDAQ", "NYSE"]),
                "country_code": "US",
                "ipo_date": random_date(rand, date(1992, 1, 1), date(2023, 12, 31)),
                "is_active": rand.random() < 0.96,
                "market_cap_bucket": rand.choices(["mid_cap", "large_cap", "mega_cap"], weights=[45, 35, 20], k=1)[0],
                "beta": round(rand.uniform(0.65, 1.85), 3),
            }
        )
    return tickers


def generate_stock_price_rows(
    tickers: list[dict[str, object]],
    market_years: int,
    rand: random.Random,
) -> Iterator[Sequence[object]]:
    end_day = date.today()
    start_day = end_day - timedelta(days=365 * market_years)
    trading_days = list(business_days(start_day, end_day))
    anomaly_pairs = {
        (ticker["ticker"], trading_days[rand.randint(5, len(trading_days) - 6)])
        for ticker in rand.sample(tickers, max(5, len(tickers) // 30))
    }
    for ticker in tickers:
        sector = ticker["sector"]
        drift = {
            "Technology": 0.0009,
            "Healthcare": 0.0006,
            "Financials": 0.0005,
            "Consumer": 0.0004,
            "Energy": 0.0003,
            "Industrials": 0.00045,
            "Communication": 0.00055,
        }[sector]
        volatility = {
            "Technology": 0.028,
            "Healthcare": 0.025,
            "Financials": 0.022,
            "Consumer": 0.021,
            "Energy": 0.031,
            "Industrials": 0.019,
            "Communication": 0.024,
        }[sector]
        close_price = rand.uniform(18.0, 320.0)
        for trading_day in trading_days:
            overnight_move = rand.gauss(drift, volatility / 2)
            intraday_move = rand.gauss(drift / 2, volatility)
            open_price = max(1.0, close_price * (1 + overnight_move))
            close_price = max(0.8, open_price * (1 + intraday_move))
            high_price = max(open_price, close_price) * (1 + abs(rand.gauss(0.0, volatility / 4)))
            low_price = min(open_price, close_price) * max(0.5, 1 - abs(rand.gauss(0.0, volatility / 4)))
            volume = int(rand.lognormvariate(11.7, 0.45))
            regime = "volatile" if trading_day.month in {3, 9, 10} else "bull" if trading_day.month in {4, 5, 6} else "normal"
            open_value = round(open_price, 4)
            high_value = round(high_price, 4)
            low_value = round(low_price, 4)
            close_value = round(close_price, 4)
            adjusted_close = round(close_price * rand.uniform(0.995, 1.005), 4)
            if (ticker["ticker"], trading_day) in anomaly_pairs:
                low_value = -abs(low_value)
                close_value = 0.0
                adjusted_close = 0.0
            yield (
                ticker["ticker"],
                trading_day,
                open_value,
                max(high_value, open_value, close_value),
                min(low_value, open_value, close_value),
                close_value,
                adjusted_close,
                volume,
                regime,
            )


def generate_ticker_change_log(
    tickers: list[dict[str, object]],
    target_count: int,
    rand: random.Random,
) -> Iterator[Sequence[object]]:
    change_start = datetime(2023, 1, 1, 8, 0, 0)
    change_end = datetime(2026, 4, 30, 18, 0, 0)
    for index in range(target_count):
        ticker = rand.choice(tickers)
        operation = rand.choices(["UPDATE", "UPDATE", "DELETE"], weights=[78, 17, 5], k=1)[0]
        payload = {
            "sector": rand.choice(list(SECTOR_INDUSTRY)),
            "industry": rand.choice(SECTOR_INDUSTRY[rand.choice(list(SECTOR_INDUSTRY))]),
            "is_active": rand.random() < 0.97,
        }
        if operation == "DELETE":
            payload = {"delisted_reason": rand.choice(["acquired", "bankruptcy", "merged"])}
        yield (
            f"TCHG{index + 1:07d}",
            ticker["ticker"],
            operation,
            random_datetime(rand, change_start, change_end),
            json.dumps(payload, sort_keys=True),
        )


def write_financial_dataset(
    db_path: Path,
    customers: list[dict[str, object]],
    accounts: list[dict[str, object]],
    merchants: list[dict[str, object]],
    profile: GenerationProfile,
    rand: random.Random,
) -> dict[str, int]:
    if db_path.exists():
        db_path.unlink()
    customers_by_id = {customer["customer_id"]: customer for customer in customers}
    conn = duckdb.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE customers (
            customer_id VARCHAR,
            full_name VARCHAR,
            email VARCHAR,
            phone VARCHAR,
            address_line1 VARCHAR,
            city VARCHAR,
            state VARCHAR,
            postal_code VARCHAR,
            country_code VARCHAR,
            birth_date DATE,
            joined_at TIMESTAMP,
            segment VARCHAR,
            risk_band VARCHAR,
            annual_income INTEGER,
            status VARCHAR
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE accounts (
            account_id VARCHAR,
            customer_id VARCHAR,
            opened_at TIMESTAMP,
            account_type VARCHAR,
            account_status VARCHAR,
            credit_limit DOUBLE,
            current_balance DOUBLE,
            utilization_ratio DOUBLE,
            currency_code VARCHAR,
            autopay_enabled BOOLEAN,
            card_number VARCHAR,
            expiry_month INTEGER,
            expiry_year INTEGER
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE merchants (
            merchant_id VARCHAR,
            merchant_name VARCHAR,
            merchant_category VARCHAR,
            mcc VARCHAR,
            city VARCHAR,
            state VARCHAR,
            country_code VARCHAR,
            risk_level VARCHAR
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE card_transactions (
            transaction_id VARCHAR,
            account_id VARCHAR,
            customer_id VARCHAR,
            merchant_id VARCHAR,
            posted_at TIMESTAMP,
            settlement_at TIMESTAMP,
            amount DOUBLE,
            currency_code VARCHAR,
            transaction_type VARCHAR,
            channel VARCHAR,
            card_present BOOLEAN,
            merchant_category VARCHAR,
            country_code VARCHAR,
            state VARCHAR,
            is_refund BOOLEAN,
            is_dispute BOOLEAN,
            status VARCHAR,
            running_balance DOUBLE
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE customer_change_log (
            change_id VARCHAR,
            customer_id VARCHAR,
            operation VARCHAR,
            changed_at TIMESTAMP,
            payload_json VARCHAR
        )
        """
    )

    insert_rows(
        conn,
        "customers",
        [
            "customer_id",
            "full_name",
            "email",
            "phone",
            "address_line1",
            "city",
            "state",
            "postal_code",
            "country_code",
            "birth_date",
            "joined_at",
            "segment",
            "risk_band",
            "annual_income",
            "status",
        ],
        (
            (
                customer["customer_id"],
                customer["full_name"],
                customer["email"],
                customer["phone"],
                customer["address_line1"],
                customer["city"],
                customer["state"],
                customer["postal_code"],
                customer["country_code"],
                customer["birth_date"],
                customer["joined_at"],
                customer["segment"],
                customer["risk_band"],
                customer["annual_income"],
                "active",
            )
            for customer in customers
        ),
    )
    insert_rows(
        conn,
        "accounts",
        [
            "account_id",
            "customer_id",
            "opened_at",
            "account_type",
            "account_status",
            "credit_limit",
            "current_balance",
            "utilization_ratio",
            "currency_code",
            "autopay_enabled",
            "card_number",
            "expiry_month",
            "expiry_year",
        ],
        (
            (
                account["account_id"],
                account["customer_id"],
                account["opened_at"],
                account["account_type"],
                account["account_status"],
                account["credit_limit"],
                account["current_balance"],
                account["utilization_ratio"],
                account["currency_code"],
                account["autopay_enabled"],
                account["card_number"],
                account["expiry_month"],
                account["expiry_year"],
            )
            for account in accounts
        ),
    )
    insert_rows(
        conn,
        "merchants",
        [
            "merchant_id",
            "merchant_name",
            "merchant_category",
            "mcc",
            "city",
            "state",
            "country_code",
            "risk_level",
        ],
        (
            (
                merchant["merchant_id"],
                merchant["merchant_name"],
                merchant["merchant_category"],
                merchant["mcc"],
                merchant["city"],
                merchant["state"],
                merchant["country_code"],
                merchant["risk_level"],
            )
            for merchant in merchants
        ),
    )
    insert_rows(
        conn,
        "card_transactions",
        [
            "transaction_id",
            "account_id",
            "customer_id",
            "merchant_id",
            "posted_at",
            "settlement_at",
            "amount",
            "currency_code",
            "transaction_type",
            "channel",
            "card_present",
            "merchant_category",
            "country_code",
            "state",
            "is_refund",
            "is_dispute",
            "status",
            "running_balance",
        ],
        generate_transaction_rows(accounts, customers_by_id, merchants, profile.transactions, rand),
    )
    insert_rows(
        conn,
        "customer_change_log",
        ["change_id", "customer_id", "operation", "changed_at", "payload_json"],
        generate_customer_change_log(customers, profile.customer_changes, rand),
    )
    counts = {
        "customers": count_rows(conn, "customers"),
        "accounts": count_rows(conn, "accounts"),
        "merchants": count_rows(conn, "merchants"),
        "card_transactions": count_rows(conn, "card_transactions"),
        "customer_change_log": count_rows(conn, "customer_change_log"),
    }
    conn.close()
    return counts


def write_healthcare_dataset(
    db_path: Path,
    customers: list[dict[str, object]],
    profile: GenerationProfile,
    rand: random.Random,
) -> dict[str, int]:
    if db_path.exists():
        db_path.unlink()
    patients = generate_patients(customers, profile.patients, rand)
    providers = generate_providers(profile.providers, rand)
    conn = duckdb.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE patients (
            patient_id VARCHAR,
            customer_id VARCHAR,
            patient_name VARCHAR,
            email VARCHAR,
            phone VARCHAR,
            address_line1 VARCHAR,
            city VARCHAR,
            state VARCHAR,
            postal_code VARCHAR,
            insurance_member_id VARCHAR,
            birth_date DATE,
            gender VARCHAR,
            chronic_condition_count INTEGER,
            risk_score DOUBLE,
            created_at TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE providers (
            provider_id VARCHAR,
            provider_name VARCHAR,
            specialty VARCHAR,
            facility_name VARCHAR,
            city VARCHAR,
            state VARCHAR,
            region VARCHAR,
            npi VARCHAR,
            network_status VARCHAR
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE diagnoses (
            diagnosis_code VARCHAR,
            diagnosis_category VARCHAR,
            description VARCHAR,
            chronic_flag BOOLEAN,
            severity_level VARCHAR
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE medical_visits (
            visit_id VARCHAR,
            patient_id VARCHAR,
            provider_id VARCHAR,
            diagnosis_code VARCHAR,
            visit_at TIMESTAMP,
            claim_amount DOUBLE,
            paid_amount DOUBLE,
            visit_type VARCHAR,
            length_minutes INTEGER,
            facility_type VARCHAR,
            state VARCHAR,
            outcome VARCHAR,
            follow_up_required BOOLEAN,
            admission_source VARCHAR
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE patient_change_log (
            change_id VARCHAR,
            patient_id VARCHAR,
            operation VARCHAR,
            changed_at TIMESTAMP,
            payload_json VARCHAR
        )
        """
    )

    insert_rows(
        conn,
        "patients",
        [
            "patient_id",
            "customer_id",
            "patient_name",
            "email",
            "phone",
            "address_line1",
            "city",
            "state",
            "postal_code",
            "insurance_member_id",
            "birth_date",
            "gender",
            "chronic_condition_count",
            "risk_score",
            "created_at",
        ],
        (
            (
                patient["patient_id"],
                patient["customer_id"],
                patient["patient_name"],
                patient["email"],
                patient["phone"],
                patient["address_line1"],
                patient["city"],
                patient["state"],
                patient["postal_code"],
                patient["insurance_member_id"],
                patient["birth_date"],
                patient["gender"],
                patient["chronic_condition_count"],
                patient["risk_score"],
                patient["created_at"],
            )
            for patient in patients
        ),
    )
    insert_rows(
        conn,
        "providers",
        [
            "provider_id",
            "provider_name",
            "specialty",
            "facility_name",
            "city",
            "state",
            "region",
            "npi",
            "network_status",
        ],
        (
            (
                provider["provider_id"],
                provider["provider_name"],
                provider["specialty"],
                provider["facility_name"],
                provider["city"],
                provider["state"],
                provider["region"],
                provider["npi"],
                provider["network_status"],
            )
            for provider in providers
        ),
    )
    insert_rows(
        conn,
        "diagnoses",
        ["diagnosis_code", "diagnosis_category", "description", "chronic_flag", "severity_level"],
        DIAGNOSES,
    )
    insert_rows(
        conn,
        "medical_visits",
        [
            "visit_id",
            "patient_id",
            "provider_id",
            "diagnosis_code",
            "visit_at",
            "claim_amount",
            "paid_amount",
            "visit_type",
            "length_minutes",
            "facility_type",
            "state",
            "outcome",
            "follow_up_required",
            "admission_source",
        ],
        generate_medical_visit_rows(patients, providers, rand, profile.visits),
    )
    insert_rows(
        conn,
        "patient_change_log",
        ["change_id", "patient_id", "operation", "changed_at", "payload_json"],
        generate_patient_change_log(patients, profile.patient_changes, rand),
    )
    counts = {
        "patients": count_rows(conn, "patients"),
        "providers": count_rows(conn, "providers"),
        "diagnoses": count_rows(conn, "diagnoses"),
        "medical_visits": count_rows(conn, "medical_visits"),
        "patient_change_log": count_rows(conn, "patient_change_log"),
    }
    conn.close()
    return counts


def write_markets_dataset(
    db_path: Path,
    profile: GenerationProfile,
    rand: random.Random,
) -> dict[str, int]:
    if db_path.exists():
        db_path.unlink()
    tickers = generate_tickers(profile.tickers, rand)
    conn = duckdb.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE tickers (
            ticker VARCHAR,
            company_name VARCHAR,
            sector VARCHAR,
            industry VARCHAR,
            exchange VARCHAR,
            country_code VARCHAR,
            ipo_date DATE,
            is_active BOOLEAN,
            market_cap_bucket VARCHAR,
            beta DOUBLE
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE stock_prices (
            ticker VARCHAR,
            trading_date DATE,
            open_price DOUBLE,
            high_price DOUBLE,
            low_price DOUBLE,
            close_price DOUBLE,
            adjusted_close DOUBLE,
            volume BIGINT,
            market_regime VARCHAR
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE ticker_change_log (
            change_id VARCHAR,
            ticker VARCHAR,
            operation VARCHAR,
            changed_at TIMESTAMP,
            payload_json VARCHAR
        )
        """
    )
    insert_rows(
        conn,
        "tickers",
        [
            "ticker",
            "company_name",
            "sector",
            "industry",
            "exchange",
            "country_code",
            "ipo_date",
            "is_active",
            "market_cap_bucket",
            "beta",
        ],
        (
            (
                ticker["ticker"],
                ticker["company_name"],
                ticker["sector"],
                ticker["industry"],
                ticker["exchange"],
                ticker["country_code"],
                ticker["ipo_date"],
                ticker["is_active"],
                ticker["market_cap_bucket"],
                ticker["beta"],
            )
            for ticker in tickers
        ),
    )
    insert_rows(
        conn,
        "stock_prices",
        [
            "ticker",
            "trading_date",
            "open_price",
            "high_price",
            "low_price",
            "close_price",
            "adjusted_close",
            "volume",
            "market_regime",
        ],
        generate_stock_price_rows(tickers, profile.market_years, rand),
        batch_size=10_000,
    )
    insert_rows(
        conn,
        "ticker_change_log",
        ["change_id", "ticker", "operation", "changed_at", "payload_json"],
        generate_ticker_change_log(tickers, profile.ticker_changes, rand),
    )
    counts = {
        "tickers": count_rows(conn, "tickers"),
        "stock_prices": count_rows(conn, "stock_prices"),
        "ticker_change_log": count_rows(conn, "ticker_change_log"),
    }
    conn.close()
    return counts


def write_crm_dataset(
    db_path: Path,
    customers: list[dict[str, object]],
    rand: random.Random,
) -> dict[str, int]:
    if db_path.exists():
        db_path.unlink()
    conn = duckdb.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE crm_customers (
            customer_id VARCHAR,
            lifecycle_stage VARCHAR,
            acquisition_channel VARCHAR,
            preferred_language VARCHAR,
            marketing_tier VARCHAR,
            risk_segment VARCHAR,
            household_income_band VARCHAR,
            last_contact_at TIMESTAMP,
            account_manager VARCHAR,
            updated_at TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE customer_segments (
            segment_id VARCHAR,
            customer_id VARCHAR,
            segment_name VARCHAR,
            risk_band VARCHAR,
            churn_score DOUBLE,
            propensity_score DOUBLE,
            effective_at TIMESTAMP,
            updated_at TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE consent_preferences (
            customer_id VARCHAR,
            email_opt_in BOOLEAN,
            sms_opt_in BOOLEAN,
            phone_opt_in BOOLEAN,
            profiling_opt_in BOOLEAN,
            consent_updated_at TIMESTAMP,
            source_system VARCHAR
        )
        """
    )
    crm_start = datetime(2023, 1, 1, 8, 0, 0)
    crm_end = datetime(2026, 4, 30, 18, 0, 0)
    account_managers = [
        "Jordan Patel",
        "Camila Rocha",
        "Megan Foster",
        "Carlos Diaz",
        "Priya Menon",
        "Sofia Mendes",
    ]
    insert_rows(
        conn,
        "crm_customers",
        [
            "customer_id",
            "lifecycle_stage",
            "acquisition_channel",
            "preferred_language",
            "marketing_tier",
            "risk_segment",
            "household_income_band",
            "last_contact_at",
            "account_manager",
            "updated_at",
        ],
        (
            (
                customer["customer_id"],
                customer["lifecycle_stage"],
                customer["acquisition_channel"],
                customer["preferred_language"],
                customer["marketing_tier"],
                customer["risk_band"],
                customer["household_income_band"],
                random_datetime(rand, crm_start, crm_end),
                rand.choice(account_managers),
                random_datetime(rand, crm_start, crm_end),
            )
            for customer in customers
        ),
    )
    insert_rows(
        conn,
        "customer_segments",
        [
            "segment_id",
            "customer_id",
            "segment_name",
            "risk_band",
            "churn_score",
            "propensity_score",
            "effective_at",
            "updated_at",
        ],
        (
            (
                f"SEG{index + 1:07d}",
                customer["customer_id"],
                customer["segment"],
                customer["risk_band"],
                round(rand.uniform(0.01, 0.98), 4),
                round(rand.uniform(0.03, 0.99), 4),
                random_datetime(rand, crm_start, crm_end),
                random_datetime(rand, crm_start, crm_end),
            )
            for index, customer in enumerate(customers)
        ),
    )
    insert_rows(
        conn,
        "consent_preferences",
        [
            "customer_id",
            "email_opt_in",
            "sms_opt_in",
            "phone_opt_in",
            "profiling_opt_in",
            "consent_updated_at",
            "source_system",
        ],
        (
            (
                customer["customer_id"],
                rand.random() < 0.73,
                rand.random() < 0.51,
                rand.random() < 0.42,
                rand.random() < 0.66,
                random_datetime(rand, crm_start, crm_end),
                rand.choice(["crm", "call_center", "web_portal"]),
            )
            for customer in customers
        ),
    )
    counts = {
        "crm_customers": count_rows(conn, "crm_customers"),
        "customer_segments": count_rows(conn, "customer_segments"),
        "consent_preferences": count_rows(conn, "consent_preferences"),
    }
    conn.close()
    return counts


def print_summary(summary: dict[str, dict[str, int]], output_dir: Path) -> None:
    print(f"Synthetic challenge datasets written to: {output_dir.resolve()}")
    for file_name, table_counts in summary.items():
        print(f"\n{file_name}")
        for table_name, row_count in table_counts.items():
            print(f"  - {table_name}: {row_count:,}")


def main() -> None:
    args = parse_args()
    profile = SIZE_PROFILES[args.profile]
    rand = random.Random(args.seed)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    customers = generate_master_customers(profile, rand)
    accounts = generate_accounts(customers, profile.accounts, rand)
    merchants = generate_merchants(profile.merchants, rand)

    summary = {
        "financial.duckdb": write_financial_dataset(
            output_dir / "financial.duckdb",
            customers,
            accounts,
            merchants,
            profile,
            rand,
        ),
        "healthcare.duckdb": write_healthcare_dataset(
            output_dir / "healthcare.duckdb",
            customers,
            profile,
            rand,
        ),
        "markets.duckdb": write_markets_dataset(output_dir / "markets.duckdb", profile, rand),
        "crm.duckdb": write_crm_dataset(output_dir / "crm.duckdb", customers, rand),
    }
    print_summary(summary, output_dir)


if __name__ == "__main__":
    main()