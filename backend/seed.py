"""Seed database with realistic multi-company demonstration data."""
from datetime import datetime, timedelta, timezone
from backend.database import SessionLocal, Base, engine
from backend.models import Company, User, Project, VehicleCategory, Vehicle, VehicleUsageLog
from backend.security import hash_password


def seed():
    # Initialize database tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(Company).first():
            print("Database already contains data, skipping seed.")
            return

        print("Seeding database with multi-company demonstration data...")

        # ---------------- 1. Super Admin ----------------
        super_admin = User(
            name="System Administrator",
            email="admin@fleetpm.com",
            password_hash=hash_password("admin123"),
            role="super_admin",
            phone="+1 800 555 0100",
            status="active"
        )
        db.add(super_admin)
        db.flush()

        # ---------------- 2. Company 1: Apex Infrastructure Ltd ----------------
        company_apex = Company(
            name="Apex Infrastructure Ltd",
            code="APEX",
            status="active"
        )
        db.add(company_apex)
        db.flush()

        # Apex Users
        apex_admin = User(
            company_id=company_apex.id,
            name="Alex Morgan",
            email="alex@apex.com",
            password_hash=hash_password("password123"),
            role="company_admin",
            phone="+1 555 0191",
            status="active"
        )
        apex_pm = User(
            company_id=company_apex.id,
            name="Sarah Lin",
            email="sarah@apex.com",
            password_hash=hash_password("password123"),
            role="project_manager",
            phone="+1 555 0192",
            status="active"
        )
        apex_driver = User(
            company_id=company_apex.id,
            name="Dave Miller",
            email="dave@apex.com",
            password_hash=hash_password("password123"),
            role="driver",
            phone="+1 555 0193",
            status="active"
        )
        db.add_all([apex_admin, apex_pm, apex_driver])
        db.flush()

        # Apex Categories
        apex_cat_truck = VehicleCategory(company_id=company_apex.id, name="Pickup Trucks", icon="truck", description="4x4 Crew cabs for site surveying & tools")
        apex_cat_heavy = VehicleCategory(company_id=company_apex.id, name="Heavy Haulers & Tippers", icon="shield", description="Earthmoving and material transport")
        apex_cat_van = VehicleCategory(company_id=company_apex.id, name="Site Utility Vans", icon="package", description="Mobile workshops and parts delivery")
        db.add_all([apex_cat_truck, apex_cat_heavy, apex_cat_van])
        db.flush()

        # Apex Projects
        apex_p1 = Project(
            company_id=company_apex.id,
            project_name="Metro Highway Expansion Phase 2",
            project_code="MHE-2026",
            client_name="State Dept of Transportation",
            site_location="East Corridor Junction 4",
            start_date="2026-02-01",
            end_date="2026-11-30",
            status="in_progress",
            description="Widening 18km of highway including drainage, culverts, and asphalt paving."
        )
        apex_p2 = Project(
            company_id=company_apex.id,
            project_name="Riverside Bridge Rehabilitation",
            project_code="RBR-104",
            client_name="City Council",
            site_location="Riverside North Pier",
            start_date="2026-03-15",
            end_date="2026-08-30",
            status="in_progress",
            description="Structural reinforcement and bearing replacement for municipal bridge."
        )
        apex_p3 = Project(
            company_id=company_apex.id,
            project_name="Harbor Container Terminal Groundwork",
            project_code="HCT-09",
            client_name="Maritime Logistics Port",
            site_location="Pier 4 Deep Water Terminal",
            start_date="2026-06-01",
            end_date="2027-01-15",
            status="planning",
            description="Soil stabilization, grading, and concrete foundations for container berths."
        )
        db.add_all([apex_p1, apex_p2, apex_p3])
        db.flush()

        # Apex Vehicles
        apex_v1 = Vehicle(
            company_id=company_apex.id,
            category_id=apex_cat_truck.id,
            plate_number="APX-881",
            model_name="Toyota Hilux 2.8L 4x4",
            vin_number="MR0HA3CD9K0192841",
            year=2024,
            color="Silver",
            fuel_type="diesel",
            current_odometer=34200.0,
            status="in_use",
            notes="Fitted with tool racks and site strobe beacon"
        )
        apex_v2 = Vehicle(
            company_id=company_apex.id,
            category_id=apex_cat_truck.id,
            plate_number="APX-412",
            model_name="Ford F-250 Super Duty",
            vin_number="1FT8W2BT3KE194827",
            year=2023,
            color="White",
            fuel_type="diesel",
            current_odometer=51150.0,
            status="available",
            notes="Heavy tow package installed"
        )
        apex_v3 = Vehicle(
            company_id=company_apex.id,
            category_id=apex_cat_heavy.id,
            plate_number="APX-900",
            model_name="Volvo FMX 400 Tipper",
            vin_number="YV2R4B0A9MA982310",
            year=2022,
            color="Yellow",
            fuel_type="diesel",
            current_odometer=112400.0,
            status="available",
            notes="Periodic hydraulic inspection passed last week"
        )
        apex_v4 = Vehicle(
            company_id=company_apex.id,
            category_id=apex_cat_van.id,
            plate_number="APX-305",
            model_name="Mercedes Sprinter 316 CDI",
            vin_number="WDB9066331P847291",
            year=2021,
            color="Dark Gray",
            fuel_type="diesel",
            current_odometer=67450.0,
            status="maintenance",
            notes="Scheduled 60k service and brake pad replacement"
        )
        db.add_all([apex_v1, apex_v2, apex_v3, apex_v4])
        db.flush()

        # Apex Usage Logs:
        # Completed log
        log_apex_completed = VehicleUsageLog(
            company_id=company_apex.id,
            vehicle_id=apex_v2.id,
            project_id=apex_p2.id,
            driver_id=apex_driver.id,
            checkout_time=datetime.now(timezone.utc) - timedelta(days=2, hours=8),
            checkin_time=datetime.now(timezone.utc) - timedelta(days=2, hours=1),
            start_odometer=50980.0,
            end_odometer=51150.0,
            purpose="Delivered hydraulic jacks and steel reinforcement rods to bridge pier",
            condition_notes="All good, refueled before return",
            status="completed"
        )
        # Active in-progress log for APX-881
        log_apex_active = VehicleUsageLog(
            company_id=company_apex.id,
            vehicle_id=apex_v1.id,
            project_id=apex_p1.id,
            driver_id=apex_driver.id,
            checkout_time=datetime.now(timezone.utc) - timedelta(hours=3, minutes=20),
            checkin_time=None,
            start_odometer=34200.0,
            purpose="Site inspection with civil engineer across Junction 4 earthworks",
            condition_notes="Clean condition, tire pressure checked",
            status="active"
        )
        db.add_all([log_apex_completed, log_apex_active])

        # ---------------- 3. Company 2: Summit Logistics Group ----------------
        company_summit = Company(
            name="Summit Logistics Group",
            code="SUMMIT",
            status="active"
        )
        db.add(company_summit)
        db.flush()

        # Summit Users
        summit_admin = User(
            company_id=company_summit.id,
            name="Elena Vance",
            email="elena@summit.com",
            password_hash=hash_password("password123"),
            role="company_admin",
            phone="+1 555 0281",
            status="active"
        )
        summit_driver = User(
            company_id=company_summit.id,
            name="Ken Adams",
            email="ken@summit.com",
            password_hash=hash_password("password123"),
            role="driver",
            phone="+1 555 0282",
            status="active"
        )
        db.add_all([summit_admin, summit_driver])
        db.flush()

        # Summit Categories
        summit_cat_van = VehicleCategory(company_id=company_summit.id, name="Delivery Vans", icon="package", description="Courier and parcels cargo vans")
        summit_cat_exec = VehicleCategory(company_id=company_summit.id, name="Executive Fleet", icon="car", description="Client transfers and corporate travel")
        db.add_all([summit_cat_van, summit_cat_exec])
        db.flush()

        # Summit Projects
        summit_p1 = Project(
            company_id=company_summit.id,
            project_name="Urban Last-Mile Fulfillment Q3",
            project_code="ULM-2026",
            client_name="E-Commerce Hub Global",
            site_location="Downtown Distribution Center",
            start_date="2026-01-01",
            end_date="2026-09-30",
            status="in_progress",
            description="Same-day delivery routing across central metropolitan area."
        )
        summit_p2 = Project(
            company_id=company_summit.id,
            project_name="Airport Express Shuttle Contract",
            project_code="AES-88",
            client_name="International Skyways",
            site_location="Terminal 3 VIP Lounge",
            start_date="2026-03-01",
            end_date="2026-12-31",
            status="in_progress",
            description="Executive and crew shuttle operations between airport and city hotels."
        )
        db.add_all([summit_p1, summit_p2])
        db.flush()

        # Summit Vehicles
        summit_v1 = Vehicle(
            company_id=company_summit.id,
            category_id=summit_cat_van.id,
            plate_number="SMT-101",
            model_name="Ford Transit Cargo High Roof",
            vin_number="1FTNE3Y89LKA01928",
            year=2023,
            color="Navy Blue",
            fuel_type="diesel",
            current_odometer=45600.0,
            status="available",
            notes="GPS tracking unit verified"
        )
        summit_v2 = Vehicle(
            company_id=company_summit.id,
            category_id=summit_cat_exec.id,
            plate_number="SMT-202",
            model_name="Tesla Model Y Long Range",
            vin_number="5YJSA1E28MF928172",
            year=2024,
            color="Pearl White",
            fuel_type="electric",
            current_odometer=18900.0,
            status="in_use",
            notes="Includes fast-charging cables and VIP interior trim"
        )
        db.add_all([summit_v1, summit_v2])
        db.flush()

        # Summit Active Log
        log_summit_active = VehicleUsageLog(
            company_id=company_summit.id,
            vehicle_id=summit_v2.id,
            project_id=summit_p2.id,
            driver_id=summit_driver.id,
            checkout_time=datetime.now(timezone.utc) - timedelta(hours=1, minutes=45),
            checkin_time=None,
            start_odometer=18900.0,
            purpose="Morning flight arrival VIP transport for airline executives",
            condition_notes="100% battery charge at departure",
            status="active"
        )
        db.add(log_summit_active)

        db.commit()
        print("Database seeded successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
