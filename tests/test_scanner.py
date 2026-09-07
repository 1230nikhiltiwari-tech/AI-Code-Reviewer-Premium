from analyzer.scanner import scan_repository, generate_summary


def test_scanner_finds_security_and_quality_rules():
    findings = scan_repository("test_repo")
    rules = {finding["rule"] for finding in findings}
    assert "PY003" in rules
    assert "PY001" in rules
    assert "JAVA003" in rules
    assert "JAVA004" in rules
    assert "JAVA001" in rules
    assert all(finding.get("category") for finding in findings)
    assert all(finding.get("recommendation") for finding in findings)


def test_password_does_not_trigger_pass_rule():
    findings = scan_repository("test_repo")
    assert "QUAL004" not in {finding["rule"] for finding in findings}


def test_summary():
    summary = generate_summary([
        {"severity": "HIGH"},
        {"severity": "MEDIUM"},
        {"severity": "LOW"},
    ])
    assert summary == {"total_issues": 3, "high": 1, "medium": 1, "low": 1}
