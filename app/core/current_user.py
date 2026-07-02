from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CurrentUser:
    id: int
    username: str
    email: str | None = None
    phone: str | None = None
    role_id: int | None = None
