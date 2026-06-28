from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

class RegisterIn(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)
    role: str = "candidate"

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    is_blocked: bool = False

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class JobIn(BaseModel):
    title: str
    company_name: str
    location: str
    required_skills: List[str] = []
    required_experience: float = 0
    salary_range: Optional[str] = None
    description: str
    status: str = "open"

class ApplicationIn(BaseModel):
    job_id: str
    cv_id: Optional[str] = None

class StatusIn(BaseModel):
    status: str

class ConversationIn(BaseModel):
    participant_id: str
    job_id: Optional[str] = None

class MessageIn(BaseModel):
    conversation_id: str
    content: str
