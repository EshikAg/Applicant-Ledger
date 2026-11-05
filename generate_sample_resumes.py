"""
Sample Resume Generator for Applicant Ledger
Creates realistic, multi-format sample resumes (PDF, DOCX, and TXT)
using only Python's standard library. Zero external dependencies required.
"""

import os
import io
import zipfile

SAMPLE_RESUMES = [
    {
        "filename": "Alex_Morgan_Senior_FullStack_Engineer.pdf",
        "name": "Alex Morgan",
        "email": "alex.morgan@techstack.io",
        "phone": "+1 (415) 890-2341",
        "location": "San Francisco, CA",
        "applied_for": "Senior Full Stack Engineer",
        "highest_qualification": "Bachelor's Degree",
        "degree": "B.S. in Computer Science",
        "college": "Stanford University",
        "grad_year": "2018",
        "total_experience": "6.5 years",
        "current_job": "Senior Full Stack Engineer",
        "current_company": "Apex Cloud Systems",
        "skills": "Python, TypeScript, React, Next.js, Node.js, FastAPI, PostgreSQL, Docker, AWS, GraphQL, Redis, Git",
        "soft_skills": "Leadership, System Architecture, Agile Mentorship, Communication",
        "achievements": "Architected distributed web application handling 4.5M monthly visitors; Reduced server costs by 35% using serverless lambdas.",
        "experience_lines": [
            "Senior Full Stack Engineer | Apex Cloud Systems (2021 - Present)",
            "- Led engineering team of 8 building responsive React and FastAPI cloud platforms.",
            "- Improved frontend load time by 60% through code splitting and edge caching.",
            "Full Stack Software Developer | Horizon Data Labs (2018 - 2021)",
            "- Built real-time analytics dashboard with React, TypeScript, and WebSocket microservices.",
            "- Maintained 99.98% uptime across PostgreSQL transactional clusters."
        ]
    },
    {
        "filename": "Priya_Sharma_Data_Scientist.docx",
        "name": "Priya Sharma",
        "email": "priya.sharma@aimodels.net",
        "phone": "+91 98111 22334",
        "location": "Bengaluru, India",
        "applied_for": "Lead Data Scientist",
        "highest_qualification": "Master's Degree",
        "degree": "M.Tech in Data Science & Artificial Intelligence",
        "college": "Indian Institute of Science (IISc)",
        "grad_year": "2019",
        "total_experience": "5.5 years",
        "current_job": "Senior Machine Learning Engineer",
        "current_company": "TensorAI Technologies",
        "skills": "Python, PyTorch, TensorFlow, Machine Learning, Deep Learning, NLP, LLMs, Pandas, NumPy, Scikit-Learn, SQL, Docker",
        "soft_skills": "Critical Thinking, Research, Cross-Functional Collaboration",
        "achievements": "Trained domain-specific LLM with 7B parameters; Co-authored 3 peer-reviewed AI research publications.",
        "experience_lines": [
            "Senior Machine Learning Engineer | TensorAI Technologies (2021 - Present)",
            "- Deployed enterprise NLP search pipelines indexing 20M+ unstructured contracts.",
            "- Decreased inference latency by 45% using TensorRT quantization.",
            "Data Scientist | Quant Insights (2019 - 2021)",
            "- Developed predictive churn models that saved $1.2M in recurring annual revenue."
        ]
    },
    {
        "filename": "David_Chen_DevOps_Cloud_Architect.pdf",
        "name": "David Chen",
        "email": "david.chen@clouddevops.com",
        "phone": "+1 (206) 445-9872",
        "location": "Seattle, WA",
        "applied_for": "DevOps & Cloud Architect",
        "highest_qualification": "Bachelor's Degree",
        "degree": "B.S. in Computer Engineering",
        "college": "University of Washington",
        "grad_year": "2016",
        "total_experience": "8.0 years",
        "current_job": "Principal Cloud Architect",
        "current_company": "SkyHigh Cloud Infrastructure",
        "skills": "AWS, Kubernetes, Docker, Terraform, CI/CD, Linux, Python, Go, Ansible, Prometheus, Grafana, Git",
        "soft_skills": "Disaster Recovery, Mentoring, Strategic Planning",
        "achievements": "Managed zero-downtime migration of 120+ microservices to Kubernetes EKS; Authored automated security guardrails.",
        "experience_lines": [
            "Principal Cloud Architect | SkyHigh Cloud Infrastructure (2020 - Present)",
            "- Architected multi-region AWS cloud infrastructure supporting SOC2 Type II compliance.",
            "- Reduced deployment pipeline cycle time from 45 minutes to 4.2 minutes.",
            "Senior DevOps Engineer | Velocity Web (2016 - 2020)",
            "- Built declarative GitOps CI/CD workflows and automated container orchestration."
        ]
    },
    {
        "filename": "Sarah_Jenkins_HR_Talent_Acquisition_Lead.docx",
        "name": "Sarah Jenkins",
        "email": "sarah.jenkins@talentexec.org",
        "phone": "+1 (312) 670-4321",
        "location": "Chicago, IL",
        "applied_for": "HR & Talent Acquisition Lead",
        "highest_qualification": "Master's Degree",
        "degree": "MBA in Human Resources Management",
        "college": "Northwestern University",
        "grad_year": "2017",
        "total_experience": "7.2 years",
        "current_job": "Head of Talent Acquisition",
        "current_company": "Global Recruiters Alliance",
        "skills": "Recruitment, HR Analytics, Workday, Jira, Applicant Tracking Systems, Interviewing, Onboarding, Executive Search",
        "soft_skills": "Negotiation, Active Listening, Emotional Intelligence, Stakeholder Management",
        "achievements": "Hired 140+ senior technical candidates across North America; Reduced average time-to-hire from 52 to 24 days.",
        "experience_lines": [
            "Head of Talent Acquisition | Global Recruiters Alliance (2021 - Present)",
            "- Built end-to-end recruitment pipelines across engineering, product, and leadership.",
            "- Implemented data-driven hiring metrics dashboard tracking offer acceptance rates.",
            "Senior Tech Recruiter | Beacon Talent (2017 - 2021)",
            "- Managed full-cycle technical recruiting for fast-growing venture backed startups."
        ]
    },
    {
        "filename": "Rahul_Verma_Product_Manager.pdf",
        "name": "Rahul Verma",
        "email": "rahul.verma@productworks.io",
        "phone": "+91 98220 33445",
        "location": "Pune, India",
        "applied_for": "Senior Product Manager",
        "highest_qualification": "Master's Degree",
        "degree": "MBA in Technology Management",
        "college": "Indian Institute of Management (IIM)",
        "grad_year": "2018",
        "total_experience": "6.0 years",
        "current_job": "Senior Product Manager",
        "current_company": "FinPulse Fintech",
        "skills": "Product Management, Agile, Scrum, Jira, Figma, SQL, Tableau, Data Analysis, User Research, Roadmapping",
        "soft_skills": "Customer Empathy, Strategic Vision, Cross-Team Alignment",
        "achievements": "Launched mobile payment wallet reaching 2.4M active users; Improved onboarding completion by 34%.",
        "experience_lines": [
            "Senior Product Manager | FinPulse Fintech (2020 - Present)",
            "- Owned core consumer payments product roadmap, managing 3 agile engineering squads.",
            "- Conducted 100+ user interviews to identify high-converting feature opportunities.",
            "Associate Product Manager | Digital Ventures (2018 - 2020)",
            "- Spearheaded feature specifications and market research for SaaS billing engine."
        ]
    },
    {
        "filename": "Emily_Watson_Frontend_React_Developer.docx",
        "name": "Emily Watson",
        "email": "emily.watson@frontendcraft.co.uk",
        "phone": "+44 20 7946 0833",
        "location": "London, UK",
        "applied_for": "Senior Frontend Developer",
        "highest_qualification": "Bachelor's Degree",
        "degree": "B.Sc. in Computer Science",
        "college": "Imperial College London",
        "grad_year": "2020",
        "total_experience": "4.5 years",
        "current_job": "Frontend Developer",
        "current_company": "Creative UI Studio",
        "skills": "React, TypeScript, Next.js, Tailwind CSS, Redux, JavaScript, HTML5, CSS3, Jest, Webpack, Git",
        "soft_skills": "Attention to Detail, Design Systems, UX Sensibility",
        "achievements": "Created modular React component library used by 25+ frontend developers; 100% test coverage with Jest.",
        "experience_lines": [
            "Frontend Developer | Creative UI Studio (2021 - Present)",
            "- Developed responsive web applications using React, TypeScript, and Tailwind CSS.",
            "- Boosted Lighthouse performance score from 68 to 99.",
            "Junior Web Developer | PixelCraft UK (2020 - 2021)",
            "- Built client portals and interactive dashboards with React and REST APIs."
        ]
    },
    {
        "filename": "Aarav_Mehta_Recent_CS_Graduate.pdf",
        "name": "Aarav Mehta",
        "email": "aarav.mehta@universitycs.edu",
        "phone": "+91 98450 11223",
        "location": "Hyderabad, India",
        "applied_for": "Junior Software Engineer",
        "highest_qualification": "Bachelor's Degree",
        "degree": "B.Tech in Computer Science and Engineering",
        "college": "National Institute of Technology (NIT)",
        "grad_year": "2024",
        "total_experience": "0.8 years",
        "current_job": "Software Engineering Intern",
        "current_company": "InnoTech Labs",
        "skills": "Python, JavaScript, React, PostgreSQL, Docker, Git, REST API, HTML, CSS, C++",
        "soft_skills": "Quick Learner, Enthusiasm, Team Collaboration",
        "achievements": "1st place in Inter-College CodeSprint 2023; Solved 400+ problems on LeetCode.",
        "experience_lines": [
            "Software Engineering Intern | InnoTech Labs (Jan 2024 - Present)",
            "- Built automated backend test suites and integrated REST endpoints with FastAPI.",
            "- Assisted in optimizing database indexing and query execution plans."
        ]
    },
    {
        "filename": "Marcus_Brody_Cybersecurity_Analyst.docx",
        "name": "Marcus Brody",
        "email": "marcus.brody@infosecshield.com",
        "phone": "+1 (512) 345-6789",
        "location": "Austin, TX",
        "applied_for": "Cybersecurity & SOC Analyst",
        "highest_qualification": "Bachelor's Degree",
        "degree": "B.S. in Cybersecurity & Information Assurance",
        "college": "University of Texas at Austin",
        "grad_year": "2021",
        "total_experience": "3.5 years",
        "current_job": "SOC Analyst II",
        "current_company": "CyberDefense Networks",
        "skills": "Cybersecurity, Penetration Testing, Linux, Python, OWASP, SIEM, Network Security, Wireshark, Splunk, Incident Response",
        "soft_skills": "Analytical Thinking, Crisis Management, Attention to Detail",
        "achievements": "Discovered and remediated 18 high-severity vulnerabilities; Certified CEH and CompTIA Security+.",
        "experience_lines": [
            "SOC Analyst II | CyberDefense Networks (2022 - Present)",
            "- Monitored enterprise SIEM alerts and managed incident containment procedures.",
            "- Automated threat intelligence feeds using Python scripts.",
            "Junior Security Associate | NetProtect LLC (2021 - 2022)",
            "- Conducted internal vulnerability assessments and firewall configuration audits."
        ]
    }
]

def create_docx_file(resume_info: dict, output_path: str):
    """Creates a valid DOCX file containing resume data using pure Python zipfile."""
    paragraphs = [
        f"{resume_info['name'].upper()}",
        f"Email: {resume_info['email']} | Phone: {resume_info['phone']} | Location: {resume_info['location']}",
        f"Position: {resume_info['applied_for']}",
        "",
        "PROFESSIONAL SUMMARY",
        f"Experienced {resume_info['applied_for']} with {resume_info['total_experience']} of professional experience.",
        f"Current Designation: {resume_info['current_job']}",
        f"Current Organization: {resume_info['current_company']}",
        "",
        "CORE TECHNICAL SKILLS",
        resume_info["skills"],
        "",
        "KEY SOFT SKILLS",
        resume_info["soft_skills"],
        "",
        "PROFESSIONAL WORK EXPERIENCE",
    ]
    for exp in resume_info["experience_lines"]:
        paragraphs.append(exp)

    paragraphs.extend([
        "",
        "EDUCATION",
        f"{resume_info['degree']} | {resume_info['college']} (Graduated: {resume_info['grad_year']})",
        "",
        "KEY ACHIEVEMENTS",
        resume_info["achievements"]
    ])

    # Build XML document
    body_xml = []
    for p in paragraphs:
        escaped_p = p.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        body_xml.append(f"<w:p><w:r><w:t>{escaped_p}</w:t></w:r></w:p>")

    doc_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {"".join(body_xml)}
  </w:body>
</w:document>"""

    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""

    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("word/document.xml", doc_xml)


def create_pdf_file(resume_info: dict, output_path: str):
    """Creates a standard compliant PDF 1.4 file containing resume data."""
    text_lines = [
        f"{resume_info['name'].upper()}",
        f"Email: {resume_info['email']} | Phone: {resume_info['phone']} | Location: {resume_info['location']}",
        f"Position: {resume_info['applied_for']}",
        "--------------------------------------------------------------------------------",
        "PROFESSIONAL SUMMARY",
        f"{resume_info['applied_for']} with {resume_info['total_experience']} hands-on experience.",
        f"Current Designation: {resume_info['current_job']}",
        f"Current Company: {resume_info['current_company']}",
        "--------------------------------------------------------------------------------",
        "TECHNICAL SKILLS",
        resume_info["skills"],
        "--------------------------------------------------------------------------------",
        "WORK EXPERIENCE",
    ]
    for el in resume_info["experience_lines"]:
        text_lines.append(el)

    text_lines.extend([
        "--------------------------------------------------------------------------------",
        "EDUCATION",
        f"{resume_info['degree']} | {resume_info['college']} (Year: {resume_info['grad_year']})",
        "--------------------------------------------------------------------------------",
        "ACHIEVEMENTS",
        resume_info["achievements"]
    ])

    # PDF Stream construction
    stream_content = ["BT", "/F1 10 Tf", "50 740 Td", "14 TL"]
    for i, line in enumerate(text_lines):
        clean = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        if i == 0:
            stream_content.append(f"/F1 16 Tf ({clean}) Tj /F1 10 Tf T*")
        elif "---" in clean:
            stream_content.append(f"({clean[:70]}) Tj T*")
        else:
            stream_content.append(f"({clean[:90]}) Tj T*")
    stream_content.append("ET")
    stream_str = "\n".join(stream_content)

    stream_bytes = stream_str.encode("latin1", errors="replace")
    stream_len = len(stream_bytes)

    objects = []
    # 1: Catalog
    objects.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj")
    # 2: Pages
    objects.append("2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj")
    # 3: Page
    objects.append("3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj")
    # 4: Font
    objects.append("4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj")
    # 5: Stream
    objects.append(f"5 0 obj\n<< /Length {stream_len} >>\nstream\n{stream_str}\nendstream\nendobj")

    output = io.BytesIO()
    output.write(b"%PDF-1.4\n")
    xref = [0]
    for obj in objects:
        xref.append(output.tell())
        output.write(obj.encode("latin1") + b"\n")

    startxref = output.tell()
    output.write(f"xref\n0 {len(xref)}\n0000000000 65535 f \n".encode("latin1"))
    for offset in xref[1:]:
        output.write(f"{offset:010d} 00000 n \n".encode("latin1"))
    output.write(f"trailer\n<< /Size {len(xref)} /Root 1 0 R >>\nstartxref\n{startxref}\n%%EOF\n".encode("latin1"))

    with open(output_path, "wb") as f:
        f.write(output.getvalue())


def create_txt_file(resume_info: dict, output_path: str):
    """Creates a clean plaintext resume."""
    text_content = f"""{resume_info['name'].upper()}
Email: {resume_info['email']}
Phone: {resume_info['phone']}
Location: {resume_info['location']}
Position: {resume_info['applied_for']}

PROFESSIONAL SUMMARY
Experienced {resume_info['applied_for']} with {resume_info['total_experience']} of professional experience.
Current Designation: {resume_info['current_job']}
Current Company: {resume_info['current_company']}

TECHNICAL SKILLS
{resume_info['skills']}

SOFT SKILLS
{resume_info['soft_skills']}

WORK EXPERIENCE
{chr(10).join(resume_info['experience_lines'])}

EDUCATION
{resume_info['degree']} | {resume_info['college']} ({resume_info['grad_year']})

KEY ACHIEVEMENTS
{resume_info['achievements']}
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text_content.strip())


def generate_all_resumes(target_dir: str):
    """Generates all sample resumes into target directory."""
    os.makedirs(target_dir, exist_ok=True)
    generated = []
    for info in SAMPLE_RESUMES:
        filename = info["filename"]
        path = os.path.join(target_dir, filename)
        if filename.endswith(".docx"):
            create_docx_file(info, path)
        elif filename.endswith(".pdf"):
            create_pdf_file(info, path)
        else:
            create_txt_file(info, path)
        generated.append(path)
    return generated

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sample_dir = os.path.join(current_dir, "sample_resumes")
    files = generate_all_resumes(sample_dir)
    print(f"Successfully generated {len(files)} sample resumes in: {sample_dir}")
