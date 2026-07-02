from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UserDTO:
    id: int
    username: str
    email: str | None
    phone: str | None
    role_id: int | None
    is_active: bool
