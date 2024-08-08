from pydantic import BaseModel
from typing import List, Dict

class UserRequest(BaseModel):
    text: str
    languages: List[str]

class UserResponse(BaseModel):
    task_id: int 

class UserStatus(BaseModel):
    task_id: int  
    status: str
    results: Dict[str, str]
