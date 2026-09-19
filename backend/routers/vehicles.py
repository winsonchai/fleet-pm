"""Vehicle fleet management router with company tenant isolation."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Vehicle, VehicleCategory, VehicleUsageLog, User
from backend.schemas import VehicleCreate, VehicleUpdate, VehicleRead
from backend.security import get_current_user, get_company_context

router = APIRouter(prefix="/api/vehicles", tags=["Vehicles"])


def _populate_vehicle_read(v: Vehicle, db: Session) -> VehicleRead:
    read_obj = VehicleRead.model_validate(v)
    if v.category:
        read_obj.category_name = v.category.name
        read_obj.category_icon = v.category.icon

    if v.status == "in_use":
        active_log = (
            db.query(VehicleUsageLog)
            .filter(
                VehicleUsageLog.vehicle_id == v.id,
                VehicleUsageLog.status == "active",
            )
            .order_by(VehicleUsageLog.checkout_time.desc())
            .first()
        )
        if active_log:
            read_obj.current_assignment = {
                "log_id": active_log.id,
                "project_id": active_log.project_id,
                "project_name": active_log.project.project_name if active_log.project else None,
                "project_code": active_log.project.project_code if active_log.project else None,
                "driver_id": active_log.driver_id,
                "driver_name": active_log.driver.name if active_log.driver else None,
                "checkout_time": active_log.checkout_time.isoformat() if active_log.checkout_time else None,
                "start_odometer": active_log.start_odometer,
                "purpose": active_log.purpose,
            }
    return read_obj


@router.get("", response_model=List[VehicleRead])
@router.get("/", response_model=List[VehicleRead])
def list_vehicles(
    category_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company_id = get_company_context(current_user)
    query = db.query(Vehicle).filter(Vehicle.company_id == company_id)

    if category_id:
        query = query.filter(Vehicle.category_id == category_id)

    if status:
        query = query.filter(Vehicle.status == status)

    if q and q.strip():
        search = f"%{q.strip()}%"
        query = query.filter(
            Vehicle.plate_number.ilike(search)
            | Vehicle.model_name.ilike(search)
            | Vehicle.vin_number.ilike(search)
        )

    vehicles = query.order_by(Vehicle.plate_number.asc()).all()
    return [_populate_vehicle_read(v, db) for v in vehicles]


@router.post("", response_model=VehicleRead, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=VehicleRead, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    req: VehicleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company_id = get_company_context(current_user)

    category = (
        db.query(VehicleCategory)
        .filter(
            VehicleCategory.id == req.category_id,
            VehicleCategory.company_id == company_id,
        )
        .first()
    )
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid vehicle category ID",
        )

    plate = req.plate_number.strip().upper()
    existing = (
        db.query(Vehicle)
        .filter(Vehicle.company_id == company_id, Vehicle.plate_number == plate)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vehicle with plate '{plate}' already exists in your fleet",
        )

    vehicle = Vehicle(
        company_id=company_id,
        category_id=req.category_id,
        plate_number=plate,
        model_name=req.model_name.strip(),
        vin_number=req.vin_number.strip() if req.vin_number else None,
        year=req.year,
        color=req.color.strip() if req.color else None,
        fuel_type=req.fuel_type,
        current_odometer=req.current_odometer,
        status=req.status,
        notes=req.notes.strip() if req.notes else None,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return _populate_vehicle_read(vehicle, db)


@router.get("/{vehicle_id}", response_model=VehicleRead)
def get_vehicle(
    vehicle_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company_id = get_company_context(current_user)
    vehicle = (
        db.query(Vehicle)
        .filter(Vehicle.id == vehicle_id, Vehicle.company_id == company_id)
        .first()
    )
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )
    return _populate_vehicle_read(vehicle, db)


@router.put("/{vehicle_id}", response_model=VehicleRead)
def update_vehicle(
    vehicle_id: int,
    req: VehicleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company_id = get_company_context(current_user)
    vehicle = (
        db.query(Vehicle)
        .filter(Vehicle.id == vehicle_id, Vehicle.company_id == company_id)
        .first()
    )
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )

    update_data = req.model_dump(exclude_unset=True)
    if "plate_number" in update_data and update_data["plate_number"]:
        update_data["plate_number"] = update_data["plate_number"].strip().upper()

    if "category_id" in update_data and update_data["category_id"]:
        category = (
            db.query(VehicleCategory)
            .filter(
                VehicleCategory.id == update_data["category_id"],
                VehicleCategory.company_id == company_id,
            )
            .first()
        )
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid vehicle category ID",
            )

    for key, value in update_data.items():
        setattr(vehicle, key, value)

    db.commit()
    db.refresh(vehicle)
    return _populate_vehicle_read(vehicle, db)


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(
    vehicle_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company_id = get_company_context(current_user)
    vehicle = (
        db.query(Vehicle)
        .filter(Vehicle.id == vehicle_id, Vehicle.company_id == company_id)
        .first()
    )
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )

    if vehicle.status == "in_use":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete vehicle while it is currently checked out",
        )

    db.delete(vehicle)
    db.commit()
    return None
