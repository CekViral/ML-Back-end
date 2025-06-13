from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserInfo(BaseModel):
    id: str
    name: str
    email: EmailStr

    
class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str


class ChangePasswordRequest(BaseModel):
    email: EmailStr
    old_password: str
    new_password: str
