import os
import time
import hashlib
import shutil
import re
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Applicant, ApplicantSkill, ProcessingLog
from ..extraction.parser import extract_text_from_file
from ..extraction.extractor import ModularResumeExtractor
from ..schemas import ProcessingLogResponse
from .applicants import get_next_sequential_id

router = APIRouter(prefix="/api/upload", tags=["upload"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resumes_storage")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".rtf"}
MAX_FILE_SIZE = 25 * 1024 * 1024

@router.post("/resumes")
async def upload_and_process_resumes(
    files: List[UploadFile] = File(...),
    department: Optional[str] = Form(None),
    gemini_api_key: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Handles bulk and individual resume upload:
    - Generates sequential IDs starting from A001 (A001, A002, A003...).
    - Strictly extracts only mentioned data (or NULL / NA).
    - Checks duplicate by file hash and candidate email/phone.
    """
    extractor = ModularResumeExtractor(gemini_api_key)
    results = []

    for file in files:
        start_time = time.time()
        filename = file.filename
        ext = os.path.splitext(filename)[1].lower()

        if ext not in ALLOWED_EXTENSIONS:
            log = ProcessingLog(
                resume_filename=filename,
                file_size_bytes=0,
                status="Failed",
                error_message=f"Unsupported format '{ext}'. Allowed: PDF, DOCX, DOC, TXT.",
                duration_ms=int((time.time() - start_time) * 1000)
            )
            db.add(log)
            db.commit()
            results.append({"filename": filename, "status": "Failed", "error": f"Unsupported format '{ext}'"})
            continue

        content = await file.read()
        file_size = len(content)

        if file_size > MAX_FILE_SIZE:
            log = ProcessingLog(
                resume_filename=filename,
                file_size_bytes=file_size,
                status="Failed",
                error_message="File exceeds 25MB limit",
                duration_ms=int((time.time() - start_time) * 1000)
            )
            db.add(log)
            db.commit()
            results.append({"filename": filename, "status": "Failed", "error": "File exceeds 25MB limit"})
            continue

        file_hash = hashlib.sha256(content).hexdigest()

        # Check duplicate by hash
        existing_applicant_by_hash = db.query(Applicant).filter(Applicant.resume_hash == file_hash).first()
        if existing_applicant_by_hash:
            log = ProcessingLog(
                resume_filename=filename,
                file_hash=file_hash,
                file_size_bytes=file_size,
                status="Duplicate",
                extracted_applicant_id=existing_applicant_by_hash.id,
                error_message=f"Identical resume file already exists in database (Applicant: {existing_applicant_by_hash.applicant}, ID: {existing_applicant_by_hash.applicant_id})",
                duration_ms=int((time.time() - start_time) * 1000)
            )
            db.add(log)
            db.commit()
            results.append({
                "filename": filename,
                "status": "Duplicate",
                "message": f"Exact duplicate file found for candidate '{existing_applicant_by_hash.applicant}' ({existing_applicant_by_hash.applicant_id})",
                "applicant_id": existing_applicant_by_hash.applicant_id,
                "id": existing_applicant_by_hash.id
            })
            continue

        safe_filename = f"{int(time.time())}_{re.sub(r'[^a-zA-Z0-9._-]', '_', filename)}"
        saved_file_path = os.path.join(UPLOAD_DIR, safe_filename)
        with open(saved_file_path, "wb") as f_out:
            f_out.write(content)

        try:
            raw_text, detected_type = extract_text_from_file(saved_file_path)
            if not raw_text.strip():
                raise ValueError("No readable text found in document.")

            extracted = extractor.extract(raw_text, filename=filename)

            # Check duplicate by email
            if extracted.get("email"):
                existing_by_email = db.query(Applicant).filter(Applicant.email == extracted["email"]).first()
                if existing_by_email:
                    log = ProcessingLog(
                        resume_filename=filename,
                        file_hash=file_hash,
                        file_size_bytes=file_size,
                        status="Duplicate",
                        extracted_applicant_id=existing_by_email.id,
                        error_message=f"Duplicate candidate detected with email '{extracted['email']}' (ID: {existing_by_email.applicant_id})",
                        duration_ms=int((time.time() - start_time) * 1000)
                    )
                    db.add(log)
                    db.commit()
                    results.append({
                        "filename": filename,
                        "status": "Duplicate",
                        "message": f"Candidate with email '{extracted['email']}' already exists ({existing_by_email.applicant_id})",
                        "applicant_id": existing_by_email.applicant_id,
                        "id": existing_by_email.id
                    })
                    continue

            # Sequential ID starting at A001
            applicant_id_str = get_next_sequential_id(db)

            # Target department override if provided by recruiter
            final_dept = department or extracted.get("department") or "Others"

            new_applicant = Applicant(
                applicant_id=applicant_id_str,
                applicant=extracted.get("applicant") or "NA",
                designation=extracted.get("designation"),
                department=final_dept,
                email=extracted.get("email"),
                contact_no=extracted.get("contact_no"),
                dob=extracted.get("dob"),
                city=extracted.get("city"),
                status="New Application",
                remarks=extracted.get("remarks"),
                resume_filename=filename,
                resume_file_path=saved_file_path,
                resume_hash=file_hash,
                extracted_text=raw_text[:4000],
                uploaded_at=datetime.utcnow()
            )
            db.add(new_applicant)
            db.commit()
            db.refresh(new_applicant)

            for skill_name in extracted.get("skills_list", []):
                db.add(ApplicantSkill(applicant_id=new_applicant.id, skill_name=skill_name.strip()))
            db.commit()

            duration = int((time.time() - start_time) * 1000)
            log = ProcessingLog(
                resume_filename=filename,
                file_hash=file_hash,
                file_size_bytes=file_size,
                status="Completed",
                extracted_applicant_id=new_applicant.id,
                duration_ms=duration
            )
            db.add(log)
            db.commit()

            results.append({
                "filename": filename,
                "status": "Completed",
                "applicant_id": new_applicant.applicant_id,
                "id": new_applicant.id,
                "applicant": new_applicant.applicant,
                "designation": new_applicant.designation,
                "department": new_applicant.department,
                "email": new_applicant.email,
                "contact_no": new_applicant.contact_no,
                "skills_count": len(extracted.get("skills_list", [])),
                "duration_ms": duration
            })

        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            log = ProcessingLog(
                resume_filename=filename,
                file_hash=file_hash,
                file_size_bytes=file_size,
                status="Failed",
                error_message=str(e),
                duration_ms=duration
            )
            db.add(log)
            db.commit()
            results.append({"filename": filename, "status": "Failed", "error": str(e)})

    return {"processed_count": len(files), "results": results}


@router.post("/retry/{log_id}")
def retry_failed_upload(log_id: int, db: Session = Depends(get_db)):
    log = db.query(ProcessingLog).filter(ProcessingLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Processing log not found")

    matching_file = None
    for f in os.listdir(UPLOAD_DIR):
        if log.resume_filename in f:
            matching_file = os.path.join(UPLOAD_DIR, f)
            break

    if not matching_file or not os.path.exists(matching_file):
        raise HTTPException(status_code=400, detail="Original resume file not found for retry. Please upload again.")

    start_time = time.time()
    try:
        raw_text, detected_type = extract_text_from_file(matching_file)
        extractor = ModularResumeExtractor()
        extracted = extractor.extract(raw_text, filename=log.resume_filename)

        applicant_id_str = get_next_sequential_id(db)

        new_applicant = Applicant(
            applicant_id=applicant_id_str,
            applicant=extracted.get("applicant") or "NA",
            designation=extracted.get("designation"),
            department=extracted.get("department") or "Others",
            email=extracted.get("email"),
            contact_no=extracted.get("contact_no"),
            dob=extracted.get("dob"),
            city=extracted.get("city"),
            status="New Application",
            remarks=extracted.get("remarks"),
            resume_filename=log.resume_filename,
            resume_file_path=matching_file,
            resume_hash=log.file_hash,
            uploaded_at=datetime.utcnow()
        )
        db.add(new_applicant)
        db.commit()
        db.refresh(new_applicant)

        log.status = "Completed"
        log.extracted_applicant_id = new_applicant.id
        log.error_message = None
        log.duration_ms = int((time.time() - start_time) * 1000)
        db.commit()

        return {"message": "Retry successful", "applicant_id": new_applicant.applicant_id, "status": "Completed"}
    except Exception as e:
        log.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Retry failed: {str(e)}")


@router.get("/logs", response_model=List[ProcessingLogResponse])
def get_processing_logs(limit: int = 50, db: Session = Depends(get_db)):
    logs = db.query(ProcessingLog).order_by(ProcessingLog.created_at.desc()).limit(limit).all()
    return logs
