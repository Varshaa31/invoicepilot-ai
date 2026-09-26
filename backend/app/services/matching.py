from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from difflib import SequenceMatcher
import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.entities import ResolutionStatus, Service, User


# Matching thresholds.
FUZZY_FLOOR = 0.72
FUZZY_AUTO_MATCH = 0.88
NEAR_TOP_DELTA = 0.05


@dataclass
class CatalogService:
    id: UUID
    name: str
    description: str | None
    unit_price: Decimal
    currency: str
    aliases: list[str]


@dataclass
class MatchResult:
    status: ResolutionStatus
    match: CatalogService | None = None
    options: list[CatalogService] = field(default_factory=list)
    score: float = 0.0
    method: str | None = None


def normalize(text: str) -> str:
    """
    Normalize service text for deterministic comparisons.

    Examples:
        "E-commerce Website" -> "e commerce website"
        "SEO Optimization" -> "seo optimization"
        "  Logo Design  " -> "logo design"
    """
    text = text.lower().strip()

    # Treat punctuation/hyphens as separators.
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Collapse repeated whitespace.
    text = re.sub(r"\s+", " ", text)

    return text


def load_catalog(
    db: Session,
    user: User,
    active_only: bool = True,
) -> list[CatalogService]:
    """
    Load the service catalog belonging to the authenticated user.

    Prices come directly from that user's database catalog and are
    converted to Decimal. No AI-generated price is involved.

    Tenant isolation is enforced here so invoice matching can never
    accidentally use another user's services.
    """
    stmt = (
        select(Service)
        .options(selectinload(Service.aliases))
        .where(Service.user_id == user.id)
    )

    if active_only:
        stmt = stmt.where(Service.active.is_(True))

    services = (
        db.execute(stmt)
        .scalars()
        .unique()
        .all()
    )

    return [
        CatalogService(
            id=row.id,
            name=row.name,
            description=row.description,
            unit_price=Decimal(str(row.price)),
            currency=row.currency,
            aliases=[
                alias.alias
                for alias in row.aliases
            ],
        )
        for row in services
    ]


def _to_candidates(
    services: list[CatalogService],
) -> list[CatalogService]:
    """
    Remove duplicate catalog services while preserving order.
    """
    unique: dict[UUID, CatalogService] = {}

    for service in services:
        unique[service.id] = service

    return list(unique.values())


def _token_related(
    query: str,
    service: CatalogService,
) -> bool:
    """
    Determine whether a short query is related to a service name
    or alias.

    This is intentionally conservative and is mainly used to
    detect ambiguity such as:

        "SEO"

    when the catalog contains:

        SEO Optimization
        SEO Growth Package
    """
    normalized_query = normalize(query)

    if not normalized_query:
        return False

    query_tokens = set(normalized_query.split())

    if not query_tokens:
        return False

    candidates = [
        service.name,
        *service.aliases,
    ]

    for candidate in candidates:
        candidate_normalized = normalize(candidate)
        candidate_tokens = set(
            candidate_normalized.split()
        )

        # Exact token overlap for short requests.
        if query_tokens.issubset(candidate_tokens):
            return True

        # Prefix relationship such as:
        # "seo" -> "seo optimization"
        if candidate_normalized.startswith(
            f"{normalized_query} "
        ):
            return True

    return False


def _similarity(
    query: str,
    candidate: str,
) -> float:
    """
    Calculate a conservative similarity score.

    SequenceMatcher handles normal fuzzy typos while token overlap
    helps natural-language service descriptions.
    """
    query_normalized = normalize(query)
    candidate_normalized = normalize(candidate)

    if not query_normalized or not candidate_normalized:
        return 0.0

    sequence_score = SequenceMatcher(
        None,
        query_normalized,
        candidate_normalized,
    ).ratio()

    query_tokens = set(query_normalized.split())
    candidate_tokens = set(candidate_normalized.split())

    if not query_tokens or not candidate_tokens:
        return sequence_score

    overlap = len(
        query_tokens.intersection(candidate_tokens)
    ) / len(query_tokens)

    # Do not let a single common word dominate the score.
    return max(
        sequence_score,
        sequence_score * 0.75 + overlap * 0.25,
    )


def resolve_service(
    requested: str,
    catalog: list[CatalogService],
) -> MatchResult:
    """
    Resolve customer wording against the service catalog.

    Resolution order:

        1. Exact name
        2. Normalized name
        3. Exact alias
        4. Related short-token ambiguity
        5. Fuzzy matching
        6. Missing

    The resolver NEVER creates a service or price.
    """

    query_raw = requested.strip()
    query = normalize(query_raw)

    if not query or not catalog:
        return MatchResult(
            status=ResolutionStatus.MISSING,
            method="empty_or_empty_catalog",
        )

    # ---------------------------------------------------------
    # 1. Exact catalog name
    # ---------------------------------------------------------

    exact = [
        service
        for service in catalog
        if service.name.strip().lower()
        == query_raw.lower()
    ]

    if len(exact) == 1:
        exact_service = exact[0]

        related = [
            service
            for service in catalog
            if (
                service.id != exact_service.id
                and _token_related(query_raw, service)
            )
        ]

        # A short query such as "SEO" should not automatically
        # win just because one service happens to have that name.
        if related and len(query.split()) == 1:
            return MatchResult(
                status=ResolutionStatus.AMBIGUOUS,
                options=_to_candidates(
                    exact + related
                )[:5],
                score=1.0,
                method="exact_name_ambiguous",
            )

        return MatchResult(
            status=ResolutionStatus.MATCHED,
            match=exact_service,
            score=1.0,
            method="exact_name",
        )

    if len(exact) > 1:
        return MatchResult(
            status=ResolutionStatus.AMBIGUOUS,
            options=exact[:5],
            score=1.0,
            method="exact_name",
        )

    # ---------------------------------------------------------
    # 2. Normalized catalog name
    # ---------------------------------------------------------

    normalized = [
        service
        for service in catalog
        if normalize(service.name) == query
    ]

    if len(normalized) == 1:
        normalized_service = normalized[0]

        related = [
            service
            for service in catalog
            if (
                service.id != normalized_service.id
                and _token_related(query, service)
            )
        ]

        if related and len(query.split()) == 1:
            return MatchResult(
                status=ResolutionStatus.AMBIGUOUS,
                options=_to_candidates(
                    normalized + related
                )[:5],
                score=0.99,
                method="normalized_name_ambiguous",
            )

        return MatchResult(
            status=ResolutionStatus.MATCHED,
            match=normalized_service,
            score=0.99,
            method="normalized_name",
        )

    if len(normalized) > 1:
        return MatchResult(
            status=ResolutionStatus.AMBIGUOUS,
            options=normalized[:5],
            score=0.99,
            method="normalized_name",
        )

    # ---------------------------------------------------------
    # 3. Exact alias matching
    # ---------------------------------------------------------

    alias_hits: list[CatalogService] = []

    for service in catalog:
        aliases = [
            normalize(alias)
            for alias in service.aliases
        ]

        if query in aliases:
            alias_hits.append(service)

    if len(alias_hits) == 1:
        alias_service = alias_hits[0]

        related = [
            service
            for service in catalog
            if (
                service.id != alias_service.id
                and _token_related(query, service)
            )
        ]

        if related:
            return MatchResult(
                status=ResolutionStatus.AMBIGUOUS,
                options=_to_candidates(
                    alias_hits + related
                )[:5],
                score=0.95,
                method="alias_ambiguous",
            )

        return MatchResult(
            status=ResolutionStatus.MATCHED,
            match=alias_service,
            score=0.95,
            method="alias",
        )

    if len(alias_hits) > 1:
        return MatchResult(
            status=ResolutionStatus.AMBIGUOUS,
            options=alias_hits[:5],
            score=0.95,
            method="alias",
        )

    # ---------------------------------------------------------
    # 4. Short natural-language terms
    # ---------------------------------------------------------
    #
    # This is important for:
    #
    #     "SEO"
    #
    # when catalog contains:
    #
    #     SEO Optimization
    #     SEO Growth Package
    #
    # We want AMBIGUOUS, not a random fuzzy match.

    related = [
        service
        for service in catalog
        if _token_related(query, service)
    ]

    if len(related) > 1:
        return MatchResult(
            status=ResolutionStatus.AMBIGUOUS,
            options=_to_candidates(related)[:5],
            score=0.90,
            method="token_ambiguity",
        )

    if len(related) == 1 and len(query.split()) == 1:
        return MatchResult(
            status=ResolutionStatus.MATCHED,
            match=related[0],
            score=0.90,
            method="token_match",
        )

    # ---------------------------------------------------------
    # 5. Fuzzy matching
    # ---------------------------------------------------------

    scored: list[
        tuple[float, CatalogService]
    ] = []

    for service in catalog:
        candidates = [
            service.name,
            *service.aliases,
        ]

        score = max(
            _similarity(query, candidate)
            for candidate in candidates
        )

        scored.append(
            (score, service)
        )

    scored.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    if not scored:
        return MatchResult(
            status=ResolutionStatus.MISSING,
            method="fuzzy",
        )

    top_score = scored[0][0]

    # Nothing is sufficiently similar.
    if top_score < FUZZY_FLOOR:
        return MatchResult(
            status=ResolutionStatus.MISSING,
            score=top_score,
            method="fuzzy",
        )

    # Keep candidates close to the best result.
    top_candidates = [
        service
        for score, service in scored
        if score
        >= max(
            FUZZY_FLOOR,
            top_score - NEAR_TOP_DELTA,
        )
    ]

    # High-confidence fuzzy match.
    if (
        len(top_candidates) == 1
        and top_score >= FUZZY_AUTO_MATCH
    ):
        return MatchResult(
            status=ResolutionStatus.MATCHED,
            match=top_candidates[0],
            score=top_score,
            method="fuzzy",
        )

    # Multiple plausible candidates require human review.
    return MatchResult(
        status=ResolutionStatus.AMBIGUOUS,
        options=top_candidates[:5],
        score=top_score,
        method="fuzzy",
    )


def match_requested_item(
    requested: str,
    catalog: list[CatalogService],
) -> MatchResult:
    """
    Public matching entry point used by the invoice service.
    """
    return resolve_service(
        requested,
        catalog,
    )