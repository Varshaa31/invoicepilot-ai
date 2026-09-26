from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.entities import User
from app.schemas.common import (
    ServiceImportOut,
    ServiceImportPreviewOut,
    ServiceIn,
    ServiceOut,
    ServiceUpdate,
)
from app.services.catalog import (
    create_service,
    deactivate_service,
    import_catalog,
    list_services,
    preview_catalog_import,
    serialize_service,
    update_service,
)


router = APIRouter(
    prefix="/services",
    tags=["services"],
)


@router.get(
    "",
    response_model=list[ServiceOut],
)
def list_all(
    q: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ServiceOut]:
    services = list_services(
        db,
        user=current_user,
        query=q,
    )

    return [
        serialize_service(service)
        for service in services
    ]


@router.post(
    "",
    response_model=ServiceOut,
    status_code=201,
)
def create(
    payload: ServiceIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ServiceOut:
    service = create_service(
        db,
        user=current_user,
        payload=payload,
    )

    return serialize_service(service)


@router.put(
    "/{service_id}",
    response_model=ServiceOut,
)
def update(
    service_id: UUID,
    payload: ServiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ServiceOut:
    service = update_service(
        db,
        user=current_user,
        service_id=service_id,
        payload=payload,
    )

    return serialize_service(service)


@router.delete(
    "/{service_id}",
    response_model=ServiceOut,
)
def deactivate(
    service_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ServiceOut:
    service = deactivate_service(
        db,
        user=current_user,
        service_id=service_id,
    )

    return serialize_service(service)


@router.post(
    "/import/preview",
    response_model=ServiceImportPreviewOut,
)
async def preview_import(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ServiceImportPreviewOut:
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Please select a CSV file.",
        )

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported.",
        )

    content = await file.read()

    try:
        return preview_catalog_import(
            db,
            user=current_user,
            content=content,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.post(
    "/import",
    response_model=ServiceImportOut,
)
async def import_services(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ServiceImportOut:
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Please select a CSV file.",
        )

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported.",
        )

    content = await file.read()

    try:
        return import_catalog(
            db,
            user=current_user,
            content=content,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc