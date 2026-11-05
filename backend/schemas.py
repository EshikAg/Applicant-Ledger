from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

# Skill schema
class SkillBase(BaseModel):
    skill_name: str
    skill_type: Optional[str] = "technical"

class SkillResponse(SkillBase):
    id: int
    class Config:
        from_attributes = True

# Core Applicant schema matching exact requirements
class ApplicantBase(BaseModel):
    applicant: str # Candidate Name
    designation: Optional[str] = None
    department: Optional[str] = None # Front office, Kitchen, Service, Account, Maintenance, Sales, Admin, Housekeeping, Stores, Purchase, Others
    email: Optional[str] = None
    contact_no: Optional[str] = None
    dob: Optional[str] = None
    city: Optional[str] = None
    status: Optional[str] = "New Application"
    remarks: Optional[str] = None

class ApplicantCreate(ApplicantBase):
    resume_filename: Optional[str] = None
    resume_file_path: Optional[str] = None
    resume_hash: Optional[str] = None
    skills_list: Optional[List[str]] = []

class ApplicantUpdate(BaseModel):
    applicant: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    email: Optional[str] = None
    contact_no: Optional[str] = None
    dob: Optional[str] = None
    city: Optional[str] = None
    status: Optional[str] = None
    remarks: Optional[str] = None
    skills_list: Optional[List[str]] = None

class ApplicantResponse(ApplicantBase):
    id: int
    applicant_id: str # A001, A002...
    resume_filename: Optional[str] = None
    resume_file_path: Optional[str] = None
    resume_hash: Optional[str] = None
    uploaded_at: datetime
    updated_at: Optional[datetime] = None
    skills: List[SkillResponse] = []

    class Config:
        from_attributes = True

class StatusUpdatePayload(BaseModel):
    status: str

class BulkStatusPayload(BaseModel):
    applicant_ids: List[int]
    status: str

class BulkDeletePayload(BaseModel):
    applicant_ids: List[int]

# Processing Logs
class ProcessingLogResponse(BaseModel):
    id: int
    resume_filename: str
    file_hash: Optional[str] = None
    file_size_bytes: int
    status: str
    extracted_applicant_id: Optional[int] = None
    error_message: Optional[str] = None
    duration_ms: int
    created_at: datetime

    class Config:
        from_attributes = True

# Dashboard & Analytics
class DashboardStats(BaseModel):
    total_applicants: int
    new_applicants: int
    under_review: int
    shortlisted: int
    interview_scheduled: int
    selected: int
    rejected: int
    on_hold: int

class ChartItem(BaseModel):
    name: str
    value: int
    color: Optional[str] = None

class TimelineItem(BaseModel):
    date: str
    count: int

class AnalyticsCharts(BaseModel):
    status_distribution: List[ChartItem]
    department_distribution: List[ChartItem]
    top_skills: List[ChartItem]
    timeline: List[TimelineItem]

# Auth Schemas
class LoginRequest(BaseModel):
    username_or_email: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
