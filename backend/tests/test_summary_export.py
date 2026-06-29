"""Backend tests for attendance summary + export PDF/Excel (Monitoring rekap).

Covers:
- Auth guard (401 without token) for /api/attendance/summary and /export.
- GET /api/attendance/summary returns {start,end,workdays,rows[],totals{present,late,absent,attended}}.
- workdays = Mon-Fri count in range, capped by today.
- Optional q filter narrows rows.
- Optional user_id filter narrows rows.
- Export ?format=pdf  -> 200, Content-Type application/pdf, starts with %PDF.
- Export ?format=xlsx -> 200, Content-Type spreadsheetml.sheet, valid zip (PK\x03\x04).
"""
import os
import io
import zipfile
from datetime import date, timedelta

import pytest
import requests

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE}/api"

OWNER = "owner@company.com"
PW = "password123"


def _count_workdays_local(start: date, end: date) -> int:
    today = date.today()
    if end > today:
        end = today
    n, d = 0, start
    while d <= end:
        if d.weekday() < 5:
            n += 1
        d += timedelta(days=1)
    return n


@pytest.fixture(scope="module")
def owner_token():
    r = requests.post(f"{API}/auth/login",
                      json={"email": OWNER, "password": PW}, timeout=20)
    assert r.status_code == 200, f"owner login failed: {r.status_code} {r.text}"
    return r.json()["token"]


@pytest.fixture(scope="module")
def auth_headers(owner_token):
    return {"Authorization": f"Bearer {owner_token}"}


# ---------------- Auth guard ----------------
class TestAuthGuard:
    def test_summary_requires_auth(self):
        r = requests.get(f"{API}/attendance/summary",
                         params={"start": "2026-01-01", "end": "2026-01-31"}, timeout=20)
        assert r.status_code in (401, 403), f"expected 401/403, got {r.status_code}"

    def test_export_requires_auth(self):
        r = requests.get(f"{API}/attendance/summary/export",
                         params={"format": "xlsx", "start": "2026-01-01",
                                 "end": "2026-01-31"}, timeout=20)
        assert r.status_code in (401, 403), f"expected 401/403, got {r.status_code}"


# ---------------- Summary payload ----------------
class TestSummaryPayload:
    def test_summary_structure_month(self, auth_headers):
        today = date.today()
        start = today.replace(day=1).isoformat()
        end = today.isoformat()
        r = requests.get(f"{API}/attendance/summary",
                         params={"start": start, "end": end},
                         headers=auth_headers, timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        for k in ("start", "end", "workdays", "rows", "totals"):
            assert k in data, f"missing key {k}"
        assert data["start"] == start
        assert data["end"] == end
        assert isinstance(data["workdays"], int)
        assert isinstance(data["rows"], list)
        for k in ("present", "late", "absent", "attended"):
            assert k in data["totals"], f"missing totals.{k}"
        # rows should include at least the seeded owner
        assert len(data["rows"]) >= 1
        row = data["rows"][0]
        for k in ("user_id", "name", "department", "role",
                  "present", "late", "absent", "attended", "workdays", "rate"):
            assert k in row, f"row missing {k}"

    def test_workdays_matches_local_computation(self, auth_headers):
        today = date.today()
        start = today.replace(day=1)
        end = today
        r = requests.get(f"{API}/attendance/summary",
                         params={"start": start.isoformat(), "end": end.isoformat()},
                         headers=auth_headers, timeout=20)
        assert r.status_code == 200
        expected = _count_workdays_local(start, end)
        assert r.json()["workdays"] == expected, \
            f"workdays {r.json()['workdays']} != expected {expected}"

    def test_workdays_capped_by_today(self, auth_headers):
        today = date.today()
        start = today.replace(day=1).isoformat()
        # end far in the future -> should be capped to today
        end_future = (today + timedelta(days=365)).isoformat()
        r = requests.get(f"{API}/attendance/summary",
                         params={"start": start, "end": end_future},
                         headers=auth_headers, timeout=20)
        assert r.status_code == 200
        capped = _count_workdays_local(today.replace(day=1), today)
        assert r.json()["workdays"] == capped

    def test_year_range(self, auth_headers):
        today = date.today()
        start = today.replace(month=1, day=1).isoformat()
        end = today.isoformat()
        r = requests.get(f"{API}/attendance/summary",
                         params={"start": start, "end": end},
                         headers=auth_headers, timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert data["workdays"] >= 1
        # absent should equal workdays for owner who has no attendance records
        owner_row = next((row for row in data["rows"]
                          if row.get("name") and "budi" in row["name"].lower()), None)
        if owner_row:
            assert owner_row["absent"] == data["workdays"]

    def test_q_filter_narrows_rows(self, auth_headers):
        today = date.today()
        start = today.replace(day=1).isoformat()
        end = today.isoformat()
        r_all = requests.get(f"{API}/attendance/summary",
                             params={"start": start, "end": end},
                             headers=auth_headers, timeout=20)
        assert r_all.status_code == 200
        all_rows = r_all.json()["rows"]

        r_q = requests.get(f"{API}/attendance/summary",
                           params={"start": start, "end": end, "q": "budi"},
                           headers=auth_headers, timeout=20)
        assert r_q.status_code == 200
        q_rows = r_q.json()["rows"]
        assert len(q_rows) <= len(all_rows)
        for row in q_rows:
            blob = ((row.get("name") or "") + " " + (row.get("department") or "")).lower()
            assert "budi" in blob

        # Search guaranteed to match nothing
        r_none = requests.get(f"{API}/attendance/summary",
                              params={"start": start, "end": end,
                                      "q": "zzz-no-such-employee-xyz"},
                              headers=auth_headers, timeout=20)
        assert r_none.status_code == 200
        assert r_none.json()["rows"] == []

    def test_user_id_filter(self, auth_headers):
        today = date.today()
        start = today.replace(day=1).isoformat()
        end = today.isoformat()
        r_all = requests.get(f"{API}/attendance/summary",
                             params={"start": start, "end": end},
                             headers=auth_headers, timeout=20)
        assert r_all.status_code == 200
        rows = r_all.json()["rows"]
        assert rows, "expected at least one row"
        uid = rows[0]["user_id"]
        r_one = requests.get(f"{API}/attendance/summary",
                             params={"start": start, "end": end, "user_id": uid},
                             headers=auth_headers, timeout=20)
        assert r_one.status_code == 200
        one_rows = r_one.json()["rows"]
        assert len(one_rows) == 1
        assert one_rows[0]["user_id"] == uid


# ---------------- Export ----------------
class TestExport:
    def test_export_pdf(self, auth_headers):
        today = date.today()
        start = today.replace(day=1).isoformat()
        end = today.isoformat()
        r = requests.get(f"{API}/attendance/summary/export",
                         params={"format": "pdf", "start": start, "end": end},
                         headers=auth_headers, timeout=30)
        assert r.status_code == 200, r.text[:300]
        ct = r.headers.get("Content-Type", "")
        assert "application/pdf" in ct, f"unexpected content-type: {ct}"
        assert r.content[:4] == b"%PDF", f"not a PDF, starts with {r.content[:8]!r}"
        cd = r.headers.get("Content-Disposition", "")
        assert "attachment" in cd and ".pdf" in cd

    def test_export_xlsx(self, auth_headers):
        today = date.today()
        start = today.replace(day=1).isoformat()
        end = today.isoformat()
        r = requests.get(f"{API}/attendance/summary/export",
                         params={"format": "xlsx", "start": start, "end": end},
                         headers=auth_headers, timeout=30)
        assert r.status_code == 200, r.text[:300]
        ct = r.headers.get("Content-Type", "")
        assert "spreadsheetml.sheet" in ct, f"unexpected content-type: {ct}"
        # XLSX is a zip; must start with PK\x03\x04 and be a valid zip
        assert r.content[:4] == b"PK\x03\x04", f"not a zip, starts with {r.content[:8]!r}"
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            names = z.namelist()
            assert any(n.startswith("xl/") for n in names), \
                "xlsx archive missing xl/ entries"
        cd = r.headers.get("Content-Disposition", "")
        assert "attachment" in cd and ".xlsx" in cd

    def test_export_default_is_xlsx(self, auth_headers):
        today = date.today()
        start = today.replace(day=1).isoformat()
        end = today.isoformat()
        r = requests.get(f"{API}/attendance/summary/export",
                         params={"start": start, "end": end},  # no format
                         headers=auth_headers, timeout=30)
        assert r.status_code == 200
        ct = r.headers.get("Content-Type", "")
        assert "spreadsheetml.sheet" in ct
        assert r.content[:4] == b"PK\x03\x04"
