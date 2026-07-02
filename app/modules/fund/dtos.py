from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FavoriteFundDTO:
    id: int
    user_id: int
    fund_code: str
    fund_name: str
    fund_type: str | None
