from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Service


def test_health(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["database"] == "ok"


def test_service_endpoints(client: TestClient):
    listed = client.get("/api/services")
    assert listed.status_code == 200
    assert len(listed.json()) >= 6

    created = client.post(
        "/api/services",
        json={
            "name": "Retainer Support",
            "description": "Monthly support",
            "unit": "month",
            "price": "9000.00",
            "currency": "INR",
            "aliases": ["retainer"],
        },
    )
    assert created.status_code == 201
    service_id = created.json()["id"]
    updated = client.put(f"/api/services/{service_id}", json={"price": "9500.00"})
    assert updated.status_code == 200
    assert updated.json()["price"] == "9500.00"
    deleted = client.delete(f"/api/services/{service_id}")
    assert deleted.status_code == 200
    assert deleted.json()["active"] is False


def test_invoice_and_approval_endpoints(client: TestClient, db: Session):
    commerce_id = str(db.execute(select(Service).where(Service.name == "E-commerce Website")).scalar_one().id)
    seo_id = str(db.execute(select(Service).where(Service.name == "SEO Optimization")).scalar_one().id)
    created = client.post(
        "/api/invoices",
        json={
            "customer": {"name": "Rahul", "email": "rahul@example.com", "company": "Acme"},
            "items": [
                {"requested_service": "E-commerce Website", "quantity": "1", "service_id": commerce_id},
                {"requested_service": "SEO Optimization", "quantity": "1", "service_id": seo_id},
            ],
            "tax_rate": "18",
        },
    )
    assert created.status_code == 201
    invoice_id = created.json()["id"]
    fetched = client.get(f"/api/invoices/{invoice_id}")
    assert fetched.status_code == 200
    approved = client.post(f"/api/invoices/{invoice_id}/approve")
    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"
    pdf = client.get(f"/api/invoices/{invoice_id}/pdf")
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF")


def test_unknown_service_blocks_approve_api(client: TestClient):
    created = client.post(
        "/api/invoices",
        json={
            "customer": {"name": "Rahul", "email": "rahul@example.com"},
            "items": [{"requested_service": "drone photography", "quantity": "1"}],
        },
    )
    assert created.status_code == 201
    invoice_id = created.json()["id"]
    assert created.json()["status"] == "REVIEW_REQUIRED"
    blocked = client.post(f"/api/invoices/{invoice_id}/approve")
    assert blocked.status_code == 422
    assert blocked.json()["issues"]


def test_dashboard_endpoint(client: TestClient):
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    body = response.json()
    assert "total_invoices" in body
    assert "total_revenue" in body
    assert "recent" in body


def test_ambiguous_resolve_endpoint(client: TestClient, db: Session):
    created = client.post(
        "/api/invoices",
        json={
            "customer": {"name": "Rahul", "email": "rahul@example.com"},
            "items": [{"requested_service": "SEO", "quantity": "1"}],
        },
    )
    assert created.status_code == 201
    item = created.json()["items"][0]
    assert item["resolution_status"] == "AMBIGUOUS"
    growth_id = str(db.execute(select(Service).where(Service.name == "SEO Growth Package")).scalar_one().id)
    resolved = client.post(
        f"/api/invoices/{created.json()['id']}/resolve-service",
        json={"item_id": item["id"], "service_id": growth_id},
    )
    assert resolved.status_code == 200
    assert resolved.json()["items"][0]["unit_price"] == "25000.00"
    assert resolved.json()["items"][0]["price_source"] == "service_catalog"
