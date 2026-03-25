"""Core MedScribe engine for clinical note processing.

Provides regex-based NLP utilities for parsing, extracting, summarizing,
and anonymizing unstructured clinical/medical notes.

Disclaimer: This software is for research and educational purposes only.
It is NOT validated for clinical use and must NOT be used for medical decisions.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from pydantic import BaseModel, Field

from medscribe.config import MedScribeConfig
from medscribe.utils import (
    CLINICAL_CONDITIONS,
    CONDITION_PATTERN,
    DIAGNOSIS_PATTERNS,
    MEDICATION_LINE_PATTERN,
    MEDICATION_PATTERN,
    PHI_PATTERNS,
    SECTION_PATTERNS,
    VITAL_PATTERNS,
    clean_section_text,
    detect_note_type,
    extract_list_items,
    validate_note_length,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic models for structured output
# ---------------------------------------------------------------------------


class Medication(BaseModel):
    """A single extracted medication entry."""

    name: str
    dose: str = ""
    frequency: str = ""
    route: str = ""


class VitalSigns(BaseModel):
    """Extracted vital signs from a clinical note."""

    bp: str = ""
    hr: str = ""
    temp: str = ""
    rr: str = ""
    spo2: str = ""


class Diagnosis(BaseModel):
    """A single extracted diagnosis or clinical condition."""

    text: str
    icd_code: str = ""


class ClinicalSummary(BaseModel):
    """Structured summary produced from an unstructured clinical note."""

    note_type: str = "progress_note"
    chief_complaint: str = ""
    hpi: str = ""
    vitals: VitalSigns = Field(default_factory=VitalSigns)
    medications: list[Medication] = Field(default_factory=list)
    diagnoses: list[Diagnosis] = Field(default_factory=list)
    assessment: str = ""
    plan: str = ""
    raw_sections: dict[str, str] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------


class MedScribe:
    """Developer-friendly clinical NLP toolkit.

    Instantiate with an optional ``MedScribeConfig`` to customise behaviour,
    then call any of the public methods on raw clinical note text.

    Example::

        ms = MedScribe()
        summary = ms.summarize(note_text)
    """

    def __init__(self, config: MedScribeConfig | None = None) -> None:
        self.config = config or MedScribeConfig()
        logging.basicConfig(level=self.config.log_level)
        logger.debug("MedScribe initialised with config: %s", self.config)

    # ------------------------------------------------------------------
    # Section parsing
    # ------------------------------------------------------------------

    def parse_note(self, text: str) -> dict[str, str]:
        """Parse a clinical note into labelled sections.

        Attempts to match common section headers (Chief Complaint, HPI,
        Vitals, Medications, Assessment, Plan) and returns a mapping of
        ``section_name -> section_text``.

        Args:
            text: Raw clinical note as a string.

        Returns:
            Dictionary of detected sections with cleaned text.
        """
        self._validate(text)
        sections: dict[str, str] = {}
        for name, pattern in SECTION_PATTERNS.items():
            match = pattern.search(text)
            if match:
                sections[name] = clean_section_text(match.group(1))
        logger.info("Parsed %d sections from note.", len(sections))
        return sections

    # ------------------------------------------------------------------
    # Medication extraction
    # ------------------------------------------------------------------

    def extract_medications(self, text: str) -> list[dict[str, str]]:
        """Extract medication names, dosages, routes, and frequencies.

        Uses both a curated medication-name list with structured regex and a
        fallback line-based pattern for bullet-style medication lists.

        Args:
            text: Raw clinical note or medication section text.

        Returns:
            List of dicts with keys ``name``, ``dose``, ``frequency``, ``route``.
        """
        self._validate(text)
        results: list[dict[str, str]] = []
        seen: set[str] = set()

        # Primary: structured pattern
        for m in MEDICATION_PATTERN.finditer(text):
            name = m.group("name").strip().title()
            if name.lower() not in seen:
                seen.add(name.lower())
                results.append(
                    {
                        "name": name,
                        "dose": (m.group("dose") or "").strip(),
                        "frequency": (m.group("frequency") or "").strip(),
                        "route": (m.group("route") or "").strip(),
                    }
                )

        # Fallback: line-based extraction
        for m in MEDICATION_LINE_PATTERN.finditer(text):
            name = m.group("name").strip().title()
            if name.lower() not in seen:
                seen.add(name.lower())
                results.append(
                    {
                        "name": name,
                        "dose": (m.group("dose") or "").strip(),
                        "frequency": (m.group("frequency") or "").strip(),
                        "route": "",
                    }
                )

        logger.info("Extracted %d medications.", len(results))
        return results

    # ------------------------------------------------------------------
    # Vitals extraction
    # ------------------------------------------------------------------

    def extract_vitals(self, text: str) -> dict[str, str]:
        """Extract vital signs from free text.

        Looks for blood pressure, heart rate, temperature, respiratory rate,
        and SpO2 values using regex patterns.

        Args:
            text: Raw clinical note or vitals section text.

        Returns:
            Dictionary with keys ``bp``, ``hr``, ``temp``, ``rr``, ``spo2``.
            Missing values are empty strings.
        """
        self._validate(text)
        vitals: dict[str, str] = {}
        for name, pattern in VITAL_PATTERNS.items():
            match = pattern.search(text)
            vitals[name] = match.group(1).strip() if match else ""
        logger.info("Extracted vitals: %s", vitals)
        return vitals

    # ------------------------------------------------------------------
    # Diagnosis extraction
    # ------------------------------------------------------------------

    def extract_diagnoses(self, text: str) -> list[dict[str, str]]:
        """Extract diagnoses and ICD-like codes from clinical text.

        Combines numbered/bulleted list extraction from the Assessment section
        with heuristic keyword matching for known clinical conditions and
        ICD-10-style codes.

        Args:
            text: Raw clinical note or assessment section text.

        Returns:
            List of dicts with keys ``text`` and ``icd_code``.
        """
        self._validate(text)
        diagnoses: list[dict[str, str]] = []
        seen: set[str] = set()

        # Try to isolate the assessment section first
        sections = self.parse_note(text)
        assessment_text = sections.get("assessment", text)

        # Extract list items from assessment
        items = extract_list_items(assessment_text)
        for item in items:
            key = item.lower().strip()
            if key and key not in seen:
                seen.add(key)
                # Check for embedded ICD code
                icd_match = re.search(r"\b([A-Z]\d{2}(?:\.\d{1,2})?)\b", item)
                diagnoses.append(
                    {
                        "text": item.strip(),
                        "icd_code": icd_match.group(1) if icd_match else "",
                    }
                )

        # Also scan for known clinical condition keywords
        for m in CONDITION_PATTERN.finditer(text):
            condition = m.group(1).lower().strip()
            if condition not in seen:
                seen.add(condition)
                diagnoses.append({"text": condition.title(), "icd_code": ""})

        logger.info("Extracted %d diagnoses.", len(diagnoses))
        return diagnoses

    # ------------------------------------------------------------------
    # Summarisation
    # ------------------------------------------------------------------

    def summarize(self, note: str) -> ClinicalSummary:
        """Create a structured summary from an unstructured clinical note.

        Orchestrates section parsing, medication extraction, vital sign
        extraction, and diagnosis extraction into a single
        ``ClinicalSummary`` model.

        Args:
            note: The full raw clinical note text.

        Returns:
            A ``ClinicalSummary`` pydantic model.
        """
        self._validate(note)

        sections = self.parse_note(note)
        meds_raw = self.extract_medications(note)
        vitals_raw = self.extract_vitals(note)
        diags_raw = self.extract_diagnoses(note)

        medications = [Medication(**m) for m in meds_raw]
        vitals = VitalSigns(**vitals_raw)
        diagnoses = [Diagnosis(**d) for d in diags_raw]

        note_type = detect_note_type(note)

        summary = ClinicalSummary(
            note_type=note_type,
            chief_complaint=sections.get("chief_complaint", ""),
            hpi=sections.get("hpi", ""),
            vitals=vitals,
            medications=medications,
            diagnoses=diagnoses,
            assessment=sections.get("assessment", ""),
            plan=sections.get("plan", ""),
            raw_sections=sections,
        )

        if self.config.anonymize_by_default:
            summary.chief_complaint = self.anonymize(summary.chief_complaint)
            summary.hpi = self.anonymize(summary.hpi)
            summary.assessment = self.anonymize(summary.assessment)
            summary.plan = self.anonymize(summary.plan)

        logger.info("Generated clinical summary (type=%s).", note_type)
        return summary

    # ------------------------------------------------------------------
    # PHI anonymisation
    # ------------------------------------------------------------------

    def anonymize(self, text: str) -> str:
        """Redact Protected Health Information (PHI) from text.

        Replaces detected names, dates, MRN numbers, SSNs, phone numbers,
        and email addresses with the configured redaction marker.

        Args:
            text: Clinical text potentially containing PHI.

        Returns:
            De-identified text with PHI replaced by redaction markers.
        """
        if not text:
            return text

        marker = self.config.redaction_marker
        result = text

        # Order matters — match specific labelled fields first, then generic patterns
        # DOB (labelled date)
        dob_pat = PHI_PATTERNS["dob"]
        result = dob_pat.sub(
            lambda m: m.group(0).replace(m.group(1), marker), result
        )

        # Patient name
        name_pat = PHI_PATTERNS["patient_name"]
        result = name_pat.sub(
            lambda m: m.group(0).replace(m.group(1), marker), result
        )

        # MRN (labelled)
        for key in ("mrn", "mrn_standalone"):
            mrn_pat = PHI_PATTERNS[key]
            result = mrn_pat.sub(
                lambda m: m.group(0).replace(m.group(1), marker), result
            )

        # SSN, phone, email, generic dates
        for key in ("ssn", "phone", "email", "date"):
            pat = PHI_PATTERNS[key]
            result = pat.sub(marker, result)

        logger.info("Anonymised text (%d chars).", len(result))
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _validate(self, text: str) -> None:
        """Validate input text against configured constraints."""
        if not isinstance(text, str):
            raise TypeError(f"Expected str, got {type(text).__name__}.")
        if not text.strip():
            raise ValueError("Input text must not be empty.")
        if not validate_note_length(text, self.config.max_note_length):
            raise ValueError(
                f"Note exceeds maximum length of {self.config.max_note_length} characters."
            )
