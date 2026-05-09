from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel
from datetime import datetime
import json, os, secrets

router  = APIRouter()
limiter = Limiter(key_func=get_remote_address)
LOG     = os.getenv("ANALYTICS_LOG_PATH", "./analytics.jsonl")
ALLOWED = {"resume_download", "page_view", "project_click", "contact_open"}

security = HTTPBasic()

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    admin_user = os.getenv("ANALYTICS_USER", "")
    admin_pass = os.getenv("ANALYTICS_PASS", "")
    if not admin_user or not admin_pass:
        raise HTTPException(status_code=503, detail="Analytics auth not configured")
    user_ok = secrets.compare_digest(credentials.username, admin_user)
    pass_ok = secrets.compare_digest(credentials.password, admin_pass)
    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )

class Event(BaseModel):
    event: str
    meta:  dict = {}

def append(rec):
    with open(LOG, "a") as f:
        f.write(json.dumps(rec) + "\n")

def read_all():
    if not os.path.exists(LOG): return []
    with open(LOG) as f:
        return [json.loads(l) for l in f if l.strip()]

@router.post("/track")
@limiter.limit("30/minute")
async def track(request: Request, payload: Event):
    if payload.event not in ALLOWED:
        raise HTTPException(400, f"Unknown event: {payload.event}")
    append({"event": payload.event, "meta": payload.meta,
            "timestamp": datetime.utcnow().isoformat(),
            "ip": request.client.host})
    return {"tracked": True}

@router.get("/summary")
async def summary(credentials: HTTPBasicCredentials = Depends(verify_admin)):
    events = read_all()
    by_type: dict[str, int] = {}
    for e in events:
        by_type[e["event"]] = by_type.get(e["event"], 0) + 1
    downloads = [e for e in events if e["event"] == "resume_download"]
    return {"total": len(events), "by_type": by_type,
            "resume_downloads": len(downloads),
            "last_download": downloads[-1]["timestamp"] if downloads else None}
