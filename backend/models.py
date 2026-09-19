from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.database import Base


def get_utc_now():
    return datetime.now(timezone.utc)


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, index=True, nullable=False)
    status = Column(String(20), default="active", nullable=False)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    users = relationship("User", back_populates="company", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="company", cascade="all, delete-orphan")
    categories = relationship("VehicleCategory", back_populates="company", cascade="all, delete-orphan")
    vehicles = relationship("Vehicle", back_populates="company", cascade="all, delete-orphan")
    usage_logs = relationship("VehicleUsageLog", back_populates="company", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), default="driver", nullable=False)
    phone = Column(String(30), nullable=True)
    status = Column(String(20), default="active", nullable=False)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    company = relationship("Company", back_populates="users")
    driven_logs = relationship("VehicleUsageLog", back_populates="driver")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    project_name = Column(String(150), nullable=False)
    project_code = Column(String(50), nullable=False, index=True)
    client_name = Column(String(100), nullable=True)
    site_location = Column(String(150), nullable=True)
    start_date = Column(String(20), nullable=True)
    end_date = Column(String(20), nullable=True)
    status = Column(String(30), default="in_progress", nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    company = relationship("Company", back_populates="projects")
    usage_logs = relationship("VehicleUsageLog", back_populates="project")


class VehicleCategory(Base):
    __tablename__ = "vehicle_categories"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(80), nullable=False)
    icon = Column(String(50), default="truck", nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    company = relationship("Company", back_populates="categories")
    vehicles = relationship("Vehicle", back_populates="category", cascade="all, delete-orphan")


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("vehicle_categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    plate_number = Column(String(50), nullable=False, index=True)
    model_name = Column(String(100), nullable=False)
    vin_number = Column(String(50), nullable=True)
    year = Column(Integer, nullable=True)
    color = Column(String(30), nullable=True)
    fuel_type = Column(String(30), default="diesel", nullable=False)
    current_odometer = Column(Float, default=0.0, nullable=False)
    status = Column(String(30), default="available", nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    company = relationship("Company", back_populates="vehicles")
    category = relationship("VehicleCategory", back_populates="vehicles")
    usage_logs = relationship("VehicleUsageLog", back_populates="vehicle")


class VehicleUsageLog(Base):
    __tablename__ = "vehicle_usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    driver_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    checkout_time = Column(DateTime, default=get_utc_now, nullable=False)
    checkin_time = Column(DateTime, nullable=True)
    start_odometer = Column(Float, nullable=False)
    end_odometer = Column(Float, nullable=True)
    purpose = Column(Text, nullable=True)
    condition_notes = Column(Text, nullable=True)
    status = Column(String(30), default="active", nullable=False)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    company = relationship("Company", back_populates="usage_logs")
    vehicle = relationship("Vehicle", back_populates="usage_logs")
    project = relationship("Project", back_populates="usage_logs")
    driver = relationship("User", back_populates="driven_logs")
