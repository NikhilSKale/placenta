"""Guardrails service: input sanitization, prompt injection defense, and PII/data leak redaction."""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from app.core.logging import get_logger

logger = get_logger(__name__)

# Patterns that indicate prompt injection, jailbreaking, or boundary escape attempts
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)",
    r"forget\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)",
    r"bypass\s+(all\s+)?(safety|rules|restrictions|guardrails)",
    r"system\s*prompt\s*(reveal|show|dump|print|override)",
    r"you\s+are\s+now\s+(in\s+developer\s+mode|unrestricted|DAN|jailbroken)",
    r"you\s+must\s+act\s+as\s+an\s+unfiltered\s+AI",
    r"pretend\s+you\s+have\s+no\s+(restrictions|rules|instructions)",
    r"reveal\s+your\s+(system\s+prompt|initial\s+prompt|hidden\s+instructions)",
    r"output\s+the\s+exact\s+prompt\s+given\s+to\s+you",
    r"repeat\s+everything\s+above\s+verbatim",
    r"jailbreak\s*(mode|prompt)?",
    r"sudo\s+mode",
]

# Regex patterns for detecting and scrubbing sensitive student/system data (PII)
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
PHONE_PATTERN = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
INDIAN_PHONE_PATTERN = re.compile(r"\b[6-9]\d{9}\b")
AADHAAR_PATTERN = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")
ROLL_NO_PATTERN = re.compile(r"\b(20\d{2}[A-Za-z]{2,4}\d{2,4})\b", re.IGNORECASE)


class GuardrailViolation:
    def __init__(self, violation_type: str, message: str, confidence: float = 1.0):
        self.violation_type = violation_type
        self.message = message
        self.confidence = confidence

    def to_dict(self) -> Dict:
        return {
            "violation_type": self.violation_type,
            "message": self.message,
            "confidence": self.confidence,
        }


class GuardrailsService:
    """Provides input safety guardrails, prompt injection detection, and PII redacting."""

    def __init__(self):
        self.injection_regexes = [
            re.compile(p, re.IGNORECASE) for p in PROMPT_INJECTION_PATTERNS
        ]

    def validate_input(self, user_query: str) -> Tuple[bool, Optional[GuardrailViolation], str]:
        """
        Validates the incoming query against attacks.
        Returns: (is_safe, violation_or_none, sanitized_query)
        """
        clean_text = user_query.strip()
        if not clean_text:
            return False, GuardrailViolation("empty_query", "The question cannot be empty."), clean_text

        # 1. Check prompt injection
        for regex in self.injection_regexes:
            if regex.search(clean_text):
                logger.warning("Prompt injection detected in query: %s", clean_text)
                return (
                    False,
                    GuardrailViolation(
                        violation_type="prompt_injection",
                        message=(
                            "Security Guardrail: Your query contains patterns attempting to override "
                            "or inspect internal system instructions. Placenta only answers questions "
                            "regarding VESIT placement experiences and policies."
                        ),
                        confidence=0.98,
                    ),
                    clean_text,
                )

        # 2. Check query length limit
        if len(clean_text) > 2000:
            return (
                False,
                GuardrailViolation(
                    violation_type="length_exceeded",
                    message="Query is too long. Please restrict your question to under 2000 characters.",
                ),
                clean_text,
            )

        # 3. Scrub input of accidental PII so queries don't search student personal info
        sanitized = self.redact_pii(clean_text)
        return True, None, sanitized

    def redact_pii(self, text: str) -> str:
        """Masks phone numbers, emails, roll numbers, and personal IDs."""
        text = EMAIL_PATTERN.sub("[EMAIL REDACTED]", text)
        text = INDIAN_PHONE_PATTERN.sub("[PHONE REDACTED]", text)
        text = PHONE_PATTERN.sub("[PHONE REDACTED]", text)
        text = AADHAAR_PATTERN.sub("[ID REDACTED]", text)
        return text

    def sanitize_output(self, response_text: str) -> str:
        """
        Output guardrail: ensures model outputs don't accidentally leak
        student personal phone numbers, emails, or personal identification.
        """
        return self.redact_pii(response_text)


guardrails_service = GuardrailsService()

