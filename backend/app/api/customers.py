from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entities import Customer
from app.schemas.common import CustomerIn, CustomerOut
from app.services.invoices import upsert_customer

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=list[CustomerOut])
def list_all(db: Session = Depends(get_db)) -> list[CustomerOut]:
    rows = db.execute(select(Customer).order_by(Customer.name)).scalars().all()
    return [CustomerOut.model_validate(row) for row in rows]


@router.post("", response_model=CustomerOut, status_code=201)
def create(payload: CustomerIn, db: Session = Depends(get_db)) -> CustomerOut:
    customer = upsert_customer(db, payload)
    db.commit()
    db.refresh(customer)
    return CustomerOut.model_validate(customer)
