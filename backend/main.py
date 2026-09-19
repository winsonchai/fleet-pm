"""FastAPI application entrypoint for FleetPM - Multi-Company Fleet Management System."""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.database import Base, engine
from backend.routers import (
    auth,
    companies,
    categories,
    projects,
    vehicles,
    logs,
    dashboard,
)

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FleetPM - Multi-Company Fleet Management System",
    description="Multi-tenant fleet and vehicle usage management system for project-based enterprises.",
    version="1.0.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(categories.router)
app.include_router(projects.router)
app.include_router(vehicles.router)
app.include_router(logs.router)
app.include_router(dashboard.router)


@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "fleet_pm_backend"}


# Serve frontend static assets if directory exists and has files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir) and os.path.exists(os.path.join(frontend_dir, "index.html")):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
