"""Vehicle usage logs router: who used what, when, and for which project."""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import VehicleUsageLog, Vehicle, Project, User
from backend.schemas import CheckOutRequest, CheckInRequest, UsageLogRead
from backend.security import get_current_user, get_company_context

router = APIRouter(prefix="/api/logs", tags=["Usage Logs"])


def _populate_log_read(log: VehicleUsageLog) -> UsageLogRead:
    read_obj = UsageLogRead.model_validate(log)
    if log.vehicle:
        read_obj.vehicle_plate = log.vehicle.plate_number
        read_obj.vehicle_model = log.vehicle.model_name
    if log.project:
        read_obj.project_name = log.project.project_name
        read_obj.project_code = log.project.project_code
    if log.driver:
        read_obj.driver_name = log.driver.name
        read_obj.driver_email = log.driver.email
    if log.end_odometer is not None and log.start_odometer is not None:
        read_obj.distance_traveled = round(log.end_odometer - log.start_odometer, 2)
    return read_obj


@router.get("", response_model=List[UsageLogRead])
@router.get("/", response_model=List[UsageLogRead])
def list_logs(
    status: Optional[str] = Query(None),
    vehicle_id: Optional[int] = Query(None),
    project_id: Optional[int] = Query(None),
    driver_id: Optional[int] = Query(None),
    q: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List vehicle usage logs strictly within current user's company.
    Supports filtering by vehicle, project, driver, or active/completed status.
    """
    company_id = get_company_context(current_user)
    query = db.query(VehicleUsageLog).filter(VehicleUsageLog.company_id == company_id)

    if status:
        query = query.filter(VehicleUsageLog.status == status)
    if vehicle_id:
        query = query.filter(VehicleUsageLog.vehicle_id == vehicle_id)
    if project_id:
        query = query.filter(VehicleUsageLog.project_id == project_id)
    if driver_id:
        query = query.filter(VehicleUsageLog.driver_id == driver_id)

    if q and q.strip():
        search = f"%{q.strip()}%"
        query = (
            query.join(Vehicle, VehicleUsageLog.vehicle_id == Vehicle.id)
            .join(Project, VehicleUsageLog.project_id == Project.id)
            .join(User, VehicleUsageLog.driver_id == User.id)
            .filter(
                Vehicle.plate_number.ilike(search)
                | Vehicle.model_name.ilike(search)
                | Project.project_name.ilike(search)
                | Project.project_code.ilike(search)
                | User.name.ilike(search)
            )
        )

    logs = query.order_by(VehicleUsageLog.checkout_time.desc()).limit(limit).all()
    return [_populate_log_read(l) for l in logs]


@router.post("/checkout", response_model=UsageLogRead, status_code=status.HTTP_201_CREATED)
def checkout_vehicle(
    req: CheckOutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Check out a vehicle for a project.
    Records driver, project, checkout timestamp, and starting odometer.
    Sets vehicle status to 'in_use'.
    """
    company_id = get_company_context(current_user)

    vehicle = (
        db.query(Vehicle)
        .filter(Vehicle.id == req.vehicle_id, Vehicle.company_id == company_id)
        .first()
    )
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found in your company",
        )

    if vehicle.status == "in_use":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vehicle '{vehicle.plate_number}' is already in use by another trip",
        )

    if vehicle.status == "maintenance":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vehicle '{vehicle.plate_number}' is currently undergoing maintenance",
        )

    project = (
        db.query(Project)
        .filter(Project.id == req.project_id, Project.company_id == company_id)
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found in your company",
        )

    driver_id = req.driver_id if req.driver_id else current_user.id
    driver = (
        db.query(User)
        .filter(User.id == driver_id, User.company_id == company_id)
        .first()
    )
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Driver not found in your company",
        )

    start_odo = req.start_odometer if req.start_odometer is not None else vehicle.current_odometer
    if start_odo < vehicle.current_odometer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Start odometer ({start_odo}) cannot be less than vehicle's current recorded odometer ({vehicle.current_odometer})",
        )

    new_log = VehicleUsageLog(
        company_id=company_id,
        vehicle_id=vehicle.id,
        project_id=project.id,
        driver_id=driver.id,
        checkout_time=datetime.now(timezone.utc),
        start_odometer=start_odo,
        purpose=req.purpose.strip() if req.purpose else None,
        condition_notes=req.condition_notes.strip() if req.condition_notes else None,
        status="active",
    )
    db.add(new_log)
    vehicle.status = "in_use"
    vehicle.current_odometer = start_odo
    db.commit()
    db.refresh(new_log)
    return _populate_log_read(new_log)


@router.post("/{log_id}/checkin", response_model=UsageLogRead)
def checkin_vehicle(
    log_id: int,
    req: CheckInRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Check in a currently checked-out vehicle.
    Records return timestamp, ending odometer, and calculates distance traveled.
    Returns vehicle status to 'available'.
    """
    company_id = get_company_context(current_user)

    log = (
        db.query(VehicleUsageLog)
        .filter(VehicleUsageLog.id == log_id, VehicleUsageLog.company_id == company_id)
        .first()
    )
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usage log record not found",
        )

    if log.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"This trip log is already '{log.status}'",
        )

    if req.end_odometer < log.start_odometer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"End odometer ({req.end_odometer}) cannot be less than start odometer ({log.start_odometer})",
        )

    vehicle = db.query(Vehicle).filter(Vehicle.id == log.vehicle_id).first()

    log.checkin_time = datetime.now(timezone.utc)
    log.end_odometer = req.end_odometer
    log.status = "completed"
    if req.condition_notes:
        existing_notes = log.condition_notes or ""
        log.condition_notes = f"{existing_notes}\nReturn: {req.condition_notes.strip()}".strip()

    if vehicle:
        vehicle.status = "available"
        vehicle.current_odometer = req.end_odometer

    db.commit()
    db.refresh(log)
    return _populate_log_read(log)
