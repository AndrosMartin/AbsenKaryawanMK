"""End-to-end backend tests for AbsensiPro.

Covers:
- /api/auth/login & /api/auth/me for owner/direksi/manager/staff
- RBAC for dashboard/employees/attendance (monitor) and CRUD (manage)
- Attendance: geofence enforcement, QR check-in success, face check-in without
  enrollment (400), duplicate check-in (400), check-out flow
- Dashboard stats payload shape
- Employees CRUD (create/update/delete) by owner
"""
import os
import uuid
import requests
import pytest

BASE = os.environ['REACT_APP_BACKEND_URL'].rstrip('/')
# Frontend .env value is used since same-origin /api routes via ingress.
# But tests run from the cluster; use the backend public URL via REACT_APP_BACKEND_URL.
# Fallback if not set in backend env:
if not BASE:
    raise RuntimeError("REACT_APP_BACKEND_URL not set")
API = f"{BASE}/api"

OWNER = "owner@company.com"
DIREKSI = "direksi@company.com"
MANAGER = "manager@company.com"
STAFF = "dewi@company.com"
PW = "password123"

OFFICE_LAT = -6.208763
OFFICE_LNG = 106.845599
OFFICE_QR = "OFFICE-HQJKT00001"


def _login(email, password=PW):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=20)
    return r


def _token(email):
    r = _login(email)
    assert r.status_code == 200, f"login {email} failed: {r.status_code} {r.text}"
    return r.json()["token"]


def _h(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def tokens():
    return {
        "owner": _token(OWNER),
        "direksi": _token(DIREKSI),
        "manager": _token(MANAGER),
        "staff": _token(STAFF),
    }


# ---------------- Auth ----------------
class TestAuth:
    @pytest.mark.parametrize("email,role", [
        (OWNER, "owner"), (DIREKSI, "direksi"),
        (MANAGER, "manager"), (STAFF, "staff"),
    ])
    def test_login_demo(self, email, role):
        r = _login(email)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "token" in data and isinstance(data["token"], str) and data["token"]
        assert data["user"]["email"] == email
        assert data["user"]["role"] == role

    def test_login_invalid(self):
        r = _login(OWNER, "wrongpassword")
        assert r.status_code == 401

    def test_me_with_bearer(self, tokens):
        r = requests.get(f"{API}/auth/me", headers=_h(tokens["owner"]))
        assert r.status_code == 200
        assert r.json()["email"] == OWNER

    def test_me_without_token(self):
        r = requests.get(f"{API}/auth/me")
        assert r.status_code == 401


# ---------------- RBAC ----------------
class TestRBACMonitor:
    @pytest.mark.parametrize("path", ["/dashboard/stats", "/employees", "/attendance"])
    @pytest.mark.parametrize("role", ["owner", "direksi", "manager"])
    def test_monitor_allowed(self, tokens, role, path):
        r = requests.get(f"{API}{path}", headers=_h(tokens[role]))
        assert r.status_code == 200, f"{role} {path}: {r.status_code} {r.text}"

    @pytest.mark.parametrize("path", ["/dashboard/stats", "/employees", "/attendance"])
    def test_monitor_forbidden_for_staff(self, tokens, path):
        r = requests.get(f"{API}{path}", headers=_h(tokens["staff"]))
        assert r.status_code == 403, f"staff {path}: {r.status_code} {r.text}"


class TestRBACManage:
    def test_create_employee_forbidden_for_manager(self, tokens):
        r = requests.post(f"{API}/employees",
                          headers=_h(tokens["manager"]),
                          json={"name": "x", "email": f"TEST_x_{uuid.uuid4().hex[:6]}@e.com"})
        assert r.status_code == 403

    def test_create_employee_forbidden_for_staff(self, tokens):
        r = requests.post(f"{API}/employees",
                          headers=_h(tokens["staff"]),
                          json={"name": "x", "email": f"TEST_x_{uuid.uuid4().hex[:6]}@e.com"})
        assert r.status_code == 403

    def test_create_office_forbidden_for_manager(self, tokens):
        r = requests.post(f"{API}/offices",
                          headers=_h(tokens["manager"]),
                          json={"name": "x", "lat": 0, "lng": 0, "radius_m": 100})
        assert r.status_code == 403


# ---------------- Attendance / geofence ----------------
class TestAttendance:
    def test_face_checkin_without_enrollment_returns_400(self, tokens):
        # staff dewi -- no face enrolled
        payload = {"method": "face", "lat": OFFICE_LAT, "lng": OFFICE_LNG,
                   "descriptor": [0.0] * 128}
        r = requests.post(f"{API}/attendance/check-in",
                          headers=_h(tokens["staff"]), json=payload)
        # Either duplicate check-in (if already today) or face not enrolled.
        assert r.status_code == 400
        msg = r.json().get("detail", "")
        assert ("Wajah belum didaftarkan" in msg) or ("sudah melakukan check-in" in msg)

    def test_qr_checkin_out_of_geofence(self, tokens):
        # Use a fresh staff account to avoid duplicate-today collision
        new_email = f"TEST_geo_{uuid.uuid4().hex[:8]}@company.com"
        cr = requests.post(f"{API}/employees", headers=_h(tokens["owner"]),
                           json={"name": "Geo Tester", "email": new_email,
                                 "password": PW, "role": "staff"})
        assert cr.status_code == 200, cr.text
        tok = _token(new_email)
        r = requests.post(f"{API}/attendance/check-in", headers=_h(tok),
                          json={"method": "qr", "lat": 0.0, "lng": 0.0,
                                "qr_code": OFFICE_QR})
        assert r.status_code == 400
        assert "dari" in r.json()["detail"].lower() or "radius" in r.json()["detail"].lower()
        # cleanup
        emp_id = cr.json()["id"]
        requests.delete(f"{API}/employees/{emp_id}", headers=_h(tokens["owner"]))

    def test_qr_checkin_success_then_checkout_then_duplicate(self, tokens):
        new_email = f"TEST_qr_{uuid.uuid4().hex[:8]}@company.com"
        cr = requests.post(f"{API}/employees", headers=_h(tokens["owner"]),
                           json={"name": "QR Tester", "email": new_email,
                                 "password": PW, "role": "staff"})
        assert cr.status_code == 200, cr.text
        emp_id = cr.json()["id"]
        tok = _token(new_email)

        # success
        r = requests.post(f"{API}/attendance/check-in", headers=_h(tok),
                          json={"method": "qr", "lat": OFFICE_LAT,
                                "lng": OFFICE_LNG, "qr_code": OFFICE_QR})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["status"] in ("present", "late")
        assert data["method"] == "qr"
        assert data["within_geofence"] is True

        # check-out
        co = requests.post(f"{API}/attendance/check-out", headers=_h(tok),
                           json={"lat": OFFICE_LAT, "lng": OFFICE_LNG})
        assert co.status_code == 200, co.text
        assert co.json()["check_out"]

        # duplicate check-in
        dup = requests.post(f"{API}/attendance/check-in", headers=_h(tok),
                            json={"method": "qr", "lat": OFFICE_LAT,
                                  "lng": OFFICE_LNG, "qr_code": OFFICE_QR})
        assert dup.status_code == 400
        assert "sudah melakukan check-in" in dup.json()["detail"]

        # cleanup
        requests.delete(f"{API}/employees/{emp_id}", headers=_h(tokens["owner"]))

    def test_qr_checkin_invalid_qr(self, tokens):
        new_email = f"TEST_qrbad_{uuid.uuid4().hex[:8]}@company.com"
        cr = requests.post(f"{API}/employees", headers=_h(tokens["owner"]),
                           json={"name": "Bad QR", "email": new_email,
                                 "password": PW, "role": "staff"})
        assert cr.status_code == 200, cr.text
        emp_id = cr.json()["id"]
        tok = _token(new_email)
        r = requests.post(f"{API}/attendance/check-in", headers=_h(tok),
                          json={"method": "qr", "lat": OFFICE_LAT,
                                "lng": OFFICE_LNG, "qr_code": "OFFICE-WRONG"})
        assert r.status_code == 400
        assert "QR" in r.json()["detail"]
        requests.delete(f"{API}/employees/{emp_id}", headers=_h(tokens["owner"]))


# ---------------- Dashboard ----------------
class TestDashboard:
    def test_dashboard_stats_shape(self, tokens):
        r = requests.get(f"{API}/dashboard/stats", headers=_h(tokens["owner"]))
        assert r.status_code == 200
        d = r.json()
        for k in ("total", "present", "late", "absent", "trend", "departments", "recent"):
            assert k in d, f"missing key {k}"
        assert isinstance(d["trend"], list) and len(d["trend"]) == 7
        assert isinstance(d["departments"], list)
        assert isinstance(d["recent"], list)
        assert d["total"] >= 1


# ---------------- Employees CRUD ----------------
class TestEmployeesCRUD:
    def test_full_crud_as_owner(self, tokens):
        email = f"TEST_crud_{uuid.uuid4().hex[:8]}@company.com"
        # Create
        cr = requests.post(f"{API}/employees", headers=_h(tokens["owner"]),
                           json={"name": "CRUD User", "email": email,
                                 "password": PW, "role": "staff",
                                 "department": "QA", "position": "Tester"})
        assert cr.status_code == 200, cr.text
        emp = cr.json()
        # Backend lowercases emails on storage; compare case-insensitively.
        assert emp["email"].lower() == email.lower()
        assert emp["role"] == "staff"
        emp_id = emp["id"]

        # GET list and verify presence
        lst = requests.get(f"{API}/employees", headers=_h(tokens["owner"]))
        assert lst.status_code == 200
        assert any(e["id"] == emp_id for e in lst.json())

        # Update
        up = requests.put(f"{API}/employees/{emp_id}", headers=_h(tokens["owner"]),
                          json={"name": "CRUD User Updated", "department": "QA-2"})
        assert up.status_code == 200, up.text
        assert up.json()["name"] == "CRUD User Updated"
        assert up.json()["department"] == "QA-2"

        # Delete
        dl = requests.delete(f"{API}/employees/{emp_id}", headers=_h(tokens["owner"]))
        assert dl.status_code == 200
        # GET list should no longer contain it
        lst2 = requests.get(f"{API}/employees", headers=_h(tokens["owner"]))
        assert not any(e["id"] == emp_id for e in lst2.json())

    def test_cannot_create_duplicate_email(self, tokens):
        r = requests.post(f"{API}/employees", headers=_h(tokens["owner"]),
                          json={"name": "Dup", "email": OWNER, "password": PW})
        assert r.status_code == 400


# ---------------- Offices ----------------
class TestOffices:
    def test_list_offices_for_staff(self, tokens):
        r = requests.get(f"{API}/offices", headers=_h(tokens["staff"]))
        assert r.status_code == 200
        offs = r.json()
        assert any(o["qr_code"] == OFFICE_QR for o in offs)

    def test_create_office_as_owner(self, tokens):
        r = requests.post(f"{API}/offices", headers=_h(tokens["owner"]),
                          json={"name": f"TEST_Branch_{uuid.uuid4().hex[:6]}",
                                "lat": -6.21, "lng": 106.85, "radius_m": 150})
        assert r.status_code == 200, r.text
        oid = r.json()["id"]
        # cleanup
        requests.delete(f"{API}/offices/{oid}", headers=_h(tokens["owner"]))
