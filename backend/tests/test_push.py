"""Backend tests for Web Push endpoints + push-hook non-regression."""
import os
import uuid
import requests
import pytest

BASE = os.environ['REACT_APP_BACKEND_URL'].rstrip('/')
API = f"{BASE}/api"

OWNER = "owner@company.com"
PW = "password123"


def _h(t):
    return {"Authorization": f"Bearer {t}"}


@pytest.fixture(scope="module")
def owner_token():
    r = requests.post(f"{API}/auth/login",
                      json={"email": OWNER, "password": PW}, timeout=20)
    assert r.status_code == 200, r.text
    return r.json()["token"]


class TestVapidPublicKey:
    def test_returns_key_and_configured_true(self):
        r = requests.get(f"{API}/push/vapid-public-key", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "key" in data
        assert isinstance(data["key"], str) and len(data["key"]) > 20
        assert data.get("configured") is True


class TestPushSubscriptionLifecycle:
    def test_subscribe_status_unsubscribe(self, owner_token):
        endpoint = (
            f"https://fcm.googleapis.com/fcm/send/TEST_{uuid.uuid4().hex[:24]}"
        )
        fake_sub = {
            "endpoint": endpoint,
            "expirationTime": None,
            "keys": {
                "p256dh": "BNcRdreALRFXTkOOUHK1EtK2wtaz5Ry4YfYCA_0QTpQtUbVlUls0VJXg7A8u-Ts1XbjhazAkj7I99e8QcYP7DkM",
                "auth": "tBHItJI5svbpez7KI4CCXg",
            },
        }

        # Status before: subscribed should be False for this endpoint scope (owner-level)
        # (Owner may have other subs; we only care about delta.)
        s0 = requests.get(f"{API}/push/status", headers=_h(owner_token), timeout=15)
        assert s0.status_code == 200, s0.text
        count_before = s0.json().get("count", 0)
        assert s0.json().get("configured") is True

        # Subscribe
        r = requests.post(f"{API}/push/subscribe", headers=_h(owner_token),
                          json={"subscription": fake_sub}, timeout=15)
        assert r.status_code == 200, r.text
        assert r.json().get("ok") is True

        # Status after subscribe: at least one and >= count_before+1 (idempotent upsert)
        s1 = requests.get(f"{API}/push/status", headers=_h(owner_token), timeout=15)
        assert s1.status_code == 200
        body1 = s1.json()
        assert body1["subscribed"] is True
        assert body1["count"] >= max(1, count_before)

        # Upsert idempotency: re-subscribe same endpoint should not duplicate
        r2 = requests.post(f"{API}/push/subscribe", headers=_h(owner_token),
                           json={"subscription": fake_sub}, timeout=15)
        assert r2.status_code == 200
        s2 = requests.get(f"{API}/push/status", headers=_h(owner_token), timeout=15)
        assert s2.json()["count"] == body1["count"], "upsert should not duplicate"

        # Unsubscribe
        u = requests.post(f"{API}/push/unsubscribe", headers=_h(owner_token),
                         json={"endpoint": endpoint}, timeout=15)
        assert u.status_code == 200
        assert u.json().get("ok") is True

        # Status after: count back to original
        s3 = requests.get(f"{API}/push/status", headers=_h(owner_token), timeout=15)
        assert s3.status_code == 200
        assert s3.json()["count"] == count_before

    def test_subscribe_requires_auth(self):
        r = requests.post(f"{API}/push/subscribe",
                         json={"subscription": {"endpoint": "x"}}, timeout=15)
        assert r.status_code == 401

    def test_subscribe_invalid_payload_returns_400(self, owner_token):
        # Missing endpoint
        r = requests.post(f"{API}/push/subscribe", headers=_h(owner_token),
                         json={"subscription": {"keys": {}}}, timeout=15)
        assert r.status_code == 400


class TestPushHooksNoRegression:
    """Verify the send_push_to_users hooks do not break existing endpoints
    when there are no subscriptions / when sending fails silently."""

    def test_create_employee_still_works(self, owner_token):
        email = f"TEST_push_{uuid.uuid4().hex[:8]}@company.com"
        cr = requests.post(f"{API}/employees", headers=_h(owner_token),
                          json={"name": "Push Hook Tester",
                                "email": email,
                                "password": PW, "role": "staff"},
                          timeout=20)
        assert cr.status_code == 200, cr.text
        emp_id = cr.json()["id"]
        # Cleanup
        requests.delete(f"{API}/employees/{emp_id}",
                       headers=_h(owner_token), timeout=15)

    def test_create_request_path_hook(self, owner_token):
        """Owner creating their own request shouldn't error (request hook fires)."""
        # Some apps reject owner self-requests; we only assert no 5xx server error.
        payload = {"type": "leave", "title": "TEST_push_request",
                   "description": "x", "date": "2026-12-31"}
        r = requests.post(f"{API}/requests", headers=_h(owner_token),
                         json=payload, timeout=20)
        # Accept 200/201/400/403 — anything except 5xx (hook must not throw)
        assert r.status_code < 500, f"hook threw 5xx: {r.text}"
