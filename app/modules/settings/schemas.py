from pydantic import BaseModel


class RegistrationSettingRequest(BaseModel):
    enabled: bool


class RegistrationSettingResponse(BaseModel):
    enabled: bool
