from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.fund.models import UserFavoriteFund


class FundFavoriteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_and_code(
        self, user_id: int, fund_code: str
    ) -> UserFavoriteFund | None:
        return await self._session.scalar(
            select(UserFavoriteFund).where(
                UserFavoriteFund.user_id == user_id,
                UserFavoriteFund.fund_code == fund_code,
            )
        )

    async def exists_for_user(self, user_id: int, fund_code: str) -> bool:
        favorite_id = await self._session.scalar(
            select(UserFavoriteFund.id).where(
                UserFavoriteFund.user_id == user_id,
                UserFavoriteFund.fund_code == fund_code,
            )
        )
        return favorite_id is not None

    async def count_for_user(self, user_id: int, keyword: str | None = None) -> int:
        return (
            await self._session.scalar(
                select(func.count())
                .select_from(UserFavoriteFund)
                .where(self._where_clause(user_id, keyword))
            )
            or 0
        )

    async def list_for_user(
        self,
        user_id: int,
        keyword: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[UserFavoriteFund]:
        result = await self._session.scalars(
            select(UserFavoriteFund)
            .where(self._where_clause(user_id, keyword))
            .order_by(UserFavoriteFund.created_at.desc(), UserFavoriteFund.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.all())

    async def list_options_for_user(self, user_id: int) -> list[UserFavoriteFund]:
        result = await self._session.scalars(
            select(UserFavoriteFund)
            .where(UserFavoriteFund.user_id == user_id)
            .order_by(UserFavoriteFund.created_at.desc(), UserFavoriteFund.id.desc())
        )
        return list(result.all())

    def add(self, favorite: UserFavoriteFund) -> None:
        self._session.add(favorite)

    async def refresh(self, favorite: UserFavoriteFund) -> None:
        await self._session.refresh(favorite)

    async def remove_for_user(self, user_id: int, fund_code: str) -> int:
        result = await self._session.execute(
            delete(UserFavoriteFund).where(
                UserFavoriteFund.user_id == user_id,
                UserFavoriteFund.fund_code == fund_code,
            )
        )
        rowcount = getattr(result, "rowcount", 0)
        return int(rowcount or 0)

    def _where_clause(self, user_id: int, keyword: str | None):
        filters = [UserFavoriteFund.user_id == user_id]
        normalized_keyword = keyword.strip() if keyword else None
        if normalized_keyword:
            like_keyword = f"%{normalized_keyword}%"
            filters.append(
                or_(
                    UserFavoriteFund.fund_code.ilike(like_keyword),
                    UserFavoriteFund.fund_name.ilike(like_keyword),
                    UserFavoriteFund.fund_type.ilike(like_keyword),
                )
            )
        return and_(*filters)
