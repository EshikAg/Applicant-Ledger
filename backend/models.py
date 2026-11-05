from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from .database import Base

class Applicant(Base):
    __tablename__ = "applicants"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    applicant_id = Column(String(50), unique=True, index=True, nullable=False) # A001, A002, A003...
    
    # Core Fields matching user specification
    applicant = Column(String(255), nullable=False, index=True) # Candidate Full Name
    designation = Column(String(255), nullable=True, index=True) # Role / Job Title
    department = Column(String(100), nullable=True, index=True) # Front office, Kitchen, Service, Account, Maintenance, Sales, Admin, Housekeeping, Stores, Purchase, Others
    email = Column(String(255), index=True, nullable=True)
    contact_no = Column(String(100), nullable=True) # Phone
    dob = Column(String(50), nullable=True) # Date of Birth
    city = Column(String(255), nullable=True) # Location / City
    status = Column(String(100), default="New Application", index=True, nullable=False) # Application status
    remarks = Column(Text, nullable=True) # Screener remarks / summary notes

    # Additional metadata
    resume_filename = Column(String(255), nullable=True)
    resume_file_path = Column(String(500), nullable=True)
    resume_hash = Column(String(128), index=True, nullable=True)
    extracted_text = Column(Text, nullable=True)

    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    skills = relationship("ApplicantSkill", back_populates="applicant", cascade="all, delete-orphan")
    logs = relationship("ProcessingLog", back_populates="applicant", cascade="all, delete-orphan")


class ApplicantSkill(Base):
    __tablename__ = "applicant_skills"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    applicant_id = Column(Integer, ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False)
    skill_name = Column(String(100), nullable=False, index=True)
    skill_type = Column(String(50), default="technical")

    applicant = relationship("Applicant", back_populates="skills")


class ProcessingLog(Base):
    __tablename__ = "processing_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    resume_filename = Column(String(255), nullable=False)
    file_hash = Column(String(128), index=True, nullable=True)
    file_size_bytes = Column(Integer, default=0)
    status = Column(String(50), default="Pending") # "Pending", "Processing", "Completed", "Failed", "Duplicate"
    extracted_applicant_id = Column(Integer, ForeignKey("applicants.id", ondelete="SET NULL"), nullable=True)
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    applicant = relationship("Applicant", back_populates="logs")


class RecruiterUser(Base):
    __tablename__ = "recruiter_users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="Recruiter")
    created_at = Column(DateTime, default=datetime.utcnow)
