"""Custom exception hierarchy for OpenTrace."""

from __future__ import annotations


class OpenTraceError(Exception):
    """Base exception for all OpenTrace errors."""


class ValidationError(OpenTraceError):
    """Invalid input data."""


class ModuleError(OpenTraceError):
    """Error within an OSINT module."""

    def __init__(self, message: str, module_id: str) -> None:
        super().__init__(message)
        self.module_id = module_id


class StorageError(OpenTraceError):
    """Error in the storage layer."""


class ExportError(OpenTraceError):
    """Error generating a report export."""


class InvestigationNotFoundError(OpenTraceError):
    """Requested investigation does not exist."""

    def __init__(self, investigation_id: str) -> None:
        super().__init__(f"Investigation not found: {investigation_id}")
        self.investigation_id = investigation_id


class InvestigationTimeoutError(OpenTraceError):
    """Investigation exceeded its maximum runtime."""
