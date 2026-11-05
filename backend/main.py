import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .database import engine, Base, SessionLocal
from .models import Applicant, ApplicantSkill, RecruiterUser
from .routes import applicants, upload, analytics, auth

# Re-create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Applicant Ledger API",
    description="AI-Powered Applicant Ledger and Resume Management System Backend",
    version="2.1.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router)
app.include_router(applicants.router)
app.include_router(upload.router)
app.include_router(analytics.router)

RESUMES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resumes_storage")
os.makedirs(RESUMES_DIR, exist_ok=True)

@app.get("/api/resumes/{filename}")
def serve_resume_file(filename: str):
    safe_name = os.path.basename(filename)
    file_path = os.path.join(RESUMES_DIR, safe_name)

    if not os.path.exists(file_path):
        sample_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_resumes", safe_name)
        if os.path.exists(sample_path):
            file_path = sample_path
        else:
            raise HTTPException(status_code=404, detail="Resume file not found")

    ext = os.path.splitext(safe_name)[1].lower()
    media_types = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc": "application/msword",
        ".txt": "text/plain",
        ".rtf": "application/rtf"
    }
    media_type = media_types.get(ext, "application/octet-stream")

    return FileResponse(file_path, media_type=media_type, filename=safe_name)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Applicant Ledger API",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "SQLite (Connected)"
    }

def seed_initial_data_if_empty():
    """Seeds initial applicant ledger starting strictly at A001."""
    db = SessionLocal()
    try:
        count = db.query(Applicant).count()
        if count == 0:
            auth.ensure_default_recruiter(db)

            # Sample candidates matching exact user requirements:
            # Starting at A001, sequential A002, A003, A004...
            sample_candidates = [
                {
                    "applicant_id": "A001",
                    "applicant": "Aarav Sharma",
                    "designation": "Front Office Executive",
                    "department": "Front office",
                    "email": "aarav.sharma@example.com",
                    "contact_no": "+91 98000 10000",
                    "dob": "01/01/1990",
                    "city": "Mumbai",
                    "status": "New Application",
                    "remarks": "Profile screened for Front Office Executive. 4 years luxury hotel desk experience.",
                    "skills": ["OPERA PMS", "Guest Relations", "Customer Service", "English"],
                    "resume_filename": "Aarav_Sharma_Resume.pdf"
                },
                {
                    "applicant_id": "A002",
                    "applicant": "Vihaan Patel",
                    "designation": "Sous Chef",
                    "department": "Kitchen",
                    "email": "vihaan.patel@example.com",
                    "contact_no": "+91 98001 10073",
                    "dob": "02/02/1991",
                    "city": "Delhi",
                    "status": "Under Review",
                    "remarks": "Experienced in Continental and Pan-Asian culinary operations with HACCP certification.",
                    "skills": ["Culinary Arts", "HACCP", "Food Safety", "Menu Planning"],
                    "resume_filename": "Vihaan_Patel_Resume.pdf"
                },
                {
                    "applicant_id": "A003",
                    "applicant": "Aditya Verma",
                    "designation": "Restaurant Captain",
                    "department": "Service",
                    "email": "aditya.verma@example.com",
                    "contact_no": "+91 98002 10146",
                    "dob": "03/03/1992",
                    "city": "Bangalore",
                    "status": "Shortlisted",
                    "remarks": "Strong F&B service leadership, handles VIP banqueting and POS billing.",
                    "skills": ["F&B Service", "Banquet", "Micros POS", "Guest Relations"],
                    "resume_filename": "Aditya_Verma_Resume.pdf"
                },
                {
                    "applicant_id": "A004",
                    "applicant": "Rohan Gupta",
                    "designation": "Senior Accountant",
                    "department": "Account",
                    "email": "rohan.gupta@example.com",
                    "contact_no": "+91 98003 10219",
                    "dob": "04/04/1993",
                    "city": "Pune",
                    "status": "Interview Scheduled",
                    "remarks": "Expert in corporate balance sheets, Tally Prime, GST filing, and financial ledger auditing.",
                    "skills": ["Tally Prime", "GST", "MS Excel", "Ledger", "Audit"],
                    "resume_filename": "Rohan_Gupta_Resume.pdf"
                },
                {
                    "applicant_id": "A005",
                    "applicant": "Kabir Singh",
                    "designation": "Facility Maintenance Engineer",
                    "department": "Maintenance",
                    "email": "kabir.singh@example.com",
                    "contact_no": "+91 98004 10292",
                    "dob": "05/05/1994",
                    "city": "Hyderabad",
                    "status": "Under Review",
                    "remarks": "Oversees high-voltage electrical, plumbing, and central HVAC plant maintenance.",
                    "skills": ["HVAC", "Electrical", "Plumbing", "Facility Maintenance"],
                    "resume_filename": "Kabir_Singh_Resume.pdf"
                },
                {
                    "applicant_id": "A006",
                    "applicant": "Ananya Reddy",
                    "designation": "B2B Sales Executive",
                    "department": "Sales",
                    "email": "ananya.reddy@example.com",
                    "contact_no": "+91 98005 10365",
                    "dob": "06/06/1995",
                    "city": "Chennai",
                    "status": "Selected",
                    "remarks": "Consistent target over-achiever in B2B corporate sales and client retention.",
                    "skills": ["B2B Sales", "CRM", "Client Retention", "Negotiation"],
                    "resume_filename": "Ananya_Reddy_Resume.pdf"
                },
                {
                    "applicant_id": "A007",
                    "applicant": "Diya Mehta",
                    "designation": "HR & Administrative Officer",
                    "department": "Admin",
                    "email": "diya.mehta@example.com",
                    "contact_no": "+91 98006 10438",
                    "dob": "07/07/1996",
                    "city": "Kolkata",
                    "status": "Interview Scheduled",
                    "remarks": "Manages talent onboarding, attendance systems, employee relations, and office administration.",
                    "skills": ["Recruitment", "Payroll", "Operations", "Employee Relations"],
                    "resume_filename": "Diya_Mehta_Resume.pdf"
                },
                {
                    "applicant_id": "A008",
                    "applicant": "Ishaan Nair",
                    "designation": "Housekeeping Supervisor",
                    "department": "Housekeeping",
                    "email": "ishaan.nair@example.com",
                    "contact_no": "+91 98007 10511",
                    "dob": "08/08/1997",
                    "city": "Ahmedabad",
                    "status": "New Application",
                    "remarks": "Supervises floor attendants, room cleanliness inspections, and linen inventory.",
                    "skills": ["Room Inspection", "Inventory", "Linen Management", "Hygiene"],
                    "resume_filename": "Ishaan_Nair_Resume.pdf"
                },
                {
                    "applicant_id": "A009",
                    "applicant": "Pooja Joshi",
                    "designation": "Store Keeper",
                    "department": "Stores",
                    "email": "pooja.joshi@example.com",
                    "contact_no": "+91 98008 10584",
                    "dob": "09/09/1998",
                    "city": "Goa",
                    "status": "Selected",
                    "remarks": "Experienced in stock auditing, goods receipt dispatch, and warehouse operations.",
                    "skills": ["Stock Auditing", "Purchase", "Warehouse", "Logistics"],
                    "resume_filename": "Pooja_Joshi_Resume.pdf"
                },
                {
                    "applicant_id": "A010",
                    "applicant": "Siddharth Rao",
                    "designation": "Procurement & Purchase Officer",
                    "department": "Purchase",
                    "email": "siddharth.rao@example.com",
                    "contact_no": "+91 98009 10657",
                    "dob": "10/10/1995",
                    "city": "Jaipur",
                    "status": "Shortlisted",
                    "remarks": "Specialized in vendor negotiation, purchase orders, and supply chain contract management.",
                    "skills": ["Procurement", "Purchase", "Supply Chain", "Vendor Management"],
                    "resume_filename": "Siddharth_Rao_Resume.pdf"
                }
            ]

            for cand in sample_candidates:
                skills_to_add = cand.pop("skills", [])
                applicant = Applicant(**cand, uploaded_at=datetime.utcnow())
                db.add(applicant)
                db.commit()
                db.refresh(applicant)

                for sk in skills_to_add:
                    db.add(ApplicantSkill(applicant_id=applicant.id, skill_name=sk))
                db.commit()

    finally:
        db.close()

seed_initial_data_if_empty()
