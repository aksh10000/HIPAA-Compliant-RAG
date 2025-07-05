from pydantic import BaseModel
from datetime import date, datetime
from typing import List, Optional

# --- Medical Record Schemas ---
class MedicalRecordBase(BaseModel):
    record_content: str

class MedicalRecordCreate(MedicalRecordBase):
    """
    Used to validate the body of a `POST /records/` request
    """
    patient_id: int

class MedicalRecordInDB(MedicalRecordBase):
    """
    Used validate the response fields in API
    """
    id: int
    patient_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- Patient Schemas ---
class PatientBase(BaseModel):
    full_name: str
    date_of_birth: date

class PatientInDB(PatientBase):
    id: int
    records: List[MedicalRecordInDB] = []

    class Config:
        #allows Pydantic to access attributes with `record.id` instead of `record['id']`
        from_attributes = True
# --- Search Schemas ---
class PatientMedicalRecordSearchResult(BaseModel):
    """
    Detailed search result for a specific patient.
    This is NOT anonymized and should only be returned after authorization.
    """
    record_id: int
    patient_id: int
    record_content: str
    created_at: datetime
    relevance_score: float
class AnonymizedMedicalRecordSearchResult(BaseModel):
    """
    HIPAA-compliant search result.
    Removes direct patient identifiers like name and DOB.
    """
    record_id: int
    patient_identifier: str = "[REDACTED]"
    record_content: str
    created_at: datetime
    relevance_score: float