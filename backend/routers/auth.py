"""Authentication and user management router."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, Company
from backend.schemas import LoginRequest, Token, UserRead, UserCreate, UserSimple
from backend.security import (
    verify_password,
    hash_password,
    create_access_token,
    get_current_user,
    get_company_context,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def _user_to_read(user: User, db: Session) -> UserRead:
    company_name = None
    if user.company_id:
        comp = db.query(Company).filter(Company.id == user.company_id).first()
        if comp:
            company_name = comp.name
    return UserRead(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        phone=user.phone,
        company_id=user.company_id,
        status=user.status,
        created_at=user.created_at,
        company_name=company_name,
    )


@router.post("/login", response_model=Token)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email.strip().lower()).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended or deactivated",
        )

    if user.company_id:
        comp = db.query(Company).filter(Company.id == user.company_id).first()
        if comp and comp.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your company account is inactive",
            )

    token = create_access_token(
        data={"sub": str(user.id), "company_id": user.company_id, "role": user.role}
    )
    return Token(access_token=token, token_type="bearer", user=_user_to_read(user, db))


@router.get("/me", response_model=UserRead)
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _user_to_read(current_user, db)


@router.get("/users", response_model=List[UserSimple])
def list_company_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company_id = get_company_context(current_user)
    users = (
        db.query(User)
        .filter(User.company_id == company_id, User.status == "active")
        .order_by(User.name)
        .all()
    )
    return users


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_company_user(
    req: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role not in ("super_admin", "company_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can register users",
        )

    company_id = get_company_context(current_user, req.company_id)
    existing = db.query(User).filter(User.email == req.email.strip().lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    new_user = User(
        company_id=company_id,
        name=req.name.strip(),
        email=req.email.strip().lower(),
        password_hash=hash_password(req.password),
        role=req.role,
        phone=req.phone,
        status="active",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return _user_to_read(new_user, db)
