"""Dashboard router aggregating company fleet metrics and active assignments."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import get_db
from backend.models import Vehicle, Project, VehicleUsageLog, User
from backend.schemas import DashboardStats
from backend.security import get_current_user, get_company_context
from backend.routers.logs import _populate_log_read

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Calculate fleet and project KPI summaries for the logged-in user's company."""
    company_id = get_company_context(current_user)

    total_vehicles = (
        db.query(func.count(Vehicle.id))
        .filter(Vehicle.company_id == company_id)
        .scalar()
        or 0
    )
    available_vehicles = (
        db.query(func.count(Vehicle.id))
        .filter(Vehicle.company_id == company_id, Vehicle.status == "available")
        .scalar()
        or 0
    )
    in_use_vehicles = (
        db.query(func.count(Vehicle.id))
        .filter(Vehicle.company_id == company_id, Vehicle.status == "in_use")
        .scalar()
        or 0
    )
    maint_vehicles = (
        db.query(func.count(Vehicle.id))
        .filter(Vehicle.company_id == company_id, Vehicle.status == "maintenance")
        .scalar()
        or 0
    )
    active_projects = (
        db.query(func.count(Project.id))
        .filter(
            Project.company_id == company_id,
            Project.status.in_(["in_progress", "planning"]),
        )
        .scalar()
        or 0
    )
    active_logs_count = (
        db.query(func.count(VehicleUsageLog.id))
        .filter(VehicleUsageLog.company_id == company_id, VehicleUsageLog.status == "active")
        .scalar()
        or 0
    )
    recent_logs = (
        db.query(VehicleUsageLog)
        .filter(VehicleUsageLog.company_id == company_id)
        .order_by(VehicleUsageLog.checkout_time.desc())
        .limit(8)
        .all()
    )

    return DashboardStats(
        total_vehicles=total_vehicles,
        available_vehicles=available_vehicles,
        in_use_vehicles=in_use_vehicles,
        maintenance_vehicles=maint_vehicles,
        active_projects=active_projects,
        active_logs_count=active_logs_count,
        recent_logs=[_populate_log_read(l) for l in recent_logs],
    )
