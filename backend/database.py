import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "code_reviewer.db")


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database() -> None:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS repositories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                source_type TEXT NOT NULL DEFAULT 'upload',
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repository_id INTEGER NOT NULL,
                file TEXT NOT NULL,
                line INTEGER,
                severity TEXT,
                category TEXT,
                rule TEXT,
                rule_id TEXT,
                title TEXT,
                message TEXT,
                recommendation TEXT,
                code TEXT,
                ai_review TEXT,
                suggested_fix TEXT,
                ai_status TEXT,
                FOREIGN KEY (repository_id) REFERENCES repositories(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("PRAGMA table_info(repositories)")
        repository_columns = {row["name"] for row in cursor.fetchall()}
        if "source_type" not in repository_columns:
            cursor.execute("ALTER TABLE repositories ADD COLUMN source_type TEXT NOT NULL DEFAULT 'upload'")
        cursor.execute("PRAGMA table_info(findings)")
        finding_columns = {row["name"] for row in cursor.fetchall()}
        migrations = {
            "category": "TEXT", "rule_id": "TEXT", "recommendation": "TEXT",
            "ai_review": "TEXT", "suggested_fix": "TEXT", "ai_status": "TEXT"
        }
        for column, column_type in migrations.items():
            if column not in finding_columns:
                cursor.execute(f"ALTER TABLE findings ADD COLUMN {column} {column_type}")
        connection.commit()
    finally:
        connection.close()


def save_repository(name: str, source_type: str = "upload") -> int:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO repositories (name, source_type) VALUES (?, ?)", (name, source_type))
        repository_id = int(cursor.lastrowid)
        connection.commit()
        return repository_id
    finally:
        connection.close()


def save_findings(repository_id: int, findings: list[dict]) -> None:
    connection = get_connection()
    try:
        connection.executemany("""
            INSERT INTO findings (
                repository_id, file, line, severity, category, rule, rule_id,
                title, message, recommendation, code, ai_review, suggested_fix, ai_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [(
            repository_id,
            finding.get("file", ""), finding.get("line"), finding.get("severity", "LOW"),
            finding.get("category", "General"), finding.get("rule", finding.get("rule_id")),
            finding.get("rule_id", finding.get("rule")), finding.get("title", "Code finding"),
            finding.get("message", ""), finding.get("recommendation", "Review this finding manually."),
            finding.get("code", ""), finding.get("ai_review"), finding.get("suggested_fix"),
            finding.get("ai_status")
        ) for finding in findings])
        connection.commit()
    finally:
        connection.close()


def get_repository_history() -> list[dict]:
    connection = get_connection()
    try:
        rows = connection.execute("""
            SELECT
                r.id,
                r.name AS repository,
                r.source_type,
                r.uploaded_at AS created_at,
                COUNT(f.id) AS findings_count,
                SUM(CASE WHEN UPPER(f.severity) = 'HIGH' THEN 1 ELSE 0 END) AS high_count,
                SUM(CASE WHEN UPPER(f.severity) = 'MEDIUM' THEN 1 ELSE 0 END) AS medium_count,
                SUM(CASE WHEN UPPER(f.severity) = 'LOW' THEN 1 ELSE 0 END) AS low_count
            FROM repositories r
            LEFT JOIN findings f ON r.id = f.repository_id
            GROUP BY r.id
            ORDER BY r.id DESC
        """).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def get_repository(repository_id: int) -> dict | None:
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT id, name, source_type, uploaded_at FROM repositories WHERE id = ?",
            (repository_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        connection.close()


def get_repository_findings(repository_id: int) -> list[dict]:
    connection = get_connection()
    try:
        rows = connection.execute("""
            SELECT id, repository_id, file, line, severity, category, rule, rule_id,
                   title, message, recommendation, code, ai_review, suggested_fix, ai_status
            FROM findings
            WHERE repository_id = ?
            ORDER BY CASE UPPER(severity) WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 WHEN 'LOW' THEN 3 ELSE 4 END,
                     file, line
        """, (repository_id,)).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()
