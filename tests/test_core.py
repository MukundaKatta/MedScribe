"""Tests for the MedScribe core engine.

Uses realistic sample clinical notes to verify section parsing,
medication extraction, vitals extraction, diagnosis extraction,
summarization, and PHI anonymization.
"""

from __future__ import annotations

import pytest

from medscribe import MedScribe, MedScribeConfig

# ---------------------------------------------------------------------------
# Sample clinical notes
# ---------------------------------------------------------------------------

SAMPLE_PROGRESS_NOTE = """\
Patient: John Smith
DOB: 03/15/1980
MRN: 123456789

Chief Complaint: Chest pain for 2 days.

History of Present Illness:
Mr. Smith is a 46-year-old male presenting with substernal chest pain
radiating to the left arm, onset 2 days ago. Pain is 7/10, worsened
with exertion. No prior cardiac history. He denies shortness of breath,
nausea, or diaphoresis.

Vitals: BP 142/90, HR 88, Temp 98.6F, RR 18, SpO2 97%

Medications:
- Aspirin 81mg daily
- Lisinopril 10mg daily
- Atorvastatin 40mg nightly

Assessment:
1. Acute chest pain, rule out ACS
2. Hypertension, uncontrolled

Plan:
- Obtain 12-lead ECG and serial troponins
- Start heparin drip per ACS protocol
- Cardiology consult
- Continue home medications
"""

SAMPLE_DISCHARGE_NOTE = """\
Discharge Summary

Patient: Jane Doe
DOB: 07/22/1955
MRN: 987654321
SSN: 123-45-6789
Phone: (555) 123-4567

Chief Complaint: Shortness of breath and lower extremity edema.

History of Present Illness:
Mrs. Doe is a 70-year-old female admitted for acute decompensated heart
failure. She reports progressive dyspnea on exertion over the past week
with 3-pillow orthopnea and bilateral lower extremity edema.

Vitals: BP 118/72, HR 102, Temp 97.8F, RR 24, SpO2 92%

Medications:
- Furosemide 40mg daily
- Carvedilol 12.5mg twice daily
- Lisinopril 20mg daily
- Spironolactone 25mg daily

Assessment:
1. Acute decompensated heart failure (I50.21)
2. Chronic kidney disease stage 3 (N18.3)
3. Atrial fibrillation

Plan:
- IV diuresis with furosemide
- Daily weights and strict I/O monitoring
- Echocardiogram
- Discharged to home with close follow-up
"""

SAMPLE_MINIMAL_NOTE = """\
Chief Complaint: Headache

Assessment:
Migraine without aura

Plan:
- Ibuprofen 400mg prn
- Follow up in 2 weeks
"""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def ms() -> MedScribe:
    return MedScribe()


@pytest.fixture
def ms_anon() -> MedScribe:
    config = MedScribeConfig(anonymize_by_default=True)
    return MedScribe(config=config)


# ---------------------------------------------------------------------------
# Section parsing tests
# ---------------------------------------------------------------------------


class TestSectionParsing:
    def test_parses_standard_sections(self, ms: MedScribe) -> None:
        sections = ms.parse_note(SAMPLE_PROGRESS_NOTE)
        assert "chief_complaint" in sections
        assert "hpi" in sections
        assert "assessment" in sections
        assert "plan" in sections

    def test_chief_complaint_content(self, ms: MedScribe) -> None:
        sections = ms.parse_note(SAMPLE_PROGRESS_NOTE)
        assert "chest pain" in sections["chief_complaint"].lower()

    def test_parses_discharge_note(self, ms: MedScribe) -> None:
        sections = ms.parse_note(SAMPLE_DISCHARGE_NOTE)
        assert "chief_complaint" in sections
        assert "shortness of breath" in sections["chief_complaint"].lower()

    def test_minimal_note(self, ms: MedScribe) -> None:
        sections = ms.parse_note(SAMPLE_MINIMAL_NOTE)
        assert "chief_complaint" in sections
        assert "headache" in sections["chief_complaint"].lower()


# ---------------------------------------------------------------------------
# Medication extraction tests
# ---------------------------------------------------------------------------


class TestMedicationExtraction:
    def test_extracts_medications_from_progress_note(self, ms: MedScribe) -> None:
        meds = ms.extract_medications(SAMPLE_PROGRESS_NOTE)
        med_names = [m["name"].lower() for m in meds]
        assert "aspirin" in med_names
        assert "lisinopril" in med_names
        assert "atorvastatin" in med_names

    def test_medication_dosages(self, ms: MedScribe) -> None:
        meds = ms.extract_medications(SAMPLE_PROGRESS_NOTE)
        aspirin = next(m for m in meds if m["name"].lower() == "aspirin")
        assert "81" in aspirin["dose"]
        assert "mg" in aspirin["dose"].lower()

    def test_extracts_medications_from_discharge_note(self, ms: MedScribe) -> None:
        meds = ms.extract_medications(SAMPLE_DISCHARGE_NOTE)
        med_names = [m["name"].lower() for m in meds]
        assert "furosemide" in med_names
        assert "carvedilol" in med_names

    def test_medication_frequency(self, ms: MedScribe) -> None:
        meds = ms.extract_medications(SAMPLE_PROGRESS_NOTE)
        aspirin = next(m for m in meds if m["name"].lower() == "aspirin")
        assert "daily" in aspirin["frequency"].lower()


# ---------------------------------------------------------------------------
# Vitals extraction tests
# ---------------------------------------------------------------------------


class TestVitalsExtraction:
    def test_extracts_all_vitals(self, ms: MedScribe) -> None:
        vitals = ms.extract_vitals(SAMPLE_PROGRESS_NOTE)
        assert vitals["bp"] == "142/90"
        assert vitals["hr"] == "88"
        assert vitals["temp"] == "98.6"
        assert vitals["rr"] == "18"
        assert vitals["spo2"] == "97"

    def test_discharge_vitals(self, ms: MedScribe) -> None:
        vitals = ms.extract_vitals(SAMPLE_DISCHARGE_NOTE)
        assert vitals["bp"] == "118/72"
        assert vitals["hr"] == "102"
        assert vitals["spo2"] == "92"


# ---------------------------------------------------------------------------
# Diagnosis extraction tests
# ---------------------------------------------------------------------------


class TestDiagnosisExtraction:
    def test_extracts_diagnoses(self, ms: MedScribe) -> None:
        diags = ms.extract_diagnoses(SAMPLE_PROGRESS_NOTE)
        diag_texts = [d["text"].lower() for d in diags]
        assert any("chest pain" in t for t in diag_texts)

    def test_extracts_icd_codes(self, ms: MedScribe) -> None:
        diags = ms.extract_diagnoses(SAMPLE_DISCHARGE_NOTE)
        icd_codes = [d["icd_code"] for d in diags if d["icd_code"]]
        assert "I50.21" in icd_codes or "N18.3" in icd_codes

    def test_extracts_clinical_conditions(self, ms: MedScribe) -> None:
        diags = ms.extract_diagnoses(SAMPLE_PROGRESS_NOTE)
        all_text = " ".join(d["text"].lower() for d in diags)
        assert "hypertension" in all_text


# ---------------------------------------------------------------------------
# Anonymization tests
# ---------------------------------------------------------------------------


class TestAnonymization:
    def test_redacts_patient_name(self, ms: MedScribe) -> None:
        result = ms.anonymize(SAMPLE_PROGRESS_NOTE)
        assert "John Smith" not in result
        assert "[REDACTED]" in result

    def test_redacts_mrn(self, ms: MedScribe) -> None:
        result = ms.anonymize(SAMPLE_PROGRESS_NOTE)
        assert "123456789" not in result

    def test_redacts_dob(self, ms: MedScribe) -> None:
        result = ms.anonymize(SAMPLE_PROGRESS_NOTE)
        assert "03/15/1980" not in result

    def test_redacts_ssn(self, ms: MedScribe) -> None:
        result = ms.anonymize(SAMPLE_DISCHARGE_NOTE)
        assert "123-45-6789" not in result

    def test_redacts_phone(self, ms: MedScribe) -> None:
        result = ms.anonymize(SAMPLE_DISCHARGE_NOTE)
        assert "(555) 123-4567" not in result

    def test_custom_redaction_marker(self) -> None:
        config = MedScribeConfig(redaction_marker="***")
        ms = MedScribe(config=config)
        result = ms.anonymize(SAMPLE_PROGRESS_NOTE)
        assert "John Smith" not in result
        assert "***" in result


# ---------------------------------------------------------------------------
# Summarization tests
# ---------------------------------------------------------------------------


class TestSummarization:
    def test_produces_clinical_summary(self, ms: MedScribe) -> None:
        summary = ms.summarize(SAMPLE_PROGRESS_NOTE)
        assert summary.note_type == "progress_note"
        assert "chest pain" in summary.chief_complaint.lower()
        assert len(summary.medications) >= 3
        assert summary.vitals.bp == "142/90"

    def test_discharge_summary_type(self, ms: MedScribe) -> None:
        summary = ms.summarize(SAMPLE_DISCHARGE_NOTE)
        assert summary.note_type == "discharge_summary"

    def test_anonymize_by_default(self, ms_anon: MedScribe) -> None:
        summary = ms_anon.summarize(SAMPLE_PROGRESS_NOTE)
        # HPI should have names redacted
        assert "Smith" not in summary.hpi


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------


class TestValidation:
    def test_rejects_empty_text(self, ms: MedScribe) -> None:
        with pytest.raises(ValueError, match="empty"):
            ms.parse_note("")

    def test_rejects_non_string(self, ms: MedScribe) -> None:
        with pytest.raises(TypeError, match="str"):
            ms.parse_note(12345)  # type: ignore[arg-type]

    def test_rejects_oversized_note(self) -> None:
        config = MedScribeConfig(max_note_length=50)
        ms = MedScribe(config=config)
        with pytest.raises(ValueError, match="exceeds"):
            ms.parse_note("A" * 100)
