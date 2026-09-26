from decimal import Decimal
from pricing import PriceCatalog


def test_exact_match():
    catalog = PriceCatalog("data/services.csv")
    result = catalog.resolve("landing page")
    assert result.status == "MATCHED"
    assert result.match["service_id"] == "WEB001"
    assert result.match["unit_price"] == Decimal("15000")


def test_alias_match():
    catalog = PriceCatalog("data/services.csv")
    result = catalog.resolve("logo")
    assert result.status == "MATCHED"
    assert result.match["service_id"] == "DES001"


def test_missing_service():
    catalog = PriceCatalog("data/services.csv")
    result = catalog.resolve("quantum marketing campaign")
    assert result.status == "MISSING"
