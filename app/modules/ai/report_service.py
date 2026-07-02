from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.schemas import AiFundReportDetailResponse, AiFundReportListItem
from app.core.current_user import CurrentUser
from app.core.exception import NotFoundError
from app.core.pagination import PageResponse
from app.modules.ai.models import AiFundReport
from app.modules.ai.uow import AiUnitOfWork
from app.modules.user.models import User


class AiFundReportService:
    def __init__(self, uow_factory: Callable[[], AiUnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def create_report(
        self, user: CurrentUser, fund_code: str, content: str
    ) -> AiFundReportDetailResponse:
        async with self._uow_factory() as uow:
            report = AiFundReport(
                user_id=user.id,
                fund_code=fund_code.strip(),
                content=content,
            )
            uow.ai_fund_reports.add(report)
            await uow.commit()
            await uow.ai_fund_reports.refresh(report)
            return _to_detail_item(report)

    async def list_reports(
        self,
        user: CurrentUser,
        fund_code: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> PageResponse[AiFundReportListItem]:
        async with self._uow_factory() as uow:
            total = await uow.ai_fund_reports.count_for_user(user.id, fund_code)
            pages = (total + page_size - 1) // page_size if total else 0
            offset = (page - 1) * page_size
            reports = await uow.ai_fund_reports.list_for_user(
                user.id, fund_code, offset=offset, limit=page_size
            )
            return PageResponse(
                page=page,
                page_size=page_size,
                total=total,
                pages=pages,
                items=[_to_list_item(report) for report in reports],
            )

    async def get_report_detail(
        self, user: CurrentUser, report_id: int
    ) -> AiFundReportDetailResponse:
        async with self._uow_factory() as uow:
            report = await uow.ai_fund_reports.get_by_id_for_user(report_id, user.id)
            if report is None:
                raise NotFoundError("report not found")
            return _to_detail_item(report)


def _to_current_user(user: User | CurrentUser) -> CurrentUser:
    if isinstance(user, CurrentUser):
        return user
    return CurrentUser(
        id=user.id,
        username=user.username,
        email=user.email,
        phone=user.phone,
        role_id=user.role_id,
    )


def _service_from_session(db: AsyncSession) -> AiFundReportService:
    return AiFundReportService(lambda: AiUnitOfWork(lambda: db))


async def create_report(
    db: AsyncSession, user: User | CurrentUser, fund_code: str, content: str
) -> AiFundReportDetailResponse:
    return await _service_from_session(db).create_report(
        _to_current_user(user), fund_code, content
    )


async def list_reports(
    db: AsyncSession,
    user: User | CurrentUser,
    fund_code: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> PageResponse[AiFundReportListItem]:
    return await _service_from_session(db).list_reports(
        _to_current_user(user), fund_code=fund_code, page=page, page_size=page_size
    )


async def get_report_detail(
    db: AsyncSession, user: User | CurrentUser, report_id: int
) -> AiFundReportDetailResponse:
    return await _service_from_session(db).get_report_detail(
        _to_current_user(user), report_id
    )


def _to_list_item(report: AiFundReport) -> AiFundReportListItem:
    return AiFundReportListItem(
        id=report.id,
        fund_code=report.fund_code,
        created_at=report.created_at.isoformat(),
    )


def _to_detail_item(report: AiFundReport) -> AiFundReportDetailResponse:
    return AiFundReportDetailResponse(
        id=report.id,
        fund_code=report.fund_code,
        content=report.content,
        created_at=report.created_at.isoformat(),
    )
