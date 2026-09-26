from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.core.exceptions import AppError
from app.schemas.common import InvoiceRequest
from app.services import extraction as extraction_module


def test_structured_extraction_schema_validation():
    parsed = InvoiceRequest.model_validate(
        {
            "customer": {
                "name": "Rahul",
                "email": "rahul@example.com",
            },
            "requested_items": [
                {
                    "requested_service": "E-commerce Website",
                    "quantity": 1,
                },
                {
                    "requested_service": "SEO",
                    "quantity": 1,
                },
            ],
            "notes": None,
            "missing_information": [],
        }
    )

    assert parsed.customer.name == "Rahul"
    assert parsed.requested_items[0].quantity == Decimal("1")


def test_malformed_response_handling():
    with pytest.raises(ValidationError):
        InvoiceRequest.model_validate(
            {
                "customer": {},
                "requested_items": [],
            }
        )


def test_missing_information_handling():
    parsed = InvoiceRequest.model_validate(
        {
            "customer": {
                "name": None,
                "email": None,
            },
            "requested_items": [
                {
                    "requested_service": "Logo Design",
                    "quantity": None,
                }
            ],
            "missing_information": [
                "customer name",
                "customer email",
                "quantity",
            ],
        }
    )

    assert "customer name" in parsed.missing_information
    assert parsed.requested_items[0].quantity is None


def test_extract_requires_api_key(monkeypatch):
    monkeypatch.setattr(
        extraction_module,
        "get_settings",
        lambda: type(
            "S",
            (),
            {
                "groq_api_key": "",
                "groq_model": "openai/gpt-oss-20b",
                "groq_base_url": "https://api.groq.com/openai/v1",
            },
        )(),
    )

    with pytest.raises(AppError) as exc:
        extraction_module.extract_invoice_request(
            "Hi, I need a logo"
        )

    assert exc.value.code == "missing_groq_key"