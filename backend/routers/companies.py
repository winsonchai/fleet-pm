"""Company management router with tenant scoping."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Company, User
from backend.schemas import CompanyRead, CompanyCreate
from backend.security import get_current_user

router = APIRouter(prefix="/api/companies", tags=["Companies"])


@router.get("", response_model=List[CompanyRead])
@router.get("/", response_model=List[CompanyRead])
def list_companies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == "super_admin":
        return db.query(Company).order_by(Company.name).all()
    if not current_user.company_id:
        return []
    company = db.query(Company).filter(Company.id == current_user.company_id).all()
    return company


@router.post("", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
def create_company(
    req: CompanyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Admins can create new companies",
        )

    code_clean = req.code.upper().strip()
    existing = db.query(Company).filter(Company.code == code_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Company code '{req.code}' is already taken",
        )

    comp = Company(
        name=req.name.strip(),
        code=code_clean,
        status=req.status,
    )
    db.add(comp)
    db.commit()
    db.refresh(comp)
    return comp
