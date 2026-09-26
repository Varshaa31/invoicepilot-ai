from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.entities import User
from app.schemas.auth import AuthOut, LoginIn, SignupIn, UserOut

router = APIRouter(prefix="/auth", tags=["authentication"])


def serialize_user(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        workspace_name=user.workspace_name,
        email_verified=user.email_verified,
    )


@router.post("/signup", response_model=AuthOut, status_code=status.HTTP_201_CREATED)
def signup(
    payload: SignupIn,
    db: Session = Depends(get_db),
) -> AuthOut:
    if payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match.",
        )

    email = str(payload.email).strip().lower()

    existing_user = db.scalar(
        select(User).where(User.email == email)
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        name=payload.name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        email_verified=False,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(str(user.id))

    return AuthOut(
        access_token=access_token,
        user=serialize_user(user),
    )


@router.post("/login", response_model=AuthOut)
def login(
    payload: LoginIn,
    db: Session = Depends(get_db),
) -> AuthOut:
    email = str(payload.email).strip().lower()

    user = db.scalar(
        select(User).where(User.email == email)
    )

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    access_token = create_access_token(str(user.id))

    return AuthOut(
        access_token=access_token,
        user=serialize_user(user),
    )