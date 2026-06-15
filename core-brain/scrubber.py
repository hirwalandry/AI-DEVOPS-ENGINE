import re

SECRET_PATTERNS = {
    "Generic API Key": r"(?i)(api[_-]?key|secret|password|passwd|auth[_-]?token|bearer)[\"']?\s*[:=]\s*[\"']([a-zA-Z0-9_\-\.~\+/]{16,})[\"']",
    "AWS Access Key": r"AKIA[0-9A-Z]{16}",
    "GitHub OAuth Token": r"gh[opr]_[a-zA-Z0-9]{36}",
    "Slack Webhook URL": r"https://hooks\.slack\.com/services/[A-Z0-9]+/[A-Z0-9]+/[A-Za-z0-9]+",
    "Private RSA/EC Cryptographic Key": r"-----BEGIN [A-Z]+ PRIVATE KEY-----[\s\S]+?-----END [A-Z]+ PRIVATE KEY-----",
}


def sanitize_source_code(raw_code: str) -> tuple[str, list[str]]:
    sanitized_code = raw_code
    detected_threats = []

    for label, pattern in SECRET_PATTERNS.items():
        compiled_regex = re.compile(pattern)
        matches = compiled_regex.findall(sanitized_code)

        if matches:
            detected_threats.append(label)
            sanitized_code = compiled_regex.sub(
                f'/* REDACTED_BY_ENTERPRISE_COMPLIANCE_LAYER [{label}] */',
                sanitized_code,
            )

    return sanitized_code, detected_threats
