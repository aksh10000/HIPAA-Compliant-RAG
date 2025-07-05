import os
import sys
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from datetime import date

# # Add app directory to path to import modules
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

from app.database import SessionLocal, engine
from app.models import Base, Patient, MedicalRecord
from app.rag_system import RAGSystem
from app.crud import create_patient, create_medical_record

load_dotenv()

print("Setting up databases and populating with mock data...")

# Initialize RAG system (this will also clear any old ChromaDB data)
rag_system = RAGSystem(recreate_collection=True)
db: Session = SessionLocal()

# Create SQL tables
Base.metadata.create_all(bind=engine)

# --- Mock Data ---

patients_data = [
    {"full_name": "John Doe", "date_of_birth": date(1985, 1, 15)},
    {"full_name": "Jane Smith", "date_of_birth": date(1992, 7, 22)},
]

records_data = {
    "John Doe": [
        "Patient with a dry cough and fever for three days. Denies shortness of breath. Physical exam reveals clear lung sounds. Suspected viral bronchitis. Recommended rest and hydration.",
        "Patient is suffering from hypertension. Blood pressure is 140/90 mmHg. Patient reports good adherence to medication. Discussed importance of low-sodium diet and regular exercise. Will re-evaluate in 3 months.",
        "Complains of seasonal allergy symptoms including sneezing, itchy eyes, and nasal congestion. Prescribed Loratadine 10mg daily."
    ],
    "Jane Smith": [
        "Patient reports a severe, throbbing headache on the left side, accompanied by nausea and sensitivity to light. Symptoms are consistent with a migraine attack. Administered sumatriptan, which provided relief.",
        "Annual physical exam. All vitals are stable. Blood work is normal. Patient is in good health. Discussed preventive care and maintaining a healthy lifestyle.",
    ]
}

# --- Population Logic ---

try:
    print("Populating Patients...")
    for patient_data in patients_data:
        create_patient(db, patient_data)

    print("Populating Medical Records and Vector DB...")
    for patient_name, records in records_data.items():
        # Find patient in DB
        patient = db.query(Patient).filter(Patient.full_name == patient_name).first()
        if not patient:
            continue
        
        for record_content in records:
            # 1. Create record in SQL DB
            db_record = create_medical_record(db, record_content, patient.id)
            db.flush() # Ensure the record gets an ID
            
            # 2. Add record to RAG system (Vector DB)
            rag_system.add_record(
                record_content=db_record.record_content,
                record_id=db_record.id,
                patient_id=patient.id # Also include the fix from the previous step
            )
            print(f"  - Added record {db_record.id} for {patient.full_name}")

    db.commit()
    print("\nDatabase population complete!")
    print(f"Total documents in Vector DB: {rag_system.collection.count()}")

except Exception as e:
    db.rollback()
    print(f"An error occurred: {e}")
finally:
    db.close()