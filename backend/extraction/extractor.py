import os
import re
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

class LocalNLPExtractor:
    """
    High-accuracy, rule-based and NLP heuristic extraction pipeline.
    Extracts strictly what is present in the resume text without hallucination.
    """

    DEPARTMENTS = [
        "Front office",
        "Kitchen",
        "Service",
        "Account",
        "Maintenance",
        "Sales",
        "Admin",
        "Housekeeping",
        "Stores",
        "Purchase",
        "Others"
    ]

    SKILL_DATABASE = {
        # Hospitality, Office & Operations
        "OPERA PMS", "Micros POS", "Guest Relations", "Customer Service", "Front Desk",
        "Culinary Arts", "HACCP", "Food Safety", "F&B Service", "Banquet", "Tally Prime",
        "GST", "MS Excel", "Ledger", "HVAC", "Electrical", "Plumbing", "B2B Sales", "CRM",
        "Client Retention", "Recruitment", "Payroll", "Operations", "Room Inspection",
        "Inventory", "Linen Management", "Stock Auditing", "Purchase", "Warehouse",
        "Procurement", "Supply Chain", "Vendor Management", "Workday",

        # Technical & Programming
        "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust", 
        "SQL", "HTML", "CSS", "React", "Next.js", "FastAPI", "Django", "Node.js", 
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Docker", "Kubernetes", "AWS", 
        "Linux", "Git", "Machine Learning", "NLP", "Pandas", "Scikit-Learn", "Jira", "Figma"
    }

    def extract(self, text: str, filename: str = "", target_role: str = "") -> Dict[str, Any]:
        """Runs rule-based and NLP heuristic extraction across the raw resume text."""
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        email = self._extract_email(text)
        contact_no = self._extract_phone(text)
        name = self._extract_name(lines, email)
        dob = self._extract_dob(text, lines)
        city = self._extract_location(text, lines)
        designation = target_role or self._extract_designation(text, lines, filename)
        department = self._extract_department(text, designation)
        remarks = self._extract_remarks(text, lines)
        extracted_skills = self._extract_skills(text)

        # Strictly extract only what is mentioned; missing values are None (NULL/NA)
        return {
            "applicant": name or "NA",
            "designation": designation or None,
            "department": department or "Others",
            "email": email or None,
            "contact_no": contact_no or None,
            "dob": dob or None,
            "city": city or None,
            "status": "New Application",
            "remarks": remarks or None,
            "skills_list": extracted_skills
        }

    def _extract_email(self, text: str) -> Optional[str]:
        match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        return match.group(0).strip().lower() if match else None

    def _extract_phone(self, text: str) -> Optional[str]:
        patterns = [
            r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\+?\d{1,3}[-.\s]?\d{5}[-.\s]?\d{5}',
            r'\b\d{10}\b'
        ]
        for pat in patterns:
            match = re.search(pat, text)
            if match:
                phone = match.group(0).strip()
                digits = re.sub(r'\D', '', phone)
                if len(digits) >= 10:
                    return phone
        return None

    def _extract_name(self, lines: List[str], email: Optional[str]) -> Optional[str]:
        blacklist = {
            "resume", "curriculum", "vitae", "cv", "profile", "contact", "email", "phone", 
            "experience", "education", "skills", "summary", "objective", "work", "page",
            "address", "projects", "certifications", "portfolio", "developer", "engineer"
        }
        
        for line in lines[:6]:
            clean = line.strip()
            if "@" in clean or "http" in clean or len(clean) > 50:
                continue
            if any(term in clean.lower() for term in ["resume", "curriculum vitae", "biodata"]):
                continue

            name_candidate = re.sub(r'^(Name|Full\s*Name|Candidate\s*Name|Applicant)\s*[:\-]\s*', '', clean, flags=re.IGNORECASE).strip()
            words = name_candidate.split()
            if 1 <= len(words) <= 4:
                if all(w.isalpha() for w in words) and not any(w.lower() in blacklist for w in words):
                    return name_candidate.title()

        if email:
            prefix = email.split('@')[0]
            prefix_parts = re.split(r'[._]', prefix)
            clean_parts = [p.capitalize() for p in prefix_parts if p.isalpha() and len(p) > 1]
            if 1 <= len(clean_parts) <= 3:
                return " ".join(clean_parts)

        return None

    def _extract_dob(self, text: str, lines: List[str]) -> Optional[str]:
        # Search for Date of Birth / DOB
        dob_match = re.search(r'(?:Date\s*of\s*Birth|DOB|Birth\s*Date|D\.O\.B\.?)\s*[:\-]\s*([0-9]{1,2}[-/.][0-9]{1,2}[-/.][0-9]{2,4}|[0-9]{1,2}\s+[A-Za-z]{3,9}\s+[0-9]{4}|[A-Za-z]{3,9}\s+[0-9]{1,2},?\s+[0-9]{4})', text, re.IGNORECASE)
        if dob_match:
            return dob_match.group(1).strip()
        return None

    def _extract_location(self, text: str, lines: List[str]) -> Optional[str]:
        loc_match = re.search(r'(?:City|Location|Address|Current\s*Location|Place|Residing\s*in)\s*[:\-]\s*([^\n\r,]+(?:,[^\n\r]+)?)', text, re.IGNORECASE)
        if loc_match:
            loc = loc_match.group(1).strip()
            if len(loc) < 50 and not any(char in loc for char in ['@', 'http', '{', '}']):
                return loc

        common_cities = [
            "San Francisco", "New York", "Seattle", "Austin", "Boston", "Chicago", "Los Angeles", 
            "London", "Berlin", "Toronto", "Vancouver", "Singapore", "Sydney", "Dubai", 
            "Bangalore", "Bengaluru", "Mumbai", "Delhi", "New Delhi", "Hyderabad", "Pune", 
            "Chennai", "Kolkata", "Ahmedabad", "Jaipur", "Goa", "Gurgaon", "Noida"
        ]
        for line in lines[:5]:
            if any(term in line.lower() for term in ["university", "college", "school", "institute"]):
                continue
            for city in common_cities:
                if re.search(r'\b' + re.escape(city) + r'\b', line, re.IGNORECASE):
                    match = re.search(r'\b(' + re.escape(city) + r'(?:\s*,\s*[A-Za-z\s]+)?)\b', line, re.IGNORECASE)
                    if match:
                        return match.group(1).strip()
                    return city

        return None

    def _extract_designation(self, text: str, lines: List[str], filename: str) -> Optional[str]:
        match = re.search(r'(?:Current\s*Designation|Designation|Current\s*Role|Position|Applied\s*For|Role|Target\s*Role|Applying\s*for)\s*[:\-]\s*([^\n\r]+)', text, re.IGNORECASE)
        if match:
            role = match.group(1).strip()
            if len(role) < 50:
                return role.title()

        if filename:
            name_no_ext = os.path.splitext(filename)[0]
            parts = re.split(r'[-_]', name_no_ext)
            role_keywords = ["Executive", "Captain", "Chef", "Engineer", "Developer", "Manager", "Lead", "Officer", "Supervisor", "Keeper", "Accountant", "Associate", "Analyst", "Receptionist"]
            role_tokens = []
            capturing = False
            for part in parts:
                if any(kw.lower() in part.lower() for kw in role_keywords) or capturing:
                    role_tokens.append(part)
                    capturing = True
            if role_tokens:
                return " ".join(role_tokens).title()

        return None

    def _extract_department(self, text: str, designation: Optional[str]) -> str:
        # Check explicit department label
        dept_match = re.search(r'(?:DEPARTMENT|Department|Dept)\s*[:\-]\s*([A-Za-z\s/&]+)', text, re.IGNORECASE)
        if dept_match:
            d_val = dept_match.group(1).strip().lower()
            if "front" in d_val or "reception" in d_val: return "Front office"
            if "kitchen" in d_val or "culinary" in d_val or "chef" in d_val: return "Kitchen"
            if "service" in d_val or "f&b" in d_val: return "Service"
            if "account" in d_val or "finance" in d_val: return "Account"
            if "maintenance" in d_val or "electric" in d_val: return "Maintenance"
            if "sales" in d_val or "marketing" in d_val: return "Sales"
            if "admin" in d_val or "hr" in d_val or "engineer" in d_val or "software" in d_val: return "Admin"
            if "housekeeping" in d_val: return "Housekeeping"
            if "store" in d_val or "inventory" in d_val: return "Stores"
            if "purchase" in d_val or "procurement" in d_val: return "Purchase"

        # Heuristic mapping based on designation and text
        combined = f"{designation or ''} {text[:2000]}".lower()

        if any(w in combined for w in ["front office", "receptionist", "front desk", "concierge", "guest relations"]):
            return "Front office"
        if any(w in combined for w in ["chef", "sous chef", "cook", "culinary", "commis", "pastry", "kitchen"]):
            return "Kitchen"
        if any(w in combined for w in ["service", "steward", "waiter", "captain", "f&b", "food & beverage", "banquet", "bartender"]):
            return "Service"
        if any(w in combined for w in ["accountant", "accounts", "finance", "billing", "cashier", "tally", "ledger", "taxation"]):
            return "Account"
        if any(w in combined for w in ["maintenance", "electrician", "hvac", "plumber", "facility maintenance", "plumbing"]):
            return "Maintenance"
        if any(w in combined for w in ["sales", "business development", "b2b sales", "marketing executive", "client retention"]):
            return "Sales"
        if any(w in combined for w in ["housekeeping", "room inspection", "linen management", "laundry", "room attendant"]):
            return "Housekeeping"
        if any(w in combined for w in ["store keeper", "stores", "stock auditing", "warehouse inventory", "stock keeper"]):
            return "Stores"
        if any(w in combined for w in ["purchase", "procurement", "supply chain", "buyer", "vendor management"]):
            return "Purchase"
        if any(w in combined for w in ["admin", "hr officer", "human resources", "recruiter", "software engineer", "backend", "frontend", "devops"]):
            return "Admin"

        return "Others"

    def _extract_remarks(self, text: str, lines: List[str]) -> Optional[str]:
        rem_match = re.search(r'(?:REMARKS|Remarks|Notes|Screener\s*Remarks|Comments)\s*[:\-]\s*([^\n\r]+)', text, re.IGNORECASE)
        if rem_match:
            rem = rem_match.group(1).strip()
            if len(rem) > 3:
                return rem

        # Look for Professional Summary or Objective
        for i, line in enumerate(lines):
            if re.match(r'^(?:PROFESSIONAL SUMMARY|SUMMARY|CAREER OBJECTIVE|OBJECTIVE)\b', line, re.IGNORECASE):
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if len(next_line) > 15:
                        return next_line[:180]
        return None

    def _extract_skills(self, text: str) -> List[str]:
        found_skills = set()
        text_lower = f" {text.lower()} "
        
        for skill in self.SKILL_DATABASE:
            escaped = re.escape(skill.lower())
            if re.search(r'(?<![a-zA-Z0-9#+])' + escaped + r'(?![a-zA-Z0-9#+])', text_lower):
                found_skills.add(skill)

        # Also check explicit "SKILLS" line e.g. "SKILLS: OPERA PMS, Guest Relations, English"
        skills_line_match = re.search(r'(?:SKILLS|TECHNICAL\s*SKILLS|CORE\s*COMPETENCIES)\s*[:\-]\s*([^\n\r]+)', text, re.IGNORECASE)
        if skills_line_match:
            raw_skills = skills_line_match.group(1).split(',')
            for s in raw_skills:
                s_clean = s.strip()
                if len(s_clean) > 1 and len(s_clean) < 30:
                    found_skills.add(s_clean)

        return sorted(list(found_skills))


class GeminiExtractor:
    """Optional LLM extraction provider using Google Gemini API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def extract(self, text: str, filename: str = "", target_role: str = "") -> Optional[Dict[str, Any]]:
        if not self.is_available():
            return None

        prompt = f"""You are an expert HR data parser. Extract candidate details strictly from the resume text provided.
IMPORTANT:
- Extract ONLY facts actually present in the resume.
- Do NOT invent, assume, or hallucinate missing information.
- If a field is not mentioned, set its value to null.
- Department must be one of: "Front office", "Kitchen", "Service", "Account", "Maintenance", "Sales", "Admin", "Housekeeping", "Stores", "Purchase", "Others".

RESUME TEXT:
\"\"\"
{text[:8000]}
\"\"\"

Return ONLY a valid JSON object with these exact keys:
{{
  "applicant": string or null,
  "designation": string or null,
  "department": string,
  "email": string or null,
  "contact_no": string or null,
  "dob": string or null,
  "city": string or null,
  "status": "New Application",
  "remarks": string or null,
  "skills_list": list of strings
}}
"""
        try:
            import urllib.request
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.0, "responseMimeType": "application/json"}
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                res_body = json.loads(response.read().decode('utf-8'))
                raw_json = res_body['candidates'][0]['content']['parts'][0]['text']
                return json.loads(raw_json)
        except Exception:
            return None


class ModularResumeExtractor:
    def __init__(self, gemini_api_key: Optional[str] = None):
        self.local_extractor = LocalNLPExtractor()
        self.gemini_extractor = GeminiExtractor(gemini_api_key)

    def extract(self, text: str, filename: str = "", target_role: str = "") -> Dict[str, Any]:
        if self.gemini_extractor.is_available():
            llm_result = self.gemini_extractor.extract(text, filename, target_role)
            if llm_result:
                return llm_result

        return self.local_extractor.extract(text, filename, target_role)
