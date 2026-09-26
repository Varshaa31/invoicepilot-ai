from __future__ import annotations

import csv
import sys
from decimal import Decimal
from pathlib import Path

from pwdlib import PasswordHash
from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.db.session import SessionLocal
from app.models.entities import Customer, Service, ServiceAlias, User


CSV_PATH = Path(__file__).with_name("services.csv")

DEMO_EMAIL = "demo@invoicepilot.ai"
DEMO_PASSWORD = "DemoInvoice123!"
DEMO_NAME = "Demo Operator"
DEMO_WORKSPACE = "InvoicePilot Demo"

password_hash = PasswordHash.recommended()


def get_or_create_demo_user(db) -> User:
    user = db.execute(
        select(User).where(User.email == DEMO_EMAIL)
    ).scalar_one_or_none()

    if user is None:
        user = User(
            name=DEMO_NAME,
            email=DEMO_EMAIL,
            workspace_name=DEMO_WORKSPACE,
            password_hash=password_hash.hash(DEMO_PASSWORD),
            email_verified=True,
        )
        db.add(user)
        db.flush()
    else:
        # Keep the demo account usable for local/demo environments.
        if not user.password_hash:
            user.password_hash = password_hash.hash(DEMO_PASSWORD)

        user.email_verified = True

    return user


def get_or_create_demo_customer(db) -> Customer:
    customer = db.execute(
        select(Customer).where(Customer.email == "rahul@example.com")
    ).scalar_one_or_none()

    if customer is None:
        customer = Customer(
            name="Rahul",
            email="rahul@example.com",
            company="Acme",
            phone="+91 90000 00000",
            address="Bengaluru, India",
        )
        db.add(customer)
        db.flush()

    return customer


def seed_services(db, user: User) -> None:
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            code = row["service_id"].strip()

            service = db.execute(
                select(Service).where(
                    Service.user_id == user.id,
                    Service.code == code,
                )
            ).scalar_one_or_none()

            if service is None:
                service = Service(
                    user_id=user.id,
                    code=code,
                    name=row["service_name"].strip(),
                    description=(row.get("description") or "").strip() or None,
                    unit=(row.get("unit") or "project").strip(),
                    price=Decimal(row["unit_price"].strip()),
                    currency="INR",
                    active=str(row["active"]).strip().lower()
                    in {"true", "1", "yes"},
                )
                db.add(service)
                db.flush()
            else:
                # Keep an existing demo service synchronized with the CSV.
                service.name = row["service_name"].strip()
                service.description = (
                    (row.get("description") or "").strip() or None
                )
                service.unit = (row.get("unit") or "project").strip()
                service.price = Decimal(row["unit_price"].strip())
                service.currency = "INR"
                service.active = (
                    str(row["active"]).strip().lower()
                    in {"true", "1", "yes"}
                )

            aliases = [
                item.strip()
                for item in (row.get("aliases") or "").split("|")
                if item.strip()
            ]

            existing_aliases = {
                alias.alias.lower()
                for alias in service.aliases
            }

            for alias in aliases:
                if alias.lower() not in existing_aliases:
                    db.add(
                        ServiceAlias(
                            service_id=service.id,
                            alias=alias,
                        )
                    )
                    existing_aliases.add(alias.lower())


def seed() -> None:
    db = SessionLocal()

    try:
        demo_user = get_or_create_demo_user(db)
        get_or_create_demo_customer(db)
        seed_services(db, demo_user)

        db.commit()

        print("Seed complete.")
        print(f"Demo email: {DEMO_EMAIL}")
        print(f"Demo password: {DEMO_PASSWORD}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed()