from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class AiFundReportDTO:
    id: int
    user_id: int
    fund_code: str
    content: str
    created_at: datetime
