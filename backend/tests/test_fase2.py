"""FASE 2 tests: /api/settings + HRD->approve flow + 3-status rekap + export columns."""
import os, io, zipfile
import pytest
import requests

def _load_base():
    from pathlib import Path
    env = Path("/app/frontend/.env").read_text()
    for line in env.splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    raise RuntimeError("REACT_APP_BACKEND_URL not found")

BASE = os.environ.get("REACT_APP_BACKEND_URL", _load_base()).rstrip("/")
OWNER = {"email": "owner@company.com", "password": "password123"}


# ---------- helpers / fixtures ----------
@pytest.fixture(scope="module")
def owner_token():
    r = requests.post(f"{BASE}/api/auth/login", json=OWNER, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def owner_h(owner_token):
    return {"Authorization": f"Bearer {owner_token}"}


@pytest.fixture(scope="module")
def hrd_session(owner_h):
    """Create a throwaway HRD user via owner (auto-applied), yield token+id, then delete."""
    email = "test_hrd_fase2@company.com"
    payload = {
        "name": "Test HRD F2", "email": email, "password": "hrdpass123",
        "role": "hrd", "department": "HR", "position": "HRD",
    }
    # cleanup existing (idempotent)
    existing = requests.get(f"{BASE}/api/employees", headers=owner_h, timeout=30).json()
    for u in existing:
        if u.get("email") == email:
            requests.delete(f"{BASE}/api/employees/{u['id']}", headers=owner_h, timeout=30)
    r = requests.post(f"{BASE}/api/employees", json=payload, headers=owner_h, timeout=30)
    assert r.status_code in (200, 201), r.text
    j = r.json()
    # response may be the created employee or wrapper
    emp_id = j.get("id") or (j.get("applied") and j.get("employee", {}).get("id"))
    if not emp_id:
        # fetch again
        for u in requests.get(f"{BASE}/api/employees", headers=owner_h).json():
            if u.get("email") == email:
                emp_id = u["id"]; break
    assert emp_id, f"could not resolve hrd id: {j}"

    login = requests.post(f"{BASE}/api/auth/login",
                         json={"email": email, "password": "hrdpass123"}, timeout=30)
    assert login.status_code == 200, login.text
    token = login.json()["token"]
    yield {"id": emp_id, "token": token, "h": {"Authorization": f"Bearer {token}"}}
    requests.delete(f"{BASE}/api/employees/{emp_id}", headers=owner_h, timeout=30)


@pytest.fixture(autouse=True)
def _reset_settings_after(owner_h):
    """Always restore defaults after each test."""
    yield
    requests.put(f"{BASE}/api/settings",
                 json={"work_start": "09:00", "work_end": "17:00", "tolerance_minutes": 15},
                 headers=owner_h, timeout=30)


# ---------- GET /api/settings ----------
class TestGetSettings:
    def test_defaults(self, owner_h):
        r = requests.get(f"{BASE}/api/settings", headers=owner_h, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["work_start"] == "09:00"
        assert d["work_end"] == "17:00"
        assert d["tolerance_minutes"] == 15

    def test_requires_auth(self):
        r = requests.get(f"{BASE}/api/settings", timeout=30)
        assert r.status_code in (401, 403)


# ---------- PUT /api/settings as OWNER ----------
class TestOwnerApplyImmediately:
    def test_apply_and_persist(self, owner_h):
        body = {"work_start": "08:30", "work_end": "16:30", "tolerance_minutes": 20}
        r = requests.put(f"{BASE}/api/settings", json=body, headers=owner_h, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("ok") is True
        assert d.get("applied") is True
        assert d["work_start"] == "08:30"
        assert d["tolerance_minutes"] == 20
        # GET reflects
        g = requests.get(f"{BASE}/api/settings", headers=owner_h, timeout=30).json()
        assert g["work_start"] == "08:30"
        assert g["work_end"] == "16:30"
        assert g["tolerance_minutes"] == 20

    def test_invalid_tolerance_negative(self, owner_h):
        r = requests.put(f"{BASE}/api/settings",
                         json={"work_start": "09:00", "work_end": "17:00", "tolerance_minutes": -1},
                         headers=owner_h, timeout=30)
        assert r.status_code == 400

    def test_invalid_tolerance_too_large(self, owner_h):
        r = requests.put(f"{BASE}/api/settings",
                         json={"work_start": "09:00", "work_end": "17:00", "tolerance_minutes": 121},
                         headers=owner_h, timeout=30)
        assert r.status_code == 400

    def test_invalid_hhmm(self, owner_h):
        for bad in ("25:00", "12:60", "abc", "1200", ""):
            r = requests.put(f"{BASE}/api/settings",
                             json={"work_start": bad, "work_end": "17:00", "tolerance_minutes": 15},
                             headers=owner_h, timeout=30)
            assert r.status_code == 400, f"expected 400 for work_start={bad!r}, got {r.status_code}"
        # also work_end
        r = requests.put(f"{BASE}/api/settings",
                         json={"work_start": "09:00", "work_end": "99:99", "tolerance_minutes": 15},
                         headers=owner_h, timeout=30)
        assert r.status_code == 400


# ---------- PUT /api/settings as HRD -> request, then approve ----------
class TestHrdApprovalFlow:
    def test_hrd_creates_pending_request_then_owner_approves(self, owner_h, hrd_session):
        # Ensure baseline default first
        requests.put(f"{BASE}/api/settings",
                     json={"work_start": "09:00", "work_end": "17:00", "tolerance_minutes": 15},
                     headers=owner_h, timeout=30)

        proposed = {"work_start": "08:45", "work_end": "17:30", "tolerance_minutes": 10}
        r = requests.put(f"{BASE}/api/settings", json=proposed,
                         headers=hrd_session["h"], timeout=30)
        assert r.status_code == 200, r.text
        body = r.json()
        # not applied yet
        assert body.get("applied") is not True or body.get("status") == "pending"

        # Settings unchanged
        g = requests.get(f"{BASE}/api/settings", headers=owner_h, timeout=30).json()
        assert g["work_start"] == "09:00" and g["tolerance_minutes"] == 15

        # Find pending request with action=settings
        reqs = requests.get(f"{BASE}/api/employee-requests", headers=owner_h, timeout=30).json()
        cand = [x for x in reqs if x.get("action") == "settings" and x.get("status") == "pending"]
        assert cand, f"no pending settings request in {reqs}"
        req_id = cand[0]["id"]
        pl = cand[0].get("payload") or {}
        assert pl.get("work_start") == "08:45"
        assert pl.get("work_end") == "17:30"
        assert pl.get("tolerance_minutes") == 10

        # Approve
        ap = requests.post(f"{BASE}/api/employee-requests/{req_id}/approve",
                          headers=owner_h, timeout=30)
        assert ap.status_code == 200, ap.text

        # Settings now reflect proposed values
        g2 = requests.get(f"{BASE}/api/settings", headers=owner_h, timeout=30).json()
        assert g2["work_start"] == "08:45"
        assert g2["work_end"] == "17:30"
        assert g2["tolerance_minutes"] == 10


# ---------- compute_status / rekap totals include tolerance ----------
class TestThreeStatusComputeAndRekap:
    def test_compute_status_direct(self):
        from datetime import datetime
        from backend.server import compute_status, TZ  # type: ignore
        def at(h, m):
            return datetime(2025, 1, 6, h, m, tzinfo=TZ)
        assert compute_status(at(8, 55), "09:00", 15) == "present"
        assert compute_status(at(9, 0), "09:00", 15) == "present"
        assert compute_status(at(9, 10), "09:00", 15) == "tolerance"
        assert compute_status(at(9, 15), "09:00", 15) == "tolerance"
        assert compute_status(at(9, 20), "09:00", 15) == "late"

    def test_summary_includes_tolerance_field(self, owner_h):
        from datetime import date, timedelta
        end = date.today().isoformat()
        start = (date.today() - timedelta(days=7)).isoformat()
        r = requests.get(f"{BASE}/api/attendance/summary?start={start}&end={end}",
                         headers=owner_h, timeout=30)
        assert r.status_code == 200, r.text
        j = r.json()
        totals = j.get("totals") or j.get("total") or {}
        assert "tolerance" in totals, f"totals missing tolerance: {totals}"
        rows = j.get("rows") or []
        if rows:
            assert "tolerance" in rows[0], f"rows missing tolerance: {rows[0]}"


# ---------- Exports: xlsx & pdf have Toleransi column ----------
class TestExports:
    def _range(self):
        from datetime import date, timedelta
        end = date.today().isoformat()
        start = (date.today() - timedelta(days=7)).isoformat()
        return start, end

    def test_xlsx_two_sheets_and_toleransi_column(self, owner_h):
        s, e = self._range()
        r = requests.get(f"{BASE}/api/attendance/summary/export?format=xlsx&start={s}&end={e}",
                         headers=owner_h, timeout=60)
        assert r.status_code == 200, r.text
        z = zipfile.ZipFile(io.BytesIO(r.content))
        names = z.namelist()
        wb = z.read("xl/workbook.xml").decode("utf-8", errors="ignore")
        assert wb.count("<sheet ") >= 2, f"expected >=2 sheets, got: {wb}"
        sst = ""
        if "xl/sharedStrings.xml" in names:
            sst = z.read("xl/sharedStrings.xml").decode("utf-8", errors="ignore")
        all_xml = sst + "".join(z.read(n).decode("utf-8", errors="ignore")
                                 for n in names if n.startswith("xl/worksheets/"))
        assert "Toleransi" in all_xml, "Toleransi column missing in xlsx"

    def test_pdf_magic_and_toleransi(self, owner_h):
        s, e = self._range()
        r = requests.get(f"{BASE}/api/attendance/summary/export?format=pdf&start={s}&end={e}",
                         headers=owner_h, timeout=60)
        assert r.status_code == 200
        assert r.content[:4] == b"%PDF"
