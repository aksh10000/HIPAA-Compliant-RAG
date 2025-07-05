import httpx
import chromadb
from chromadb.config import Settings
from .config import settings
from . import models
from typing import List, Dict, Any
class RAGSystem:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RAGSystem, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self, recreate_collection: bool = False):
        if self.initialized and not recreate_collection:
            return
            
        print("Initializing RAG System...")
        
        # --- NEW: HTTP Client Setup ---
        self.api_key = settings.ultrasafe_api_key
        self.embedding_url = "https://api.us.inc/usf/v1/hiring/embed/embeddings"
        self.reranker_url = "https://api.us.inc/usf/v1/hiring/embed/reranker"
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        # Use a persistent httpx client for connection pooling
        self.http_client = httpx.Client(headers=self.headers, timeout=30.0)
        
        # --- ChromaDB Setup (with telemetry disabled) ---
        self.chroma_client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection_name = "medical_records"
        
        if recreate_collection:
            try:
                self.chroma_client.delete_collection(name=self.collection_name)
                print(f"Collection '{self.collection_name}' deleted successfully.")
            except Exception as e:
                print(f"An unexpected error occurred while deleting collection: {e}")

        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        self.initialized = True
        print("RAG System Initialized.")

    def get_embedding(self, text: str) -> list[float]:
        """
        Gets an embedding for a given text using the specified embeddings API.
        """
        payload = {
            "model": "usf-embed",
            "input": text.replace("\n", " ")
        }
        
        try:
            response = self.http_client.post(self.embedding_url, json=payload)
            response.raise_for_status()  # Raises an exception for 4XX/5XX responses
            
            response_data = response.json()
            
            # --- FIX: Update the parsing logic to match the actual API response ---
            # The actual path is response['result']['data'][0]['embedding']
            return response_data["result"]["data"][0]["embedding"]
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise

    def add_record(self, record_content: str, record_id: int, patient_id: int):
        embedding = self.get_embedding(record_content)
        self.collection.add(
            embeddings=[embedding],
            documents=[record_content],
            metadatas=[{"sql_record_id": record_id, "patient_id": patient_id}],
            ids=[str(record_id)]
        )

    def search(self, query: str, top_k: int = 5, patient_id: int | None = None) -> list[dict]:
        query_embedding = self.get_embedding(query)
        query_args = {
            "query_embeddings": [query_embedding],
            "n_results": top_k
        }

        # Only add the 'where' filter to the arguments if a patient_id is provided
        if patient_id is not None:
            query_args["where"] = {"patient_id": patient_id}

        results = self.collection.query(**query_args)
        
        if not results['ids'] or not results['ids'][0]:
            return []
            
        retrieved_ids = results['ids'][0]
        distances = results['distances'][0]
        
        relevance_scores = [1.0 - dist for dist in distances]

        return [
            {"record_id": int(id), "score": score}
            for id, score in zip(retrieved_ids, relevance_scores)
        ]
    
    def rerank(self, query: str, db_records: List[models.MedicalRecord]) -> List[Dict[str, Any]]:
        """
        Reranks a list of database records using the reranker API.

        Args:
            query: The original search query.
            db_records: A list of SQLAlchemy MedicalRecord objects from the initial search.

        Returns:
            A list of dictionaries, sorted by the new rerank score. 
            Each dictionary contains the original record and its new score.
            Example: [{'record': MedicalRecord, 'score': 0.98}, ...]
        """
        if not db_records:
            return []

        texts_to_rerank = [record.record_content for record in db_records]

        payload = {
            "model": "usf-rerank",
            "query": query,
            "texts": texts_to_rerank
        }

        try:
            response = self.http_client.post(self.reranker_url, json=payload)
            response.raise_for_status()
            rerank_data = response.json()["result"]["data"]
            
            # Create a list to hold records with their new scores
            scored_records = []
            for item in rerank_data:
                original_index = item['index']
                new_score = item['score']
                
                # Get the original record corresponding to this index
                original_record = db_records[original_index]
                
                scored_records.append({
                    "record": original_record,
                    "score": new_score
                })

            # Sort the results in descending order based on the new reranker score
            scored_records.sort(key=lambda x: x['score'], reverse=True)
            
            return scored_records
        except Exception as e:
            print(f"An unexpected error occurred during reranking: {e}")
            return [{"record": rec, "score": 0.0} for rec in db_records]
rag_system = RAGSystem() 