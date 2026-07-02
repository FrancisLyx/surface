from pydantic import BaseModel, EmailStr, Field, model_validator


class RegisterStatusResponse(BaseModel):
    enabled: bool


class UserRegisterRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    password: str = Field(min_length=6)

    @model_validator(mode="after")
    def validate_contact(self):
        if not self.email and not self.phone:
            raise ValueError("email or phone is required")
        return self


class UserLoginRequest(BaseModel):
    account: str = Field(min_length=1)
    password: str = Field(min_length=1)


class UserResponse(BaseModel):
    id: int
    username: str
    email: str | None
    phone: str | None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
