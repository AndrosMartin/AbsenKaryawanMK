"""FASE 3 — Pengajuan Cuti (Leave) backend tests.

Tests:
- POST /api/leave-requests validation + happy path (weekday count, quota check)
- Sequential 3-layer approval: HRD -> Direksi/Manager -> Reviewer
- Wrong-role 403 guards
- Rejection at any stage
- Reviewer toggle (HR_ROLES, only managers)
- Balance endpoint (year, quota, used, pending, remaining)
- Leave-list scoping (mine/all + can_act), pending-count
- Notifications include leave items
- Settings leave_quota persistence

After tests we cleanup created test users + their leave requests, and reset
settings to defaults so the preview DB stays clean.
"""
import os
import pytest
import requests
from datetime import date, timedelta

def _load_frontend_env():
    p = "/app/frontend/.env"
    if os.path.exists(p):
        with open(p) as f:
            for line in f:
                line = line.strip()
                if line.startswith("REACT_APP_BACKEND_URL="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    os.environ.setdefault("REACT_APP_BACKEND_URL", val)
                    return val
    return None

_load_frontend_env()
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL must be set"
OWNER_EMAIL = "owner@company.com"
OWNER_PASSWORD = "password123"

USERS = {
    "staff":   {"email": "TEST_staff_f3@company.com",   "name": "TEST Staff F3",   "role": "staff",    "department": "QA"},
    "hrd":     {"email": "TEST_hrd_f3@company.com",     "name": "TEST HRD F3",     "role": "hrd",      "department": "HR"},
    "direksi": {"email": "TEST_direksi_f3@company.com", "name": "TEST Direksi F3", "role": "direksi",  "department": "BOD"},
    "mgr":     {"email": "TEST_mgr_f3@company.com",     "name": "TEST Mgr F3",     "role": "manager",  "department": "Eng"},
    "rev":     {"email": "TEST_rev_f3@company.com",     "name": "TEST Reviewer",   "role": "manager",  "department": "Eng"},
}
PASSWORD = "password123"


# ---------- helpers / fixtures ----------
def _login(email, password):
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": email, "password": password}, timeout=20)
    assert r.status_code == 200, f"login {email}: {r.status_code} {r.text}"
    return r.json()["token"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def owner_token():
    return _login(OWNER_EMAIL, OWNER_PASSWORD)


@pytest.fixture(scope="module")
def created_users(owner_token):
    """Create the 5 test users, set reviewer flag on rev, return {key: user_id}."""
    ids = {}
    for key, body in USERS.items():
        payload = {**body, "password": PASSWORD}
        r = requests.post(f"{BASE_URL}/api/employees", headers=_h(owner_token),
                          json=payload, timeout=20)
        # if already exists from a previous failed run, locate by email
        if r.status_code in (200, 201):
            ids[key] = r.json()["id"]
        else:
            # find from list
            lst = requests.get(f"{BASE_URL}/api/employees", headers=_h(owner_token), timeout=20).json()
            found = next((u for u in lst if u["email"] == body["email"]), None)
            assert found, f"could not create or locate {body['email']}: {r.status_code} {r.text}"
            ids[key] = found["id"]

    # set rev as reviewer (must be manager already)
    r = requests.put(f"{BASE_URL}/api/employees/{ids['rev']}/reviewer",
                     headers=_h(owner_token), json={"is_reviewer": True}, timeout=20)
    assert r.status_code == 200, r.text
    assert r.json().get("is_reviewer") is True

    yield ids

    # ---- teardown: delete all created users + their leave requests ----
    owner_tok = _login(OWNER_EMAIL, OWNER_PASSWORD)
    # delete leave_requests by user_id via owner: there's no public delete; rely on direct API absence -> use db not available here.
    # Best-effort: delete each user (cascades not guaranteed). Also reset leave_quota.
    for uid in ids.values():
        requests.delete(f"{BASE_URL}/api/employees/{uid}", headers=_h(owner_tok), timeout=20)
    # reset settings
    requests.put(f"{BASE_URL}/api/settings", headers=_h(owner_tok),
                 json={"work_start": "09:00", "work_end": "17:00",
                       "tolerance_minutes": 15, "leave_quota": 12}, timeout=20)


@pytest.fixture(scope="module")
def tokens(created_users):
    return {k: _login(u["email"] if isinstance(u, dict) else USERS[k]["email"], PASSWORD)
            for k, u in {**USERS, **{kk: kk for kk in USERS}}.items() if False} or {
        k: _login(USERS[k]["email"], PASSWORD) for k in USERS
    }


# ---------- helpers ----------
def _next_weekday(d: date) -> date:
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def _range_n_weekdays(n: int, start_offset_days: int = 14):
    """Pick a Monday start far in the future and n weekdays inclusive."""
    s = date.today() + timedelta(days=start_offset_days)
    # roll to next Monday
    while s.weekday() != 0:
        s += timedelta(days=1)
    # need n weekdays inclusive starting Monday
    cur, count = s, 0
    e = s
    while count < n:
        if cur.weekday() < 5:
            count += 1
            e = cur
        cur += timedelta(days=1)
    return s.isoformat(), e.isoformat()


# ---------- tests ----------
class TestLeaveValidation:
    def test_create_invalid_dates_end_before_start(self, tokens):
        r = requests.post(f"{BASE_URL}/api/leave-requests", headers=_h(tokens["staff"]),
                          json={"leave_type": "tahunan", "start_date": "2030-01-10",
                                "end_date": "2030-01-05", "reason": "x"}, timeout=20)
        assert r.status_code == 400

    def test_create_bad_date_format(self, tokens):
        r = requests.post(f"{BASE_URL}/api/leave-requests", headers=_h(tokens["staff"]),
                          json={"leave_type": "tahunan", "start_date": "bad",
                                "end_date": "2030-01-05", "reason": "x"}, timeout=20)
        assert r.status_code == 400

    def test_create_no_weekdays_in_range(self, tokens):
        # 2030-01-05 (Sat) and 2030-01-06 (Sun)
        r = requests.post(f"{BASE_URL}/api/leave-requests", headers=_h(tokens["staff"]),
                          json={"leave_type": "tahunan", "start_date": "2030-01-05",
                                "end_date": "2030-01-06", "reason": "x"}, timeout=20)
        assert r.status_code == 400

    def test_quota_exceeded(self, tokens):
        # quota=12; pick a 13-weekday range
        s, e = _range_n_weekdays(13)
        r = requests.post(f"{BASE_URL}/api/leave-requests", headers=_h(tokens["staff"]),
                          json={"leave_type": "tahunan", "start_date": s,
                                "end_date": e, "reason": "too much"}, timeout=20)
        assert r.status_code == 400
        assert "cuti" in r.text.lower() or "sisa" in r.text.lower()


class TestSequentialApproval:
    """Create a 3-weekday 'tahunan' leave, push through HRD -> Direksi -> Reviewer."""

    @pytest.fixture(scope="class")
    def leave_id(self, tokens, created_users):
        s, e = _range_n_weekdays(3, start_offset_days=20)
        r = requests.post(f"{BASE_URL}/api/leave-requests", headers=_h(tokens["staff"]),
                          json={"leave_type": "tahunan", "start_date": s,
                                "end_date": e, "reason": "family"}, timeout=20)
        assert r.status_code in (200, 201), r.text
        data = r.json()
        assert data["status"] == "pending"
        assert data["stage"] == "hrd"
        assert data["days"] == 3
        return data["id"]

    def test_wrong_role_reviewer_cannot_act_at_hrd(self, tokens, leave_id):
        r = requests.post(f"{BASE_URL}/api/leave-requests/{leave_id}/approve",
                          headers=_h(tokens["rev"]), json={"note": ""}, timeout=20)
        assert r.status_code == 403

    def test_wrong_role_direksi_cannot_act_at_hrd(self, tokens, leave_id):
        r = requests.post(f"{BASE_URL}/api/leave-requests/{leave_id}/approve",
                          headers=_h(tokens["direksi"]), json={"note": ""}, timeout=20)
        assert r.status_code == 403

    def test_hrd_approves(self, tokens, leave_id):
        r = requests.post(f"{BASE_URL}/api/leave-requests/{leave_id}/approve",
                          headers=_h(tokens["hrd"]), json={"note": "ok"}, timeout=20)
        assert r.status_code == 200, r.text
        assert r.json()["stage"] == "direksi"
        assert r.json()["status"] == "pending"

    def test_hrd_cannot_act_again(self, tokens, leave_id):
        r = requests.post(f"{BASE_URL}/api/leave-requests/{leave_id}/approve",
                          headers=_h(tokens["hrd"]), json={"note": ""}, timeout=20)
        assert r.status_code == 403

    def test_direksi_approves(self, tokens, leave_id):
        r = requests.post(f"{BASE_URL}/api/leave-requests/{leave_id}/approve",
                          headers=_h(tokens["direksi"]), json={"note": "ok"}, timeout=20)
        assert r.status_code == 200, r.text
        assert r.json()["stage"] == "reviewer"
        assert r.json()["status"] == "pending"

    def test_non_reviewer_manager_blocked_at_reviewer(self, tokens, leave_id):
        r = requests.post(f"{BASE_URL}/api/leave-requests/{leave_id}/approve",
                          headers=_h(tokens["mgr"]), json={"note": ""}, timeout=20)
        assert r.status_code == 403

    def test_reviewer_approves_finalizes(self, tokens, leave_id):
        r = requests.post(f"{BASE_URL}/api/leave-requests/{leave_id}/approve",
                          headers=_h(tokens["rev"]), json={"note": "ok"}, timeout=20)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["status"] == "approved"
        assert body["stage"] == "done"

    def test_balance_after_full_approval(self, tokens, created_users):
        r = requests.get(f"{BASE_URL}/api/leave/balance", headers=_h(tokens["staff"]), timeout=20)
        assert r.status_code == 200
        bal = r.json()
        assert bal["quota"] == 12
        assert bal["used"] >= 3
        assert bal["remaining"] == bal["quota"] - bal["used"]


class TestRejection:
    def test_reject_at_hrd_then_no_more_actions(self, tokens):
        s, e = _range_n_weekdays(2, start_offset_days=40)
        r = requests.post(f"{BASE_URL}/api/leave-requests", headers=_h(tokens["staff"]),
                          json={"leave_type": "izin", "start_date": s, "end_date": e,
                                "reason": "personal"}, timeout=20)
        assert r.status_code in (200, 201), r.text
        lid = r.json()["id"]

        r = requests.post(f"{BASE_URL}/api/leave-requests/{lid}/reject",
                          headers=_h(tokens["hrd"]), json={"note": "tidak disetujui"}, timeout=20)
        assert r.status_code == 200, r.text
        assert r.json().get("status") == "rejected"

        # verify via GET that stage=done, reject_reason persisted
        lst = requests.get(f"{BASE_URL}/api/leave-requests?scope=mine",
                          headers=_h(tokens["staff"]), timeout=20).json()
        items = lst.get("items", lst) if isinstance(lst, dict) else lst
        match = next((it for it in items if it["id"] == lid), None)
        assert match is not None
        assert match["status"] == "rejected"
        assert match["stage"] == "done"
        assert "tidak disetujui" in (match.get("reject_reason") or "")

        # subsequent approve must fail
        r = requests.post(f"{BASE_URL}/api/leave-requests/{lid}/approve",
                          headers=_h(tokens["hrd"]), json={"note": ""}, timeout=20)
        assert r.status_code in (400, 403)


class TestReviewerToggle:
    def test_owner_can_set_reviewer_on_manager(self, owner_token, created_users):
        r = requests.put(f"{BASE_URL}/api/employees/{created_users['mgr']}/reviewer",
                         headers=_h(owner_token), json={"is_reviewer": True}, timeout=20)
        assert r.status_code == 200
        assert r.json()["is_reviewer"] is True
        # revert
        r2 = requests.put(f"{BASE_URL}/api/employees/{created_users['mgr']}/reviewer",
                         headers=_h(owner_token), json={"is_reviewer": False}, timeout=20)
        assert r2.status_code == 200
        assert r2.json()["is_reviewer"] is False

    def test_cannot_set_reviewer_on_non_manager(self, owner_token, created_users):
        r = requests.put(f"{BASE_URL}/api/employees/{created_users['staff']}/reviewer",
                         headers=_h(owner_token), json={"is_reviewer": True}, timeout=20)
        assert r.status_code == 400

    def test_employees_list_includes_is_reviewer(self, owner_token, created_users):
        r = requests.get(f"{BASE_URL}/api/employees", headers=_h(owner_token), timeout=20)
        assert r.status_code == 200
        rev = next((u for u in r.json() if u["id"] == created_users["rev"]), None)
        assert rev is not None
        assert "is_reviewer" in rev
        assert rev["is_reviewer"] is True


class TestBalanceAndPending:
    def test_balance_with_pending(self, tokens):
        # create a pending tahunan request and check 'pending' field
        s, e = _range_n_weekdays(2, start_offset_days=60)
        r = requests.post(f"{BASE_URL}/api/leave-requests", headers=_h(tokens["staff"]),
                          json={"leave_type": "tahunan", "start_date": s, "end_date": e,
                                "reason": "pending check"}, timeout=20)
        assert r.status_code in (200, 201), r.text
        bal = requests.get(f"{BASE_URL}/api/leave/balance", headers=_h(tokens["staff"]), timeout=20).json()
        assert bal["pending"] >= 2
        assert bal["remaining"] == bal["quota"] - bal["used"]


class TestListScopingAndCounts:
    def test_mine_scope_returns_only_own(self, tokens, created_users):
        r = requests.get(f"{BASE_URL}/api/leave-requests?scope=mine",
                         headers=_h(tokens["staff"]), timeout=20)
        assert r.status_code == 200
        data = r.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        assert all(it["user_id"] == created_users["staff"] for it in items)

    def test_all_scope_for_approver_with_can_act(self, tokens):
        r = requests.get(f"{BASE_URL}/api/leave-requests?scope=all",
                         headers=_h(tokens["hrd"]), timeout=20)
        assert r.status_code == 200
        data = r.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        # at least one pending at stage 'hrd' should have can_act=True for HRD
        assert any(it.get("stage") == "hrd" and it.get("can_act") is True
                   for it in items if it.get("status") == "pending")

    def test_pending_count_for_hrd(self, tokens):
        r = requests.get(f"{BASE_URL}/api/leave-requests/pending-count",
                         headers=_h(tokens["hrd"]), timeout=20)
        assert r.status_code == 200
        assert r.json().get("count", 0) >= 1


class TestNotifications:
    def test_hrd_sees_leave_notification(self, tokens):
        r = requests.get(f"{BASE_URL}/api/notifications", headers=_h(tokens["hrd"]), timeout=20)
        assert r.status_code == 200
        data = r.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        assert any(it.get("type") == "leave" and it.get("route") == "leave" for it in items)

    def test_requester_sees_decided_leave_notif(self, tokens):
        r = requests.get(f"{BASE_URL}/api/notifications", headers=_h(tokens["staff"]), timeout=20)
        assert r.status_code == 200
        data = r.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        # staff should see at least one route=='leave' item (approved/rejected after the flows above)
        assert any(it.get("route") == "leave" for it in items)


class TestSettingsLeaveQuota:
    def test_settings_has_leave_quota_default(self, owner_token):
        r = requests.get(f"{BASE_URL}/api/settings", headers=_h(owner_token), timeout=20)
        assert r.status_code == 200
        assert r.json().get("leave_quota") == 12

    def test_owner_can_update_leave_quota(self, owner_token):
        r = requests.put(f"{BASE_URL}/api/settings", headers=_h(owner_token),
                         json={"work_start": "09:00", "work_end": "17:00",
                               "tolerance_minutes": 15, "leave_quota": 15}, timeout=20)
        assert r.status_code == 200
        get_r = requests.get(f"{BASE_URL}/api/settings", headers=_h(owner_token), timeout=20).json()
        assert get_r["leave_quota"] == 15
        # restore
        requests.put(f"{BASE_URL}/api/settings", headers=_h(owner_token),
                     json={"work_start": "09:00", "work_end": "17:00",
                           "tolerance_minutes": 15, "leave_quota": 12}, timeout=20)
