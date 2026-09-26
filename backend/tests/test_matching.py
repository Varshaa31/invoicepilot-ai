from decimal import Decimal

from app.models.entities import ResolutionStatus
from app.services.matching import load_catalog, resolve_service


def test_exact_match(db):
    catalog = load_catalog(db)
    result = resolve_service("Landing Page", catalog)
    assert result.status == ResolutionStatus.MATCHED
    assert result.match is not None
    assert result.match.name == "Landing Page"
    assert result.match.unit_price == Decimal("15000")
    assert result.method == "exact_name"


def test_normalized_match(db):
    catalog = load_catalog(db)
    result = resolve_service("landing page", catalog)
    assert result.status == ResolutionStatus.MATCHED
    assert result.match is not None
    assert result.match.name == "Landing Page"


def test_alias_match(db):
    catalog = load_catalog(db)
    result = resolve_service("logo", catalog)
    assert result.status == ResolutionStatus.MATCHED
    assert result.match is not None
    assert result.match.name == "Logo Design"


def test_fuzzy_match(db):
    catalog = load_catalog(db)
    result = resolve_service("e commerce website", catalog)
    assert result.status == ResolutionStatus.MATCHED
    assert result.match is not None
    assert result.match.name == "E-commerce Website"


def test_ambiguous_seo(db):
    catalog = load_catalog(db)
    result = resolve_service("SEO", catalog)
    assert result.status == ResolutionStatus.AMBIGUOUS
    names = {item.name for item in result.options}
    assert "SEO Optimization" in names
    assert "SEO Growth Package" in names


def test_missing_match(db):
    catalog = load_catalog(db)
    result = resolve_service("drone photography", catalog)
    assert result.status == ResolutionStatus.MISSING
    assert result.match is None
