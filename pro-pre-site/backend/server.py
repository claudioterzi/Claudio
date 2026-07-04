from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response, status
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import uuid
import base64
import httpx
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Literal
from datetime import datetime, timezone, timedelta, date as date_type
import requests as _requests
from fastapi import UploadFile, File, Form
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
APP_NAME = "r3nettoyage"
_storage_key = None

def init_storage():
    global _storage_key
    if _storage_key:
        return _storage_key
    key = os.environ.get("EMERGENT_LLM_KEY")
    if not key:
        return None
    try:
        r = _requests.post(f"{STORAGE_URL}/init", json={"emergent_key": key}, timeout=15)
        r.raise_for_status()
        _storage_key = r.json()["storage_key"]
        return _storage_key
    except Exception:
        return None

def storage_put(path: str, data: bytes, content_type: str):
    key = init_storage()
    if not key:
        raise HTTPException(status_code=503, detail="Storage not configured")
    r = _requests.put(f"{STORAGE_URL}/objects/{path}",
                      headers={"X-Storage-Key": key, "Content-Type": content_type},
                      data=data, timeout=60)
    r.raise_for_status()
    return r.json()

def storage_get(path: str):
    key = init_storage()
    if not key:
        raise HTTPException(status_code=503, detail="Storage not configured")
    r = _requests.get(f"{STORAGE_URL}/objects/{path}",
                      headers={"X-Storage-Key": key}, timeout=30)
    r.raise_for_status()
    return r.content, r.headers.get("Content-Type", "application/octet-stream")

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI(title="Pro-pre API")
api_router = APIRouter(prefix="/api")

# ---------- Constants ----------
ADMIN_EMAILS = {"terziclaudio@gmail.com"}

# Service catalog — prices in EUR
SERVICES = [
    {"id": "canape_2",   "category": "canape",    "name_fr": "Canapé 2 places",   "price": 80,  "unit": "fixe"},
    {"id": "canape_3",   "category": "canape",    "name_fr": "Canapé 3 places",   "price": 110, "unit": "fixe"},
    {"id": "canape_ang", "category": "canape",    "name_fr": "Canapé d'angle",    "price": 150, "unit": "fixe"},
    {"id": "matelas_1",  "category": "matelas",   "name_fr": "Matelas 1 place",   "price": 65,  "unit": "fixe"},
    {"id": "matelas_2",  "category": "matelas",   "name_fr": "Matelas 2 places",  "price": 90,  "unit": "fixe"},
    {"id": "tapis",      "category": "tapis",     "name_fr": "Tapis",             "price": 20,  "unit": "m2"},
    {"id": "escaliers",  "category": "escaliers", "name_fr": "Escaliers moquette","price": 7,   "unit": "marche"},
    {"id": "auto",       "category": "auto",      "name_fr": "Sièges auto (5 sièges)","price": 100, "unit": "fixe"},
]

TIME_SLOTS = ["09:00-12:00", "13:00-16:00", "16:00-19:00"]
MAX_BOOKINGS_PER_SLOT = 1

# Promo codes — DB-backed. Legacy hard-coded fallback kept for backwards compat
# but only used if no active DB code exists with the same identifier.
PROMO_CODES = {
    "VOISIN20": {"discount": 20, "min_amount": 80, "type": "fixed"},
}


async def resolve_promo_code(code: str, subtotal: float) -> tuple[float, str]:
    """Return (discount_amount, promo_applied). Checks DB first, then legacy dict."""
    code = (code or "").strip().upper()
    if not code:
        return 0.0, ""
    now = datetime.now(timezone.utc).isoformat()
    doc = await db.promo_codes.find_one({"code": code, "active": True})
    if doc:
        if doc.get("expires_at") and doc["expires_at"] < now:
            return 0.0, ""
        if doc.get("max_uses") and doc.get("uses_count", 0) >= doc["max_uses"]:
            return 0.0, ""
        if subtotal < float(doc.get("min_amount") or 0):
            return 0.0, ""
        if doc.get("type") == "percent":
            return round(subtotal * float(doc["value"]) / 100.0, 2), code
        return float(doc["value"]), code
    legacy = PROMO_CODES.get(code)
    if legacy and subtotal >= legacy.get("min_amount", 0):
        return float(legacy["discount"]), code
    return 0.0, ""

# Travel fee tiers (by postal code prefix)
def compute_travel_fee(postal_code: str) -> int:
    pc = (postal_code or "").strip().replace(" ", "")
    if not pc:
        return 0
    # Brussels centre (1000-1210)
    if pc.isdigit() and len(pc) == 4:
        n = int(pc)
        if 1000 <= n <= 1210:
            return 0
        if 1211 <= n <= 1500:
            return 20
        return 40
    # France
    if pc.isdigit() and len(pc) == 5:
        # Paris intra-muros 75001-75020
        if pc.startswith("750") and pc[3:5] != "00":
            return 0
        # Île-de-France suburbs
        if pc[:2] in {"77", "78", "91", "92", "93", "94", "95"}:
            return 20
        return 40
    return 40

# ---------- Models ----------
class BookingItem(BaseModel):
    service_id: str
    quantity: float = 1  # m² for tapis, marches for escaliers, else 1

class BookingCreate(BaseModel):
    items: List[BookingItem]
    full_name: str
    phone: str
    email: EmailStr
    address: str
    city: str
    postal_code: str
    date: str  # YYYY-MM-DD
    time_slot: str
    notes: Optional[str] = ""
    language: Optional[str] = "fr"
    promo_code: Optional[str] = ""

class Booking(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[BookingItem]
    full_name: str
    phone: str
    email: str
    address: str
    city: str
    postal_code: str
    date: str
    time_slot: str
    notes: Optional[str] = ""
    language: str = "fr"
    estimated_price: float
    services_subtotal: float = 0.0
    travel_fee: float = 0.0
    promo_code: Optional[str] = ""
    promo_discount: float = 0.0
    status: Literal["nouvelle", "confirmee", "completee", "annulee"] = "nouvelle"
    type: Literal["service", "defi"] = "service"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DefiCreate(BaseModel):
    full_name: str
    phone: str
    email: EmailStr
    address: str
    city: str
    postal_code: str
    date: str
    time_slot: str
    notes: Optional[str] = ""
    language: Optional[str] = "fr"

class StatusUpdate(BaseModel):
    status: Literal["nouvelle", "confirmee", "completee", "annulee"]

# ---------- Helpers ----------
def calc_price(items: List[BookingItem]) -> float:
    total = 0.0
    svc_map = {s["id"]: s for s in SERVICES}
    for it in items:
        svc = svc_map.get(it.service_id)
        if not svc:
            continue
        total += svc["price"] * max(1, it.quantity)
    return round(total, 2)

def compute_quote(items: List[BookingItem], postal_code: str, promo_code: str = ""):
    subtotal = calc_price(items)
    travel = compute_travel_fee(postal_code)
    discount = 0.0
    promo_applied = ""
    code = (promo_code or "").strip().upper()
    if code and code in PROMO_CODES:
        promo = PROMO_CODES[code]
        if subtotal >= promo.get("min_amount", 0):
            discount = float(promo["discount"])
            promo_applied = code
    total = max(0.0, subtotal + travel - discount)
    return {
        "subtotal": round(subtotal, 2),
        "travel_fee": float(travel),
        "promo_discount": round(discount, 2),
        "promo_applied": promo_applied,
        "total": round(total, 2),
    }


async def compute_quote_async(items: List[BookingItem], postal_code: str, promo_code: str = ""):
    subtotal = calc_price(items)
    travel = compute_travel_fee(postal_code)
    discount, promo_applied = await resolve_promo_code(promo_code, subtotal)
    total = max(0.0, subtotal + travel - discount)
    return {
        "subtotal": round(subtotal, 2),
        "travel_fee": float(travel),
        "promo_discount": round(discount, 2),
        "promo_applied": promo_applied,
        "total": round(total, 2),
    }

def serialize_booking(doc: dict) -> dict:
    if isinstance(doc.get("created_at"), str):
        try:
            doc["created_at"] = datetime.fromisoformat(doc["created_at"])
        except Exception:
            pass
    return doc

async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("session_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    sess = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not sess:
        raise HTTPException(status_code=401, detail="Invalid session")
    expires_at = sess["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    user = await db.users.find_one({"user_id": sess["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# ---------- Public Routes ----------
@api_router.get("/")
async def root():
    return {"message": "Pro-pre API", "status": "ok"}

@api_router.get("/services")
async def get_services():
    return {"services": SERVICES, "time_slots": TIME_SLOTS}

@api_router.get("/availability")
async def get_availability(date: str):
    """Return which slots are taken (booked or admin-blocked) for a given date."""
    booked = await db.bookings.find(
        {"date": date, "status": {"$ne": "annulee"}}, {"_id": 0, "time_slot": 1}
    ).to_list(100)
    blocked = await db.blocked_slots.find({"date": date}, {"_id": 0, "time_slot": 1}).to_list(100)
    taken = {b["time_slot"] for b in booked} | {b["time_slot"] for b in blocked}
    return {
        "date": date,
        "slots": [
            {"slot": s, "available": s not in taken}
            for s in TIME_SLOTS
        ],
    }

@api_router.post("/quote")
async def quote(payload: dict):
    items = [BookingItem(**i) for i in payload.get("items", [])]
    return compute_quote(items, payload.get("postal_code", ""), payload.get("promo_code", ""))

@api_router.post("/bookings", response_model=Booking)
async def create_booking(payload: BookingCreate):
    # check slot availability (bookings + admin blocks)
    count = await db.bookings.count_documents(
        {"date": payload.date, "time_slot": payload.time_slot, "status": {"$ne": "annulee"}}
    )
    blocked = await db.blocked_slots.count_documents({"date": payload.date, "time_slot": payload.time_slot})
    if count >= MAX_BOOKINGS_PER_SLOT or blocked > 0:
        raise HTTPException(status_code=409, detail="Slot already booked")
    if payload.time_slot not in TIME_SLOTS:
        raise HTTPException(status_code=400, detail="Invalid time slot")
    if not payload.items:
        raise HTTPException(status_code=400, detail="At least one service required")
    q = compute_quote(payload.items, payload.postal_code, payload.promo_code or "")
    booking = Booking(
        **payload.model_dump(),
        estimated_price=q["total"],
        services_subtotal=q["subtotal"],
        travel_fee=q["travel_fee"],
        promo_discount=q["promo_discount"],
        type="service",
    )
    doc = booking.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    # Link booking to user_id if account exists with same email
    existing_user = await db.users.find_one({"email": payload.email.lower()}, {"_id": 0, "user_id": 1})
    if existing_user:
        doc["user_id"] = existing_user["user_id"]
    await db.bookings.insert_one(doc)
    return booking

@api_router.post("/defi", response_model=Booking)
async def create_defi(payload: DefiCreate):
    count = await db.bookings.count_documents(
        {"date": payload.date, "time_slot": payload.time_slot, "status": {"$ne": "annulee"}}
    )
    if count >= MAX_BOOKINGS_PER_SLOT:
        raise HTTPException(status_code=409, detail="Slot already booked")
    if payload.time_slot not in TIME_SLOTS:
        raise HTTPException(status_code=400, detail="Invalid time slot")
    booking = Booking(
        **payload.model_dump(),
        items=[],
        estimated_price=0.0,
        type="defi",
    )
    doc = booking.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    await db.bookings.insert_one(doc)
    return booking

# ---------- Auth Routes (Emergent Google Auth) ----------
@api_router.post("/auth/session")
async def auth_session(request: Request, response: Response):
    """Exchange session_id from URL fragment for a session_token cookie."""
    body = await request.json()
    session_id = body.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")

    async with httpx.AsyncClient(timeout=10.0) as http:
        r = await http.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id},
        )
    if r.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid session_id")
    data = r.json()
    email = data.get("email", "").lower()
    name = data.get("name", "")
    picture = data.get("picture", "")
    session_token = data["session_token"]

    is_admin = email in ADMIN_EMAILS

    # Upsert user
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    if existing:
        user_id = existing["user_id"]
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": name, "picture": picture, "is_admin": is_admin}},
        )
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        await db.users.insert_one({
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "is_admin": is_admin,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60,
    )
    return {
        "user_id": user_id,
        "email": email,
        "name": name,
        "picture": picture,
        "is_admin": is_admin,
    }

@api_router.get("/auth/me")
async def auth_me(user: dict = Depends(get_current_user)):
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user.get("name", ""),
        "picture": user.get("picture", ""),
        "is_admin": bool(user.get("is_admin")),
    }

@api_router.post("/auth/logout")
async def auth_logout(request: Request, response: Response):
    token = request.cookies.get("session_token")
    if token:
        await db.user_sessions.delete_one({"session_token": token})
    response.delete_cookie("session_token", path="/", samesite="none", secure=True)
    return {"ok": True}

# ---------- Chatbot ----------
class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    language: Optional[str] = "fr"
    session_id: Optional[str] = None

SYSTEM_PROMPT = """You are the friendly assistant of Pro-pre — main website: https://www.pro-pre.com (also reachable via https://www.pro-pre.fr). A professional textile cleaning service based in Brussels (open) with future tournées to Paris and Bergamo (waitlist). Run by Claudio.
Services with current prices in EUR:
- Canapé 2 places: €80
- Canapé 3 places: €110
- Canapé d'angle: €150
- Matelas 1 place: €65
- Matelas 2 places: €90
- Tapis: €20/m²
- Escaliers moquette: €7 per step
- Sièges auto (5 seats): €100
- Free 30x30cm test ("Défi de la Bande")
Travel fee: Bruxelles 1000-1210 and Paris 75001-75020 = FREE. Periphery = +€20. Beyond = +€40.
Launch promo code: VOISIN20 (-€20 on bookings ≥ €80).
Service areas: Bruxelles (open) · Paris and Bergamo (coming soon, waitlist).
Technology: Kärcher injection-extraction (deep, residue-free, dries in 2-6h).
Payment: cash, bank transfer or **card (Revolut Tap to Pay on iPhone)** AT THE END of the job. No deposit.
Contact: WhatsApp / phone +33 6 74 93 20 00, email Terziclaudio@gmail.com.
Always be warm and concise (max 3 short sentences). Reply in the language of the user.
If asked to book, invite them to use the "Prendre RDV" button on the site.
"""

@api_router.post("/chat")
async def chat(payload: ChatRequest):
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat library missing: {e}")
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Chat not configured")
    sid = payload.session_id or f"chat_{uuid.uuid4().hex[:12]}"
    lang_hint = f"\nUser language preference: {payload.language}."
    chat_inst = LlmChat(
        api_key=api_key, session_id=sid,
        system_message=SYSTEM_PROMPT + lang_hint,
    ).with_model("anthropic", "claude-sonnet-4-6")
    # Replay history for context (library is stateless per session_id within this request)
    last_user = ""
    for m in payload.messages:
        if m.role == "user":
            last_user = m.content
    if not last_user:
        raise HTTPException(status_code=400, detail="No user message")
    reply_text = ""
    try:
        reply_text = await chat_inst.send_message(UserMessage(text=last_user))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Chat error: {e}")
    return {"reply": reply_text, "session_id": sid}

# ---------- Admin Routes ----------
@api_router.get("/admin/bookings")
async def admin_list_bookings(user: dict = Depends(require_admin)):
    projection = {"_id": 0, "id": 1, "date": 1, "time_slot": 1, "full_name": 1, "email": 1,
                  "phone": 1, "address": 1, "city": 1, "postal_code": 1, "status": 1,
                  "estimated_price": 1, "type": 1, "items": 1, "notes": 1, "created_at": 1}
    docs = await db.bookings.find({}, projection).sort("date", 1).to_list(1000)
    for d in docs:
        serialize_booking(d)
    return {"bookings": docs}

@api_router.patch("/admin/bookings/{booking_id}")
async def admin_update_booking(booking_id: str, payload: StatusUpdate, user: dict = Depends(require_admin)):
    res = await db.bookings.update_one({"id": booking_id}, {"$set": {"status": payload.status}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"ok": True}

@api_router.get("/admin/stats")
async def admin_stats(user: dict = Depends(require_admin)):
    pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    results = await db.bookings.aggregate(pipeline).to_list(10)
    stats = {r["_id"]: r["count"] for r in results}
    return {
        "total": sum(stats.values()),
        "nouvelle": stats.get("nouvelle", 0),
        "confirmee": stats.get("confirmee", 0),
        "completee": stats.get("completee", 0),
    }

class BlockPayload(BaseModel):
    date: str
    time_slot: str

# ---------- Gallery (public + admin) ----------
class GalleryItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    storage_path: str
    caption: str = ""
    category: str = "avant_apres"  # avant_apres | eau_extraite | canape | matelas | tapis | auto
    is_published: bool = True
    content_type: str = "image/jpeg"
    created_at: str = ""

@api_router.get("/gallery")
async def public_gallery():
    docs = await db.gallery_items.find(
        {"is_published": True},
        {"_id": 0, "id": 1, "storage_path": 1, "caption": 1, "category": 1, "created_at": 1}
    ).sort("created_at", -1).to_list(200)
    return {"items": docs}

@api_router.get("/gallery/{path:path}")
async def serve_gallery_file(path: str):
    """Public endpoint to serve gallery images (published only)."""
    rec = await db.gallery_items.find_one({"storage_path": path, "is_published": True}, {"_id": 0})
    if not rec:
        raise HTTPException(status_code=404, detail="Not found")
    data, ctype = storage_get(path)
    return Response(content=data, media_type=rec.get("content_type", ctype))

@api_router.post("/admin/gallery")
async def admin_upload_gallery(
    caption: str = Form(""),
    category: str = Form("avant_apres"),
    file: UploadFile = File(...),
    user: dict = Depends(require_admin),
):
    ext = (file.filename or "").split(".")[-1].lower() if "." in (file.filename or "") else "jpg"
    if ext not in {"jpg", "jpeg", "png", "webp"}:
        raise HTTPException(status_code=400, detail="Image required")
    item_id = str(uuid.uuid4())
    path = f"{APP_NAME}/gallery/{category}/{item_id}.{ext}"
    data = await file.read()
    ctype = file.content_type or f"image/{'jpeg' if ext=='jpg' else ext}"
    storage_put(path, data, ctype)
    rec = {
        "id": item_id,
        "storage_path": path,
        "caption": caption,
        "category": category,
        "is_published": True,
        "content_type": ctype,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.gallery_items.insert_one(rec)
    return {**rec}

@api_router.get("/admin/gallery")
async def admin_list_gallery(user: dict = Depends(require_admin)):
    docs = await db.gallery_items.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
    return {"items": docs}

@api_router.patch("/admin/gallery/{item_id}")
async def admin_toggle_gallery(item_id: str, payload: dict, user: dict = Depends(require_admin)):
    await db.gallery_items.update_one({"id": item_id}, {"$set": {"is_published": bool(payload.get("is_published", True))}})
    return {"ok": True}

@api_router.delete("/admin/gallery/{item_id}")
async def admin_delete_gallery(item_id: str, user: dict = Depends(require_admin)):
    await db.gallery_items.delete_one({"id": item_id})
    return {"ok": True}

# ---------- Admin: clients ----------
@api_router.get("/admin/clients")
async def admin_list_clients(user: dict = Depends(require_admin)):
    pipeline = [
        {"$group": {
            "_id": "$email",
            "full_name": {"$last": "$full_name"},
            "phone": {"$last": "$phone"},
            "city": {"$last": "$city"},
            "postal_code": {"$last": "$postal_code"},
            "bookings_count": {"$sum": 1},
            "total_spent": {"$sum": {"$ifNull": ["$estimated_price", 0]}},
            "last_booking": {"$max": "$date"},
            "last_status": {"$last": "$status"},
        }},
        {"$sort": {"last_booking": -1}},
    ]
    results = await db.bookings.aggregate(pipeline).to_list(1000)
    clients = [{"email": r["_id"], **{k: v for k, v in r.items() if k != "_id"}} for r in results]
    return {"clients": clients}

@api_router.get("/admin/blocks")
async def admin_list_blocks(user: dict = Depends(require_admin)):
    docs = await db.blocked_slots.find({}, {"_id": 0}).sort("date", 1).to_list(1000)
    return {"blocks": docs}

@api_router.post("/admin/blocks")
async def admin_block_slot(payload: BlockPayload, user: dict = Depends(require_admin)):
    if payload.time_slot not in TIME_SLOTS:
        raise HTTPException(status_code=400, detail="Invalid time slot")
    existing = await db.blocked_slots.find_one({"date": payload.date, "time_slot": payload.time_slot})
    if existing:
        return {"ok": True, "already": True}
    await db.blocked_slots.insert_one({
        "id": str(uuid.uuid4()),
        "date": payload.date,
        "time_slot": payload.time_slot,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"ok": True}

@api_router.delete("/admin/blocks")
async def admin_unblock_slot(date: str, time_slot: str, user: dict = Depends(require_admin)):
    await db.blocked_slots.delete_many({"date": date, "time_slot": time_slot})
    return {"ok": True}

# ---------- Customer space (any logged user) ----------
@api_router.get("/me/bookings")
async def my_bookings(user: dict = Depends(get_current_user)):
    projection = {"_id": 0, "id": 1, "date": 1, "time_slot": 1, "full_name": 1, "email": 1,
                  "address": 1, "city": 1, "postal_code": 1, "status": 1,
                  "estimated_price": 1, "type": 1, "items": 1}
    docs = await db.bookings.find({"$or": [{"user_id": user["user_id"]}, {"email": user["email"]}]}, projection).sort("date", -1).to_list(500)
    booking_ids = [d["id"] for d in docs]
    all_photos = await db.booking_photos.find({"booking_id": {"$in": booking_ids}, "is_deleted": False}, {"_id": 0}).to_list(5000)
    all_contracts = await db.contracts.find({"booking_id": {"$in": booking_ids}}, {"_id": 0}).to_list(500)
    photos_by_booking = {}
    for p in all_photos:
        photos_by_booking.setdefault(p["booking_id"], []).append(p)
    contracts_by_booking = {c["booking_id"]: c for c in all_contracts}
    for d in docs:
        d["photos"] = photos_by_booking.get(d["id"], [])
        d["contract"] = contracts_by_booking.get(d["id"])
    return {"bookings": docs}

@api_router.post("/bookings/{booking_id}/photos")
async def upload_booking_photo(
    booking_id: str,
    kind: str = Form(...),  # 'before' | 'after' | 'issue'
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    b = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not b:
        raise HTTPException(status_code=404, detail="Booking not found")
    # Permission: admin OR booking owner (by user_id or email)
    if not user.get("is_admin") and b.get("user_id") != user["user_id"] and b.get("email") != user["email"]:
        raise HTTPException(status_code=403, detail="Not your booking")
    # Clients only allowed 'issue', admin allowed all
    if not user.get("is_admin") and kind != "issue":
        raise HTTPException(status_code=403, detail="Clients can only upload issue photos")
    if kind not in {"before", "after", "issue"}:
        raise HTTPException(status_code=400, detail="Invalid kind")
    ext = (file.filename or "").split(".")[-1].lower() if "." in (file.filename or "") else "jpg"
    if ext not in {"jpg", "jpeg", "png", "webp"}:
        raise HTTPException(status_code=400, detail="Image required")
    photo_id = str(uuid.uuid4())
    path = f"{APP_NAME}/bookings/{booking_id}/{kind}/{photo_id}.{ext}"
    data = await file.read()
    storage_put(path, data, file.content_type or f"image/{'jpeg' if ext=='jpg' else ext}")
    rec = {
        "id": photo_id,
        "booking_id": booking_id,
        "kind": kind,
        "storage_path": path,
        "content_type": file.content_type or f"image/{'jpeg' if ext=='jpg' else ext}",
        "uploaded_by": user["user_id"],
        "is_deleted": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.booking_photos.insert_one(rec)
    return {"id": photo_id, "kind": kind, "url": f"/api/files/{path}"}

@api_router.get("/files/{path:path}")
async def serve_file(path: str, request: Request):
    # Require auth and ensure the file relates to one of user's bookings or user is admin
    try:
        user = await get_current_user(request)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Not authenticated")
    rec = await db.booking_photos.find_one({"storage_path": path, "is_deleted": False}, {"_id": 0})
    if not rec:
        raise HTTPException(status_code=404, detail="Not found")
    if not user.get("is_admin"):
        b = await db.bookings.find_one({"id": rec["booking_id"]}, {"_id": 0})
        if not b or (b.get("user_id") != user["user_id"] and b.get("email") != user["email"]):
            raise HTTPException(status_code=403, detail="Forbidden")
    data, ctype = storage_get(path)
    return Response(content=data, media_type=rec.get("content_type", ctype))

class ContractAccept(BaseModel):
    accepted: bool

@api_router.post("/bookings/{booking_id}/contract")
async def accept_contract(booking_id: str, payload: ContractAccept, request: Request, user: dict = Depends(get_current_user)):
    b = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not b:
        raise HTTPException(status_code=404, detail="Booking not found")
    if b.get("user_id") != user["user_id"] and b.get("email") != user["email"]:
        raise HTTPException(status_code=403, detail="Not your booking")
    if not payload.accepted:
        raise HTTPException(status_code=400, detail="Must accept")
    ip = request.client.host if request.client else ""
    ua = request.headers.get("user-agent", "")
    record = {
        "id": str(uuid.uuid4()),
        "booking_id": booking_id,
        "user_id": user["user_id"],
        "email": user["email"],
        "ip": ip,
        "user_agent": ua,
        "accepted_at": datetime.now(timezone.utc).isoformat(),
        "snapshot": {
            "full_name": b["full_name"],
            "address": b["address"],
            "postal_code": b["postal_code"],
            "city": b["city"],
            "date": b["date"],
            "time_slot": b["time_slot"],
            "items": b.get("items", []),
            "estimated_price": b["estimated_price"],
            "conditions": [
                "Paiement à la fin du travail (espèces ou virement)",
                "Garantie Défi de la Bande : si insatisfait au test, aucun engagement",
                "Annulation gratuite jusqu'à 24h avant l'intervention",
            ],
        },
    }
    await db.contracts.insert_one(record)
    return {"ok": True, "contract_id": record["id"]}

# ---------- Contracts (Défi de la Bande with signature + PDF + payment) ----------
from pdf_generator import generate_contract_pdf
from email_service import (
    send_contract_confirmation,
    send_magic_link,
    send_admin_new_contract,
)

MAGIC_SECRET = os.environ.get("MAGIC_LINK_SECRET", "dev-secret-change-me")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://tissu-propre.preview.emergentagent.com")
_magic_signer = URLSafeTimedSerializer(MAGIC_SECRET, salt="pro-pre-magic-v1")


def _service_by_id(sid: str):
    for s in SERVICES:
        if s["id"] == sid:
            return s
    return None


def _label_for_service(sid: str, lang: str = "fr") -> str:
    svc = _service_by_id(sid)
    if not svc:
        return sid
    # Only French names in SERVICES catalog; return name_fr as canonical label
    return svc.get("name_fr", sid)


class ContractCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    address: str
    city: str = "Bruxelles"
    postal_code: str
    date: str  # YYYY-MM-DD
    time_slot: str
    service_id: str
    quantity: float = 1
    dirty_area_description: str
    photo_before_base64: str  # data:image/...;base64,...
    signature_typed: str  # client's typed name to render as signature
    deposit_choice: Literal["none", "stripe", "revolut", "bonifico", "in_person"] = "none"
    language: str = "fr"
    accept_terms: bool = True
    gallery_consent: bool = False
    notes: Optional[str] = ""


def _validate_photo_b64(b64_str: str, max_bytes: int = 8 * 1024 * 1024):
    if not b64_str:
        raise HTTPException(status_code=400, detail="Photo required")
    try:
        raw = b64_str
        if raw.startswith("data:"):
            _, raw = raw.split(",", 1)
        data = base64.b64decode(raw)
        if len(data) > max_bytes:
            raise HTTPException(status_code=413, detail="Photo too large (max 8 MB)")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid photo")


@api_router.post("/contracts")
async def create_contract(payload: ContractCreate, request: Request):
    if not payload.accept_terms:
        raise HTTPException(status_code=400, detail="Terms must be accepted")
    if payload.time_slot not in TIME_SLOTS:
        raise HTTPException(status_code=400, detail="Invalid time slot")
    if not payload.signature_typed.strip():
        raise HTTPException(status_code=400, detail="Signature required")
    _validate_photo_b64(payload.photo_before_base64)

    svc = _service_by_id(payload.service_id)
    if not svc:
        raise HTTPException(status_code=400, detail="Invalid service")

    # Check slot availability (defi + bookings share same slots)
    booked = await db.bookings.count_documents(
        {"date": payload.date, "time_slot": payload.time_slot, "status": {"$ne": "annulee"}}
    )
    blocked = await db.blocked_slots.count_documents(
        {"date": payload.date, "time_slot": payload.time_slot}
    )
    if booked >= MAX_BOOKINGS_PER_SLOT or blocked > 0:
        raise HTTPException(status_code=409, detail="Slot already booked")

    # Price
    qty = max(1.0, float(payload.quantity or 1))
    price = round(svc["price"] * qty, 2)

    contract_id = str(uuid.uuid4())
    booking_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    ip = request.client.host if request.client else ""

    # Persist booking (type='defi' so it links to Défi de la Bande flow)
    booking_doc = {
        "id": booking_id,
        "items": [{"service_id": svc["id"], "quantity": qty}],
        "full_name": payload.full_name,
        "phone": payload.phone,
        "email": payload.email.lower(),
        "address": payload.address,
        "city": payload.city,
        "postal_code": payload.postal_code,
        "date": payload.date,
        "time_slot": payload.time_slot,
        "language": payload.language,
        "notes": payload.notes or "",
        "estimated_price": price,
        "services_subtotal": price,
        "travel_fee": 0.0,
        "promo_discount": 0.0,
        "promo_code": "",
        "status": "nouvelle",
        "type": "defi",
        "created_at": now.isoformat(),
        "contract_id": contract_id,
    }
    # Link to existing user if any
    existing_user = await db.users.find_one({"email": payload.email.lower()}, {"_id": 0, "user_id": 1})
    if existing_user:
        booking_doc["user_id"] = existing_user["user_id"]
    await db.bookings.insert_one(booking_doc)

    # Persist contract
    contract_doc = {
        "id": contract_id,
        "booking_id": booking_id,
        "client_name": payload.full_name,
        "client_email": payload.email.lower(),
        "client_phone": payload.phone,
        "address": payload.address,
        "city": payload.city,
        "postal_code": payload.postal_code,
        "date": payload.date,
        "time_slot": payload.time_slot,
        "service_id": svc["id"],
        "service_label": svc["name_fr"],
        "service_price": price,
        "quantity": qty,
        "dirty_area_description": payload.dirty_area_description,
        "signature_typed": payload.signature_typed.strip(),
        "deposit_choice": payload.deposit_choice,
        "deposit_status": "pending" if payload.deposit_choice != "none" else "not_required",
        "language": payload.language,
        "photo_before_base64": payload.photo_before_base64,
        "photo_after_base64": None,
        "gallery_consent": bool(payload.gallery_consent),
        "gallery_consent_at": now.isoformat() if payload.gallery_consent else None,
        "status": "signed",
        "signed_at": now.isoformat(),
        "ip_address": ip,
        "created_at": now.isoformat(),
        "city_signed": payload.city,
    }
    await db.contracts.insert_one(contract_doc)

    # Build URLs
    pdf_url = f"{FRONTEND_URL.rstrip('/')}/api/contracts/{contract_id}/pdf"
    space_url = f"{FRONTEND_URL.rstrip('/')}/mon-espace"

    # Fire-and-forget emails
    try:
        # Client confirmation
        await send_contract_confirmation(
            to=payload.email,
            lang=payload.language,
            client_name=payload.full_name,
            date_str=payload.date,
            time_slot=payload.time_slot,
            address=f"{payload.address}, {payload.postal_code} {payload.city}",
            contract_pdf_url=pdf_url,
            space_url=space_url,
        )
        # Magic link so client can access their space (no password)
        magic_token = _magic_signer.dumps({"email": payload.email.lower()})
        magic_url = f"{FRONTEND_URL.rstrip('/')}/mon-espace?token={magic_token}"
        await send_magic_link(payload.email, payload.language, magic_url)
        # Admin notification
        admin_url = f"{FRONTEND_URL.rstrip('/')}/admin"
        await send_admin_new_contract(
            lang=payload.language,
            client_name=payload.full_name,
            client_email=payload.email,
            client_phone=payload.phone,
            date_str=payload.date,
            time_slot=payload.time_slot,
            service_label=svc["name_fr"],
            service_price=price,
            deposit_choice=payload.deposit_choice,
            admin_url=admin_url,
        )
    except Exception as e:
        logger.warning(f"Email dispatch failed: {e}")

    return {
        "ok": True,
        "contract_id": contract_id,
        "booking_id": booking_id,
        "pdf_url": pdf_url,
        "space_url": space_url,
        "estimated_price": price,
    }


@api_router.get("/contracts/{contract_id}/pdf")
async def get_contract_pdf(contract_id: str):
    """Public download of the PDF (signed contract). Anyone with the ID can view.
    (Contract ID is a UUID acting as an unguessable token.)"""
    c = await db.contracts.find_one({"id": contract_id}, {"_id": 0})
    if not c:
        raise HTTPException(status_code=404, detail="Contract not found")
    pdf_bytes = generate_contract_pdf(
        c,
        photo_before_b64=c.get("photo_before_base64"),
        photo_after_b64=c.get("photo_after_base64"),
    )
    filename = f"pro-pre-contract-{contract_id[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


# ---------- Client magic-link auth ----------
class MagicLinkRequest(BaseModel):
    email: EmailStr
    language: Optional[str] = "fr"


@api_router.post("/client/request-magic-link")
async def request_magic_link(payload: MagicLinkRequest):
    email = payload.email.lower()
    # Only send if we have contracts or bookings for this email (prevents spam of random emails)
    has_contract = await db.contracts.find_one({"client_email": email}, {"_id": 0, "id": 1})
    has_booking = await db.bookings.find_one({"email": email}, {"_id": 0, "id": 1})
    if not has_contract and not has_booking:
        # Silent success to avoid enumerating clients
        return {"ok": True, "sent": False}
    token = _magic_signer.dumps({"email": email})
    magic_url = f"{FRONTEND_URL.rstrip('/')}/mon-espace?token={token}"
    await send_magic_link(email, payload.language or "fr", magic_url)
    return {"ok": True, "sent": True}


@api_router.get("/client/verify-magic-link")
async def verify_magic_link(token: str, response: Response):
    try:
        data = _magic_signer.loads(token, max_age=60 * 15)  # 15 min
    except SignatureExpired:
        raise HTTPException(status_code=401, detail="Magic link expired")
    except BadSignature:
        raise HTTPException(status_code=401, detail="Invalid magic link")
    email = data["email"]
    # Create client session token (independent of admin/Google auth)
    session_token = f"client_{uuid.uuid4().hex}"
    expires = datetime.now(timezone.utc) + timedelta(days=7)
    await db.client_sessions.insert_one({
        "session_token": session_token,
        "email": email,
        "expires_at": expires.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    response.set_cookie(
        key="client_session",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60,
    )
    return {"ok": True, "email": email}


async def get_current_client(request: Request) -> str:
    """Returns client email if session valid, else raises 401."""
    token = request.cookies.get("client_session")
    if not token:
        # Fallback: allow via Google auth user too
        try:
            user = await get_current_user(request)
            return user["email"]
        except HTTPException:
            raise HTTPException(status_code=401, detail="Not authenticated")
    sess = await db.client_sessions.find_one({"session_token": token}, {"_id": 0})
    if not sess:
        raise HTTPException(status_code=401, detail="Invalid session")
    exp = sess["expires_at"]
    if isinstance(exp, str):
        exp = datetime.fromisoformat(exp)
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if exp < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    return sess["email"]


@api_router.post("/client/logout")
async def client_logout(request: Request, response: Response):
    token = request.cookies.get("client_session")
    if token:
        await db.client_sessions.delete_one({"session_token": token})
    response.delete_cookie("client_session", path="/", samesite="none", secure=True)
    return {"ok": True}


@api_router.get("/client/me")
async def client_me(request: Request):
    email = await get_current_client(request)
    return {"email": email}


@api_router.get("/client/contracts")
async def client_list_contracts(request: Request):
    email = await get_current_client(request)
    docs = await db.contracts.find(
        {"client_email": email},
        {"_id": 0, "photo_before_base64": 0, "photo_after_base64": 0},
    ).sort("created_at", -1).to_list(500)
    # Add flags for photos
    ids = [d["id"] for d in docs]
    photos = {c["id"]: c for c in await db.contracts.find(
        {"id": {"$in": ids}}, {"_id": 0, "id": 1, "photo_before_base64": 1, "photo_after_base64": 1}
    ).to_list(500)}
    for d in docs:
        p = photos.get(d["id"], {})
        d["has_photo_before"] = bool(p.get("photo_before_base64"))
        d["has_photo_after"] = bool(p.get("photo_after_base64"))
    return {"contracts": docs}


# ---------- Admin: Contracts management ----------
@api_router.get("/admin/contracts")
async def admin_list_contracts(user: dict = Depends(require_admin)):
    docs = await db.contracts.find(
        {},
        {"_id": 0, "photo_before_base64": 0, "photo_after_base64": 0},
    ).sort("created_at", -1).to_list(1000)
    ids = [d["id"] for d in docs]
    photos = {c["id"]: c for c in await db.contracts.find(
        {"id": {"$in": ids}}, {"_id": 0, "id": 1, "photo_before_base64": 1, "photo_after_base64": 1}
    ).to_list(1000)}
    for d in docs:
        p = photos.get(d["id"], {})
        d["has_photo_before"] = bool(p.get("photo_before_base64"))
        d["has_photo_after"] = bool(p.get("photo_after_base64"))
    return {"contracts": docs}


class ContractStatusUpdate(BaseModel):
    status: Optional[Literal["signed", "test_done", "completed", "cancelled"]] = None
    deposit_status: Optional[Literal["pending", "paid", "failed", "refunded", "not_required"]] = None
    first_contact_at: Optional[str] = None
    admin_notes: Optional[str] = None
    # Editable client / RDV fields
    date: Optional[str] = None
    time_slot: Optional[str] = None
    service_label: Optional[str] = None
    service_price: Optional[float] = None
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    client_email: Optional[str] = None
    client_address: Optional[str] = None


@api_router.patch("/admin/contracts/{contract_id}")
async def admin_update_contract(
    contract_id: str,
    payload: ContractStatusUpdate,
    user: dict = Depends(require_admin),
):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        return {"ok": True, "no_change": True}
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    res = await db.contracts.update_one({"id": contract_id}, {"$set": updates})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Contract not found")
    return {"ok": True, "updated": list(updates.keys())}


# ---------- Admin: Communication tools ----------
class ContactLogPayload(BaseModel):
    channel: Literal["phone", "whatsapp", "email", "sms", "in_person", "other"]
    outcome: Literal["reached", "no_answer", "voicemail", "confirmed", "cancelled", "other"] = "reached"
    note: Optional[str] = ""


@api_router.post("/admin/contracts/{contract_id}/log-contact")
async def admin_log_contact(
    contract_id: str,
    payload: ContactLogPayload,
    user: dict = Depends(require_admin),
):
    contract = await db.contracts.find_one({"id": contract_id}, {"_id": 0})
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    now = datetime.now(timezone.utc).isoformat()
    entry = {
        "at": now,
        "by": user.get("email", "admin"),
        "channel": payload.channel,
        "outcome": payload.outcome,
        "note": (payload.note or "").strip()[:800],
    }
    updates = {"$push": {"contact_log": entry}, "$set": {"last_contact_at": now}}
    if not contract.get("first_contact_at"):
        updates["$set"]["first_contact_at"] = now
    await db.contracts.update_one({"id": contract_id}, updates)
    return {"ok": True, "entry": entry}


class SendEmailPayload(BaseModel):
    template: Literal["confirm", "reminder", "reschedule", "custom", "test_done", "thank_you"]
    subject: Optional[str] = None
    body: Optional[str] = None


@api_router.post("/admin/contracts/{contract_id}/send-email")
async def admin_send_client_email(
    contract_id: str,
    payload: SendEmailPayload,
    user: dict = Depends(require_admin),
):
    contract = await db.contracts.find_one({"id": contract_id}, {"_id": 0})
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    to_email = contract.get("client_email")
    if not to_email:
        raise HTTPException(status_code=400, detail="Client has no email")
    name = contract.get("client_name") or "Client"
    date = contract.get("date") or "-"
    ts = contract.get("time_slot") or "-"

    templates = {
        "confirm": (
            f"Confirmation RDV Pro-pre — {date} {ts}",
            f"Bonjour {name},\n\nJe vous confirme notre rendez-vous le {date} ({ts}) pour le Défi de la Bande.\nJe passerai à l'adresse indiquée avec ma machine Kärcher.\n\nÀ très vite,\nClaudio — Pro-pre",
        ),
        "reminder": (
            f"Rappel RDV Pro-pre — {date} {ts}",
            f"Bonjour {name},\n\nPetit rappel de notre RDV du {date} à {ts}.\nMerci de préparer un accès à la pièce concernée.\n\nÀ demain !\nClaudio",
        ),
        "reschedule": (
            "Report du RDV Pro-pre",
            f"Bonjour {name},\n\nJe dois reporter notre RDV initialement prévu le {date} ({ts}).\nPouvez-vous me proposer une nouvelle date ? Je m'adapte à vos disponibilités.\n\nMerci,\nClaudio — Pro-pre",
        ),
        "test_done": (
            "Test effectué — Pro-pre",
            f"Bonjour {name},\n\nLe Défi de la Bande a été effectué. Vous pouvez consulter la photo AVANT/APRÈS dans votre Espace Client :\n{os.environ.get('FRONTEND_URL', 'https://pro-pre.com')}/mon-espace\n\nSi vous souhaitez maintenant le service complet, je reste à votre disposition.\n\nCordialement,\nClaudio",
        ),
        "thank_you": (
            "Merci de votre confiance — Pro-pre",
            f"Bonjour {name},\n\nMerci d'avoir choisi Pro-pre. Une note de 5 étoiles sur Google nous aiderait énormément :\nhttps://g.page/r/pro-pre\n\nÀ bientôt,\nClaudio",
        ),
    }

    if payload.template == "custom":
        subj = payload.subject or "Message de Pro-pre"
        body = payload.body or ""
    else:
        subj, body = templates.get(payload.template, ("Message de Pro-pre", ""))
        if payload.subject:
            subj = payload.subject
        if payload.body:
            body = payload.body

    try:
        from email_service import send_generic_email
        await send_generic_email(to_email, subj, body)
    except Exception as e:
        logger.warning(f"send-email failed: {e}")
        raise HTTPException(status_code=500, detail=f"Email failed: {e}")

    now = datetime.now(timezone.utc).isoformat()
    entry = {
        "at": now,
        "by": user.get("email", "admin"),
        "channel": "email",
        "outcome": "reached",
        "note": f"[{payload.template}] {subj}",
    }
    await db.contracts.update_one(
        {"id": contract_id},
        {"$push": {"contact_log": entry}, "$set": {"last_contact_at": now}},
    )
    return {"ok": True, "sent_to": to_email, "template": payload.template}


@api_router.post("/admin/contracts/{contract_id}/resend-pdf")
async def admin_resend_pdf(contract_id: str, user: dict = Depends(require_admin)):
    contract = await db.contracts.find_one({"id": contract_id}, {"_id": 0})
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if not contract.get("client_email"):
        raise HTTPException(status_code=400, detail="Client has no email")
    try:
        from email_service import send_contract_pdf_email
        await send_contract_pdf_email(contract)
    except Exception as e:
        logger.warning(f"resend-pdf failed: {e}")
        raise HTTPException(status_code=500, detail=f"Email failed: {e}")
    return {"ok": True}


@api_router.post("/admin/contracts/{contract_id}/resend-magic-link")
async def admin_resend_magic_link(contract_id: str, user: dict = Depends(require_admin)):
    contract = await db.contracts.find_one({"id": contract_id}, {"_id": 0})
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    email = (contract.get("client_email") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Client has no email")
    token = _magic_signer.dumps({"email": email})
    link = f"{os.environ.get('FRONTEND_URL', 'https://pro-pre.com')}/mon-espace?token={token}"
    try:
        from email_service import send_generic_email
        await send_generic_email(
            email,
            "Votre lien d'accès Espace Client — Pro-pre",
            f"Bonjour,\n\nVoici votre lien de connexion à votre Espace Client (valide 24h) :\n{link}\n\nCordialement,\nClaudio — Pro-pre",
        )
    except Exception as e:
        logger.warning(f"resend-magic-link failed: {e}")
        raise HTTPException(status_code=500, detail=f"Email failed: {e}")
    return {"ok": True}


class CancelPayload(BaseModel):
    reason: Optional[str] = ""
    notify_client: bool = True


@api_router.post("/admin/contracts/{contract_id}/cancel")
async def admin_cancel_contract(
    contract_id: str,
    payload: CancelPayload,
    user: dict = Depends(require_admin),
):
    contract = await db.contracts.find_one({"id": contract_id}, {"_id": 0})
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    now = datetime.now(timezone.utc).isoformat()
    await db.contracts.update_one(
        {"id": contract_id},
        {"$set": {
            "status": "cancelled",
            "cancelled_at": now,
            "cancel_reason": (payload.reason or "").strip()[:500],
            "cancelled_by": user.get("email", "admin"),
        }},
    )
    if payload.notify_client and contract.get("client_email"):
        try:
            from email_service import send_generic_email
            name = contract.get("client_name") or "Client"
            reason_txt = f"\nMotif : {payload.reason}" if payload.reason else ""
            await send_generic_email(
                contract["client_email"],
                "Annulation de votre RDV — Pro-pre",
                f"Bonjour {name},\n\nVotre RDV Pro-pre a été annulé.{reason_txt}\n\nN'hésitez pas à me recontacter pour reprogrammer.\n\nCordialement,\nClaudio — Pro-pre",
            )
        except Exception as e:
            logger.warning(f"cancel email failed: {e}")
    return {"ok": True}


class AfterPhotoPayload(BaseModel):
    photo_after_base64: str


@api_router.post("/admin/contracts/{contract_id}/after-photo")
async def admin_upload_after_photo(
    contract_id: str,
    payload: AfterPhotoPayload,
    user: dict = Depends(require_admin),
):
    _validate_photo_b64(payload.photo_after_base64)
    res = await db.contracts.update_one(
        {"id": contract_id},
        {"$set": {
            "photo_after_base64": payload.photo_after_base64,
            "photo_after_uploaded_at": datetime.now(timezone.utc).isoformat(),
            "status": "test_done",
        }},
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Contract not found")
    return {"ok": True}


@api_router.delete("/admin/contracts/{contract_id}")
async def admin_delete_contract(contract_id: str, user: dict = Depends(require_admin)):
    await db.contracts.delete_one({"id": contract_id})
    return {"ok": True}


@api_router.get("/admin/contracts/{contract_id}/photo/{kind}")
async def admin_get_contract_photo(
    contract_id: str,
    kind: Literal["before", "after"],
    user: dict = Depends(require_admin),
):
    c = await db.contracts.find_one({"id": contract_id}, {"_id": 0})
    if not c:
        raise HTTPException(status_code=404, detail="Not found")
    field = "photo_before_base64" if kind == "before" else "photo_after_base64"
    b64 = c.get(field)
    if not b64:
        raise HTTPException(status_code=404, detail="Photo not available")
    if b64.startswith("data:"):
        header, raw = b64.split(",", 1)
        mime = header.split(";")[0].replace("data:", "") or "image/jpeg"
    else:
        raw = b64
        mime = "image/jpeg"
    return Response(content=base64.b64decode(raw), media_type=mime)


# ---------- Admin: enhanced KPIs ----------
@api_router.get("/admin/kpi")
async def admin_kpi(user: dict = Depends(require_admin)):
    now = datetime.now(timezone.utc)
    thirty_days_ago = (now - timedelta(days=30)).isoformat()

    # Booking counts by status
    all_bookings = await db.bookings.find({}, {"_id": 0}).to_list(5000)
    total = len(all_bookings)
    by_status = {"nouvelle": 0, "confirmee": 0, "completee": 0, "annulee": 0}
    by_type = {"service": 0, "defi": 0}
    revenue_confirmed = 0.0
    revenue_completed = 0.0
    revenue_all = 0.0
    last_30_count = 0
    last_30_revenue = 0.0
    services_count = {}

    for b in all_bookings:
        st = b.get("status", "nouvelle")
        by_status[st] = by_status.get(st, 0) + 1
        by_type[b.get("type", "service")] = by_type.get(b.get("type", "service"), 0) + 1
        price = float(b.get("estimated_price") or 0)
        revenue_all += price
        if st == "confirmee":
            revenue_confirmed += price
        if st == "completee":
            revenue_completed += price
        for it in b.get("items", []) or []:
            sid = it.get("service_id")
            if sid:
                services_count[sid] = services_count.get(sid, 0) + 1
        if b.get("created_at", "") >= thirty_days_ago:
            last_30_count += 1
            last_30_revenue += price

    # Contracts (Défi de la Bande signed)
    total_contracts = await db.contracts.count_documents({})
    contracts_signed = await db.contracts.count_documents({"status": "signed"})
    contracts_test_done = await db.contracts.count_documents({"status": "test_done"})
    contracts_completed = await db.contracts.count_documents({"status": "completed"})
    deposits_pending = await db.contracts.count_documents({"deposit_status": "pending", "deposit_choice": {"$ne": "none"}})
    deposits_paid = await db.contracts.count_documents({"deposit_status": "paid"})

    # Unique clients
    unique_emails = len({b.get("email") for b in all_bookings if b.get("email")})

    # Conversion rates
    # Defi → completed = signed contracts that led to a paid completed booking
    converted = 0
    contracts_docs = await db.contracts.find({}, {"_id": 0, "booking_id": 1, "client_email": 1}).to_list(2000)
    booking_by_id = {b.get("id"): b for b in all_bookings}
    emails_completed = {b.get("email") for b in all_bookings if b.get("status") == "completee"}
    for c in contracts_docs:
        b = booking_by_id.get(c.get("booking_id"))
        if b and b.get("status") == "completee":
            converted += 1
        elif c.get("client_email") in emails_completed:
            converted += 1
    conversion_rate = (converted / total_contracts * 100.0) if total_contracts else 0.0
    avg_ticket = (revenue_completed / by_status.get("completee", 1)) if by_status.get("completee") else 0.0

    # Top services
    svc_labels = {s["id"]: s["name_fr"] for s in SERVICES}
    top_services = sorted(
        [{"id": k, "label": svc_labels.get(k, k), "count": v} for k, v in services_count.items()],
        key=lambda x: x["count"], reverse=True,
    )[:5]

    return {
        "total_bookings": total,
        "by_status": by_status,
        "by_type": by_type,
        "revenue": {
            "confirmed": round(revenue_confirmed, 2),
            "completed": round(revenue_completed, 2),
            "all_estimated": round(revenue_all, 2),
        },
        "last_30_days": {
            "bookings": last_30_count,
            "revenue_estimated": round(last_30_revenue, 2),
        },
        "clients": {
            "unique": unique_emails,
            "avg_ticket_completed": round(avg_ticket, 2),
        },
        "contracts": {
            "total": total_contracts,
            "signed": contracts_signed,
            "test_done": contracts_test_done,
            "completed": contracts_completed,
            "deposits_pending": deposits_pending,
            "deposits_paid": deposits_paid,
        },
        "conversion_rate_percent": round(conversion_rate, 1),
        "top_services": top_services,
    }


# ---------- Client prefill + client-side photo upload + admin client detail + delete ops ----------
@api_router.get("/client/prefill")
async def client_prefill(request: Request):
    """Return the most recent contact info for the authenticated client
    so the /booking and /defi forms can be pre-filled with one call."""
    email = await get_current_client(request)
    doc = await db.bookings.find_one(
        {"email": email},
        {"_id": 0, "full_name": 1, "phone": 1, "email": 1, "address": 1,
         "city": 1, "postal_code": 1, "language": 1},
        sort=[("created_at", -1)],
    )
    if not doc:
        # Try users collection (Google-auth signup)
        u = await db.users.find_one({"email": email}, {"_id": 0, "name": 1, "email": 1})
        if u:
            return {"prefill": {"full_name": u.get("name", ""), "email": email,
                                "phone": "", "address": "", "city": "Bruxelles",
                                "postal_code": ""}}
        return {"prefill": None}
    return {"prefill": doc}


class ClientPhotoPayload(BaseModel):
    photo_after_base64: str
    dirty_area_note: Optional[str] = None


@api_router.post("/client/contracts/{contract_id}/photo-after")
async def client_upload_after_photo(
    contract_id: str,
    payload: ClientPhotoPayload,
    request: Request,
):
    """Let the client upload the 'After' photo themselves (in addition to admin uploads)."""
    email = await get_current_client(request)
    _validate_photo_b64(payload.photo_after_base64)
    c = await db.contracts.find_one({"id": contract_id, "client_email": email}, {"_id": 0, "id": 1})
    if not c:
        raise HTTPException(status_code=404, detail="Contract not found")
    updates = {
        "photo_after_base64": payload.photo_after_base64,
        "photo_after_uploaded_at": datetime.now(timezone.utc).isoformat(),
        "photo_after_source": "client",
        "status": "test_done",
    }
    if payload.dirty_area_note:
        updates["dirty_area_note_client"] = payload.dirty_area_note
    await db.contracts.update_one({"id": contract_id}, {"$set": updates})
    return {"ok": True}


@api_router.get("/client/contracts/{contract_id}/photo/{kind}")
async def client_get_photo(
    contract_id: str,
    kind: Literal["before", "after"],
    request: Request,
):
    """Client-side auth-gated image fetch for their own contract photos."""
    email = await get_current_client(request)
    c = await db.contracts.find_one({"id": contract_id, "client_email": email}, {"_id": 0})
    if not c:
        raise HTTPException(status_code=404, detail="Not found")
    field = "photo_before_base64" if kind == "before" else "photo_after_base64"
    b64 = c.get(field)
    if not b64:
        raise HTTPException(status_code=404, detail="Photo not available")
    if b64.startswith("data:"):
        header, raw = b64.split(",", 1)
        mime = header.split(";")[0].replace("data:", "") or "image/jpeg"
    else:
        raw = b64
        mime = "image/jpeg"
    return Response(content=base64.b64decode(raw), media_type=mime)


# ---------- Admin: Client detail view + delete ops ----------
@api_router.get("/admin/clients/{email}/detail")
async def admin_client_detail(email: str, user: dict = Depends(require_admin)):
    email_lower = email.lower()
    booking_projection = {"_id": 0, "id": 1, "date": 1, "time_slot": 1,
                          "full_name": 1, "phone": 1, "email": 1, "address": 1,
                          "city": 1, "postal_code": 1, "status": 1, "type": 1,
                          "items": 1, "estimated_price": 1, "notes": 1, "created_at": 1,
                          "language": 1, "contract_id": 1}
    bookings = await db.bookings.find({"email": email_lower}, booking_projection).sort("created_at", -1).to_list(500)
    contract_projection = {"_id": 0, "photo_before_base64": 0, "photo_after_base64": 0}
    contracts_docs = await db.contracts.find({"client_email": email_lower}, contract_projection).sort("created_at", -1).to_list(500)
    ids = [d["id"] for d in contracts_docs]
    photo_flags = {c["id"]: c for c in await db.contracts.find(
        {"id": {"$in": ids}}, {"_id": 0, "id": 1, "photo_before_base64": 1, "photo_after_base64": 1}
    ).to_list(500)}
    for c in contracts_docs:
        p = photo_flags.get(c["id"], {})
        c["has_photo_before"] = bool(p.get("photo_before_base64"))
        c["has_photo_after"] = bool(p.get("photo_after_base64"))
    # Aggregate stats
    total_spent = sum(float(b.get("estimated_price") or 0) for b in bookings)
    completed = sum(1 for b in bookings if b.get("status") == "completee")
    last_visit = bookings[0].get("date") if bookings else None
    return {
        "email": email_lower,
        "bookings": bookings,
        "contracts": contracts_docs,
        "stats": {
            "total_bookings": len(bookings),
            "total_contracts": len(contracts_docs),
            "total_spent": round(total_spent, 2),
            "completed_services": completed,
            "last_visit": last_visit,
        },
    }


@api_router.delete("/admin/bookings/{booking_id}")
async def admin_delete_booking(booking_id: str, user: dict = Depends(require_admin)):
    """Hard-delete a booking (useful to wipe test data). Related contract stays intact."""
    res = await db.bookings.delete_one({"id": booking_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"ok": True}


class BulkDeletePayload(BaseModel):
    booking_ids: Optional[List[str]] = None
    contract_ids: Optional[List[str]] = None


@api_router.post("/admin/bulk-delete")
async def admin_bulk_delete(payload: BulkDeletePayload, user: dict = Depends(require_admin)):
    """Bulk clean-up endpoint for test data. Deletes multiple bookings/contracts in one call."""
    deleted_bookings = 0
    deleted_contracts = 0
    if payload.booking_ids:
        r = await db.bookings.delete_many({"id": {"$in": payload.booking_ids}})
        deleted_bookings = r.deleted_count
    if payload.contract_ids:
        r = await db.contracts.delete_many({"id": {"$in": payload.contract_ids}})
        deleted_contracts = r.deleted_count
    return {"ok": True, "deleted_bookings": deleted_bookings, "deleted_contracts": deleted_contracts}


# ---------- Stripe Checkout ----------
from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout,
    CheckoutSessionResponse,
    CheckoutStatusResponse,
    CheckoutSessionRequest,
)

STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "")

# Fixed backend-only packages (never accept amounts from frontend)
STRIPE_PACKAGES = {
    "defi_deposit_30": {"amount": 30.0, "currency": "eur",
                        "label_fr": "Défi de la Bande — Acompte", "kind": "deposit"},
}


def _stripe_client(request: Request) -> StripeCheckout:
    if not STRIPE_API_KEY:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    # Build webhook URL from the actual host (behind ingress -> use configured FRONTEND_URL)
    webhook_url = f"{FRONTEND_URL.rstrip('/')}/api/webhook/stripe"
    return StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)


class CheckoutRequestPayload(BaseModel):
    package_id: str
    origin_url: str
    contract_id: Optional[str] = None
    booking_id: Optional[str] = None
    metadata: Optional[dict] = None


@api_router.post("/checkout/session")
async def create_stripe_checkout(
    payload: CheckoutRequestPayload,
    request: Request,
):
    pkg = STRIPE_PACKAGES.get(payload.package_id)
    if not pkg:
        raise HTTPException(status_code=400, detail="Invalid package")
    if not payload.origin_url:
        raise HTTPException(status_code=400, detail="origin_url required")

    origin = payload.origin_url.rstrip("/")
    success_url = f"{origin}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = (
        f"{origin}/defi" if pkg["kind"] == "deposit" else f"{origin}/booking"
    )

    # Build metadata
    meta = {
        "source": "pro-pre",
        "package_id": payload.package_id,
        "kind": pkg["kind"],
    }
    if payload.contract_id:
        meta["contract_id"] = payload.contract_id
    if payload.booking_id:
        meta["booking_id"] = payload.booking_id
    if payload.metadata:
        for k, v in payload.metadata.items():
            meta[str(k)[:40]] = str(v)[:200]

    stripe = _stripe_client(request)
    req = CheckoutSessionRequest(
        amount=float(pkg["amount"]),
        currency=pkg["currency"],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=meta,
    )
    session: CheckoutSessionResponse = await stripe.create_checkout_session(req)

    # Persist a payment_transactions row (initiated)
    now = datetime.now(timezone.utc).isoformat()
    await db.payment_transactions.insert_one({
        "session_id": session.session_id,
        "amount": float(pkg["amount"]),
        "currency": pkg["currency"],
        "package_id": payload.package_id,
        "contract_id": payload.contract_id,
        "booking_id": payload.booking_id,
        "metadata": meta,
        "status": "initiated",
        "payment_status": "unpaid",
        "created_at": now,
        "updated_at": now,
    })

    # Link deposit status on contract if applicable
    if payload.contract_id:
        await db.contracts.update_one(
            {"id": payload.contract_id},
            {"$set": {
                "deposit_choice": "stripe",
                "deposit_status": "pending",
                "stripe_session_id": session.session_id,
            }},
        )

    return {"url": session.url, "session_id": session.session_id}


@api_router.get("/checkout/status/{session_id}")
async def stripe_checkout_status(session_id: str, request: Request):
    stripe = _stripe_client(request)
    tx = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Poll Stripe for current status
    status_resp: CheckoutStatusResponse = await stripe.get_checkout_status(session_id)

    # Idempotent update: only mutate if changed
    now = datetime.now(timezone.utc).isoformat()
    updates = {"updated_at": now, "status": status_resp.status,
               "payment_status": status_resp.payment_status}
    already_finalised = tx.get("payment_status") == "paid"
    if not already_finalised and status_resp.payment_status == "paid":
        # First time we see it paid → finalise related documents
        updates["paid_at"] = now
        if tx.get("contract_id"):
            await db.contracts.update_one(
                {"id": tx["contract_id"]},
                {"$set": {"deposit_status": "paid", "deposit_paid_at": now}},
            )
        if tx.get("booking_id"):
            await db.bookings.update_one(
                {"id": tx["booking_id"]},
                {"$set": {"payment_status": "paid", "payment_paid_at": now}},
            )
    await db.payment_transactions.update_one({"session_id": session_id}, {"$set": updates})

    return {
        "session_id": session_id,
        "status": status_resp.status,
        "payment_status": status_resp.payment_status,
        "amount_total": status_resp.amount_total,
        "currency": status_resp.currency,
        "metadata": status_resp.metadata,
    }


@api_router.get("/admin/backup-download")
async def admin_backup_download(fmt: str = "zip", user: dict = Depends(require_admin)):
    """Serve the latest generated Pro-pre full-source backup archive (admin only).
    Query param `fmt`: `zip` (default) or `tar.gz`.
    """
    import glob
    from fastapi.responses import FileResponse
    ext = "zip" if fmt == "zip" else "tar.gz"
    pattern = f"/app/pro-pre-fullbackup-*.{ext}"
    files = sorted(glob.glob(pattern), reverse=True)
    if not files:
        # Fall back to legacy static-only archive
        files = sorted(glob.glob("/app/pro-pre-backup-*.tar.gz"), reverse=True)
    if not files:
        raise HTTPException(status_code=404, detail="No backup found")
    latest = files[0]
    filename = os.path.basename(latest)
    media = "application/zip" if latest.endswith(".zip") else "application/gzip"
    return FileResponse(latest, media_type=media, filename=filename)


@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    sig = request.headers.get("Stripe-Signature", "")
    stripe = _stripe_client(request)
    try:
        wh = await stripe.handle_webhook(body, sig)
    except Exception as e:
        logger.warning(f"Stripe webhook rejected: {e}")
        raise HTTPException(status_code=400, detail="Invalid webhook")

    now = datetime.now(timezone.utc).isoformat()
    tx = await db.payment_transactions.find_one({"session_id": wh.session_id}, {"_id": 0})
    if not tx:
        return {"received": True, "unknown_session": True}
    if tx.get("payment_status") == "paid":
        return {"received": True, "already_finalised": True}
    updates = {"updated_at": now, "payment_status": wh.payment_status,
               "webhook_event_id": wh.event_id, "webhook_event_type": wh.event_type}
    if wh.payment_status == "paid":
        updates["paid_at"] = now
        if tx.get("contract_id"):
            await db.contracts.update_one(
                {"id": tx["contract_id"]},
                {"$set": {"deposit_status": "paid", "deposit_paid_at": now}},
            )
        if tx.get("booking_id"):
            await db.bookings.update_one(
                {"id": tx["booking_id"]},
                {"$set": {"payment_status": "paid", "payment_paid_at": now}},
            )
    await db.payment_transactions.update_one({"session_id": wh.session_id}, {"$set": updates})
    return {"received": True}


@api_router.delete("/client/my-data")
async def client_delete_my_data(request: Request):
    """GDPR Article 17 — Right to erasure. Client authenticates via magic link cookie
    and deletes ALL personal data: bookings, contracts, photos, sessions.
    Keeps only an anonymised audit log (no PII) for legal compliance."""
    email = await get_current_client(request)
    ts = datetime.now(timezone.utc).isoformat()

    # Count what will be deleted (for audit)
    bookings_n = await db.bookings.count_documents({"email": email})
    contracts_n = await db.contracts.count_documents({"client_email": email})
    photos_n = await db.booking_photos.count_documents({"client_email": email})

    # Delete
    await db.bookings.delete_many({"email": email})
    await db.contracts.delete_many({"client_email": email})
    await db.booking_photos.delete_many({"client_email": email})
    await db.client_sessions.delete_many({"email": email})
    # Detach from users (Google auth) but keep audit row without PII
    await db.users.delete_many({"email": email})
    await db.payment_transactions.delete_many({"metadata.client_email": email})

    # Store anonymous audit log (no PII, only counters + hash)
    import hashlib
    email_hash = hashlib.sha256(email.encode("utf-8")).hexdigest()[:16]
    await db.gdpr_audit.insert_one({
        "email_hash": email_hash,
        "deleted_at": ts,
        "counts": {"bookings": bookings_n, "contracts": contracts_n, "photos": photos_n},
        "action": "right_to_erasure",
    })

    return {
        "ok": True,
        "deleted": {"bookings": bookings_n, "contracts": contracts_n, "photos": photos_n},
        "message": "All personal data has been permanently deleted per GDPR Art. 17.",
    }


# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
