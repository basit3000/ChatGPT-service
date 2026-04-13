from pydantic import BaseModel
from typing import List, Dict, Optional

class UserRequest(BaseModel):
    text: str
    languages: List[str]

class UserResponse(BaseModel):
    task_id: int 

class UserStatus(BaseModel):
    task_id: int  
    status: str
    results: Dict[str, str]

class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class TaskHistoryItem(BaseModel):
    task_id: int
    text: str
    languages: list
    status: str
    results: Optional[Dict[str, str]] = None
    created_at: Optional[str] = None

class LLMSettingsRequest(BaseModel):
    provider: str
    model: str
    api_key: Optional[str] = None

class LLMSettingsResponse(BaseModel):
    provider: str
    model: str
    has_api_key: bool
