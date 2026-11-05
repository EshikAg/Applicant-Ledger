"""
Applicant Ledger - Backend Server Runner
Automatically checks dependencies, generates sample resumes, and launches FastAPI.
"""

import os
import sys

def main():
    print("=" * 70)
    print("   APPLICANT LEDGER - AI-POWERED RESUME MANAGEMENT SYSTEM")
    print("=" * 70)
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sample_dir = os.path.join(current_dir, "sample_resumes")

    # Step 1: Generate sample resumes if not already created
    try:
        from generate_sample_resumes import generate_all_resumes
        print("[1/3] Checking and generating sample test resumes...")
        generated = generate_all_resumes(sample_dir)
        print(f"      Generated {len(generated)} sample resumes in: {sample_dir}")
    except Exception as e:
        print(f"      Notice: Sample resume generator note: {e}")

    # Step 2: Verify FastAPI & Uvicorn
    print("[2/3] Checking server dependencies...")
    try:
        import uvicorn
        import fastapi
        import sqlalchemy
        print("      Core dependencies verified (FastAPI, SQLAlchemy, Uvicorn).")
    except ImportError:
        print("      Installing missing core packages (fastapi, uvicorn, sqlalchemy)...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn", "sqlalchemy", "python-multipart"])

    # Step 3: Start Uvicorn Server
    print("[3/3] Starting Applicant Ledger API Server on http://127.0.0.1:8000 ...")
    print("      Swagger API Docs: http://127.0.0.1:8000/docs")
    print("      Frontend UI:      Open index.html directly in your browser!")
    print("=" * 70)
    
    import uvicorn
    # Change working dir to project root
    os.chdir(current_dir)
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    main()
