"""Pydantic schemas for data validation and API request/response serialization."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: str
    phone: Optional[str] = None
    company_id: Optional[int] = None
    status: str
    created_at: datetime
    company_name: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class LoginRequest(BaseModel):
    email: str
    password: str


class UserSimple(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: str


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=6)
    role: str = Field("driver", pattern="^(super_admin|company_admin|project_manager|driver)$")
    phone: Optional[str] = None
    company_id: Optional[int] = None


class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=20)
    status: str = "active"


class CompanyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    status: str
    created_at: datetime


class ProjectCreate(BaseModel):
    project_name: str = Field(..., min_length=2, max_length=150)
    project_code: str = Field(..., min_length=2, max_length=50)
    client_name: Optional[str] = None
    site_location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: str = "in_progress"
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    project_code: Optional[str] = None
    client_name: Optional[str] = None
    site_location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    project_name: str
    project_code: str
    client_name: Optional[str] = None
    site_location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: str
    description: Optional[str] = None
    created_at: datetime
    active_vehicles_count: Optional[int] = 0


class VehicleCategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    icon: str = "truck"
    description: Optional[str] = None


class VehicleCategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    name: str
    icon: str
    description: Optional[str] = None
    created_at: datetime
    vehicle_count: Optional[int] = 0


class VehicleCreate(BaseModel):
    category_id: int
    plate_number: str = Field(..., min_length=2, max_length=50)
    model_name: str = Field(..., min_length=2, max_length=100)
    vin_number: Optional[str] = None
    year: Optional[int] = None
    color: Optional[str] = None
    fuel_type: str = "diesel"
    current_odometer: float = Field(0.0, ge=0)
    status: str = "available"
    notes: Optional[str] = None


class VehicleUpdate(BaseModel):
    category_id: Optional[int] = None
    plate_number: Optional[str] = None
    model_name: Optional[str] = None
    vin_number: Optional[str] = None
    year: Optional[int] = None
    color: Optional[str] = None
    fuel_type: Optional[str] = None
    current_odometer: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class VehicleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    category_id: int
    plate_number: str
    model_name: str
    vin_number: Optional[str] = None
    year: Optional[int] = None
    color: Optional[str] = None
    fuel_type: str
    current_odometer: float
    status: str
    notes: Optional[str] = None
    created_at: datetime
    category_name: Optional[str] = None
    category_icon: Optional[str] = None
    current_assignment: Optional[Dict[str, Any]] = None


class CheckOutRequest(BaseModel):
    vehicle_id: int
    project_id: int
    driver_id: Optional[int] = None
    start_odometer: Optional[float] = None
    purpose: Optional[str] = None
    condition_notes: Optional[str] = None


class CheckInRequest(BaseModel):
    end_odometer: float
    condition_notes: Optional[str] = None


class UsageLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    vehicle_id: int
    project_id: int
    driver_id: int
    checkout_time: datetime
    checkin_time: Optional[datetime] = None
    start_odometer: float
    end_odometer: Optional[float] = None
    distance_traveled: Optional[float] = None
    purpose: Optional[str] = None
    condition_notes: Optional[str] = None
    status: str
    created_at: datetime
    vehicle_plate: Optional[str] = None
    vehicle_model: Optional[str] = None
    project_name: Optional[str] = None
    project_code: Optional[str] = None
    driver_name: Optional[str] = None
    driver_email: Optional[str] = None


class DashboardStats(BaseModel):
    total_vehicles: int
    available_vehicles: int
    in_use_vehicles: int
    maintenance_vehicles: int
    active_projects: int
    active_logs_count: int
    recent_logs: List[UsageLogRead]
