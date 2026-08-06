"""Privacy pipeline exceptions."""

from __future__ import annotations


class PrivacyServiceError(Exception):
    """Base error for Presidio/NeMo client failures."""

    def __init__(self, service: str, message: str):
        self.service = service
        super().__init__(f"{service}: {message}")


class PresidioUnavailableError(PrivacyServiceError):
    def __init__(self, message: str = "Presidio service unreachable"):
        super().__init__("presidio", message)


class GuardrailsUnavailableError(PrivacyServiceError):
    def __init__(self, message: str = "NeMo Guardrails service unreachable"):
        super().__init__("nemo-guardrails", message)


class PrivacyPipelineBlockedError(Exception):
    """Raised when guardrails block content."""

    def __init__(self, stage: str, reason: str, blocked_by: str | None = None):
        self.stage = stage
        self.reason = reason
        self.blocked_by = blocked_by
        super().__init__(f"Blocked at {stage}: {reason}")
