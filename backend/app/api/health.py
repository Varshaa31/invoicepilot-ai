from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.common import HealthOut


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
def health(db: Session = Depends(get_db)) -> HealthOut:
    settings = get_settings()

    database = "ok"

    try:
        db.execute(text("SELECT 1"))
    except Exception:
        database = "unavailable"

    return HealthOut(
        status="ok" if database == "ok" else "degraded",
        database=database,
        groq_configured=bool(settings.groq_api_key),
    )