from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.models import AiFundReport


class AiFundReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def add(self, report: AiFundReport) -> None:
        self._session.add(report)

    async def refresh(self, report: AiFundReport) -> None:
        await self._session.refresh(report)

    async def count_for_user(self, user_id: int, fund_code: str | None = None) -> int:
        return (
            await self._session.scalar(
                select(func.count())
                .select_from(AiFundReport)
                .where(self._where_clause(user_id, fund_code))
            )
            or 0
        )

    async def list_for_user(
        self,
        user_id: int,
        fund_code: str | None = None,
        offset: int = 0,
        limit: int = 10,
    ) -> list[AiFundReport]:
        result = await self._session.scalars(
            select(AiFundReport)
            .where(self._where_clause(user_id, fund_code))
            .order_by(AiFundReport.created_at.desc(), AiFundReport.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.all())

    async def get_by_id_for_user(
        self, report_id: int, user_id: int
    ) -> AiFundReport | None:
        return await self._session.scalar(
            select(AiFundReport).where(
                AiFundReport.id == report_id,
                AiFundReport.user_id == user_id,
            )
        )

    def _where_clause(self, user_id: int, fund_code: str | None):
        filters = [AiFundReport.user_id == user_id]
        normalized_fund_code = fund_code.strip() if fund_code else None
        if normalized_fund_code:
            filters.append(AiFundReport.fund_code == normalized_fund_code)
        return and_(*filters)
