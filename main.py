import os
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from datetime import datetime

from database import create_document, get_documents, db
from schemas import Lead, DemoRequest, Tenant, Event

app = FastAPI(title="DBaaS Marketing API", description="Leads, demo requests, and demo tenant preview")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "DBaaS Marketing API running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = getattr(db, 'name', None) or ("✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set")
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:120]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:120]}"
    return response

# ----- API models for responses -----
class LeadResponse(BaseModel):
    ok: bool
    id: Optional[str] = None

class DemoResponse(BaseModel):
    ok: bool
    id: Optional[str] = None

class DemoTenantPreview(BaseModel):
    tenant: Tenant
    metrics: Dict[str, Any]
    recent_queries: List[Dict[str, Any]]

# ----- Endpoints -----
@app.post("/api/leads", response_model=LeadResponse)
def create_lead(payload: Lead):
    try:
        inserted_id = create_document("lead", payload)
        # also log an event
        try:
            create_document("event", Event(type="lead_created", metadata={"email": payload.email}).dict())
        except Exception:
            pass
        return {"ok": True, "id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/demos", response_model=DemoResponse)
def create_demo_request(payload: DemoRequest):
    try:
        inserted_id = create_document("demorequest", payload)
        try:
            create_document("event", Event(type="demo_requested", metadata={"email": payload.email}).dict())
        except Exception:
            pass
        return {"ok": True, "id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tenant/demo", response_model=DemoTenantPreview)
def get_demo_tenant():
    # a lightweight, non-sensitive mock of a demo tenant for the playground UI
    tenant = Tenant(
        name="Acme Analytics",
        slug="acme-analytics",
        plan="pro",
        regions=["us-east-1", "eu-west-1"],
        backups_enabled=True,
        created_by="demo@acme.co",
    )
    metrics = {
        "qps": 842,
        "storage_gb": 128.6,
        "avg_latency_ms": 6.4,
        "uptime_pct": 99.991,
        "backups": [
            {"at": datetime.utcnow().isoformat() + "Z", "status": "ok"},
            {"at": "2025-11-16T03:00:00Z", "status": "ok"},
        ],
    }
    recent_queries = [
        {"id": 1, "sql": "SELECT * FROM users LIMIT 5;", "latency_ms": 3.2, "rows": 5},
        {"id": 2, "sql": "SELECT country, COUNT(*) FROM orders GROUP BY 1;", "latency_ms": 7.9, "rows": 42},
        {"id": 3, "sql": "EXPLAIN SELECT * FROM events WHERE ts > now()-interval '1 day';", "latency_ms": 5.1, "rows": 0},
    ]
    return {"tenant": tenant, "metrics": metrics, "recent_queries": recent_queries}

@app.get("/schema")
def get_schema_definitions():
    # Minimal schema exposure for tooling
    return {
        "lead": Lead.model_json_schema(),
        "demorequest": DemoRequest.model_json_schema(),
        "tenant": Tenant.model_json_schema(),
        "event": Event.model_json_schema(),
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
