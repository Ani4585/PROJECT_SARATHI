"""
PII Redaction Interceptor and Data Sanitizer.
"""
import re
from typing import Dict, Any, List, Optional

class PIIRedactor:
    DEFAULT_PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone": r'\b\+?\d{1,4}[-.\s]?\(?\d{1,3}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b',
        "credit_card": r'\b(?:\d[ -]*?){13,16}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b'
    }

    def __init__(self, custom_patterns: Optional[Dict[str, str]] = None, mask_str: str = "[REDACTED]"):
        self.patterns = self.DEFAULT_PATTERNS.copy()
        if custom_patterns:
            self.patterns.update(custom_patterns)
        self.mask_str = mask_str

    def redact_text(self, text: str) -> str:
        sanitized = text
        for p_name, pattern in self.patterns.items():
            sanitized = re.sub(pattern, self.mask_str, sanitized)
        return sanitized

    def redact_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        cleaned = {}
        for k, v in data.items():
            if isinstance(v, str):
                cleaned[k] = self.redact_text(v)
            elif isinstance(v, dict):
                cleaned[k] = self.redact_dict(v)
            elif isinstance(v, list):
                cleaned[k] = [self.redact_text(i) if isinstance(i, str) else i for i in v]
            else:
                cleaned[k] = v
        return cleaned
