"""MedScribe — A developer-friendly Python toolkit for clinical NLP.

Process, summarize, and structure clinical/medical notes using regex-based
NLP. No GPU or ML models required.

Disclaimer: This software is for research and educational purposes only.
It is NOT validated for clinical use and must NOT be used for medical decisions.

Example::

    from medscribe import MedScribe

    ms = MedScribe()
    summary = ms.summarize(clinical_note_text)

Built by Officethree Technologies.
"""

from __future__ import annotations

from medscribe.config import MedScribeConfig
from medscribe.core import (
    ClinicalSummary,
    Diagnosis,
    MedScribe,
    Medication,
    VitalSigns,
)

__all__ = [
    "MedScribe",
    "MedScribeConfig",
    "ClinicalSummary",
    "Medication",
    "VitalSigns",
    "Diagnosis",
]

__version__ = "0.1.0"
