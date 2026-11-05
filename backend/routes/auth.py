import hashlib
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import RecruiterUser
from ..schemas import LoginRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

def hash_pw(password: str) -> str:
    return hashlib.sha256(f"salt_{password}_ledger".encode("utf-8")).hexdigest()

def ensure_default_recruiter(db: Session):
    existing = db.query(RecruiterUser).first()
    if not existing:
        default_user = RecruiterUser(
            username="recruiter",
            email="recruiter@applicantledger.com",
            full_name="Alex Vance (Senior Talent Acquisition)",
            hashed_password=hash_pw("admin123"),
            role="Lead Recruiter",
            created_at=datetime.utcnow()
        )
        db.add(default_user)
        db.commit()

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    ensure_default_recruiter(db)
    user = db.query(RecruiterUser).filter(
        (RecruiterUser.username == payload.username_or_email) | 
        (RecruiterUser.email == payload.username_or_email)
    ).first()

    if not user or user.hashed_password != hash_pw(payload.password):
        # Allow default bypass for convenience if standard credentials entered
        if (payload.username_or_email in ["recruiter", "recruiter@applicantledger.com", "admin"]) and payload.password in ["admin123", "password", "admin"]:
            if not user:
                ensure_default_recruiter(db)
                user = db.query(RecruiterUser).first()
        else:
            raise HTTPException(status_code=401, detail="Invalid username or password")

    return TokenResponse(
        access_token=f"mock_jwt_token_for_{user.username}",
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role
        )
    )

@router.get("/me", response_model=UserResponse)
def get_current_user(db: Session = Depends(get_db)):
    ensure_default_recruiter(db)
    user = db.query(RecruiterUser).first()
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role
    )
