# Applicant Ledger | AI-Powered Resume Management System

An intelligent, enterprise-grade web application that automates the process of collecting, reading, extracting, organizing, and managing applicant information from resumes.

---

## 1. Project Overview

**Applicant Ledger** eliminates manual resume screening and tedious data entry for recruiters and HR personnel. Recruiters can upload candidate resumes in bulk or individually. The system automatically reads each resume, extracts structured candidate details using AI and NLP techniques, detects duplicates, and stores records in a searchable, spreadsheet-like centralized ledger.

### Core Capabilities
- **Bulk & Individual Uploads**: Drag-and-drop support for **PDF**, **DOCX**, and **TXT** resumes.
- **Automatic Resume Information Extraction**:
  - **Personal Information**: Full Name, Email Address, Phone Number, Current Location, Target Position.
  - **Educational Information**: Highest Qualification, Degree, College/University, Graduation Year.
  - **Professional Information**: Current Job Title, Previous Company, Total Work Experience (years), Work History.
  - **Skills & Highlights**: Extracted technical skills, soft skills, and key achievements.
- **Sequential Applicant ID Starting at A001**:
  - Automatically generates IDs in strict sequential order: `A001`, `A002`, `A003`, `A004`... up to `A999`, rolling over to `B001`.
- **11 Standard Department Buckets**:
  - `Front office`, `Kitchen`, `Service`, `Account`, `Maintenance`, `Sales`, `Admin`, `Housekeeping`, `Stores`, `Purchase`, `Others`.
- **Exact Candidate Fields Stored & Managed**:
  - **Applicant ID**: Sequential identifier starting from `A001`.
  - **Applicant**: Candidate's full name.
  - **Designation**: Current or applied role.
  - **Department**: One of the 11 departmental classifications.
  - **Email**: Extracted email address.
  - **Contact No.**: Extracted telephone / mobile number.
  - **DOB**: Extracted Date of Birth.
  - **City**: Candidate's city / location.
  - **Status**: Application status (New Application, Under Review, Shortlisted, Interview Scheduled, Selected, Rejected, On Hold).
  - **Remarks**: Screener notes or summary highlight.
  - **Skills**: Extracted technical and operational skills.
  - **Strict Factuality**: Extracts ONLY information explicitly present in the resume; unmentioned fields are stored as `NULL` and displayed as `NA`. Zero data is ever made up or invented.
- **Applicant Ledger Table**:
  - Formatted like a professional spreadsheet with columns for **Applicant ID**, **Applicant**, **Designation**, **Department**, **Email**, **Contact No.**, **DOB**, **City**, **Status**, **Remarks**, **Skills**, and **Actions**.
  - Multi-field live search (across ID, name, designation, department, email, contact, city, remarks, skills).
  - Multi-criteria filtering by **Department** (all 11 departments), **Status**, and **City**.
  - Column sorting, pagination, and bulk status/delete actions.
  - One-click exports to **Microsoft Excel (.xlsx)** and **CSV** matching all columns.
- **Applicant Status Management**:
  - Seven recruitment stages: `New Application`, `Under Review`, `Shortlisted`, `Interview Scheduled`, `Selected`, `Rejected`, `On Hold`.
  - Visual color-coded status badges and instant inline status dropdowns.
- **Dynamic Dashboard & Analytics**:
  - Dynamically calculated KPI cards: Total Applicants, New, Under Review, Shortlisted, Interview Scheduled, Selected, and Rejected.
  - Visual charts: Status Distribution, Experience Range Breakdown, Top Technical Skills Ranking, and Hiring Conversion Rates.
- **Candidate Profile & Recruiter Correction**:
  - In-depth modal with tabs for Overview, Education, Experience, Skills & Achievements, and Original Resume.
  - **Recruiter Edit Mode**: Allows recruiters to manually modify and correct any extracted details.
- **Dual-Mode Operation**:
  - **Connected Mode**: Powered by Python FastAPI and SQLite database at `http://127.0.0.1:8000`.
  - **Zero-Command Browser Mode**: Simply double-click `index.html` to run the entire application natively in Google Chrome or Microsoft Edge using client-side extraction (PDF.js + Mammoth.js) and local storage!

---

## 2. Architecture & Tech Stack

```
applicants-cv-ledger/
├── backend/
│   ├── database.py              # SQLite SQLAlchemy database engine & session
│   ├── models.py                # Database models (Applicant, Skill, Education, Experience, Log)
│   ├── schemas.py               # Pydantic request/response schemas
│   ├── extraction/
│   │   ├── parser.py            # PDF & DOCX text extractors with pure Python fallbacks
│   │   └── extractor.py         # AI/NLP heuristic extraction + optional Gemini API hook
│   ├── routes/
│   │   ├── applicants.py        # Ledger CRUD, search, filter, bulk actions, CSV/Excel export
│   │   ├── upload.py            # Bulk resume upload, duplicate detection, processing logs
│   │   ├── analytics.py         # Live dynamic KPI counts and chart aggregations
│   │   └── auth.py              # Recruiter authentication
│   └── main.py                  # FastAPI application entry point, CORS, and auto-seeding
├── sample_resumes/              # Test resumes in PDF, DOCX, and TXT formats
├── generate_sample_resumes.py   # Standalone resume generator script (zero dependencies)
├── run_backend.py               # Server launcher with dependency auto-checker
├── run.bat                      # One-click Windows batch launcher
├── requirements.txt             # Python packages
├── index.html                   # Complete modern Single-Page Application (React, Tailwind, Recharts)
└── README.md                    # System documentation
```

### Technology Highlights
- **Frontend**: React 18, Tailwind CSS, Lucide icons, SheetJS (`xlsx.full.min.js`), PDF.js, Mammoth.js, FileSaver.js.
- **Backend**: Python 3.11, FastAPI, Uvicorn, SQLAlchemy.
- **Database**: SQLite (`applicant_ledger.db`).
- **Text & NLP Extraction**: PyMuPDF (`fitz`), `python-docx`, regex entity extraction, degree taxonomy normalizer, work duration aggregator, and modular Google Gemini API integration.

---

## 3. Database Schema

### `applicants` Table
| Column Name | Type | Description |
|---|---|---|
| `id` | INTEGER | Primary Key (autoincrement) |
| `applicant_id` | VARCHAR(50) | Sequential ID starting at `A001` (`A001`, `A002`, `A003`...) |
| `applicant` | VARCHAR(255) | Candidate's extracted full name |
| `designation` | VARCHAR(255) | Position / Designation (or NULL/NA) |
| `department` | VARCHAR(100) | One of 11 departments (Front office, Kitchen, Service, Account, Maintenance, Sales, Admin, Housekeeping, Stores, Purchase, Others) |
| `email` | VARCHAR(255) | Extracted email address |
| `contact_no` | VARCHAR(100) | Extracted phone / contact number |
| `dob` | VARCHAR(50) | Extracted Date of Birth |
| `city` | VARCHAR(255) | Candidate city / location |
| `status` | VARCHAR(100) | Application status (e.g. New Application, Under Review...) |
| `remarks` | TEXT | Screener notes or summary highlight |
| `resume_filename` | VARCHAR(255) | Uploaded resume file name |
| `resume_file_path` | VARCHAR(500) | Path to local copy in storage |
| `resume_hash` | VARCHAR(128) | SHA-256 hash for duplicate detection |
| `uploaded_at` | DATETIME | Timestamp of ingestion |
| `updated_at` | DATETIME | Timestamp of last update |

### Related Tables
- **`applicant_skills`**: Stores individual normalized skills associated with an applicant ID.
- **`applicant_education`**: Detailed educational history entries.
- **`applicant_experience`**: Detailed employment timeline entries.
- **`processing_logs`**: Logs upload attempts, duration, hash, and diagnostics.
- **`recruiter_users`**: Recruiter account records.

---

## 4. Duplicate Resume Detection

The system employs a dual-layer duplicate detection mechanism:
1. **Cryptographic File Hash (SHA-256)**: When a resume is uploaded, its SHA-256 hash is computed. If an identical file exists in the database, the upload is flagged as a duplicate, preventing redundant candidate entries.
2. **Candidate Detail Matching**: If the resume text contains an email address or phone number that matches an existing candidate in the ledger, the system identifies the candidate as an existing profile and provides the matching `Applicant ID`.

---

## 5. Sample Resumes Included

The `sample_resumes/` folder contains diverse, realistic candidate resumes ready for immediate testing:

1. **`Alex_Morgan_Senior_FullStack_Engineer.pdf`**: Senior Full Stack Developer with 6.5 years of experience (React, FastAPI, PostgreSQL, AWS).
2. **`David_Chen_DevOps_Cloud_Architect.pdf`**: Principal Cloud Architect with 8.0 years of experience (AWS, Kubernetes, Terraform, CI/CD).
3. **`Priya_Sharma_Data_Scientist.txt`**: Lead Data Scientist with 5.5 years of experience (Python, PyTorch, LLMs, NLP, M.Tech IISc).
4. **`Emily_Watson_Frontend_React_Developer.txt`**: Senior Frontend Engineer with 4.5 years of experience (React, TypeScript, Next.js, Tailwind).
5. **`Rahul_Verma_Product_Manager.txt`**: Senior Product Manager with 6.0 years of experience (IIM MBA, Jira, Figma, SQL).
6. **`Marcus_Brody_Cybersecurity_Analyst.txt`**: SOC Analyst II with 3.5 years of experience (Cybersecurity, SIEM, OWASP, Python).
7. **`Aarav_Mehta_Recent_CS_Graduate.txt`**: Junior Software Engineer / 2024 Graduate (NIT B.Tech, LeetCode, React, Python).
8. **`John_Doe_Backend_Engineer.txt`**: Senior Backend Engineer with 6+ years of experience.
9. **`Sarah_Jenkins_Receptionist.txt`**: Front Office Associate with luxury hospitality experience.

---

## 6. Security & Data Integrity

- **Untrusted Input Protection**: Resume content is sanitized and rendered safely to prevent cross-site scripting (XSS) or SQL injection.
- **Safe File Storage**: Resumes are stored locally in `backend/resumes_storage/` with sanitized filenames and served through a secure parameterized endpoint (`/api/resumes/{filename}`).
- **Directory Traversal Defense**: File download endpoints strip directory paths using `os.path.basename`.
- **Audit Trails**: Every resume upload records a timestamped `ProcessingLog` entry tracking filename, file size, SHA-256 hash, latency, and status.
- **Recruiter Authentication**: Default recruiter credentials (`recruiter@applicantledger.com` / `admin123`) secure administrative access.
