from pydantic import BaseModel, EmailStr, Field

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class Request2FAIn(BaseModel):
    email: EmailStr

class Verify2FAIn(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)

class StepCompleteIn(BaseModel):
    step_id: int
