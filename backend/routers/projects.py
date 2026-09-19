"""Projects management router with company tenant isolation."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import get_db
from backend.models import Project, VehicleUsageLog, User
from backend.schemas import ProjectCreate, ProjectUpdate, ProjectRead
from backend.security import get_current_user, get_company_context

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.get("", response_model=List[ProjectRead])
@router.get("/", response_model=List[ProjectRead])
def list_projects(
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company_id = get_company_context(current_user)
    query = db.query(Project).filter(Project.company_id == company_id)

    if status:
        query = query.filter(Project.status == status)

    if q and q.strip():
        search_term = f"%{q.strip()}%"
        query = query.filter(
            Project.project_name.ilike(search_term)
            | Project.project_code.ilike(search_term)
            | Project.client_name.ilike(search_term)
        )

    projects = query.order_by(Project.created_at.desc()).all()
    result = []
    for proj in projects:
        active_veh = (
            db.query(func.count(VehicleUsageLog.id))
            .filter(
                VehicleUsageLog.project_id == proj.id,
                VehicleUsageLog.status == "active",
            )
            .scalar()
            or 0
        )
        read_obj = ProjectRead.model_validate(proj)
        read_obj.active_vehicles_count = active_veh
        result.append(read_obj)
    return result


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    req: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company_id = get_company_context(current_user)
    existing = (
        db.query(Project)
        .filter(
            Project.company_id == company_id,
            Project.project_code == req.project_code.strip(),
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project code '{req.project_code}' already exists in your company.",
        )

    project = Project(
        company_id=company_id,
        project_name=req.project_name.strip(),
        project_code=req.project_code.strip(),
        client_name=req.client_name.strip() if req.client_name else None,
        site_location=req.site_location.strip() if req.site_location else None,
        start_date=req.start_date,
        end_date=req.end_date,
        status=req.status,
        description=req.description.strip() if req.description else None,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    read_obj = ProjectRead.model_validate(project)
    read_obj.active_vehicles_count = 0
    return read_obj


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company_id = get_company_context(current_user)
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.company_id == company_id)
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    active_veh = (
        db.query(func.count(VehicleUsageLog.id))
        .filter(
            VehicleUsageLog.project_id == project.id,
            VehicleUsageLog.status == "active",
        )
        .scalar()
        or 0
    )
    read_obj = ProjectRead.model_validate(project)
    read_obj.active_vehicles_count = active_veh
    return read_obj


@router.put("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: int,
    req: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company_id = get_company_context(current_user)
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.company_id == company_id)
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)

    db.commit()
    db.refresh(project)
    read_obj = ProjectRead.model_validate(project)
    return read_obj


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company_id = get_company_context(current_user)
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.company_id == company_id)
        .first()
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    active_logs = (
        db.query(VehicleUsageLog)
        .filter(
            VehicleUsageLog.project_id == project.id,
            VehicleUsageLog.status == "active",
        )
        .first()
    )
    if active_logs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete project with active vehicle checkouts. Return vehicles first.",
        )

    db.delete(project)
    db.commit()
    return None
