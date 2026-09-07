import os
import re
from .rules import RULES

SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".java": "java",
}

IGNORED_DIRECTORIES = {
    ".git", ".venv", "venv", "env", "__pycache__",
    "node_modules", "dist", "build", ".idea", ".vscode",
    ".pytest_cache", ".mypy_cache", ".ruff_cache"
}

COMPILED_RULES = []
for rule in RULES:
    try:
        COMPILED_RULES.append({**rule, "regex": re.compile(rule["pattern"], re.IGNORECASE)})
    except re.error:
        continue


def _is_comment_only(line: str, language: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if language == "python":
        return stripped.startswith("#")
    if language == "java":
        return stripped.startswith("//") or stripped.startswith("*") or stripped.startswith("/*") or stripped.startswith("*/")
    return False


def _is_noise_match(rule_id: str, line: str) -> bool:
    # Reserved for future rule-specific suppression logic.
    return False


def scan_file(file_path: str, repo_path: str | None = None) -> list[dict]:
    extension = os.path.splitext(file_path)[1].lower()
    language = SUPPORTED_EXTENSIONS.get(extension)
    if not language:
        return []

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            lines = file.readlines()
    except OSError as exc:
        return [{
            "file": os.path.relpath(file_path, repo_path) if repo_path else file_path,
            "line": 0,
            "severity": "ERROR",
            "category": "System",
            "rule": "SYSTEM",
            "rule_id": "SYSTEM",
            "title": "Could not read file",
            "message": str(exc),
            "recommendation": "Check that the file exists and is readable.",
            "code": "",
        }]

    relative_path = os.path.relpath(file_path, repo_path) if repo_path else file_path
    findings = []

    for line_number, line in enumerate(lines, start=1):
        if _is_comment_only(line, language):
            continue

        for rule in COMPILED_RULES:
            rule_language = rule.get("language", "any")
            if rule_language not in ("any", language):
                continue
            if _is_noise_match(rule["id"], line):
                continue
            if rule["regex"].search(line):
                findings.append({
                    "file": relative_path,
                    "line": line_number,
                    "severity": rule.get("severity", "LOW"),
                    "category": rule.get("category", "General"),
                    "rule": rule.get("id", "UNKNOWN"),
                    "rule_id": rule.get("id", "UNKNOWN"),
                    "title": rule.get("title", "Code finding"),
                    "message": rule.get("message", ""),
                    "recommendation": rule.get("recommendation", "Review this finding manually."),
                    "code": line.strip(),
                })

    return findings


def scan_repository(repo_path: str) -> list[dict]:
    findings = []
    if not os.path.isdir(repo_path):
        return [{
            "file": repo_path,
            "line": 0,
            "severity": "ERROR",
            "category": "System",
            "rule": "SYSTEM",
            "rule_id": "SYSTEM",
            "title": "Repository not found",
            "message": "The supplied repository path is not a directory.",
            "recommendation": "Provide a valid repository directory.",
            "code": "",
        }]

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRECTORIES and not d.startswith(".pytest_cache")]
        for filename in files:
            if os.path.splitext(filename)[1].lower() not in SUPPORTED_EXTENSIONS:
                continue
            findings.extend(scan_file(os.path.join(root, filename), repo_path))

    return findings


def generate_summary(findings: list[dict]) -> dict:
    summary = {"total_issues": len(findings), "high": 0, "medium": 0, "low": 0}
    for finding in findings:
        severity = str(finding.get("severity", "")).lower()
        if severity in summary:
            summary[severity] += 1
    return summary
