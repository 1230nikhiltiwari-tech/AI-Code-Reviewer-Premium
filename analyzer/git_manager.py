import os
import shutil
import subprocess
import tempfile


def clone_repository(repo_url: str) -> str:
    repo_id = next(tempfile._get_candidate_names())
    clone_root = os.path.join(tempfile.gettempdir(), "ai_code_reviewer")
    clone_path = os.path.join(clone_root, repo_id)
    os.makedirs(clone_root, exist_ok=True)

    result = subprocess.run(
        ["git", "clone", "--depth", "1", "--filter=blob:none", repo_url, clone_path],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git clone failed"
        raise RuntimeError(message)
    return clone_path


def cleanup_repository(repo_path: str | None) -> None:
    if repo_path and os.path.exists(repo_path):
        shutil.rmtree(repo_path, ignore_errors=True)
