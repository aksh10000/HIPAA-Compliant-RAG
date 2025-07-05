# Test A: HIPAA-Compliant Medical Records API with Semantic Search

This project is a prototype FastAPI application for managing medical records. It features a secure API, integration with a SQL database, and a Retrieval-Augmented Generation (RAG) system for HIPAA-compliant semantic search.

## Features

- **FastAPI Backend**: A modern, fast web framework for building APIs.
- **SQL Database**: Uses SQLAlchemy and SQLite for managing patient and medical record data.
- **RAG for Semantic Search**: Integrates with a vector database (ChromaDB) and the UltraSafe embeddings API to allow for searching medical records based on clinical meaning rather than just keywords.
- **HIPAA Compliance Demonstrations**:
  - **Authentication**: All endpoints are protected by an API key.
  - **Audit Logging**: A middleware logs every request for compliance and monitoring.
  - **Data Anonymization**: The search endpoint returns anonymized data, removing patient identifiers to protect privacy.
  - **Placeholder Authorization**: Includes a placeholder for fine-grained, per-patient access control.

## Project Structure

The project is organized into logical modules to separate concerns:

- `app/`: Contains the core application logic.
  - `main.py`: The FastAPI application entry point, including middleware.
  - `api.py`: Defines the API routes (`/records`, `/search`).
  - `crud.py`: Handles all database create, read, update, delete operations.
  - `models.py` & `schemas.py`: Define the database structure and Pydantic data models.
  - `rag_system.py`: Encapsulates all logic for the vector database and embeddings.
  - `security.py`: Manages authentication and authorization.
- `tests/`: Contains the `pytest` suite for the API.
- `populate_db.py`: A utility script to initialize the database with mock data.

---

## Setup and Installation

**Prerequisites:** Python and a virtual environment tool.

1.  **Copy the files into a folder in this directory structure**
```
├── .env
├── README.md
├── app
│   ├── api.py
│   ├── config.py
│   ├── crud.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── rag_system.py
│   ├── schemas.py
│   └── security.py
├── medical_records.db
├── populate_db.py
├── requirements.txt
└── tests
    └── test_simple_suite.py
```
2.  **Create and Activate a Virtual Environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `source venv\Scripts\activate`
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**
    -   Open `.env` and fill in your `ULTRASAFE_API_KEY`, the `ULTRASAFE_API_BASE` URL, and a `VALID_API_KEY` of your choice (e.g., `secret-dev-key`).

5.  **Populate the Database**
    -   This one-time script will create the `medical_records.db` (SQLite) and `chroma_db/` (ChromaDB) files and populate them with mock data.
    ```bash
    python populate_db.py
    ```

6.  **Run the Application**
    ```bash
    uvicorn app.main:app --reload
    ```
    The API will be available at `http://127.0.0.1:8000`. You can access the auto-generated documentation at `http://127.0.0.1:8000/docs`.

---

## API Usage

All requests to `/api/v1/` endpoints require an `X-API-KEY` header with the value you set in your `.env` file.

**1. Create a Medical Record**
- **Endpoint**: `POST /api/v1/records/`
- **Description**: Adds a new medical record for an existing patient.
- **Example `curl`**:
  ```bash
  curl -X POST "http://127.0.0.1:8000/api/v1/records/" \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: secret-dev-key" \
  -d '{
    "patient_id": 1,
    "record_content": "Patient shows signs of recovery from bronchitis."
  }'
  ```

**2. Semantic Search for Records**
- **Endpoint**: `GET /api/v1/search/`
- **Description**: Searches for relevant medical records using a natural language query. The behavior changes based on whether a `patient_id` is provided.

- **Use Case 1: Global, Anonymized Search**
  - **Description**: When no `patient_id` is given, the search is performed across all records and the results are anonymized for privacy.
  - **Example `curl`**:
    ```bash
    curl -X GET "http://127.0.0.1:8000/api/v1/search/?q=hypertension%20management" \
    -H "X-API-KEY: secret-dev-key"
    ```
  - **Example Response (Anonymized)**:
    ```json
    [
      {
        "record_id": 2,
        "patient_identifier": "[REDACTED]",//this is to show that patient data is hidden in case of anonymous search
        "record_content": "Follow-up for hypertension management. Blood pressure is 140/90 mmHg...",
        "created_at": "2024-05-21T12:00:00.000Z",
        "relevance_score": 0.91
      }
    ]
    ```

- **Use Case 2: Specific Patient Search**
  - **Description**: When a `patient_id` is provided, the system first verifies authorization and then searches **only** within that patient's records. The results are detailed and **not** anonymized.
  - **Example `curl`**:
    ```bash
    curl -X GET "http://127.0.0.1:8000/api/v1/search/?q=headache&patient_id=2" \
    -H "X-API-KEY: secret-dev-key"
    ```
  - **Example Response (Detailed)**:
    ```json
    [
      {
        "record_id": 4,
        "patient_id": 2,
        "record_content": "Patient reports a severe, throbbing headache on the left side, accompanied by nausea...",
        "created_at": "2024-05-21T12:00:00.000Z",
        "relevance_score": 0.95
      }
    ]
    ```

## Design Decisions and Trade-offs

-   **Database Choice**: I chose **SQLite** and file-based **ChromaDB** to ensure the project is self-contained and easy to run without external dependencies like Docker or a cloud database. For a production system, I would use **PostgreSQL** for its robustness and a managed vector database like **Pinecone** or **Weaviate** for scalability and performance.
-   **Authentication**: Simple **API Key authentication** was implemented as required. In a real-world scenario with multiple users and roles (doctors, nurses, admins), **Authentication with JWTs** would be a more appropriate and secure choice.


## Running the Test Suite

The project includes a test suite using `pytest` to ensure the API's functionality and security measures are working as expected.

To run the tests, execute the following command from the project's root directory:
```bash
pytest
```
The tests cover testing various functionalities of the fastapi app.
