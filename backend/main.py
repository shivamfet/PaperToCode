import asyncio
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from services.job_manager import JobManager, JobStatus
from services.notebook_builder import build_notebook, notebook_to_bytes
from services.openai_service import generate_tutorial
from services.pdf_extractor import extract_text_from_pdf
from services.text_sanitizer import sanitize_pdf_text

app = FastAPI(title="PaperToCode API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

job_manager = JobManager()


@app.get("/health")
async def health_check():
    return {"status": "ok"}


MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
PDF_MAGIC_BYTES = b"%PDF"


@app.post("/api/convert")
async def convert_pdf(
    file: UploadFile = File(...),
    openai_api_key: str = Form(...),
):
    # Validate file extension
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    file_bytes = await file.read()

    # Validate file size
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File too large. Maximum size is 50 MB.",
        )

    # Validate PDF magic bytes
    if len(file_bytes) < 4 or not file_bytes[:4].startswith(PDF_MAGIC_BYTES):
        raise HTTPException(
            status_code=400,
            detail="Invalid file. Only PDF files are accepted.",
        )

    # Create job and start processing in background
    job_id = job_manager.create_job()

    asyncio.get_event_loop().run_in_executor(
        None, _process_job, job_id, file_bytes, openai_api_key
    )

    return {"job_id": job_id}


def _process_job(job_id: str, file_bytes: bytes, api_key: str) -> None:
    """Run the full conversion pipeline in a background thread."""
    try:
        job_manager.set_status(job_id, JobStatus.PROCESSING)

        # Step 1: Extract text
        job_manager.add_message(job_id, "Extracting text from PDF...")
        try:
            pdf_text = extract_text_from_pdf(file_bytes)
        except ValueError as e:
            job_manager.set_error(job_id, str(e))
            return

        page_count = pdf_text.count("--- Page ")
        job_manager.add_message(job_id, f"Extracted text from {page_count} pages.")

        # Step 1b: Sanitize text to mitigate prompt injection
        pdf_text = sanitize_pdf_text(pdf_text)

        # Step 2: Generate tutorial
        job_manager.add_message(job_id, "Analyzing paper with GPT-5.4...")
        try:
            tutorial_data = generate_tutorial(pdf_text, api_key)
        except ValueError as e:
            error_msg = str(e)
            if "API key" in error_msg:
                job_manager.set_error(job_id, f"AUTH:{error_msg}")
            else:
                job_manager.set_error(job_id, error_msg)
            return

        algo_count = len(tutorial_data.get("algorithms", []))
        job_manager.add_message(
            job_id, f"Identified {algo_count} algorithms to implement."
        )

        # Step 3: Build notebook
        job_manager.add_message(job_id, "Building research notebook...")
        nb = build_notebook(tutorial_data)
        nb_bytes = notebook_to_bytes(nb)

        cell_count = len(nb.cells)
        code_cells = sum(1 for c in nb.cells if c.cell_type == "code")
        job_manager.add_message(
            job_id, f"Notebook ready — {cell_count} cells, {code_cells} code blocks."
        )

        job_manager.set_result(job_id, nb_bytes)
        job_manager.set_status(job_id, JobStatus.COMPLETED)

    except Exception as e:
        job_manager.set_error(job_id, f"Unexpected error: {e}")


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    job = job_manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")

    return {
        "job_id": job_id,
        "status": job["status"],
        "messages": job["messages"],
        "error": job["error"],
    }


@app.get("/api/download/{job_id}")
async def download_notebook(job_id: str):
    job = job_manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")

    if job["status"] != JobStatus.COMPLETED or job["result"] is None:
        raise HTTPException(status_code=400, detail="Notebook not ready yet.")

    return Response(
        content=job["result"],
        media_type="application/octet-stream",
        headers={"Content-Disposition": 'attachment; filename="notebook.ipynb"'},
    )
