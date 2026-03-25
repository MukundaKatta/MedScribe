"""Configuration management for MedScribe.

Loads settings from environment variables with sensible defaults.

Disclaimer: For research and educational purposes only. Not for clinical use.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class MedScribeConfig:
    """Configuration for the MedScribe pipeline.

    Attributes:
        log_level: Logging verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        max_note_length: Maximum allowed character length for a clinical note.
        anonymize_by_default: Whether to auto-anonymize PHI during summarization.
        redaction_marker: The string used to replace PHI tokens.
        extract_icd_codes: Whether to look for ICD-10-style codes in diagnoses.
        section_separator: Regex-friendly separator between major note sections.
    """

    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    max_note_length: int = field(
        default_factory=lambda: int(os.getenv("MAX_NOTE_LENGTH", "10000"))
    )
    anonymize_by_default: bool = False
    redaction_marker: str = "[REDACTED]"
    extract_icd_codes: bool = True
    section_separator: str = r"\n\s*\n"

    def __post_init__(self) -> None:
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.log_level.upper() not in valid_levels:
            raise ValueError(
                f"Invalid log_level '{self.log_level}'. Must be one of {valid_levels}."
            )
        self.log_level = self.log_level.upper()

        if self.max_note_length <= 0:
            raise ValueError("max_note_length must be a positive integer.")
