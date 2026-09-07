import os
from dotenv import load_dotenv

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
AI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna").strip()

client = OpenAI(api_key=API_KEY) if API_KEY and OpenAI else None


def _fallback_review(finding: dict) -> str:
    title = finding.get("title", "Code finding")
    message = finding.get("message", "No description available.")
    recommendation = finding.get("recommendation", "Review this finding manually.")
    category = finding.get("category", "General")
    severity = finding.get("severity", "LOW")
    code = finding.get("code", "")
    return (
        "## Verdict\n"
        f"{title} is a **{severity} {category}** finding based on the static rule match.\n\n"
        "## Why this matters\n"
        f"{message}\n\n"
        "## Root cause\n"
        f"The detected source line matches the rule condition: `{code}`.\n\n"
        "## Impact\n"
        "The exact runtime impact depends on surrounding code and input flow, which the static finding alone may not establish.\n\n"
        "## Recommended fix\n"
        f"{recommendation}\n\n"
        "## Corrected example\n"
        "Apply the smallest safe change that removes the risky construct while preserving intended behavior.\n\n"
        "## Verification\n"
        "Re-run the repository analysis and add a focused test for the affected behavior.\n\n"
        "## False-positive analysis\n"
        "Review surrounding code and data flow to confirm whether the matched construct is actually reachable with untrusted data."
    )


def generate_ai_review(finding: dict) -> dict:
    if not isinstance(finding, dict):
        return {
            "ai_review": "Invalid finding data.",
            "suggested_fix": "Provide a valid static-analysis finding.",
            "ai_status": "error"
        }

    fallback = _fallback_review(finding)

    if client is None:
        return {
            "ai_review": fallback,
            "suggested_fix": finding.get("recommendation", "Review the finding manually."),
            "ai_status": "fallback"
        }

    prompt = f"""
You are a senior software security and reliability engineer.
Review exactly one static-analysis finding using only the evidence below.
Do not invent code, architecture, data flow, or exploitability.

Rule: {finding.get('rule_id', finding.get('rule', 'UNKNOWN'))}
Category: {finding.get('category', 'General')}
Severity: {finding.get('severity', 'LOW')}
Title: {finding.get('title', 'Code finding')}
File: {finding.get('file', 'Unknown')}
Line: {finding.get('line', 'Unknown')}
Message: {finding.get('message', '')}
Recommendation: {finding.get('recommendation', '')}
Code: {finding.get('code', '')}

Use exactly these headings:
## Verdict
## Why this matters
## Root cause
## Impact
## Recommended fix
## Corrected example
## Verification
## False-positive analysis

Be concise, technically precise, and distinguish confirmed facts from assumptions.
"""

    try:
        response = client.responses.create(
            model=AI_MODEL,
            instructions=(
                "You are an expert software-security reviewer. "
                "Be evidence-driven, conservative, and practical."
            ),
            input=prompt,
        )
        review = (response.output_text or "").strip()
        if not review:
            raise RuntimeError("Empty response from AI reviewer")
        return {
            "ai_review": review,
            "suggested_fix": finding.get("recommendation", "Review the finding manually."),
            "ai_status": "success",
            "ai_model": AI_MODEL,
        }
    except Exception as exc:
        print(f"AI review failed ({type(exc).__name__}): {exc}")
        return {
            "ai_review": fallback,
            "suggested_fix": finding.get("recommendation", "Review the finding manually."),
            "ai_status": "fallback",
            "ai_error": str(exc),
        }
