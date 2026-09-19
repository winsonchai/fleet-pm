# FleetPM — Multi-Company Fleet & Project Vehicle Management System

FleetPM is a multi-tenant fleet operations platform designed for project-based enterprises (such as construction, civil engineering, and regional logistics). It enables organizations to manage vehicle assignments, enforce strict company data isolation, track project dispatches, and record vehicle mileage.

---

## Key Features

- **Multi-Tenant Data Isolation**: Strict tenant scoping across companies (e.g. Apex Infrastructure Ltd vs Summit Logistics Group) for all vehicles, projects, drivers, categories, and logs.
- **Interactive KPI Dashboard**: Real-time fleet metrics (Total Fleet, Available, On Trip, Maintenance, Active Projects) with live on-trip vehicle status cards.
- **Vehicle Catalog & Status Tracking**: Real-time fleet status (`available`, `in_use`, `maintenance`), odometer tracking, fuel types, and active assignment badges.
- **Trip Check-Out & Check-In**:
  - **Check Out**: Assign vehicles to active projects and drivers with departure odometer validation.
  - **Check In**: Return vehicles with return odometer validation, automated distance calculation, and condition notes.
- **Project Allocation**: Project lifecycle tracking with active vehicle checkout counters and search.
- **Audit Trail & Usage Logs**: Historical logs of all vehicle checkouts, drivers, departure/arrival timestamps, and distance traveled.
- **1-Click Demo Persona Switcher**: Top banner to switch between Apex Admin, Apex Driver, Summit Admin, and Super Admin in real-time.

---

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0, SQLite (WAL mode, foreign key enforcement), Pydantic v2, PyJWT.
- **Frontend**: Vanilla HTML5, modern CSS (glassmorphic dark design system, responsive grids), Vanilla JavaScript.
- **Package Manager & Tooling**: [uv](https://github.com/astral-sh/uv), Pytest.

---

## Quick Start

### 1. Install Dependencies
```powershell
uv sync
```

### 2. Seed Demo Data (Optional)
The database automatically initializes and seeds default multi-company demo data on startup if empty:
```powershell
uv run python -m backend.seed
```

### 3. Run the Application
Start the unified server (serves both API and frontend):
```powershell
uv run uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Open your browser to:
- **Web App**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Interactive API Documentation (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Running Automated Tests

Run the multi-tenant isolation and security test suite:
```powershell
uv run pytest tests/test_isolation.py -v
```

---

## Demo Accounts

| Role | Email | Password | Company |
|---|---|---|---|
| **Company Admin** | `alex@apex.com` | `password123` | Apex Infrastructure Ltd |
| **Project Manager** | `sarah@apex.com` | `password123` | Apex Infrastructure Ltd |
| **Driver** | `dave@apex.com` | `password123` | Apex Infrastructure Ltd |
| **Company Admin** | `elena@summit.com` | `password123` | Summit Logistics Group |
| **Driver** | `ken@summit.com` | `password123` | Summit Logistics Group |
| **Super Admin** | `admin@fleetpm.com` | `admin123` | System Administrator |
