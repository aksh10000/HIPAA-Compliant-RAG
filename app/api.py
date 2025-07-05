from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Union, Optional

from . import crud, schemas, security, rag_system
from .database import get_db

router = APIRouter(
    prefix="/api/v1",
    tags=["Medical Records"],
    dependencies=[Depends(security.get_api_key)]
)

@router.post("/records/", response_model=schemas.MedicalRecordInDB, status_code=status.HTTP_201_CREATED)
def create_new_medical_record(
    record: schemas.MedicalRecordCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(security.get_api_key)
):
    """
    Create a new medical record for a patient.
    - Validates patient existence.
    - (Mocks) Authorization check.
    - Saves record to SQL database.
    - Adds record to Vector DB for semantic search.
    """
    # 1. Check if patient exists
    db_patient = crud.get_patient(db, patient_id=record.patient_id)
    if not db_patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # 2. Placeholder Authorization check
    if not security.check_permissions(api_key, record.patient_id):
        raise HTTPException(status_code=403, detail="Not authorized to access this patient's records")

    try:
        # 3. Create record in SQL DB
        db_record = crud.create_medical_record(
            db=db, record_content=record.record_content, patient_id=record.patient_id
        )
        db.flush() # To assign an ID to db_record

        # 4. Add record to RAG system
        rag_system.rag_system.add_record(
            record_content=db_record.record_content,
            record_id=db_record.id,
            patient_id=record.patient_id  # Pass the patient_id
        )
        
        # 5. Commit transaction
        db.commit()
        db.refresh(db_record)
        return db_record

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An internal error occurred: {str(e)}"
        )

@router.get(
    "/search/",
    response_model=Union[List[schemas.PatientMedicalRecordSearchResult], List[schemas.AnonymizedMedicalRecordSearchResult]],
    summary="Search and Rerank medical records"
)
def search_medical_records(
    q: str,
    patient_id: Optional[int] = None,
    db: Session = Depends(get_db),
    api_key: str = Depends(security.get_api_key)
):
    """
    HIPAA-compliant semantic search with a reranking step.

    1. Retrieves initial candidates from the vector database.
    2. Uses a powerful reranker model to improve the relevance of the final results.
    There are 2 types of search results:
    1. Patient-specific search: Returns records for a specific patient(could be used by a doctor to search for a patient's records).
    2. Global search: Returns records for all patients.(for global search, we need to anonymize individual patient records)
    """
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' cannot be empty.")

    # 1. Initial Retrieval from Vector DB
    search_results = rag_system.rag_system.search(query=q, top_k=10, patient_id=patient_id) # Retrieve more (e.g., 10) for the reranker
    if not search_results:
        return []

    record_ids = [res["record_id"] for res in search_results]
    
    # 2. Retrieve full records from SQL
    db_records = crud.get_records_by_ids(db=db, record_ids=record_ids)

    # 3. Rerank the retrieved records for better clinical relevance
    reranked_results = rag_system.rag_system.rerank(query=q, db_records=db_records)

    # 4. Format the final response based on the reranked list
    if patient_id is not None:
        # Authorization Check
        if not security.check_permissions(api_key, patient_id):
            raise HTTPException(status_code=403, detail="Not authorized to access this patient's records")

        detailed_results = []
        for result in reranked_results:
            record = result['record']
            score = result['score']
            detailed_results.append(
                schemas.PatientMedicalRecordSearchResult(
                    record_id=record.id,
                    patient_id=record.patient_id,
                    record_content=record.record_content,
                    created_at=record.created_at,
                    relevance_score=score
                )
            )
        return detailed_results

    else: # Global, anonymized search
        anonymized_results = []
        for result in reranked_results:
            record = result['record']
            score = result['score']
            anonymized_results.append(
                schemas.AnonymizedMedicalRecordSearchResult(
                    record_id=record.id,
                    record_content=record.record_content,
                    created_at=record.created_at,
                    relevance_score=score
                )
            )
        return anonymized_results