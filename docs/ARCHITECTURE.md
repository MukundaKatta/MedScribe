# MedScribe Architecture

> **Disclaimer:** MedScribe is for research and educational purposes only. Not for clinical use.

## Overview

MedScribe is a regex-based clinical NLP toolkit designed to be lightweight, dependency-minimal, and developer-friendly. It processes unstructured clinical notes into structured data without requiring ML models or GPU resources.

## Design Principles

1. **No ML Dependencies** — All text processing uses curated regex patterns and heuristic rules. This keeps the library lightweight and deterministic.
2. **Pydantic-First** — Structured outputs use Pydantic v2 models for validation, serialization, and IDE support.
3. **Modular Extraction** — Each extraction capability (medications, vitals, diagnoses, PHI) is independently usable.
4. **Configurable** — Behavior is controlled via `MedScribeConfig`, with environment variable support.

## Module Structure

```
src/medscribe/
├── __init__.py    # Public API surface
├── core.py        # MedScribe class — orchestration & extraction logic
├── config.py      # MedScribeConfig dataclass
└── utils.py       # Regex patterns, constants, helper functions
```

### `core.py` — The Engine

The `MedScribe` class is the primary entry point. It provides six public methods:

| Method | Input | Output | Description |
|--------|-------|--------|-------------|
| `parse_note(text)` | Raw note | `dict[str, str]` | Split note into labelled sections |
| `extract_medications(text)` | Raw note | `list[dict]` | Find medication names, doses, frequencies |
| `extract_vitals(text)` | Raw note | `dict[str, str]` | Extract BP, HR, Temp, RR, SpO2 |
| `extract_diagnoses(text)` | Raw note | `list[dict]` | Extract diagnoses and ICD codes |
| `summarize(note)` | Raw note | `ClinicalSummary` | Full structured summary |
| `anonymize(text)` | Any text | `str` | Redact PHI (names, dates, MRN, SSN, etc.) |

### `utils.py` — Pattern Library

Contains all regex patterns organized by category:

- **Section Patterns** — Detect clinical note section headers (Chief Complaint, HPI, Assessment, Plan, etc.)
- **Medication Patterns** — Match ~60 common medication names with dose/frequency capture groups
- **Vital Sign Patterns** — Extract BP, HR, Temp, RR, SpO2 from various formats
- **Diagnosis Patterns** — Numbered lists, ICD-10 codes, clinical condition keywords
- **PHI Patterns** — SSN, MRN, dates, phone numbers, emails, patient names

### `config.py` — Configuration

`MedScribeConfig` is a Python dataclass that reads from environment variables with sensible defaults:

| Setting | Default | Description |
|---------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `MAX_NOTE_LENGTH` | `10000` | Max input character length |
| `anonymize_by_default` | `False` | Auto-anonymize during summarization |
| `redaction_marker` | `[REDACTED]` | PHI replacement string |
| `extract_icd_codes` | `True` | Look for ICD-10 codes |

## Data Flow

```
Raw Clinical Note (str)
        │
        ▼
┌─────────────────────┐
│   Input Validation   │  ← MedScribeConfig (max length, etc.)
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│   Section Parsing    │  ← SECTION_PATTERNS from utils.py
│   (parse_note)       │
└─────────────────────┘
        │
        ├──────────────────┬──────────────────┬──────────────────┐
        ▼                  ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Medications │  │    Vitals    │  │  Diagnoses   │  │  Anonymizer  │
│  Extractor   │  │  Extractor   │  │  Extractor   │  │  (optional)  │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
        │                  │                  │                  │
        └──────────────────┴──────────────────┴──────────────────┘
                                    │
                                    ▼
                          ┌──────────────────┐
                          │ ClinicalSummary  │  ← Pydantic model
                          │  (structured)    │
                          └──────────────────┘
```

## Testing Strategy

Tests use realistic sample clinical notes (progress notes, discharge summaries) to verify:

- Section detection accuracy
- Medication name and dosage extraction
- Vital sign parsing across formats
- Diagnosis and ICD code extraction
- PHI redaction completeness
- Input validation and error handling

## Limitations

- **English only** — Patterns are designed for US clinical documentation conventions
- **No semantic understanding** — Regex cannot resolve ambiguity or context
- **Pattern coverage** — The medication list (~60 drugs) and condition list are non-exhaustive
- **Not HIPAA-certified** — The anonymizer is best-effort and should not be relied upon for HIPAA compliance

## Future Directions

- Expand medication and condition pattern libraries
- Add support for SNOMED CT code extraction
- Pluggable pattern modules for specialty-specific notes (radiology, pathology)
- Optional spaCy integration for named entity recognition
