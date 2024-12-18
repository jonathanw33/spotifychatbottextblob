from pydantic import BaseModel
from typing import Optional, Dict, Any

class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    message: str
    debug_info: Dict[str, Any]

class AuthRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    success: bool
    user: Optional[Dict[str, Any]] = None