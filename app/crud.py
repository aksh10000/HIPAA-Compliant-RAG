from sqlalchemy.orm import Session
from . import models, schemas

# --- Patient CRUD ---
def get_patient(db: Session, patient_id: int):
    return db.query(models.Patient).filter(models.Patient.id == patient_id).first()

def create_patient(db: Session, patient_data: dict):
    db_patient = models.Patient(**patient_data)
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

# --- Medical Record CRUD ---
def get_medical_record(db: Session, record_id: int):
    return db.query(models.MedicalRecord).filter(models.MedicalRecord.id == record_id).first()
    
def get_records_by_ids(db: Session, record_ids: list[int]):
    return db.query(models.MedicalRecord).filter(models.MedicalRecord.id.in_(record_ids)).all()

def create_medical_record(db: Session, record_content: str, patient_id: int):
    db_record = models.MedicalRecord(record_content=record_content, patient_id=patient_id)
    db.add(db_record)
    return db_record