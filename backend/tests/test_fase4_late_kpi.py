"""FASE 4 — Late approval + KPI 'Kartu Kuning' backend tests.

Covers:
- Role-based guards: STAFF -> 403 on /api/late/pending, /api/late/{id}/approve, /api/late/{id}/reject
- HRD approval flow:
    * check_in <=10:00 WIB -> compensated true, status -> 'present', yellow_card=false
    * check_in 10:01-12:00 WIB -> compensated false, status stays 'late', yellow_card=false
    * reject -> yellow_card=true, late_review_status='rejected'
- Potong cuti: late_category='potong_cuti' + leave_deductions doc -> balance.deducted includes 0.5
- POST /api/late/reason: sets reason on TODAY's perlu_approval record; 404 if no late record today
- KPI /api/kpi/discipline?month=YYYY-MM:
    * owner/direksi/hrd allowed
    * manager without kpi_access -> 403
    * after PUT /employees/{id}/kpi-access {kpi_access:true} -> 200
    * rows aggregate yellow_cards/late_count/leave_deducted, sorted desc

Seeds attendance docs DIRECTLY into Mongo (collection 'attendance' / 'leave_deductions')
via pymongo using MONGO_URL/DB_NAME from backend/.env. Cleans up everything afterwards.
"""
import os
import pytest
import requests
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from pymongo import MongoClient


def _load_env(path, prefix):
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line.startswith(prefix):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                key = prefix.rstrip("=")
                os.environ.setdefault(key, val)


_load_env("/app/frontend/.env", "REACT_APP_BACKEND_URL=")
_load_env("/app/backend/.env", "MONGO_URL=")
_load_env("/app/backend/.env", "DB_NAME=")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")
assert BASE_URL and MONGO_URL and DB_NAME, "Missing env"

OWNER_EMAIL = "owner@company.com"
OWNER_PASSWORD = "password123"
PASSWORD = "password123"

WIB = timezone(timedelta(hours=7))

USERS = {
    "staff":   {"email": "TEST_staff_f4@company.com",   "name": "TEST Staff F4",   "role": "staff",    "department": "QA"},
    "hrd":     {"email": "TEST_hrd_f4@company.com",     "name": "TEST HRD F4",     "role": "hrd",      "department": "HR"},
    "manager": {"email": "TEST_mgr_f4@company.com",     "name": "TEST Mgr F4",     "role": "manager",  "department": "Eng"},
    "staff2":  {"email": "TEST_staff2_f4@company.com",  "name": "TEST Staff2 F4",  "role": "staff",    "department": "QA"},
}


def _login(email, pw):
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": pw}, timeout=20)
    assert r.status_code == 200, f"login {email}: {r.status_code} {r.text}"
    return r.json()["token"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


def _wib_today_str():
    return datetime.now(WIB).strftime("%Y-%m-%d")


def _wib_iso_today(hour_wib, minute_wib=30):
    """Return UTC ISO string whose WIB time-of-day = HH:MM on today (Asia/Jakarta)."""
    today_wib = datetime.now(WIB).date()
    local = datetime(today_wib.year, today_wib.month, today_wib.day,
                     hour_wib, minute_wib, tzinfo=WIB)
    return local.astimezone(timezone.utc).isoformat()


@pytest.fixture(scope="module")
def mongo():
    cli = MongoClient(MONGO_URL)
    db = cli[DB_NAME]
    yield db
    cli.close()


@pytest.fixture(scope="module")
def tokens(mongo):
    owner_tok = _login(OWNER_EMAIL, OWNER_PASSWORD)
    ids = {}
    toks = {"owner": owner_tok}
    # create the 4 users via owner
    for k, info in USERS.items():
        # cleanup any leftover with same email
        mongo.users.delete_many({"email": info["email"]})
        payload = {**info, "password": PASSWORD}
        r = requests.post(f"{BASE_URL}/api/employees", json=payload, headers=_h(owner_tok), timeout=20)
        assert r.status_code == 200, f"create {k}: {r.status_code} {r.text}"
        ids[k] = r.json()["id"]
        toks[k] = _login(info["email"], PASSWORD)
    yield toks, ids
    # Cleanup users + all related collections
    for uid in ids.values():
        mongo.users.delete_one({"_id": ObjectId(uid)})
        mongo.attendance.delete_many({"user_id": uid})
        mongo.leave_deductions.delete_many({"user_id": uid})
        mongo.leave_requests.delete_many({"user_id": uid})


# ============================================================================
# Late approval flow: role guards + approve/reject behavior
# ============================================================================
class TestLateApprovalFlow:
    def _seed_late_pending(self, mongo, user_id, hour_wib, minute=30, date_str=None):
        date_str = date_str or _wib_today_str()
        doc = {
            "user_id": user_id,
            "date": date_str,
            "check_in": _wib_iso_today(hour_wib, minute),
            "status": "late",
            "late_category": "perlu_approval",
            "late_review_status": "pending",
            "yellow_card": True,
            "leave_deducted": 0,
            "created_at": datetime.utcnow().isoformat(),
        }
        res = mongo.attendance.insert_one(doc)
        return str(res.inserted_id)

    def test_staff_forbidden_on_late_pending(self, tokens, mongo):
        toks, ids = tokens
        self._seed_late_pending(mongo, ids["staff"], 9, 30)
        r = requests.get(f"{BASE_URL}/api/late/pending", headers=_h(toks["staff"]), timeout=20)
        assert r.status_code == 403

    def test_hrd_sees_pending(self, tokens, mongo):
        toks, ids = tokens
        r = requests.get(f"{BASE_URL}/api/late/pending", headers=_h(toks["hrd"]), timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert "items" in data and "count" in data
        assert data["count"] >= 1

    def test_staff_forbidden_on_approve(self, tokens, mongo):
        toks, ids = tokens
        att_id = self._seed_late_pending(mongo, ids["staff2"], 9, 30)
        r = requests.post(f"{BASE_URL}/api/late/{att_id}/approve", json={}, headers=_h(toks["staff"]), timeout=20)
        assert r.status_code == 403
        # cleanup
        mongo.attendance.delete_one({"_id": ObjectId(att_id)})

    def test_approve_compensated_under_10am(self, tokens, mongo):
        toks, ids = tokens
        att_id = self._seed_late_pending(mongo, ids["staff"], 9, 30)  # 09:30 WIB
        r = requests.post(f"{BASE_URL}/api/late/{att_id}/approve", json={}, headers=_h(toks["hrd"]), timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("compensated") is True
        rec = mongo.attendance.find_one({"_id": ObjectId(att_id)})
        assert rec["status"] == "present"
        assert rec["yellow_card"] is False
        assert rec["late_review_status"] == "approved"

    def test_approve_no_compensate_10_to_12(self, tokens, mongo):
        toks, ids = tokens
        att_id = self._seed_late_pending(mongo, ids["staff2"], 10, 30)  # 10:30 WIB
        r = requests.post(f"{BASE_URL}/api/late/{att_id}/approve", json={}, headers=_h(toks["hrd"]), timeout=20)
        assert r.status_code == 200, r.text
        assert r.json().get("compensated") is False
        rec = mongo.attendance.find_one({"_id": ObjectId(att_id)})
        assert rec["status"] == "late"
        assert rec["yellow_card"] is False
        assert rec["late_review_status"] == "approved"

    def test_reject_sets_yellow_card(self, tokens, mongo):
        toks, ids = tokens
        att_id = self._seed_late_pending(mongo, ids["staff"], 11, 0)
        r = requests.post(f"{BASE_URL}/api/late/{att_id}/reject",
                          json={"note": "alasan tidak valid"}, headers=_h(toks["hrd"]), timeout=20)
        assert r.status_code == 200, r.text
        rec = mongo.attendance.find_one({"_id": ObjectId(att_id)})
        assert rec["yellow_card"] is True
        assert rec["late_review_status"] == "rejected"


# ============================================================================
# Potong cuti: balance.deducted reflects leave_deductions
# ============================================================================
class TestPotongCuti:
    def test_balance_includes_deductions(self, tokens, mongo):
        toks, ids = tokens
        uid = ids["staff2"]
        year = datetime.now(WIB).year
        # cleanup any existing deductions for staff2
        mongo.leave_deductions.delete_many({"user_id": uid})
        # seed a potong_cuti attendance + leave_deduction
        mongo.attendance.insert_one({
            "user_id": uid, "date": _wib_today_str(),
            "check_in": _wib_iso_today(12, 30), "status": "late",
            "late_category": "potong_cuti", "late_review_status": "auto",
            "yellow_card": False, "leave_deducted": 0.5,
            "created_at": datetime.utcnow().isoformat(),
        })
        mongo.leave_deductions.insert_one({
            "user_id": uid, "date": f"{year}-{datetime.now(WIB).strftime('%m-%d')}",
            "days": 0.5, "created_at": datetime.utcnow().isoformat(),
        })
        r = requests.get(f"{BASE_URL}/api/leave/balance?user_id={uid}",
                         headers=_h(toks["owner"]), timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["deducted"] == 0.5
        assert data["used"] >= 0.5
        assert data["remaining"] == data["quota"] - data["used"]
        assert data["remaining"] == data["quota"] - 0.5 or data["used"] > 0.5


# ============================================================================
# /api/late/reason
# ============================================================================
class TestLateReason:
    def test_404_when_no_late_today(self, tokens, mongo):
        toks, ids = tokens
        # ensure no late record today for manager (used as a 'no late' user)
        mongo.attendance.delete_many({"user_id": ids["manager"], "date": _wib_today_str()})
        r = requests.post(f"{BASE_URL}/api/late/reason",
                          json={"reason": "macet"}, headers=_h(toks["manager"]), timeout=20)
        assert r.status_code == 404

    def test_sets_reason_for_today(self, tokens, mongo):
        toks, ids = tokens
        uid = ids["staff"]
        # clear and seed fresh perlu_approval today
        mongo.attendance.delete_many({"user_id": uid, "date": _wib_today_str()})
        att_id = mongo.attendance.insert_one({
            "user_id": uid, "date": _wib_today_str(),
            "check_in": _wib_iso_today(9, 45), "status": "late",
            "late_category": "perlu_approval", "late_review_status": "pending",
            "yellow_card": True, "leave_deducted": 0,
            "created_at": datetime.utcnow().isoformat(),
        }).inserted_id
        r = requests.post(f"{BASE_URL}/api/late/reason",
                          json={"reason": "macet parah"}, headers=_h(toks["staff"]), timeout=20)
        assert r.status_code == 200, r.text
        rec = mongo.attendance.find_one({"_id": att_id})
        assert rec["late_reason"] == "macet parah"


# ============================================================================
# KPI Discipline + access control
# ============================================================================
class TestKpiDiscipline:
    def test_owner_can_access(self, tokens):
        toks, _ = tokens
        month = datetime.now(WIB).strftime("%Y-%m")
        r = requests.get(f"{BASE_URL}/api/kpi/discipline?month={month}",
                         headers=_h(toks["owner"]), timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["month"] == month
        assert "rows" in data
        assert data.get("can_access") is True

    def test_hrd_can_access(self, tokens):
        toks, _ = tokens
        r = requests.get(f"{BASE_URL}/api/kpi/discipline", headers=_h(toks["hrd"]), timeout=20)
        assert r.status_code == 200

    def test_manager_blocked_then_unblocked(self, tokens, mongo):
        toks, ids = tokens
        # Reset kpi_access to false
        mongo.users.update_one({"_id": ObjectId(ids["manager"])}, {"$set": {"kpi_access": False}})
        # re-login manager to get fresh token? token decodes by id; current_user reads db
        r = requests.get(f"{BASE_URL}/api/kpi/discipline", headers=_h(toks["manager"]), timeout=20)
        assert r.status_code == 403

        # owner grants access
        r2 = requests.put(f"{BASE_URL}/api/employees/{ids['manager']}/kpi-access",
                          json={"kpi_access": True}, headers=_h(toks["owner"]), timeout=20)
        assert r2.status_code == 200, r2.text
        assert r2.json().get("kpi_access") is True

        # now manager should access
        r3 = requests.get(f"{BASE_URL}/api/kpi/discipline", headers=_h(toks["manager"]), timeout=20)
        assert r3.status_code == 200, r3.text

    def test_staff_forbidden(self, tokens):
        toks, _ = tokens
        r = requests.get(f"{BASE_URL}/api/kpi/discipline", headers=_h(toks["staff"]), timeout=20)
        assert r.status_code == 403

    def test_rows_aggregate_and_sorted(self, tokens, mongo):
        toks, ids = tokens
        month = datetime.now(WIB).strftime("%Y-%m")
        r = requests.get(f"{BASE_URL}/api/kpi/discipline?month={month}",
                         headers=_h(toks["owner"]), timeout=20)
        assert r.status_code == 200
        rows = r.json()["rows"]
        # rows for staff/staff2 should exist (we seeded earlier)
        uids = [row["user_id"] for row in rows]
        assert ids["staff"] in uids or ids["staff2"] in uids
        # check sort: descending by (yellow+deduct, late)
        scored = [(row["yellow_cards"] + row["leave_deducted"], row["late_count"]) for row in rows]
        assert scored == sorted(scored, reverse=True)
        # field shape
        for row in rows:
            assert {"user_id", "name", "yellow_cards", "late_count", "leave_deducted"} <= set(row.keys())
