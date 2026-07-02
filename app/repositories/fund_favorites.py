from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.orm import Session

from app.db.models.fund_favorite import UserFavoriteFund


class FundFavoriteRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_user_and_code(self, user_id: int, fund_code: str) -> UserFavoriteFund | None:
        return self._session.scalar(
            select(UserFavoriteFund).where(
                UserFavoriteFund.user_id == user_id,
                UserFavoriteFund.fund_code == fund_code,
            )
        )

    def exists_for_user(self, user_id: int, fund_code: str) -> bool:
        favorite_id = self._session.scalar(
            select(UserFavoriteFund.id).where(
                UserFavoriteFund.user_id == user_id,
                UserFavoriteFund.fund_code == fund_code,
            )
        )
        return favorite_id is not None

    def count_for_user(self, user_id: int, keyword: str | None = None) -> int:
        return self._session.scalar(select(func.count()).select_from(UserFavoriteFund).where(self._where_clause(user_id, keyword))) or 0

    def list_for_user(
        self,
        user_id: int,
        keyword: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[UserFavoriteFund]:
        return list(
            self._session.scalars(
                select(UserFavoriteFund)
                .where(self._where_clause(user_id, keyword))
                .order_by(UserFavoriteFund.created_at.desc(), UserFavoriteFund.id.desc())
                .offset(offset)
                .limit(limit)
            ).all()
        )

    def list_options_for_user(self, user_id: int) -> list[UserFavoriteFund]:
        return list(
            self._session.scalars(
                select(UserFavoriteFund)
                .where(UserFavoriteFund.user_id == user_id)
                .order_by(UserFavoriteFund.created_at.desc(), UserFavoriteFund.id.desc())
            ).all()
        )

    def add(self, favorite: UserFavoriteFund) -> None:
        self._session.add(favorite)

    def refresh(self, favorite: UserFavoriteFund) -> None:
        self._session.refresh(favorite)

    def remove_for_user(self, user_id: int, fund_code: str) -> int:
        result = self._session.execute(
            delete(UserFavoriteFund).where(
                UserFavoriteFund.user_id == user_id,
                UserFavoriteFund.fund_code == fund_code,
            )
        )
        return result.rowcount or 0

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
