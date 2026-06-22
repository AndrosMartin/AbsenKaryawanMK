from dotenv import load_dotenv
from pathlib import Path
import os

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Query
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from pydantic import BaseModel, Field, EmailStr, ConfigDict, BeforeValidator
from typing import List, Optional, Annotated, Any
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import logging
import math
import uuid
import bcrypt
import jwt
import secrets

# ----------------------------------------------------------------------------
# Setup
# ----------------------------------------------------------------------------
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_SECRET = os.environ['JWT_SECRET']
JWT_ALGORITHM = "HS256"
TZ = ZoneInfo("Asia/Jakarta")
WORK_START = os.environ.get("WORK_START", "09:00")
FACE_MATCH_THRESHOLD = 0.55

MONITOR_ROLES = {"owner", "direksi", "manager", "hrd"}
MANAGE_ROLES = {"owner", "direksi"}        # dapat menerapkan perubahan langsung
HR_ROLES = {"owner", "direksi", "hrd"}     # dapat mengajukan CRUD karyawan
APPROVER_ROLES = {"owner", "direksi"}      # dapat menyetujui/menolak permintaan HRD
VALID_ROLES = {"owner", "direksi", "manager", "hrd", "staff"}
HRD_ASSIGNABLE_ROLES = {"manager", "hrd", "staff"}  # role yang boleh diatur HRD

app = FastAPI(title="AbsensiPro API")
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("absensipro")

PyObjectId = Annotated[str, BeforeValidator(str)]


# ----------------------------------------------------------------------------
# Auth helpers
# ----------------------------------------------------------------------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "sub": user_id, "email": email, "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_roles(roles: set):
    async def checker(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Akses ditolak untuk role Anda")
        return user
    return checker


def public_user(u: dict) -> dict:
    return {
        "id": str(u["_id"]),
        "email": u["email"],
        "name": u.get("name"),
        "role": u.get("role"),
        "department": u.get("department"),
        "position": u.get("position"),
        "employee_id": u.get("employee_id"),
        "phone": u.get("phone"),
        "face_enrolled": bool(u.get("face_descriptor")),
        "created_at": u.get("created_at"),
    }


# ----------------------------------------------------------------------------
# Utilities
# ----------------------------------------------------------------------------
def haversine_m(lat1, lon1, lat2, lon2) -> float:
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def euclidean(a: List[float], b: List[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def today_str() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%d")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def compute_status(check_in_dt: datetime) -> str:
    local = check_in_dt.astimezone(TZ)
    hh, mm = map(int, WORK_START.split(":"))
    limit = local.replace(hour=hh, minute=mm, second=0, microsecond=0)
    return "late" if local > limit else "present"


# ----------------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------------
class RegisterBody(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "staff"
    department: Optional[str] = "Umum"
    position: Optional[str] = "Staff"
    phone: Optional[str] = None


class LoginBody(BaseModel):
    email: EmailStr
    password: str


class EmployeeBody(BaseModel):
    name: str
    email: EmailStr
    password: str = "password123"
    role: str = "staff"
    department: Optional[str] = "Umum"
    position: Optional[str] = "Staff"
    phone: Optional[str] = None


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None


class FaceEnrollBody(BaseModel):
    descriptor: List[float]


class OfficeBody(BaseModel):
    name: str
    lat: float
    lng: float
    radius_m: int = 200


class CheckInBody(BaseModel):
    method: str  # "face" | "qr"
    lat: float
    lng: float
    descriptor: Optional[List[float]] = None
    qr_code: Optional[str] = None


class CheckOutBody(BaseModel):
    lat: Optional[float] = None
    lng: Optional[float] = None


class RejectBody(BaseModel):
    reason: Optional[str] = None


# ----------------------------------------------------------------------------
# Auth routes
# ----------------------------------------------------------------------------
@api_router.post("/auth/register")
async def register(body: RegisterBody):
    email = body.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email sudah terdaftar")
    count = await db.users.count_documents({})
    doc = {
        "name": body.name, "email": email,
        "password_hash": hash_password(body.password),
        "role": body.role if body.role in VALID_ROLES else "staff",
        "department": body.department, "position": body.position,
        "phone": body.phone,
        "employee_id": f"EMP-{count + 1:04d}",
        "face_descriptor": None,
        "created_at": now_iso(),
    }
    res = await db.users.insert_one(doc)
    doc["_id"] = res.inserted_id
    token = create_access_token(str(res.inserted_id), email, doc["role"])
    return {"token": token, "user": public_user(doc)}


@api_router.post("/auth/login")
async def login(body: LoginBody):
    email = body.email.lower()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email atau password salah")
    token = create_access_token(str(user["_id"]), email, user["role"])
    return {"token": token, "user": public_user(user)}


@api_router.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return public_user(user)


# ----------------------------------------------------------------------------
# Face enrollment
# ----------------------------------------------------------------------------
@api_router.post("/face/enroll")
async def enroll_face(body: FaceEnrollBody, user: dict = Depends(get_current_user)):
    if len(body.descriptor) != 128:
        raise HTTPException(status_code=400, detail="Descriptor wajah tidak valid")
    await db.users.update_one({"_id": user["_id"]},
                              {"$set": {"face_descriptor": body.descriptor}})
    return {"ok": True, "message": "Wajah berhasil didaftarkan"}


# ----------------------------------------------------------------------------
# Offices
# ----------------------------------------------------------------------------
@api_router.get("/offices")
async def list_offices(user: dict = Depends(get_current_user)):
    offices = await db.offices.find().to_list(100)
    return [{"id": str(o["_id"]), "name": o["name"], "lat": o["lat"],
             "lng": o["lng"], "radius_m": o["radius_m"], "qr_code": o["qr_code"]}
            for o in offices]


@api_router.post("/offices")
async def create_office(body: OfficeBody, user: dict = Depends(require_roles(MANAGE_ROLES))):
    doc = body.model_dump()
    doc["qr_code"] = f"OFFICE-{uuid.uuid4().hex[:10].upper()}"
    res = await db.offices.insert_one(doc)
    doc["_id"] = res.inserted_id
    return {"id": str(res.inserted_id), **{k: doc[k] for k in ("name", "lat", "lng", "radius_m", "qr_code")}}


@api_router.put("/offices/{office_id}")
async def update_office(office_id: str, body: OfficeBody, user: dict = Depends(require_roles(MANAGE_ROLES))):
    await db.offices.update_one({"_id": ObjectId(office_id)}, {"$set": body.model_dump()})
    return {"ok": True}


@api_router.delete("/offices/{office_id}")
async def delete_office(office_id: str, user: dict = Depends(require_roles(MANAGE_ROLES))):
    await db.offices.delete_one({"_id": ObjectId(office_id)})
    return {"ok": True}


async def validate_geofence(lat: float, lng: float):
    offices = await db.offices.find().to_list(100)
    if not offices:
        raise HTTPException(status_code=400, detail="Belum ada lokasi kantor yang dikonfigurasi")
    best = None
    for o in offices:
        d = haversine_m(lat, lng, o["lat"], o["lng"])
        if best is None or d < best[1]:
            best = (o, d)
    office, dist = best
    within = dist <= office["radius_m"]
    return office, dist, within


def verify_attendance_identity(user: dict, body: "CheckInBody", office: dict) -> None:
    """Raise HTTPException if the chosen verification method fails."""
    if body.method == "face":
        stored = user.get("face_descriptor")
        if not stored:
            raise HTTPException(status_code=400, detail="Wajah belum didaftarkan. Daftarkan wajah Anda dulu.")
        if not body.descriptor or len(body.descriptor) != 128:
            raise HTTPException(status_code=400, detail="Data wajah tidak terbaca, coba lagi")
        if euclidean(stored, body.descriptor) > FACE_MATCH_THRESHOLD:
            raise HTTPException(status_code=400, detail="Wajah tidak cocok dengan data terdaftar")
    elif body.method == "qr":
        if not body.qr_code or body.qr_code != office["qr_code"]:
            raise HTTPException(status_code=400, detail="QR Code tidak valid untuk lokasi ini")
    else:
        raise HTTPException(status_code=400, detail="Metode absensi tidak dikenal")


# ----------------------------------------------------------------------------
# Attendance
# ----------------------------------------------------------------------------
def att_public(a: dict, user: Optional[dict] = None) -> dict:
    out = {
        "id": str(a["_id"]),
        "user_id": a["user_id"],
        "date": a["date"],
        "check_in": a.get("check_in"),
        "check_out": a.get("check_out"),
        "status": a.get("status"),
        "method": a.get("method"),
        "office_name": a.get("office_name"),
        "distance_m": a.get("distance_m"),
        "within_geofence": a.get("within_geofence"),
    }
    if user:
        out.update({"name": user.get("name"), "department": user.get("department"),
                    "position": user.get("position"), "employee_id": user.get("employee_id"),
                    "role": user.get("role")})
    return out


@api_router.post("/attendance/check-in")
async def check_in(body: CheckInBody, user: dict = Depends(get_current_user)):
    date = today_str()
    existing = await db.attendance.find_one({"user_id": str(user["_id"]), "date": date})
    if existing and existing.get("check_in"):
        raise HTTPException(status_code=400, detail="Anda sudah melakukan check-in hari ini")

    office, dist, within = await validate_geofence(body.lat, body.lng)
    if not within:
        raise HTTPException(status_code=400,
                            detail=f"Anda berada {int(dist)}m dari {office['name']} (radius {office['radius_m']}m). Mendekatlah ke kantor.")

    verify_attendance_identity(user, body, office)

    check_in_dt = datetime.now(timezone.utc)
    status = compute_status(check_in_dt)
    doc = {
        "user_id": str(user["_id"]),
        "date": date,
        "check_in": check_in_dt.isoformat(),
        "check_out": None,
        "status": status,
        "method": body.method,
        "office_name": office["name"],
        "distance_m": int(dist),
        "within_geofence": True,
        "lat": body.lat, "lng": body.lng,
    }
    await db.attendance.insert_one(doc)
    doc["_id"] = "tmp"
    return att_public(doc, user)


@api_router.post("/attendance/check-out")
async def check_out(body: CheckOutBody, user: dict = Depends(get_current_user)):
    date = today_str()
    rec = await db.attendance.find_one({"user_id": str(user["_id"]), "date": date})
    if not rec or not rec.get("check_in"):
        raise HTTPException(status_code=400, detail="Anda belum check-in hari ini")
    if rec.get("check_out"):
        raise HTTPException(status_code=400, detail="Anda sudah check-out hari ini")
    await db.attendance.update_one({"_id": rec["_id"]},
                                   {"$set": {"check_out": now_iso()}})
    rec["check_out"] = now_iso()
    return att_public(rec, user)


@api_router.get("/attendance/today")
async def attendance_today(user: dict = Depends(get_current_user)):
    rec = await db.attendance.find_one({"user_id": str(user["_id"]), "date": today_str()})
    if not rec:
        return {"checked_in": False}
    return {"checked_in": True, **att_public(rec, user)}


@api_router.get("/attendance/me")
async def my_attendance(user: dict = Depends(get_current_user), limit: int = 60):
    recs = await db.attendance.find({"user_id": str(user["_id"])}).sort("date", -1).to_list(limit)
    return [att_public(r, user) for r in recs]


@api_router.get("/attendance")
async def all_attendance(date: Optional[str] = Query(None),
                         user: dict = Depends(require_roles(MONITOR_ROLES))):
    date = date or today_str()
    users = await db.users.find().to_list(1000)
    recs = await db.attendance.find({"date": date}).to_list(2000)
    rec_by_user = {r["user_id"]: r for r in recs}
    rows = []
    for u in users:
        uid = str(u["_id"])
        r = rec_by_user.get(uid)
        if r:
            rows.append(att_public(r, u))
        else:
            rows.append({"id": None, "user_id": uid, "date": date, "check_in": None,
                         "check_out": None, "status": "absent", "method": None,
                         "office_name": None, "distance_m": None, "within_geofence": None,
                         "name": u.get("name"), "department": u.get("department"),
                         "position": u.get("position"), "employee_id": u.get("employee_id"),
                         "role": u.get("role")})
    return rows


# ----------------------------------------------------------------------------
# Dashboard stats
# ----------------------------------------------------------------------------
def _summarize_today(users: list, rec_by_user: dict) -> dict:
    present = late = 0
    dept_map = {}
    for u in users:
        r = rec_by_user.get(str(u["_id"]))
        st = r["status"] if r else "absent"
        if st == "present":
            present += 1
        elif st == "late":
            late += 1
        dept = u.get("department") or "Umum"
        dept_map.setdefault(dept, {"department": dept, "total": 0, "hadir": 0})
        dept_map[dept]["total"] += 1
        if st in ("present", "late"):
            dept_map[dept]["hadir"] += 1
    return {"present": present, "late": late, "departments": list(dept_map.values())}


async def _seven_day_trend() -> list:
    trend = []
    for i in range(6, -1, -1):
        day = datetime.now(TZ) - timedelta(days=i)
        date = day.strftime("%Y-%m-%d")
        day_recs = await db.attendance.find({"date": date}).to_list(2000)
        p = sum(1 for r in day_recs if r.get("status") == "present")
        l = sum(1 for r in day_recs if r.get("status") == "late")
        trend.append({"date": date, "label": day.strftime("%a"), "present": p, "late": l, "total": p + l})
    return trend


def _recent_activity(recs: list, users: list) -> list:
    recent = sorted([r for r in recs if r.get("check_in")],
                    key=lambda r: r["check_in"], reverse=True)[:8]
    user_by_id = {str(u["_id"]): u for u in users}
    return [att_public(r, user_by_id.get(r["user_id"])) for r in recent]


@api_router.get("/dashboard/stats")
async def dashboard_stats(user: dict = Depends(require_roles(MONITOR_ROLES))):
    date = today_str()
    users = await db.users.find().to_list(1000)
    total = len(users)
    recs = await db.attendance.find({"date": date}).to_list(2000)
    rec_by_user = {r["user_id"]: r for r in recs}

    summary = _summarize_today(users, rec_by_user)
    present, late = summary["present"], summary["late"]
    absent = total - present - late

    return {
        "date": date,
        "total": total, "present": present, "late": late, "absent": absent,
        "attendance_rate": round((present + late) / total * 100, 1) if total else 0,
        "departments": summary["departments"],
        "trend": await _seven_day_trend(),
        "recent": _recent_activity(recs, users),
    }


# ----------------------------------------------------------------------------
# Employees (management) — with HRD approval workflow
# ----------------------------------------------------------------------------
def req_public(r: dict) -> dict:
    payload = r.get("payload")
    if isinstance(payload, dict):
        payload = {k: v for k, v in payload.items() if k != "password_hash"}
    return {
        "id": str(r["_id"]),
        "action": r["action"],
        "summary": r.get("summary"),
        "status": r["status"],
        "target_emp_id": r.get("target_emp_id"),
        "payload": payload,
        "requested_by_name": r.get("requested_by_name"),
        "created_at": r.get("created_at"),
        "reviewed_by_name": r.get("reviewed_by_name"),
        "reviewed_at": r.get("reviewed_at"),
        "reject_reason": r.get("reject_reason"),
    }


async def _apply_create_employee(payload: dict) -> dict:
    if await db.users.find_one({"email": payload["email"]}):
        raise HTTPException(status_code=400, detail="Email sudah terdaftar")
    count = await db.users.count_documents({})
    doc = {
        "name": payload["name"], "email": payload["email"],
        "password_hash": payload["password_hash"],
        "role": payload["role"], "department": payload.get("department"),
        "position": payload.get("position"), "phone": payload.get("phone"),
        "employee_id": f"EMP-{count + 1:04d}", "face_descriptor": None,
        "created_at": now_iso(),
    }
    res = await db.users.insert_one(doc)
    doc["_id"] = res.inserted_id
    return public_user(doc)


async def _apply_update_employee(emp_id: str, update: dict) -> dict:
    if update:
        await db.users.update_one({"_id": ObjectId(emp_id)}, {"$set": update})
    u = await db.users.find_one({"_id": ObjectId(emp_id)})
    return public_user(u)


async def _apply_delete_employee(emp_id: str) -> None:
    await db.users.delete_one({"_id": ObjectId(emp_id)})
    await db.attendance.delete_many({"user_id": emp_id})


async def _create_request(action: str, requester: dict, summary: str,
                          payload: Optional[dict] = None, target_emp_id: Optional[str] = None) -> dict:
    doc = {
        "action": action, "payload": payload, "target_emp_id": target_emp_id,
        "summary": summary, "status": "pending",
        "requested_by": str(requester["_id"]), "requested_by_name": requester.get("name"),
        "created_at": now_iso(),
        "reviewed_by": None, "reviewed_by_name": None, "reviewed_at": None, "reject_reason": None,
    }
    res = await db.employee_requests.insert_one(doc)
    doc["_id"] = res.inserted_id
    out = req_public(doc)
    out["pending"] = True
    return out


def _guard_hrd_role(requester: dict, role: Optional[str]):
    """HRD tidak boleh menetapkan/ mengubah seseorang menjadi owner/direksi."""
    if requester["role"] == "hrd" and role is not None and role not in HRD_ASSIGNABLE_ROLES:
        raise HTTPException(status_code=403, detail="HRD tidak dapat menetapkan role Owner/Direksi")


@api_router.get("/employees")
async def list_employees(user: dict = Depends(require_roles(MONITOR_ROLES))):
    users = await db.users.find().sort("created_at", 1).to_list(1000)
    return [public_user(u) for u in users]


@api_router.post("/employees")
async def create_employee(body: EmployeeBody, user: dict = Depends(require_roles(HR_ROLES))):
    email = body.email.lower()
    role = body.role if body.role in VALID_ROLES else "staff"
    _guard_hrd_role(user, role)
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email sudah terdaftar")
    payload = {
        "name": body.name, "email": email, "password_hash": hash_password(body.password),
        "role": role, "department": body.department, "position": body.position, "phone": body.phone,
    }
    if user["role"] in APPROVER_ROLES:
        return await _apply_create_employee(payload)
    return await _create_request("create", user, payload=payload,
                                 summary=f"Tambah karyawan: {body.name} ({email}) — role {role}")


@api_router.put("/employees/{emp_id}")
async def update_employee(emp_id: str, body: EmployeeUpdate, user: dict = Depends(require_roles(HR_ROLES))):
    _guard_hrd_role(user, body.role)
    target = await db.users.find_one({"_id": ObjectId(emp_id)})
    if not target:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")
    if user["role"] == "hrd" and target.get("role") in {"owner", "direksi"}:
        raise HTTPException(status_code=403, detail="HRD tidak dapat mengubah data Owner/Direksi")
    update = {k: v for k, v in body.model_dump().items() if v is not None}
    if "password" in update:
        update["password_hash"] = hash_password(update.pop("password"))
    if user["role"] in APPROVER_ROLES:
        return await _apply_update_employee(emp_id, update)
    return await _create_request("update", user, payload=update, target_emp_id=emp_id,
                                 summary=f"Ubah data karyawan: {target.get('name')}")


@api_router.delete("/employees/{emp_id}")
async def delete_employee(emp_id: str, user: dict = Depends(require_roles(HR_ROLES))):
    if str(user["_id"]) == emp_id:
        raise HTTPException(status_code=400, detail="Tidak dapat menghapus akun sendiri")
    target = await db.users.find_one({"_id": ObjectId(emp_id)})
    if not target:
        raise HTTPException(status_code=404, detail="Karyawan tidak ditemukan")
    if user["role"] == "hrd" and target.get("role") in {"owner", "direksi"}:
        raise HTTPException(status_code=403, detail="HRD tidak dapat menghapus Owner/Direksi")
    if user["role"] in APPROVER_ROLES:
        await _apply_delete_employee(emp_id)
        return {"ok": True}
    return await _create_request("delete", user, target_emp_id=emp_id,
                                 summary=f"Hapus karyawan: {target.get('name')}")


# ----------------------------------------------------------------------------
# Employee change requests (HRD -> Direksi approval)
# ----------------------------------------------------------------------------
@api_router.get("/employee-requests")
async def list_employee_requests(status: Optional[str] = Query(None),
                                 user: dict = Depends(require_roles(HR_ROLES))):
    q = {}
    if status:
        q["status"] = status
    if user["role"] not in APPROVER_ROLES:
        q["requested_by"] = str(user["_id"])  # HRD hanya melihat permintaannya sendiri
    reqs = await db.employee_requests.find(q).sort("created_at", -1).to_list(500)
    return [req_public(r) for r in reqs]


@api_router.get("/employee-requests/pending-count")
async def pending_count(user: dict = Depends(require_roles(APPROVER_ROLES))):
    n = await db.employee_requests.count_documents({"status": "pending"})
    return {"count": n}


@api_router.post("/employee-requests/{req_id}/approve")
async def approve_request(req_id: str, user: dict = Depends(require_roles(APPROVER_ROLES))):
    req = await db.employee_requests.find_one({"_id": ObjectId(req_id)})
    if not req:
        raise HTTPException(status_code=404, detail="Permintaan tidak ditemukan")
    if req["status"] != "pending":
        raise HTTPException(status_code=400, detail="Permintaan sudah diproses")
    action = req["action"]
    result = None
    if action == "create":
        result = await _apply_create_employee(req["payload"])
    elif action == "update":
        result = await _apply_update_employee(req["target_emp_id"], req.get("payload") or {})
    elif action == "delete":
        await _apply_delete_employee(req["target_emp_id"])
    await db.employee_requests.update_one({"_id": req["_id"]}, {"$set": {
        "status": "approved", "reviewed_by": str(user["_id"]),
        "reviewed_by_name": user.get("name"), "reviewed_at": now_iso()}})
    return {"ok": True, "result": result}


@api_router.post("/employee-requests/{req_id}/reject")
async def reject_request(req_id: str, body: RejectBody, user: dict = Depends(require_roles(APPROVER_ROLES))):
    req = await db.employee_requests.find_one({"_id": ObjectId(req_id)})
    if not req:
        raise HTTPException(status_code=404, detail="Permintaan tidak ditemukan")
    if req["status"] != "pending":
        raise HTTPException(status_code=400, detail="Permintaan sudah diproses")
    await db.employee_requests.update_one({"_id": req["_id"]}, {"$set": {
        "status": "rejected", "reviewed_by": str(user["_id"]),
        "reviewed_by_name": user.get("name"), "reviewed_at": now_iso(),
        "reject_reason": body.reason or "Ditolak"}})
    return {"ok": True}


# ----------------------------------------------------------------------------
# Notifications (role-aware)
# ----------------------------------------------------------------------------
_ACTION_LABEL = {"create": "Tambah karyawan", "update": "Ubah data karyawan", "delete": "Hapus karyawan"}


@api_router.get("/notifications")
async def notifications(user: dict = Depends(get_current_user)):
    role = user.get("role")
    items = []
    if role in APPROVER_ROLES:
        reqs = await db.employee_requests.find({"status": "pending"}).sort("created_at", -1).to_list(50)
        for r in reqs:
            items.append({
                "id": str(r["_id"]), "type": "pending",
                "title": f"Permintaan: {_ACTION_LABEL.get(r['action'], r['action'])}",
                "body": r.get("summary"), "by": r.get("requested_by_name"),
                "created_at": r.get("created_at"),
            })
    elif role == "hrd":
        reqs = await db.employee_requests.find(
            {"requested_by": str(user["_id"]), "status": {"$in": ["approved", "rejected"]}}
        ).sort("reviewed_at", -1).to_list(50)
        for r in reqs:
            items.append({
                "id": str(r["_id"]), "type": r["status"],
                "title": "Permintaan disetujui" if r["status"] == "approved" else "Permintaan ditolak",
                "body": r.get("summary"), "by": r.get("reviewed_by_name"),
                "created_at": r.get("reviewed_at"),
            })
    return {"items": items, "count": len(items)}


# ----------------------------------------------------------------------------
# App wiring + seed
# ----------------------------------------------------------------------------
app.include_router(api_router)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=False,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


DEMO_USERS = [
    {"name": "Budi Santoso", "email": None, "role": "owner",
     "department": "Direksi", "position": "Owner / CEO"},
    {"name": "Siti Rahmawati", "email": "direksi@company.com", "role": "direksi",
     "department": "Direksi", "position": "Direktur Operasional"},
    {"name": "Agus Wijaya", "email": "manager@company.com", "role": "manager",
     "department": "Penjualan", "position": "Manager Penjualan"},
    {"name": "Maya Anggraini", "email": "hrd@company.com", "role": "hrd",
     "department": "HRD", "position": "Manager HRD"},
    {"name": "Dewi Lestari", "email": "dewi@company.com", "role": "staff",
     "department": "Penjualan", "position": "Sales Executive"},
    {"name": "Rizki Pratama", "email": "rizki@company.com", "role": "staff",
     "department": "Keuangan", "position": "Staff Keuangan"},
    {"name": "Nina Putri", "email": "nina@company.com", "role": "staff",
     "department": "HRD", "position": "Staff HRD"},
    {"name": "Eko Saputra", "email": "eko@company.com", "role": "staff",
     "department": "Operasional", "position": "Teknisi"},
]

TEST_CREDENTIALS_DOC = """# Test Credentials

All demo accounts use password: **password123**

| Role | Email | Password |
|------|-------|----------|
| Owner | owner@company.com | password123 |
| Direksi | direksi@company.com | password123 |
| Manager | manager@company.com | password123 |
| HRD | hrd@company.com | password123 |
| Staff | dewi@company.com | password123 |
| Staff | rizki@company.com | password123 |
| Staff | nina@company.com | password123 |
| Staff | eko@company.com | password123 |

## Auth endpoints
- POST /api/auth/login  body {email, password} -> {token, user}
- POST /api/auth/register
- GET  /api/auth/me  (Bearer token)

## Notes
- Frontend stores token in localStorage and sends `Authorization: Bearer <token>`.
- Monitoring (dashboard/employees/all-attendance): roles owner, direksi, manager, hrd.
- Direct management (apply employees & offices): roles owner, direksi.
- HRD can request employee create/update/delete (cannot touch owner/direksi roles); requests need owner/direksi approval via /api/employee-requests/{id}/approve.
- Default office: "Kantor Pusat Jakarta" lat -6.208763 lng 106.845599 radius 250m, QR: OFFICE-HQJKT00001
"""


async def _ensure_indexes():
    await db.users.create_index("email", unique=True)
    await db.attendance.create_index([("user_id", 1), ("date", 1)])


async def _seed_users(admin_email: str, admin_password: str):
    for i, d in enumerate(DEMO_USERS):
        email = admin_email if d["email"] is None else d["email"]
        pwd = admin_password if email == admin_email else "password123"
        existing = await db.users.find_one({"email": email})
        if existing is None:
            await db.users.insert_one({
                **{k: v for k, v in d.items() if k != "email"}, "email": email,
                "password_hash": hash_password(pwd),
                "phone": None, "employee_id": f"EMP-{i + 1:04d}",
                "face_descriptor": None, "created_at": now_iso(),
            })
        elif not verify_password(pwd, existing["password_hash"]):
            await db.users.update_one({"email": email},
                                      {"$set": {"password_hash": hash_password(pwd)}})


async def _seed_office():
    if await db.offices.count_documents({}) == 0:
        await db.offices.insert_one({
            "name": "Kantor Pusat Jakarta", "lat": -6.208763, "lng": 106.845599,
            "radius_m": 250, "qr_code": "OFFICE-HQJKT00001",
        })


def _rand_below(n: int) -> int:
    return secrets.randbelow(n)


async def _seed_attendance_history():
    """Populate the last 7 days of demo attendance for charts (uses `secrets`)."""
    if await db.attendance.count_documents({}) != 0:
        return
    users = await db.users.find({"role": {"$in": ["manager", "staff", "direksi"]}}).to_list(100)
    for i in range(7, 0, -1):
        day = datetime.now(TZ) - timedelta(days=i)
        date = day.strftime("%Y-%m-%d")
        for u in users:
            if _rand_below(100) < 12:
                continue  # absent
            late = _rand_below(100) < 20
            hour = 9 if late else 8
            minute = (5 + _rand_below(36)) if late else _rand_below(56)
            ci = day.replace(hour=hour, minute=minute, second=0, microsecond=0).astimezone(timezone.utc)
            co = day.replace(hour=17, minute=_rand_below(60), second=0, microsecond=0).astimezone(timezone.utc)
            await db.attendance.insert_one({
                "user_id": str(u["_id"]), "date": date,
                "check_in": ci.isoformat(), "check_out": co.isoformat(),
                "status": "late" if late else "present",
                "method": secrets.choice(["face", "qr"]),
                "office_name": "Kantor Pusat Jakarta", "distance_m": 5 + _rand_below(116),
                "within_geofence": True, "lat": -6.2087, "lng": 106.8456,
            })


def _write_test_credentials():
    try:
        Path("/app/memory/test_credentials.md").write_text(TEST_CREDENTIALS_DOC)
    except Exception as e:
        logger.warning(f"could not write creds: {e}")


async def seed():
    await _ensure_indexes()
    await _seed_users(os.environ["ADMIN_EMAIL"], os.environ["ADMIN_PASSWORD"])
    await _seed_office()
    await _seed_attendance_history()
    logger.info("Seed complete.")
    _write_test_credentials()


@app.on_event("startup")
async def on_startup():
    await seed()


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
