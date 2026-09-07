import os
import shutil
import tempfile
import zipfile
from urllib.parse import urlparse

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from analyzer.git_manager import clone_repository, cleanup_repository
from analyzer.scanner import scan_repository, generate_summary
from backend.database import (
    initialize_database,
    save_repository,
    save_findings,
    get_repository_history,
    get_repository,
    get_repository_findings,
)
from backend.ai_reviewer import generate_ai_review

app = FastAPI(
    title="AI Code Engineering Agent",
    description="Repository-level static analysis with AI engineering review",
    version="2.0.0",
)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploaded_repositories")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_UPLOAD_SIZE = 25 * 1024 * 1024
MAX_EXTRACTED_SIZE = 100 * 1024 * 1024
MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_FILE_COUNT = 5000

initialize_database()
app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")


def enrich_findings_with_ai(findings: list[dict]) -> list[dict]:
    for finding in findings:
        finding.update(generate_ai_review(finding))
    return findings


def safe_extract_zip(zip_path: str, destination: str) -> None:
    destination_root = os.path.abspath(destination)
    extracted_size = 0
    file_count = 0

    with zipfile.ZipFile(zip_path, "r") as archive:
        members = archive.infolist()
        if len(members) > MAX_FILE_COUNT:
            raise ValueError("Repository contains too many files.")

        for member in members:
            if member.is_dir():
                continue
            file_count += 1
            if file_count > MAX_FILE_COUNT:
                raise ValueError("Repository contains too many files.")
            if member.file_size > MAX_FILE_SIZE:
                raise ValueError("A file in the repository exceeds the maximum allowed file size.")

            target_path = os.path.abspath(os.path.join(destination, member.filename))
            try:
                common = os.path.commonpath([destination_root, target_path])
            except ValueError as exc:
                raise ValueError("Invalid file path detected in ZIP.") from exc
            if common != destination_root:
                raise ValueError("Unsafe ZIP file path detected.")

            unix_mode = (member.external_attr >> 16) & 0o170000
            if unix_mode == 0o120000:
                raise ValueError("Symbolic links are not allowed inside uploaded repositories.")

            extracted_size += member.file_size
            if extracted_size > MAX_EXTRACTED_SIZE:
                raise ValueError("Extracted repository exceeds the maximum allowed size.")

            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with archive.open(member, "r") as source, open(target_path, "wb") as target:
                shutil.copyfileobj(source, target)


def validate_github_url(repo_url: str) -> str:
    parsed = urlparse((repo_url or "").strip())
    if parsed.scheme != "https" or (parsed.hostname or "").lower() not in {"github.com", "www.github.com"}:
        raise HTTPException(status_code=400, detail="Only public GitHub HTTPS repository URLs are supported.")
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        raise HTTPException(status_code=400, detail="Invalid GitHub repository URL.")
    return repo_url.strip()


def analyze_repository_path(path: str) -> tuple[list[dict], dict]:
    findings = enrich_findings_with_ai(scan_repository(path))
    return findings, generate_summary(findings)


@app.get("/", response_class=HTMLResponse)
def home():
    return dashboard()


@app.get("/health")
def health():
    return {"status": "healthy", "service": "AI Code Engineering Agent", "version": app.version}


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if not os.path.isfile(index_path):
        raise HTTPException(status_code=500, detail="Dashboard frontend is unavailable.")
    with open(index_path, "r", encoding="utf-8") as file:
        return file.read()


@app.post("/review")
async def review_repository(file: UploadFile = File(...)):
    filename = os.path.basename(file.filename or "")
    if not filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Please upload a ZIP repository.")

    repository_id = next(tempfile._get_candidate_names())
    repository_path = os.path.join(UPLOAD_DIR, repository_id)
    os.makedirs(repository_path, exist_ok=True)
    zip_path = os.path.join(repository_path, "repository.zip")

    try:
        total = 0
        with open(zip_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_UPLOAD_SIZE:
                    raise ValueError("Uploaded ZIP exceeds the maximum allowed size of 25 MB.")
                buffer.write(chunk)

        safe_extract_zip(zip_path, repository_path)
        findings, summary = analyze_repository_path(repository_path)
        db_id = save_repository(filename, "upload")
        save_findings(db_id, findings)

        return {
            "repository": filename,
            "database_id": db_id,
            "summary": summary,
            "findings": findings,
        }
    except zipfile.BadZipFile as exc:
        raise HTTPException(status_code=400, detail="Invalid ZIP file.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        print(f"Repository analysis failed: {type(exc).__name__}: {exc}")
        raise HTTPException(status_code=500, detail="Repository analysis failed. Check the server logs for details.") from exc
    finally:
        shutil.rmtree(repository_path, ignore_errors=True)


class RepositoryRequest(BaseModel):
    repo_url: str


@app.post("/review/github")
def review_github_repository(request: RepositoryRequest):
    repo_url = validate_github_url(request.repo_url)
    repo_path = None
    try:
        repo_path = clone_repository(repo_url)
        findings, summary = analyze_repository_path(repo_path)
        db_id = save_repository(repo_url, "github")
        save_findings(db_id, findings)
        return {
            "repository": repo_url,
            "database_id": db_id,
            "summary": summary,
            "findings": findings,
        }
    except HTTPException:
        raise
    except Exception as exc:
        print(f"GitHub review failed: {type(exc).__name__}: {exc}")
        raise HTTPException(status_code=500, detail="GitHub repository analysis failed. Make sure the repository is public and the URL is valid.") from exc
    finally:
        cleanup_repository(repo_path)


@app.get("/history")
def history():
    return get_repository_history()


@app.get("/history/{repository_id}")
def history_detail(repository_id: int):
    repository = get_repository(repository_id)
    if repository is None:
        raise HTTPException(status_code=404, detail="Repository analysis not found.")
    findings = get_repository_findings(repository_id)
    return {
        "repository": repository,
        "summary": generate_summary(findings),
        "findings": findings,
    }
