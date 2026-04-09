from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    store_name: str
    whatsapp_phone: str | None = None

    @field_validator("name", "password", "store_name")
    @classmethod
    def require_non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value cannot be blank.")
        return value


class RegisterResponse(BaseModel):
    merchant_id: int
    merchant_name: str
    store_id: int
    store_name: str
    email: EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    store_name: str

    @field_validator("password", "store_name")
    @classmethod
    def require_non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Value cannot be blank.")
        return value


class LoginResponse(BaseModel):
    merchant_id: int
    merchant_name: str
    store_id: int
    store_name: str
    email: EmailStr
