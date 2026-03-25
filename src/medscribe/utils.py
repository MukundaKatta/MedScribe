"""Medical regex patterns and section detection helpers.

This module provides curated regular expression patterns for extracting
structured information from unstructured clinical notes. All patterns are
designed for common US-format clinical documentation.

Disclaimer: For research and educational purposes only. Not for clinical use.
"""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Section header patterns
# ---------------------------------------------------------------------------

SECTION_PATTERNS: dict[str, re.Pattern[str]] = {
    "chief_complaint": re.compile(
        r"(?:chief\s+complaint|cc|reason\s+for\s+visit)\s*[:\-]\s*(.+?)(?=\n\n|\n[A-Z]|\Z)",
        re.IGNORECASE | re.DOTALL,
    ),
    "hpi": re.compile(
        r"(?:history\s+of\s+present\s+illness|hpi)\s*[:\-]?\s*\n?(.+?)(?=\n\s*(?:vitals|medications|assessment|plan|review\s+of\s+systems|physical\s+exam|past\s+medical)|$)",
        re.IGNORECASE | re.DOTALL,
    ),
    "vitals": re.compile(
        r"(?:vital\s+signs?|vitals)\s*[:\-]?\s*\n?(.+?)(?=\n\s*(?:medications|assessment|plan|physical\s+exam|review\s+of\s+systems|history)|$)",
        re.IGNORECASE | re.DOTALL,
    ),
    "medications": re.compile(
        r"(?:medications?|current\s+medications?|med(?:s)?)\s*[:\-]?\s*\n?(.+?)(?=\n\s*(?:assessment|plan|vitals|allergies|physical\s+exam|review)|$)",
        re.IGNORECASE | re.DOTALL,
    ),
    "assessment": re.compile(
        r"(?:assessment|impression|diagnosis|diagnoses)\s*[:\-]?\s*\n?(.+?)(?=\n\s*(?:plan|recommendations|disposition)|$)",
        re.IGNORECASE | re.DOTALL,
    ),
    "plan": re.compile(
        r"(?:plan|recommendations|disposition)\s*[:\-]?\s*\n?(.+?)(?=\n\s*(?:follow[\s-]?up|signature|attending|$)|\Z)",
        re.IGNORECASE | re.DOTALL,
    ),
}

# ---------------------------------------------------------------------------
# Medication patterns
# ---------------------------------------------------------------------------

# Common medication names (non-exhaustive, expandable list)
COMMON_MEDICATIONS: list[str] = [
    "Aspirin", "Lisinopril", "Atorvastatin", "Metformin", "Amlodipine",
    "Metoprolol", "Omeprazole", "Losartan", "Albuterol", "Gabapentin",
    "Hydrochlorothiazide", "Sertraline", "Simvastatin", "Levothyroxine",
    "Acetaminophen", "Ibuprofen", "Prednisone", "Furosemide", "Warfarin",
    "Clopidogrel", "Pantoprazole", "Amoxicillin", "Azithromycin",
    "Ciprofloxacin", "Doxycycline", "Insulin", "Heparin", "Enoxaparin",
    "Morphine", "Hydrocodone", "Oxycodone", "Tramadol", "Diazepam",
    "Lorazepam", "Alprazolam", "Fluticasone", "Montelukast", "Carvedilol",
    "Spironolactone", "Cephalexin", "Tamsulosin", "Finasteride",
    "Rosuvastatin", "Pravastatin", "Escitalopram", "Duloxetine",
    "Venlafaxine", "Bupropion", "Trazodone", "Quetiapine", "Risperidone",
    "Lithium", "Valproic Acid", "Phenytoin", "Levetiracetam", "Digoxin",
    "Diltiazem", "Verapamil", "Nitroglycerin", "Clopidogrel",
]

_med_names_pattern = "|".join(re.escape(m) for m in COMMON_MEDICATIONS)

MEDICATION_PATTERN: re.Pattern[str] = re.compile(
    rf"(?P<name>{_med_names_pattern})"
    r"\s*(?P<dose>\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|units?|iu))"
    r"(?:\s*(?P<route>po|iv|im|sq|subq|oral|topical))?"
    r"(?:\s*(?P<frequency>(?:once|twice|three\s+times|four\s+times)?\s*(?:daily|bid|tid|qid|prn|q\d+h?|nightly|at\s+bedtime|qhs|every\s+\d+\s+hours?|as\s+needed)))?",
    re.IGNORECASE,
)

# Fallback: capture lines that look like medication entries (e.g., "- Aspirin 81mg daily")
MEDICATION_LINE_PATTERN: re.Pattern[str] = re.compile(
    r"[-•*]\s*(?P<name>[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"
    r"\s+(?P<dose>\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|units?|iu))"
    r"(?:\s+(?P<frequency>\S+(?:\s+\S+)?))?",
    re.MULTILINE,
)

# ---------------------------------------------------------------------------
# Vital sign patterns
# ---------------------------------------------------------------------------

VITAL_PATTERNS: dict[str, re.Pattern[str]] = {
    "bp": re.compile(
        r"(?:bp|blood\s+pressure)\s*[:\s]*(\d{2,3}\s*/\s*\d{2,3})",
        re.IGNORECASE,
    ),
    "hr": re.compile(
        r"(?:hr|heart\s+rate|pulse)\s*[:\s]*(\d{2,3})\s*(?:bpm)?",
        re.IGNORECASE,
    ),
    "temp": re.compile(
        r"(?:temp|temperature)\s*[:\s]*(\d{2,3}(?:\.\d{1,2})?)\s*(?:°?\s*[FCfc])?",
        re.IGNORECASE,
    ),
    "rr": re.compile(
        r"(?:rr|resp(?:iratory)?\s*rate)\s*[:\s]*(\d{1,2})",
        re.IGNORECASE,
    ),
    "spo2": re.compile(
        r"(?:spo2|sp02|o2\s*sat|oxygen\s+saturation)\s*[:\s]*(\d{2,3})\s*%?",
        re.IGNORECASE,
    ),
}

# ---------------------------------------------------------------------------
# Diagnosis / ICD-like patterns
# ---------------------------------------------------------------------------

DIAGNOSIS_PATTERNS: list[re.Pattern[str]] = [
    # Numbered list items commonly found in Assessment sections
    re.compile(r"^\s*\d+[.)]\s*(.+?)$", re.MULTILINE),
    # ICD-10-like codes (e.g., I10, E11.9, J18.1)
    re.compile(r"\b([A-Z]\d{2}(?:\.\d{1,2})?)\b"),
    # Dash/bullet items
    re.compile(r"^\s*[-•]\s*(.+?)$", re.MULTILINE),
]

# Common clinical condition keywords for heuristic extraction
CLINICAL_CONDITIONS: list[str] = [
    "hypertension", "diabetes", "mellitus", "hyperlipidemia", "obesity",
    "asthma", "copd", "pneumonia", "bronchitis", "heart failure",
    "atrial fibrillation", "coronary artery disease", "myocardial infarction",
    "stroke", "dvt", "pulmonary embolism", "anemia", "ckd",
    "chronic kidney disease", "hepatitis", "cirrhosis", "gerd",
    "gastritis", "pancreatitis", "appendicitis", "cholecystitis",
    "urinary tract infection", "uti", "cellulitis", "sepsis",
    "acute coronary syndrome", "acs", "chest pain", "dyspnea",
    "syncope", "seizure", "migraine", "depression", "anxiety",
    "hypothyroidism", "hyperthyroidism", "osteoarthritis",
    "rheumatoid arthritis", "lupus", "cancer", "malignancy",
]

CONDITION_PATTERN: re.Pattern[str] = re.compile(
    r"\b(" + "|".join(re.escape(c) for c in CLINICAL_CONDITIONS) + r")\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# PHI (Protected Health Information) patterns for anonymization
# ---------------------------------------------------------------------------

PHI_PATTERNS: dict[str, re.Pattern[str]] = {
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "mrn": re.compile(r"(?:MRN|Medical\s+Record\s+(?:Number|No\.?))\s*[:#]?\s*(\d{6,12})", re.IGNORECASE),
    "mrn_standalone": re.compile(r"\bMRN\s*[:\s]\s*(\d{6,12})\b", re.IGNORECASE),
    "date": re.compile(
        r"\b(?:0?[1-9]|1[0-2])[/\-](?:0?[1-9]|[12]\d|3[01])[/\-](?:19|20)\d{2}\b"
    ),
    "phone": re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "email": re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
    "patient_name": re.compile(
        r"(?:patient|pt|name)\s*[:\s]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
        re.IGNORECASE,
    ),
    "dob": re.compile(
        r"(?:DOB|Date\s+of\s+Birth)\s*[:\s]\s*((?:0?[1-9]|1[0-2])[/\-](?:0?[1-9]|[12]\d|3[01])[/\-](?:19|20)\d{2})",
        re.IGNORECASE,
    ),
}

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def clean_section_text(text: str) -> str:
    """Clean extracted section text by stripping whitespace and normalizing newlines."""
    text = text.strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def detect_note_type(text: str) -> str:
    """Heuristically determine the type of clinical note.

    Returns one of: 'progress_note', 'discharge_summary', 'consultation',
    'emergency', 'operative', 'unknown'.
    """
    lower = text.lower()
    if any(kw in lower for kw in ["discharge summary", "discharge instructions", "discharged to"]):
        return "discharge_summary"
    if any(kw in lower for kw in ["consultation", "consult note", "consulting"]):
        return "consultation"
    if any(kw in lower for kw in ["emergency department", "ed note", "triage"]):
        return "emergency"
    if any(kw in lower for kw in ["operative note", "operative report", "procedure note"]):
        return "operative"
    if any(kw in lower for kw in ["progress note", "soap note", "daily note"]):
        return "progress_note"
    return "progress_note"  # default


def extract_list_items(text: str) -> list[str]:
    """Extract bulleted or numbered list items from a block of text."""
    items: list[str] = []
    for line in text.strip().splitlines():
        line = line.strip()
        # Match numbered (1. or 1)) or bulleted (-, *, •) items
        match = re.match(r"^(?:\d+[.)]\s*|[-•*]\s+)(.+)$", line)
        if match:
            items.append(match.group(1).strip())
        elif line and not items:
            # If no list formatting, treat non-empty lines as items
            items.append(line)
    return items


def normalize_medication_name(name: str) -> str:
    """Normalize medication name to title case."""
    return name.strip().title()


def validate_note_length(text: str, max_length: int = 10000) -> bool:
    """Check if a clinical note is within acceptable length bounds."""
    return 0 < len(text) <= max_length
