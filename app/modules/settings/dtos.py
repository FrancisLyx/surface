from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RegistrationSettingDTO:
    enabled: bool
