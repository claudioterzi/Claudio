"""End-to-end tests for the new Contracts + Magic Link + Admin KPI endpoints."""
import base64
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv
from itsdangerous import URLSafeTimedSerializer

# Load MAGIC_LINK_SECRET from backend/.env (never hardcode secrets in tests)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://tissu-propre.preview.emergentagent.com").rstrip("/")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "test_session_1782982652632")
MAGIC_SECRET = os.environ["MAGIC_LINK_SECRET"]

# 1x1 red PNG (base64) — valid, tiny
TINY_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
)
TINY_PHOTO_DATAURL = f"data:image/png;base64,{TINY_PNG_B64}"


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def admin_api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json", "Authorization": f"Bearer {ADMIN_TOKEN}"})
    return s


import random
_BASE_OFFSET = random.randint(400, 2000)

def _unique_slot(offset_days=0):
    d = (datetime.utcnow() + timedelta(days=_BASE_OFFSET + offset_days)).strftime("%Y-%m-%d")
    return d

# Module-level state (works both under xdist and serial)
STATE = {}


# --- Contract creation ---
class TestContractCreate:
    def test_health(self, api):
        r = api.get(f"{BASE_URL}/api/")
        assert r.status_code == 200, r.text

    def test_create_contract_success(self, api, request):
        payload = {
            "full_name": "TEST Mario Rossi",
            "email": "test_mario_rossi@example.com",
            "phone": "+32 400 111 222",
            "address": "Rue TEST 12",
            "city": "Bruxelles",
            "postal_code": "1000",
            "date": _unique_slot(200),
            "time_slot": "09:00-12:00",
            "service_id": "canape_3",
            "quantity": 1,
            "dirty_area_description": "Tache TEST sur accoudoir",
            "photo_before_base64": TINY_PHOTO_DATAURL,
            "signature_typed": "Mario Rossi",
            "deposit_choice": "in_person",
            "language": "it",
            "accept_terms": True,
            "notes": "TEST"
        }
        r = api.post(f"{BASE_URL}/api/contracts", json=payload)
        assert r.status_code == 200, f"{r.status_code} {r.text}"
        data = r.json()
        assert data.get("ok") is True
        for k in ("contract_id", "booking_id", "pdf_url", "space_url", "estimated_price"):
            assert k in data, f"missing key {k}"
        assert data["estimated_price"] == 110.0
        # persist for later tests
        STATE["contract_id"] = data["contract_id"]
        STATE["contract_date"] = payload["date"]
        STATE["contract_slot"] = payload["time_slot"]
        STATE["contract_email"] = payload["email"].lower()

    def test_reject_terms_false(self, api):
        payload = {
            "full_name": "TEST", "email": "test_x@example.com", "phone": "1",
            "address": "a", "city": "b", "postal_code": "1000",
            "date": _unique_slot(210), "time_slot": "09:00-12:00",
            "service_id": "canape_3", "quantity": 1,
            "dirty_area_description": "x", "photo_before_base64": TINY_PHOTO_DATAURL,
            "signature_typed": "X", "accept_terms": False, "language": "fr",
        }
        r = api.post(f"{BASE_URL}/api/contracts", json=payload)
        assert r.status_code == 400

    def test_reject_empty_signature(self, api):
        payload = {
            "full_name": "TEST", "email": "test_x2@example.com", "phone": "1",
            "address": "a", "city": "b", "postal_code": "1000",
            "date": _unique_slot(211), "time_slot": "09:00-12:00",
            "service_id": "canape_3", "quantity": 1,
            "dirty_area_description": "x", "photo_before_base64": TINY_PHOTO_DATAURL,
            "signature_typed": "   ", "accept_terms": True, "language": "fr",
        }
        r = api.post(f"{BASE_URL}/api/contracts", json=payload)
        assert r.status_code == 400

    def test_reject_invalid_photo(self, api):
        payload = {
            "full_name": "TEST", "email": "test_x3@example.com", "phone": "1",
            "address": "a", "city": "b", "postal_code": "1000",
            "date": _unique_slot(212), "time_slot": "09:00-12:00",
            "service_id": "canape_3", "quantity": 1,
            "dirty_area_description": "x", "photo_before_base64": "data:image/png;base64,@@@notb64@@@",
            "signature_typed": "X", "accept_terms": True, "language": "fr",
        }
        r = api.post(f"{BASE_URL}/api/contracts", json=payload)
        assert r.status_code == 400

    def test_slot_conflict_returns_409(self, api, request):
        # reuse date + slot from first test
        date = STATE.get("contract_date")
        slot = STATE.get("contract_slot")
        assert date and slot, "prev test didn't run"
        payload = {
            "full_name": "TEST Dupe", "email": "test_dupe@example.com", "phone": "1",
            "address": "a", "city": "b", "postal_code": "1000",
            "date": date, "time_slot": slot,
            "service_id": "canape_3", "quantity": 1,
            "dirty_area_description": "x", "photo_before_base64": TINY_PHOTO_DATAURL,
            "signature_typed": "Dupe", "accept_terms": True, "language": "fr",
        }
        r = api.post(f"{BASE_URL}/api/contracts", json=payload)
        assert r.status_code == 409, f"expected 409 got {r.status_code} {r.text}"


# --- PDF download ---
class TestContractPDF:
    def test_pdf_download(self, api, request):
        cid = STATE.get("contract_id")
        assert cid, "no contract_id"
        r = api.get(f"{BASE_URL}/api/contracts/{cid}/pdf")
        assert r.status_code == 200, r.text
        assert r.headers.get("Content-Type", "").startswith("application/pdf")
        assert r.content[:4] == b"%PDF", f"not a PDF: {r.content[:20]!r}"
        assert len(r.content) > 2048, f"pdf too small: {len(r.content)}"


# --- Defi endpoint (fixed decorator) ---
class TestDefiEndpoint:
    def test_defi_post(self, api):
        payload = {
            "full_name": "TEST Defi",
            "phone": "+32 400 000",
            "email": "test_defi@example.com",
            "address": "Rue defi",
            "city": "Bruxelles",
            "postal_code": "1050",
            "date": _unique_slot(220),
            "time_slot": "13:00-16:00",
            "language": "fr",
        }
        r = api.post(f"{BASE_URL}/api/defi", json=payload)
        assert r.status_code == 200, r.text
        j = r.json()
        assert j.get("type") == "defi"


# --- Admin KPI + contracts admin ---
class TestAdminKPI:
    def test_kpi_requires_auth(self, api):
        r = api.get(f"{BASE_URL}/api/admin/kpi")
        assert r.status_code == 401

    def test_kpi_with_admin(self, admin_api):
        r = admin_api.get(f"{BASE_URL}/api/admin/kpi")
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("total_bookings", "by_status", "by_type", "revenue", "last_30_days",
                  "clients", "contracts", "conversion_rate_percent", "top_services"):
            assert k in d, f"missing kpi key {k}"
        assert "confirmed" in d["revenue"] and "completed" in d["revenue"] and "all_estimated" in d["revenue"]
        assert "total" in d["contracts"] and "signed" in d["contracts"]
        assert isinstance(d["top_services"], list)

    def test_admin_list_contracts(self, admin_api, request):
        r = admin_api.get(f"{BASE_URL}/api/admin/contracts")
        assert r.status_code == 200, r.text
        contracts = r.json().get("contracts", [])
        assert isinstance(contracts, list)
        assert len(contracts) >= 1
        c0 = contracts[0]
        assert "has_photo_before" in c0 and "has_photo_after" in c0
        # base64 photos MUST NOT be embedded in the list response
        assert "photo_before_base64" not in c0
        assert "photo_after_base64" not in c0

    def test_admin_patch_contract_status(self, admin_api, request):
        cid = STATE.get("contract_id")
        r = admin_api.patch(f"{BASE_URL}/api/admin/contracts/{cid}", json={"status": "test_done"})
        assert r.status_code == 200, r.text
        # verify by list
        r2 = admin_api.get(f"{BASE_URL}/api/admin/contracts")
        found = [c for c in r2.json()["contracts"] if c["id"] == cid]
        assert found and found[0]["status"] == "test_done"

    def test_admin_patch_deposit(self, admin_api, request):
        cid = STATE.get("contract_id")
        r = admin_api.patch(f"{BASE_URL}/api/admin/contracts/{cid}", json={"deposit_status": "paid"})
        assert r.status_code == 200
        r2 = admin_api.get(f"{BASE_URL}/api/admin/contracts")
        found = [c for c in r2.json()["contracts"] if c["id"] == cid]
        assert found and found[0]["deposit_status"] == "paid"

    def test_admin_after_photo(self, admin_api, request):
        cid = STATE.get("contract_id")
        r = admin_api.post(
            f"{BASE_URL}/api/admin/contracts/{cid}/after-photo",
            json={"photo_after_base64": TINY_PHOTO_DATAURL},
        )
        assert r.status_code == 200, r.text
        # verify status becomes test_done and photo flag true
        r2 = admin_api.get(f"{BASE_URL}/api/admin/contracts")
        found = [c for c in r2.json()["contracts"] if c["id"] == cid][0]
        assert found["has_photo_after"] is True

    def test_admin_get_photo_before(self, admin_api, request):
        cid = STATE.get("contract_id")
        r = admin_api.get(f"{BASE_URL}/api/admin/contracts/{cid}/photo/before")
        assert r.status_code == 200
        assert r.headers.get("Content-Type", "").startswith("image/")
        assert len(r.content) > 30

    def test_admin_get_photo_after(self, admin_api, request):
        cid = STATE.get("contract_id")
        r = admin_api.get(f"{BASE_URL}/api/admin/contracts/{cid}/photo/after")
        assert r.status_code == 200
        assert r.headers.get("Content-Type", "").startswith("image/")


# --- Client magic link ---
class TestClientMagicLink:
    def test_request_magic_link_known_email(self, api, request):
        email = STATE.get("contract_email")
        r = api.post(f"{BASE_URL}/api/client/request-magic-link", json={"email": email, "language": "it"})
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is True
        assert d["sent"] is True

    def test_request_magic_link_unknown_email(self, api):
        r = api.post(f"{BASE_URL}/api/client/request-magic-link",
                     json={"email": f"unknown_{uuid.uuid4().hex}@example.com"})
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is True
        assert d["sent"] is False

    def test_verify_magic_link_and_list_contracts(self, request):
        email = STATE.get("contract_email")
        signer = URLSafeTimedSerializer(MAGIC_SECRET, salt="pro-pre-magic-v1")
        token = signer.dumps({"email": email})
        s = requests.Session()
        r = s.get(f"{BASE_URL}/api/client/verify-magic-link", params={"token": token})
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["ok"] is True
        assert d["email"] == email
        assert "client_session" in s.cookies.get_dict(), "cookie not set"

        # now list contracts
        r2 = s.get(f"{BASE_URL}/api/client/contracts")
        assert r2.status_code == 200, r2.text
        contracts = r2.json()["contracts"]
        assert isinstance(contracts, list)
        assert any(c.get("client_email") == email for c in contracts)
        # no base64 leaking
        for c in contracts:
            assert "photo_before_base64" not in c
            assert "photo_after_base64" not in c

    def test_verify_expired_token(self):
        # Craft an obviously bad token
        r = requests.get(f"{BASE_URL}/api/client/verify-magic-link", params={"token": "not-a-real-token"})
        assert r.status_code == 401

    def test_client_contracts_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/client/contracts")
        assert r.status_code == 401


# --- Admin delete contract (cleanup) ---
class TestAdminCleanup:
    def test_admin_delete_contract(self, admin_api, request):
        cid = STATE.get("contract_id")
        r = admin_api.delete(f"{BASE_URL}/api/admin/contracts/{cid}")
        assert r.status_code == 200

    def test_cleanup_test_bookings(self, admin_api):
        # nothing to assert, best-effort cleanup via admin listing
        r = admin_api.get(f"{BASE_URL}/api/admin/bookings")
        assert r.status_code == 200
