import io
import re
import csv
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from ..database import get_db
from ..models import Applicant, ApplicantSkill
from ..schemas import (
    ApplicantResponse, ApplicantCreate, ApplicantUpdate, 
    StatusUpdatePayload, BulkStatusPayload, BulkDeletePayload
)

router = APIRouter(prefix="/api/applicants", tags=["applicants"])

def get_next_sequential_id(db: Session) -> str:
    """
    Computes next sequential Applicant ID starting strictly from A001.
    Order: A001 -> A002 -> A003 ... -> A999 -> B001 -> ...
    """
    all_apps = db.query(Applicant.applicant_id).all()
    if not all_apps:
        return "A001"

    max_prefix = "A"
    max_num = 0

    for (aid,) in all_apps:
        if not aid:
            continue
        m = re.match(r'^([A-Z])(\d{3})$', aid.strip().upper())
        if m:
            prefix, num = m.group(1), int(m.group(2))
            if (prefix > max_prefix) or (prefix == max_prefix and num > max_num):
                max_prefix = prefix
                max_num = num

    if max_num == 0 and max_prefix == "A":
        return "A001"

    next_num = max_num + 1
    if next_num > 999:
        next_prefix = chr(ord(max_prefix) + 1)
        return f"{next_prefix}001"

    return f"{max_prefix}{next_num:03d}"


@router.get("", response_model=List[ApplicantResponse])
def get_applicants(
    search: Optional[str] = Query(None, description="Search across applicant, designation, department, email, contact no, city, remarks, skills"),
    status: Optional[str] = Query(None, description="Filter by status"),
    department: Optional[str] = Query(None, description="Filter by department"),
    city: Optional[str] = Query(None, description="Filter by city"),
    sort_by: str = Query("id", description="Sort field: id, applicant_id, applicant, designation, department, uploaded_at"),
    sort_order: str = Query("asc", description="Sort order: asc or desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(Applicant)

    # 1. Search filter across fields
    if search:
        search_pattern = f"%{search.strip()}%"
        skill_subquery = db.query(ApplicantSkill.applicant_id).filter(
            ApplicantSkill.skill_name.ilike(search_pattern)
        ).subquery()

        query = query.filter(
            or_(
                Applicant.applicant_id.ilike(search_pattern),
                Applicant.applicant.ilike(search_pattern),
                Applicant.designation.ilike(search_pattern),
                Applicant.department.ilike(search_pattern),
                Applicant.email.ilike(search_pattern),
                Applicant.contact_no.ilike(search_pattern),
                Applicant.city.ilike(search_pattern),
                Applicant.remarks.ilike(search_pattern),
                Applicant.id.in_(skill_subquery)
            )
        )

    # 2. Filter by status
    if status and status.lower() != "all":
        query = query.filter(Applicant.status == status)

    # 3. Filter by department
    if department and department.lower() != "all":
        query = query.filter(Applicant.department == department)

    # 4. Filter by city
    if city and city.lower() != "all":
        query = query.filter(Applicant.city.ilike(f"%{city}%"))

    # 5. Sorting
    sort_column = getattr(Applicant, sort_by, Applicant.id)
    if sort_order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    applicants = query.offset(skip).limit(limit).all()
    return applicants


@router.get("/{applicant_id}", response_model=ApplicantResponse)
def get_applicant_by_id(applicant_id: int, db: Session = Depends(get_db)):
    applicant = db.query(Applicant).filter(Applicant.id == applicant_id).first()
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")
    return applicant


@router.post("", response_model=ApplicantResponse)
def create_applicant_manually(payload: ApplicantCreate, db: Session = Depends(get_db)):
    """Creates a candidate record with sequential ID (A001, A002, A003...)."""
    next_id = get_next_sequential_id(db)

    applicant = Applicant(
        applicant_id=next_id,
        applicant=payload.applicant or "NA",
        designation=payload.designation,
        department=payload.department or "Others",
        email=payload.email,
        contact_no=payload.contact_no,
        dob=payload.dob,
        city=payload.city,
        status=payload.status or "New Application",
        remarks=payload.remarks,
        resume_filename=payload.resume_filename,
        resume_file_path=payload.resume_file_path,
        resume_hash=payload.resume_hash,
        uploaded_at=datetime.utcnow()
    )
    db.add(applicant)
    db.commit()
    db.refresh(applicant)

    if payload.skills_list:
        for skill_name in payload.skills_list:
            if skill_name.strip():
                db.add(ApplicantSkill(applicant_id=applicant.id, skill_name=skill_name.strip()))
        db.commit()
        db.refresh(applicant)

    return applicant


@router.put("/{applicant_id}", response_model=ApplicantResponse)
def update_applicant_details(applicant_id: int, payload: ApplicantUpdate, db: Session = Depends(get_db)):
    """Allows manual recruiter review and editing of candidate details."""
    applicant = db.query(Applicant).filter(Applicant.id == applicant_id).first()
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")

    update_data = payload.dict(exclude_unset=True)
    skills_list = update_data.pop("skills_list", None)

    for field, value in update_data.items():
        setattr(applicant, field, value)

    applicant.updated_at = datetime.utcnow()

    if skills_list is not None:
        db.query(ApplicantSkill).filter(ApplicantSkill.applicant_id == applicant.id).delete()
        for skill_name in skills_list:
            if skill_name.strip():
                db.add(ApplicantSkill(applicant_id=applicant.id, skill_name=skill_name.strip()))

    db.commit()
    db.refresh(applicant)
    return applicant


@router.patch("/{applicant_id}/status")
def update_applicant_status(applicant_id: int, payload: StatusUpdatePayload, db: Session = Depends(get_db)):
    applicant = db.query(Applicant).filter(Applicant.id == applicant_id).first()
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")

    applicant.status = payload.status
    applicant.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Status updated successfully", "applicant_id": applicant.applicant_id, "status": applicant.status}


@router.delete("/{applicant_id}")
def delete_applicant(applicant_id: int, db: Session = Depends(get_db)):
    applicant = db.query(Applicant).filter(Applicant.id == applicant_id).first()
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")

    candidate_name = applicant.applicant
    db.delete(applicant)
    db.commit()
    return {"message": f"Applicant {candidate_name} deleted successfully"}


@router.post("/bulk-status")
def bulk_update_status(payload: BulkStatusPayload, db: Session = Depends(get_db)):
    if not payload.applicant_ids:
        raise HTTPException(status_code=400, detail="No applicants provided")

    db.query(Applicant).filter(Applicant.id.in_(payload.applicant_ids)).update(
        {Applicant.status: payload.status, Applicant.updated_at: datetime.utcnow()},
        synchronize_session=False
    )
    db.commit()
    return {"message": f"Updated status to '{payload.status}' for {len(payload.applicant_ids)} applicants"}


@router.post("/bulk-delete")
def bulk_delete_applicants(payload: BulkDeletePayload, db: Session = Depends(get_db)):
    if not payload.applicant_ids:
        raise HTTPException(status_code=400, detail="No applicants provided")

    count = db.query(Applicant).filter(Applicant.id.in_(payload.applicant_ids)).delete(synchronize_session=False)
    db.commit()
    return {"message": f"Deleted {count} applicants"}


@router.get("/export/csv")
def export_applicants_csv(db: Session = Depends(get_db)):
    """Exports applicant ledger to CSV matching exact required fields."""
    applicants = db.query(Applicant).order_by(asc(Applicant.id)).all()

    output = io.StringIO()
    output.write('\ufeff') # UTF-8 BOM
    writer = csv.writer(output)

    # Required columns
    writer.writerow([
        "Applicant ID", "Applicant", "Designation", "Department", 
        "Email", "Contact No.", "DOB", "City", "Status", "Remarks", "Skills", "Resume File"
    ])

    for app in applicants:
        skills_str = ", ".join([s.skill_name for s in app.skills]) if app.skills else "NA"
        writer.writerow([
            app.applicant_id,
            app.applicant or "NA",
            app.designation or "NA",
            app.department or "Others",
            app.email or "NA",
            app.contact_no or "NA",
            app.dob or "NA",
            app.city or "NA",
            app.status,
            app.remarks or "NA",
            skills_str,
            app.resume_filename or "NA"
        ])

    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=applicant_ledger_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )


@router.get("/export/excel")
def export_applicants_excel(db: Session = Depends(get_db)):
    """Exports applicant records to Microsoft Excel format."""
    applicants = db.query(Applicant).order_by(asc(Applicant.id)).all()

    try:
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Applicant Ledger"

        headers = [
            "Applicant ID", "Applicant", "Designation", "Department", 
            "Email", "Contact No.", "DOB", "City", "Status", "Remarks", "Skills", "Resume File"
        ]
        ws.append(headers)

        for app in applicants:
            skills_str = ", ".join([s.skill_name for s in app.skills]) if app.skills else "NA"
            ws.append([
                app.applicant_id,
                app.applicant or "NA",
                app.designation or "NA",
                app.department or "Others",
                app.email or "NA",
                app.contact_no or "NA",
                app.dob or "NA",
                app.city or "NA",
                app.status,
                app.remarks or "NA",
                skills_str,
                app.resume_filename or "NA"
            ])

        stream = io.BytesIO()
        wb.save(stream)
        stream.seek(0)
        return StreamingResponse(
            stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=applicant_ledger_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"}
        )
    except Exception:
        return export_applicants_csv(db)
