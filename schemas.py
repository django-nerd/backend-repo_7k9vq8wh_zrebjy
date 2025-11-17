"""
Database Schemas for Product signups and demo requests

Each Pydantic model maps to a MongoDB collection using the lowercase class name.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

class Lead(BaseModel):
    """Marketing leads captured from signup or newsletter forms.
    Collection: lead
    """
    email: EmailStr = Field(..., description="Email address")
    name: Optional[str] = Field(None, description="Full name")
    company: Optional[str] = Field(None, description="Company name")
    role: Optional[str] = Field(None, description="Job role")
    source: str = Field("website", description="Acquisition source, e.g., website, demo, pricing")
    consent: bool = Field(True, description="User consent for contact")

class DemoRequest(BaseModel):
    """Requests to book a demo.
    Collection: demorequest
    """
    email: EmailStr
    name: Optional[str] = None
    company: Optional[str] = None
    team_size: Optional[int] = Field(None, ge=1, le=5000)
    use_case: Optional[str] = None
    message: Optional[str] = None

class Tenant(BaseModel):
    """A demo tenant representation (preview only).
    Collection: tenant
    """
    name: str
    slug: str
    plan: str = Field("starter", description="starter|pro|enterprise")
    regions: List[str] = Field(default_factory=lambda: ["us-east-1"]) 
    backups_enabled: bool = True
    created_by: Optional[EmailStr] = None

class Event(BaseModel):
    """Generic event log for marketing interactions.
    Collection: event
    """
    type: str = Field(..., description="event name, e.g., signup_submitted")
    metadata: Optional[dict] = Field(default_factory=dict)
    at: datetime = Field(default_factory=datetime.utcnow)
