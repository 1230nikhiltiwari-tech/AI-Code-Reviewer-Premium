RULES = [
    {
        "id": "PY001", "language": "python", "pattern": r"\beval\s*\(",
        "severity": "HIGH", "category": "Security",
        "title": "Dangerous eval() usage",
        "message": "eval() can execute arbitrary Python code and is dangerous with untrusted input.",
        "recommendation": "Replace eval() with safe parsing or explicit logic. Never pass user-controlled input to eval()."
    },
    {
        "id": "PY002", "language": "python", "pattern": r"^\s*except\s*:\s*(#.*)?$",
        "severity": "MEDIUM", "category": "Reliability",
        "title": "Bare except",
        "message": "A bare except catches every exception and can hide real failures.",
        "recommendation": "Catch the specific exception types the code expects."
    },
    {
        "id": "PY003", "language": "python", "pattern": r"\b(?:password|passwd|pwd)\s*=\s*[\"']([^\"']+)[\"']",
        "severity": "HIGH", "category": "Security",
        "title": "Possible hardcoded credential",
        "message": "A credential-like value appears to be assigned directly in source code.",
        "recommendation": "Move credentials to environment variables or a managed secrets store."
    },
    {
        "id": "PY004", "language": "python", "pattern": r"\bos\.system\s*\(",
        "severity": "HIGH", "category": "Security",
        "title": "Unsafe system command execution",
        "message": "os.system() executes operating-system commands and can enable command injection.",
        "recommendation": "Prefer subprocess.run() with explicit argument lists and avoid shell interpretation."
    },
    {
        "id": "PY005", "language": "python", "pattern": r"\bsubprocess\.(?:call|Popen|run)\s*\(",
        "severity": "MEDIUM", "category": "Security",
        "title": "Subprocess command execution",
        "message": "Subprocess execution should be reviewed when command arguments can be influenced by untrusted data.",
        "recommendation": "Pass commands as argument lists, validate inputs, and avoid shell=True for untrusted data."
    },
    {
        "id": "PY006", "language": "python", "pattern": r"\bpickle\.(?:load|loads)\s*\(",
        "severity": "HIGH", "category": "Security",
        "title": "Unsafe deserialization",
        "message": "Python pickle deserialization is unsafe for untrusted data and can execute arbitrary code.",
        "recommendation": "Use JSON or another safe serialization format for untrusted input."
    },
    {
        "id": "PY007", "language": "python", "pattern": r"\bshell\s*=\s*True\b",
        "severity": "HIGH", "category": "Security",
        "title": "Shell execution enabled",
        "message": "shell=True allows a command to be interpreted by a shell and increases injection risk.",
        "recommendation": "Avoid shell=True and pass commands as explicit argument lists."
    },
    {
        "id": "PY008", "language": "python", "pattern": r"^\s*assert\b",
        "severity": "LOW", "category": "Reliability",
        "title": "Assert used for runtime validation",
        "message": "Assertions can be disabled in optimized Python execution.",
        "recommendation": "Use explicit validation and raise an appropriate exception for runtime checks."
    },

    {
        "id": "JAVA001", "language": "java", "pattern": r"\bSystem\.out\.println\s*\(",
        "severity": "LOW", "category": "Maintainability",
        "title": "Direct console output",
        "message": "Direct console output makes production logging harder to manage.",
        "recommendation": "Use a structured logging framework with appropriate log levels."
    },
    {
        "id": "JAVA002", "language": "java", "pattern": r"\bcatch\s*\(\s*Exception\b",
        "severity": "MEDIUM", "category": "Reliability",
        "title": "Broad exception handling",
        "message": "Catching Exception broadly can hide specific failures.",
        "recommendation": "Catch the narrowest exception type that the code can actually handle."
    },
    {
        "id": "JAVA003", "language": "java", "pattern": r"\b(?:password|passwd|pwd)\s*=\s*\"([^\"]+)\"",
        "severity": "HIGH", "category": "Security",
        "title": "Possible hardcoded credential",
        "message": "A credential-like value appears to be assigned directly in Java source code.",
        "recommendation": "Load credentials from environment variables, a vault, or another secure secret provider."
    },
    {
        "id": "JAVA004", "language": "java", "pattern": r"\bRuntime\.getRuntime\(\)\.exec\s*\(",
        "severity": "HIGH", "category": "Security",
        "title": "Runtime command execution",
        "message": "Runtime.exec() executes operating-system commands and can create injection risk.",
        "recommendation": "Avoid shell commands where possible and strictly validate command arguments."
    },
    {
        "id": "JAVA005", "language": "java", "pattern": r"\bObjectInputStream\b",
        "severity": "HIGH", "category": "Security",
        "title": "Potential unsafe deserialization",
        "message": "Java native object deserialization is risky with untrusted input.",
        "recommendation": "Prefer a safe interchange format such as JSON for untrusted data."
    },
    {
        "id": "JAVA006", "language": "java", "pattern": r"\bTODO\b",
        "severity": "LOW", "category": "Maintainability",
        "title": "Unresolved TODO",
        "message": "A TODO marker may indicate unfinished work or technical debt.",
        "recommendation": "Resolve the TODO or track it as a concrete engineering issue."
    },

    {
        "id": "SEC001", "language": "any", "pattern": r"\b(?:api[_-]?key|secret[_-]?key|private[_-]?key)\s*=\s*[\"'][^\"']+[\"']",
        "severity": "HIGH", "category": "Security",
        "title": "Possible hardcoded secret",
        "message": "A secret-like value appears to be stored directly in source code.",
        "recommendation": "Move secrets into environment variables or a managed secret store."
    },
    {
        "id": "SEC002", "language": "any", "pattern": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        "severity": "HIGH", "category": "Security",
        "title": "Private key detected",
        "message": "A private key marker appears in the repository.",
        "recommendation": "Remove the key, rotate it if exposed, and store keys in a secure key-management system."
    },
    {
        "id": "SEC003", "language": "any", "pattern": r"\bverify\s*=\s*False\b",
        "severity": "HIGH", "category": "Security",
        "title": "TLS verification disabled",
        "message": "Disabling TLS certificate verification can expose network connections to man-in-the-middle attacks.",
        "recommendation": "Keep certificate verification enabled and configure trusted certificates correctly."
    },
    {
        "id": "SEC004", "language": "any", "pattern": r"\b(?:md5|sha1)\s*\(",
        "severity": "MEDIUM", "category": "Security",
        "title": "Weak cryptographic hash",
        "message": "MD5 and SHA-1 are not appropriate for many security-sensitive applications.",
        "recommendation": "Use an approved modern algorithm appropriate for the security requirement."
    },
    {
        "id": "QUAL001", "language": "any", "pattern": r"\bprint\s*\(",
        "severity": "LOW", "category": "Maintainability",
        "title": "Console print statement",
        "message": "Direct print statements can create noisy or unstructured production output.",
        "recommendation": "Use a proper logging mechanism when output is intended for application diagnostics."
    },
]
