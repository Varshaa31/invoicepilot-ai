from collections.abc import Generator
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.entities import Service, ServiceAlias, User

get_settings.cache_clear()

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def seed_catalog(db: Session) -> None:
    db.add(User(name="Demo Operator", email="demo@invoicepilot.ai", workspace_name="Demo"))
    catalog = [
        ("WEB001", "Landing Page", Decimal("15000"), ["landing page", "landing pages"]),
        ("WEB002", "Corporate Website", Decimal("40000"), ["corporate website", "website development"]),
        ("WEB003", "E-commerce Website", Decimal("65000"), ["ecommerce website", "e-commerce website", "online store"]),
        ("SEO001", "SEO Optimization", Decimal("12000"), ["seo optimization", "search engine optimization"]),
        ("SEO002", "SEO Growth Package", Decimal("25000"), ["seo growth", "seo growth package"]),
        ("DES001", "Logo Design", Decimal("5000"), ["logo", "logo design"]),
    ]
    for code, name, price, aliases in catalog:
        service = Service(
            code=code,
            name=name,
            description=name,
            unit="project",
            price=price,
            currency="INR",
            active=True,
        )
        db.add(service)
        db.flush()
        for alias in aliases:
            db.add(ServiceAlias(service_id=service.id, alias=alias))
    db.commit()


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    seed_catalog(session)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
