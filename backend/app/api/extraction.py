from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.entities import ResolutionStatus, User
from app.schemas.common import (
    ExtractionIn,
    ExtractionOut,
    InvoiceItemRequest,
    ItemMatchOut,
)
from app.services.extraction import extract_invoice_request
from app.services.invoices import _candidate_out
from app.services.matching import (
    load_catalog,
    match_requested_item,
)

router = APIRouter(tags=["extraction"])


def _match_items(
    db: Session,
    items: list[InvoiceItemRequest],
    user: User,
) -> list[ItemMatchOut]:
    # Only load the authenticated user's service catalog.
    catalog = load_catalog(
        db,
        user,
    )

    matches: list[ItemMatchOut] = []

    for item in items:
        result = match_requested_item(
            item.requested_service,
            catalog,
        )

        matched = None
        candidates = []
        unit_price = None
        currency = None
        price_source = None

        if (
            result.status == ResolutionStatus.MATCHED
            and result.match
        ):
            matched = _candidate_out(
                result.match,
                result.score,
            )
            unit_price = result.match.unit_price
            currency = result.match.currency
            price_source = "service_catalog"

        elif result.status == ResolutionStatus.AMBIGUOUS:
            candidates = [
                _candidate_out(
                    option,
                    result.score,
                )
                for option in result.options
            ]

        matches.append(
            ItemMatchOut(
                requested_service=item.requested_service,
                quantity=item.quantity,
                notes=item.notes,
                status=result.status,
                matched_service=matched,
                candidate_services=candidates,
                unit_price=unit_price,
                currency=currency,
                price_source=price_source,
                match_score=result.score,
            )
        )

    return matches


@router.post(
    "/extraction",
    response_model=ExtractionOut,
)
def extract_requirement(
    payload: ExtractionIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExtractionOut:
    extraction = extract_invoice_request(
        payload.customer_message
    )

    matches = _match_items(
        db,
        extraction.requested_items,
        current_user,
    )

    return ExtractionOut(
        extraction=extraction,
        matches=matches,
    )


@router.post(
    "/matching",
    response_model=list[ItemMatchOut],
)
def rematch_items(
    items: list[InvoiceItemRequest],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ItemMatchOut]:
    return _match_items(
        db,
        items,
        current_user,
    )
