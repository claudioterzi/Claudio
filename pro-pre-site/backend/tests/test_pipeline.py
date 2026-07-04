"""Tests for the new Pipeline (Kanban) feature — PATCH first_contact_at/admin_notes
and GET /api/admin/clients/{email}/detail.
"""
import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "test_session_1783058333710")

TINY_PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
TINY_PHOTO_DATAURL = f"data:image/png;base64,{TINY_PNG_B64}"

STATE = {}


@pytest.fixture(scope="module")
def admin_api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json",
                      "Authorization": f"Bearer {ADMIN_TOKEN}"})
    return s


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def _future_date(offset_days: int) -> str:
    return (datetime.utcnow() + timedelta(days=offset_days)).strftime("%Y-%m-%d")


class TestPipelineFlow:
    def test_create_contract_for_pipeline(self, api):
        offset = random.randint(3000, 4000)
        payload = {
            "full_name": "TEST Pipeline Rossi",
            "email": f"test_pipeline_{uuid.uuid4().hex[:8]}@example.com",
            "phone": "+32 400 999 000",
            "address": "Rue TEST Pipeline 1",
            "city": "Bruxelles",
            "postal_code": "1000",
            "date": _future_date(offset),
            "time_slot": "09:00-12:00",
            "service_id": "canape_3",
            "quantity": 1,
            "dirty_area_description": "TEST pipeline",
            "photo_before_base64": TINY_PHOTO_DATAURL,
            "signature_typed": "TEST Pipeline",
            "accept_terms": True,
            "language": "it",
        }
        r = api.post(f"{BASE_URL}/api/contracts", json=payload)
        assert r.status_code == 200, r.text
        data = r.json()
        STATE["contract_id"] = data["contract_id"]
        STATE["email"] = payload["email"].lower()

    def test_admin_contracts_exposes_created_and_first_contact(self, admin_api):
        r = admin_api.get(f"{BASE_URL}/api/admin/contracts")
        assert r.status_code == 200
        contracts = r.json()["contracts"]
        target = next((c for c in contracts if c["id"] == STATE["contract_id"]), None)
        assert target is not None
        # Fields required for Pipeline bucketing
        assert "created_at" in target, "created_at must be exposed for pipeline age-bucketing"
        assert "first_contact_at" in target, "first_contact_at key must appear (nullable)"
        assert target["first_contact_at"] in (None, "") or isinstance(target["first_contact_at"], str)

    def test_patch_first_contact_at(self, admin_api):
        cid = STATE["contract_id"]
        iso = datetime.now(timezone.utc).isoformat()
        r = admin_api.patch(f"{BASE_URL}/api/admin/contracts/{cid}",
                            json={"first_contact_at": iso, "admin_notes": "TEST notes from pipeline"})
        assert r.status_code == 200, r.text
        # verify persistence
        r2 = admin_api.get(f"{BASE_URL}/api/admin/contracts")
        found = next(c for c in r2.json()["contracts"] if c["id"] == cid)
        assert found["first_contact_at"] == iso
        assert found.get("admin_notes") == "TEST notes from pipeline"

    def test_patch_only_admin_notes(self, admin_api):
        cid = STATE["contract_id"]
        r = admin_api.patch(f"{BASE_URL}/api/admin/contracts/{cid}",
                            json={"admin_notes": "updated"})
        assert r.status_code == 200

    def test_patch_unknown_contract_404(self, admin_api):
        r = admin_api.patch(f"{BASE_URL}/api/admin/contracts/does-not-exist",
                            json={"first_contact_at": datetime.now(timezone.utc).isoformat()})
        assert r.status_code == 404

    def test_patch_requires_admin(self, api):
        cid = STATE["contract_id"]
        r = api.patch(f"{BASE_URL}/api/admin/contracts/{cid}",
                      json={"first_contact_at": datetime.now(timezone.utc).isoformat()})
        assert r.status_code == 401


class TestClientDetail:
    def test_client_detail_requires_admin(self, api):
        r = api.get(f"{BASE_URL}/api/admin/clients/{STATE['email']}/detail")
        assert r.status_code == 401

    def test_client_detail_returns_bundle(self, admin_api):
        r = admin_api.get(f"{BASE_URL}/api/admin/clients/{STATE['email']}/detail")
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["email"] == STATE["email"]
        assert isinstance(d["bookings"], list)
        assert isinstance(d["contracts"], list)
        assert any(c["id"] == STATE["contract_id"] for c in d["contracts"])
        s = d["stats"]
        for k in ("total_bookings", "total_contracts", "total_spent",
                  "completed_services", "last_visit"):
            assert k in s
        # no base64 leaking
        for c in d["contracts"]:
            assert "photo_before_base64" not in c
            assert "photo_after_base64" not in c

    def test_client_detail_case_insensitive(self, admin_api):
        upper = STATE["email"].upper()
        r = admin_api.get(f"{BASE_URL}/api/admin/clients/{upper}/detail")
        assert r.status_code == 200
        d = r.json()
        assert d["email"] == STATE["email"]


class TestRegressionContracts:
    def test_admin_contract_pdf(self, admin_api):
        cid = STATE["contract_id"]
        r = admin_api.get(f"{BASE_URL}/api/contracts/{cid}/pdf")
        assert r.status_code == 200
        assert r.content[:4] == b"%PDF"

    def test_admin_contract_photo_before(self, admin_api):
        cid = STATE["contract_id"]
        r = admin_api.get(f"{BASE_URL}/api/admin/contracts/{cid}/photo/before")
        assert r.status_code == 200
        assert r.headers.get("Content-Type", "").startswith("image/")

    def test_admin_after_photo_upload_and_status_transition(self, admin_api):
        cid = STATE["contract_id"]
        r = admin_api.post(f"{BASE_URL}/api/admin/contracts/{cid}/after-photo",
                           json={"photo_after_base64": TINY_PHOTO_DATAURL})
        assert r.status_code == 200
        r2 = admin_api.get(f"{BASE_URL}/api/admin/contracts")
        found = next(c for c in r2.json()["contracts"] if c["id"] == cid)
        assert found["has_photo_after"] is True
        assert found["status"] == "test_done"

    def test_admin_patch_completed(self, admin_api):
        cid = STATE["contract_id"]
        r = admin_api.patch(f"{BASE_URL}/api/admin/contracts/{cid}",
                            json={"status": "completed"})
        assert r.status_code == 200
        r2 = admin_api.get(f"{BASE_URL}/api/admin/contracts")
        found = next(c for c in r2.json()["contracts"] if c["id"] == cid)
        assert found["status"] == "completed"


class TestCleanup:
    def test_delete_contract(self, admin_api):
        cid = STATE["contract_id"]
        r = admin_api.delete(f"{BASE_URL}/api/admin/contracts/{cid}")
        assert r.status_code == 200
        # verify gone
        r2 = admin_api.get(f"{BASE_URL}/api/admin/contracts")
        assert not any(c["id"] == cid for c in r2.json()["contracts"])
