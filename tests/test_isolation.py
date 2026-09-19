"""Multi-tenant isolation and security tests across companies (Apex vs Summit)."""
import pytest


def test_authentication_and_identity(client, apex_admin_headers, summit_admin_headers):
    """Verify that users authenticate and their company association is correctly populated."""
    res_apex = client.get("/api/auth/me", headers=apex_admin_headers)
    assert res_apex.status_code == 200
    data_apex = res_apex.json()
    assert data_apex["email"] == "alex@apex.com"
    assert data_apex["company_name"] == "Apex Infrastructure Ltd"

    res_summit = client.get("/api/auth/me", headers=summit_admin_headers)
    assert res_summit.status_code == 200
    data_summit = res_summit.json()
    assert data_summit["email"] == "elena@summit.com"
    assert data_summit["company_name"] == "Summit Logistics Group"


def test_vehicle_tenant_isolation(client, apex_admin_headers, summit_admin_headers):
    """Verify that a company can only view vehicles belonging to its own fleet."""
    # Apex vehicles
    res_apex = client.get("/api/vehicles", headers=apex_admin_headers)
    assert res_apex.status_code == 200
    apex_vehicles = res_apex.json()
    assert len(apex_vehicles) >= 4
    for v in apex_vehicles:
        assert v["plate_number"].startswith("APX-")

    # Summit vehicles
    res_summit = client.get("/api/vehicles", headers=summit_admin_headers)
    assert res_summit.status_code == 200
    summit_vehicles = res_summit.json()
    for v in summit_vehicles:
        # None of the Apex vehicles should appear in Summit
        assert not v["plate_number"].startswith("APX-")


def test_cross_company_vehicle_access_blocked(client, apex_admin_headers, summit_admin_headers):
    """Verify that accessing, modifying, or deleting another company's vehicle returns 404."""
    # Get an Apex vehicle ID
    res_apex = client.get("/api/vehicles", headers=apex_admin_headers)
    apex_v_id = res_apex.json()[0]["id"]

    # Summit admin attempts GET
    res_get = client.get(f"/api/vehicles/{apex_v_id}", headers=summit_admin_headers)
    assert res_get.status_code == 404
    assert res_get.json()["detail"] == "Vehicle not found"

    # Summit admin attempts PUT
    res_put = client.put(
        f"/api/vehicles/{apex_v_id}",
        json={"notes": "Hacked notes"},
        headers=summit_admin_headers,
    )
    assert res_put.status_code == 404
    assert res_put.json()["detail"] == "Vehicle not found"

    # Summit admin attempts DELETE
    res_del = client.delete(f"/api/vehicles/{apex_v_id}", headers=summit_admin_headers)
    assert res_del.status_code == 404
    assert res_del.json()["detail"] == "Vehicle not found"


def test_project_tenant_isolation(client, apex_admin_headers, summit_admin_headers):
    """Verify that project data is strictly isolated between tenants."""
    res_apex = client.get("/api/projects", headers=apex_admin_headers)
    assert res_apex.status_code == 200
    apex_projects = res_apex.json()
    apex_codes = {p["project_code"] for p in apex_projects}
    assert "MHE-2026" in apex_codes

    res_summit = client.get("/api/projects", headers=summit_admin_headers)
    assert res_summit.status_code == 200
    summit_projects = res_summit.json()
    summit_codes = {p["project_code"] for p in summit_projects}
    assert "ULM-2026" in summit_codes
    assert "MHE-2026" not in summit_codes

    # Cross-tenant GET project returns 404
    apex_p_id = apex_projects[0]["id"]
    res_cross = client.get(f"/api/projects/{apex_p_id}", headers=summit_admin_headers)
    assert res_cross.status_code == 404
    assert res_cross.json()["detail"] == "Project not found"


def test_cross_company_checkout_prevented(client, apex_admin_headers, summit_admin_headers):
    """Verify that a user cannot check out a vehicle belonging to another company."""
    # Find an available Apex vehicle
    res_apex = client.get("/api/vehicles?status=available", headers=apex_admin_headers)
    apex_available = res_apex.json()
    assert len(apex_available) > 0
    apex_vehicle_id = apex_available[0]["id"]

    # Get a Summit project
    res_summit_proj = client.get("/api/projects", headers=summit_admin_headers)
    summit_project_id = res_summit_proj.json()[0]["id"]

    # Summit attempts to checkout Apex vehicle -> 404
    res_checkout = client.post(
        "/api/logs/checkout",
        json={
            "vehicle_id": apex_vehicle_id,
            "project_id": summit_project_id,
            "purpose": "Unauthorized cross-company trip",
        },
        headers=summit_admin_headers,
    )
    assert res_checkout.status_code == 404
    assert "Vehicle not found" in res_checkout.json()["detail"]


def test_category_tenant_isolation(client, apex_admin_headers, summit_admin_headers):
    """Verify that vehicle categories are isolated per company."""
    res_apex = client.get("/api/categories", headers=apex_admin_headers)
    apex_cat_names = {c["name"] for c in res_apex.json()}
    assert "Pickup Trucks" in apex_cat_names

    res_summit = client.get("/api/categories", headers=summit_admin_headers)
    summit_cat_names = {c["name"] for c in res_summit.json()}
    assert "Delivery Vans" in summit_cat_names
    assert "Pickup Trucks" not in summit_cat_names


def test_usage_logs_isolation(client, apex_admin_headers, summit_admin_headers):
    """Verify that vehicle usage logs only show records belonging to the user's company."""
    res_apex = client.get("/api/logs", headers=apex_admin_headers)
    assert res_apex.status_code == 200
    apex_logs = res_apex.json()
    for log in apex_logs:
        assert log["vehicle_plate"].startswith("APX-")

    res_summit = client.get("/api/logs", headers=summit_admin_headers)
    assert res_summit.status_code == 200
    summit_logs = res_summit.json()
    for log in summit_logs:
        assert not log["vehicle_plate"].startswith("APX-")


def test_dashboard_stats_isolation(client, apex_admin_headers, summit_admin_headers):
    """Verify that dashboard fleet statistics are scoped solely to each company."""
    res_apex = client.get("/api/dashboard/stats", headers=apex_admin_headers)
    assert res_apex.status_code == 200
    stats_apex = res_apex.json()
    assert stats_apex["total_vehicles"] >= 4
    assert stats_apex["active_projects"] >= 2

    res_summit = client.get("/api/dashboard/stats", headers=summit_admin_headers)
    assert res_summit.status_code == 200
    stats_summit = res_summit.json()
    # Summit stats should only reflect Summit assets
    assert stats_summit["total_vehicles"] != stats_apex["total_vehicles"]


def test_usage_logs_timeframe_filtering(client, apex_admin_headers):
    """Verify that filtering logs by days, start_date, and end_date works correctly."""
    # Unfiltered
    res_all = client.get("/api/logs", headers=apex_admin_headers)
    assert res_all.status_code == 200
    all_logs = res_all.json()
    assert len(all_logs) >= 2

    # Filter last 7 days
    res_7d = client.get("/api/logs?days=7", headers=apex_admin_headers)
    assert res_7d.status_code == 200
    logs_7d = res_7d.json()
    assert len(logs_7d) >= 1

    # Filter custom date range matching recent logs
    res_custom = client.get("/api/logs?start_date=2026-09-01&end_date=2026-09-30", headers=apex_admin_headers)
    assert res_custom.status_code == 200
    assert len(res_custom.json()) >= 1

    # Filter far future date range (should return empty list)
    res_future = client.get("/api/logs?start_date=2099-01-01&end_date=2099-01-31", headers=apex_admin_headers)
    assert res_future.status_code == 200
    assert len(res_future.json()) == 0
