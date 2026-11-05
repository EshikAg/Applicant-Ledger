from datetime import datetime
from typing import Dict, List, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from ..database import get_db
from ..models import Applicant, ApplicantSkill
from ..schemas import DashboardStats, AnalyticsCharts, ChartItem, TimelineItem

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_kpis(db: Session = Depends(get_db)):
    total = db.query(func.count(Applicant.id)).scalar() or 0
    new_app = db.query(func.count(Applicant.id)).filter(Applicant.status == "New Application").scalar() or 0
    under_rev = db.query(func.count(Applicant.id)).filter(Applicant.status == "Under Review").scalar() or 0
    shortlisted = db.query(func.count(Applicant.id)).filter(Applicant.status == "Shortlisted").scalar() or 0
    interview = db.query(func.count(Applicant.id)).filter(Applicant.status == "Interview Scheduled").scalar() or 0
    selected = db.query(func.count(Applicant.id)).filter(Applicant.status == "Selected").scalar() or 0
    rejected = db.query(func.count(Applicant.id)).filter(Applicant.status == "Rejected").scalar() or 0
    on_hold = db.query(func.count(Applicant.id)).filter(Applicant.status == "On Hold").scalar() or 0

    return DashboardStats(
        total_applicants=total,
        new_applicants=new_app,
        under_review=under_rev,
        shortlisted=shortlisted,
        interview_scheduled=interview,
        selected=selected,
        rejected=rejected,
        on_hold=on_hold
    )


@router.get("/charts", response_model=AnalyticsCharts)
def get_analytics_charts(db: Session = Depends(get_db)):
    # 1. Status Distribution
    status_counts = db.query(
        Applicant.status, 
        func.count(Applicant.id)
    ).group_by(Applicant.status).all()

    status_color_map = {
        "New Application": "#3b82f6",
        "Under Review": "#f59e0b",
        "Shortlisted": "#8b5cf6",
        "Interview Scheduled": "#06b6d4",
        "Selected": "#10b981",
        "Rejected": "#ef4444",
        "On Hold": "#6b7280"
    }
    status_data = [
        ChartItem(name=s or "New Application", value=c, color=status_color_map.get(s, "#94a3b8"))
        for s, c in status_counts
    ]

    # 2. Department Distribution
    dept_counts = db.query(
        Applicant.department,
        func.count(Applicant.id)
    ).group_by(Applicant.department).all()

    dept_color_map = {
        "Front office": "#0284c7",
        "Kitchen": "#ea580c",
        "Service": "#16a34a",
        "Account": "#9333ea",
        "Maintenance": "#d97706",
        "Sales": "#dc2626",
        "Admin": "#4f46e5",
        "Housekeeping": "#0891b2",
        "Stores": "#475569",
        "Purchase": "#2563eb",
        "Others": "#64748b"
    }
    dept_data = [
        ChartItem(name=dept or "Others", value=count, color=dept_color_map.get(dept, "#6366f1"))
        for dept, count in dept_counts
    ]

    # 3. Top Skills
    skills_query = db.query(
        ApplicantSkill.skill_name, 
        func.count(ApplicantSkill.id).label("count")
    ).group_by(ApplicantSkill.skill_name).order_by(desc("count")).limit(12).all()

    skills_data = [
        ChartItem(name=name, value=count, color="#8b5cf6")
        for name, count in skills_query
    ]

    # 4. Applications Timeline
    date_counts = db.query(
        func.strftime("%Y-%m-%d", Applicant.uploaded_at).label("upload_day"),
        func.count(Applicant.id)
    ).group_by("upload_day").order_by("upload_day").all()

    timeline_data = [
        TimelineItem(date=day or "Recent", count=count)
        for day, count in date_counts
    ]
    if not timeline_data:
        timeline_data = [TimelineItem(date=datetime.now().strftime("%Y-%m-%d"), count=0)]

    return AnalyticsCharts(
        status_distribution=status_data,
        department_distribution=dept_data,
        top_skills=skills_data,
        timeline=timeline_data
    )
