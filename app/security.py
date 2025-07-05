from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from .config import settings

API_KEY_HEADER = APIKeyHeader(name="X-API-KEY", auto_error=True)

def get_api_key(api_key: str = Security(API_KEY_HEADER)):
    """
    Dependency to validate the API Key.
    Compares the provided key against the one in our settings.
    """
    if api_key == settings.valid_api_key:
        return api_key
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

def check_permissions(user_api_key: str, patient_id: int) -> bool:
    """
    Mock authorization function.
    In a real system, this would check a database to see if the user
    associated with the API key has rights to access the given patient's data.
    For this test, we will allow all access for a valid key.
    This is basically placeholder for the real authorization system.
    """
    print(f"MOCK AUTH: Checking if key has access to patient {patient_id}. (Returning True)")
    return True