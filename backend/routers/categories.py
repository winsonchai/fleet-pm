"""Vehicle categories router with company tenant isolation."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import get_db
from backend.models import VehicleCategory, Vehicle, User
from backend.schemas import VehicleCategoryCreate, VehicleCategoryRead, VehicleCategoryUpdate
from backend.security import get_current_user, get_company_context

router = APIRouter(prefix="/api/categories", tags=["Categories"])


@router.get("", response_model=List[VehicleCategoryRead])
@router.get("/", response_model=List[VehicleCategoryRead])
def list_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company_id = get_company_context(current_user)
    categories = (
        db.query(VehicleCategory)
        .filter(VehicleCategory.company_id == company_id)
        .order_by(VehicleCategory.name)
        .all()
    )
    result = []
    for cat in categories:
        count = (
            db.query(func.count(Vehicle.id))
            .filter(Vehicle.category_id == cat.id)
            .scalar()
            or 0
        )
        read_obj = VehicleCategoryRead.model_validate(cat)
        read_obj.vehicle_count = count
        result.append(read_obj)
    return result


@router.post("", response_model=VehicleCategoryRead, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=VehicleCategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    req: VehicleCategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company_id = get_company_context(current_user)
    existing = (
        db.query(VehicleCategory)
        .filter(
            VehicleCategory.company_id == company_id,
            VehicleCategory.name == req.name.strip(),
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category '{req.name}' already exists in your company.",
        )

    cat = VehicleCategory(
        company_id=company_id,
        name=req.name.strip(),
        icon=req.icon.strip() if req.icon else "truck",
        description=req.description.strip() if req.description else None,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    read_obj = VehicleCategoryRead.model_validate(cat)
    read_obj.vehicle_count = 0
    return read_obj


@router.put("/{category_id}", response_model=VehicleCategoryRead)
def update_category(
    category_id: int,
    req: VehicleCategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company_id = get_company_context(current_user)
    cat = (
        db.query(VehicleCategory)
        .filter(
            VehicleCategory.id == category_id,
            VehicleCategory.company_id == company_id,
        )
        .first()
    )
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    if req.name and req.name.strip() != cat.name:
        existing = (
            db.query(VehicleCategory)
            .filter(
                VehicleCategory.company_id == company_id,
                VehicleCategory.name == req.name.strip(),
                VehicleCategory.id != category_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{req.name}' already exists in your company.",
            )
        cat.name = req.name.strip()

    if req.icon is not None:
        cat.icon = req.icon.strip() if req.icon else "truck"

    if req.description is not None:
        cat.description = req.description.strip() if req.description else None

    db.commit()
    db.refresh(cat)
    read_obj = VehicleCategoryRead.model_validate(cat)
    read_obj.vehicle_count = (
        db.query(func.count(Vehicle.id))
        .filter(Vehicle.category_id == cat.id)
        .scalar()
        or 0
    )
    return read_obj


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company_id = get_company_context(current_user)
    cat = (
        db.query(VehicleCategory)
        .filter(
            VehicleCategory.id == category_id,
            VehicleCategory.company_id == company_id,
        )
        .first()
    )
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    vehicles_using = db.query(Vehicle).filter(Vehicle.category_id == cat.id).count()
    if vehicles_using > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete category: {vehicles_using} vehicle(s) still belong to it.",
        )

    db.delete(cat)
    db.commit()
    return None
