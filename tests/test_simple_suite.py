import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys
from datetime import date

# Add the parent directory to the path to allow importing from 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.database import Base, get_db
from app.config import settings
from app.models import Patient, MedicalRecord

# --- Test Database Setup ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_temp.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    test_patient = Patient(id=2, full_name="Simple Patient", date_of_birth=date(1985, 1, 1))
    db.add(test_patient)
    db.commit()
    db.refresh(test_patient)
    test_record = MedicalRecord(
        id=202,
        patient_id=2,
        record_content="Patient has mild fever and cough."
    )
    db.add(test_record)
    db.commit()
    db.refresh(test_record)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)
VALID_API_KEY_HEADER = {"X-API-KEY": settings.valid_api_key}
INVALID_API_KEY_HEADER = {"X-API-KEY": "invalid-key"}

# 1. Health check endpoint
def test_health_check_simple():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

# 2. Unauthorized access
def test_unauthorized_access_simple():
    response = client.get("/api/v1/search/?q=test", headers=INVALID_API_KEY_HEADER)
    assert response.status_code == 403
    assert "Could not validate credentials" in response.json()["detail"]

# 3. Create a new medical record
def test_create_medical_record():
    payload = {"patient_id": 2, "record_content": "Patient reports chest pain."}
    response = client.post("/api/v1/records/", json=payload, headers=VALID_API_KEY_HEADER)
    assert response.status_code == 201
    data = response.json()
    assert data["patient_id"] == 2
    assert "chest pain" in data["record_content"]

# 4. Search for a record (authorized)
def test_search_medical_records():
    response = client.get("/api/v1/search/?q=fever&patient_id=2", headers=VALID_API_KEY_HEADER)
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    assert any("fever" in r["record_content"] for r in results)

# 5. Patient not found on record creation
def test_create_record_patient_not_found():
    payload = {"patient_id": 999, "record_content": "Unknown patient."}
    response = client.post("/api/v1/records/", json=payload, headers=VALID_API_KEY_HEADER)
    assert response.status_code == 404
    assert "Patient not found" in response.json()["detail"] 