from collections.abc import Callable

from sqlalchemy.orm import Session

from app.api.routes.ai.ai_schema import AiFundReportDetailResponse, AiFundReportListItem
from app.core.current_user import CurrentUser
from app.core.exception import NotFoundError
from app.core.pagination import PageResponse
from app.db.models.ai_fund_report import AiFundReport
from app.db.models.user import User
from app.db.uow import SqlAlchemyUnitOfWork


class AiFundReportService:
    def __init__(self, uow_factory: Callable[[], SqlAlchemyUnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def create_report(self, user: CurrentUser, fund_code: str, content: str) -> AiFundReportDetailResponse:
        with self._uow_factory() as uow:
            report = AiFundReport(
                user_id=user.id,
                fund_code=fund_code.strip(),
                content=content,
            )
            uow.ai_fund_reports.add(report)
            uow.commit()
            uow.ai_fund_reports.refresh(report)
            return _to_detail_item(report)

    def list_reports(
        self,
        user: CurrentUser,
        fund_code: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> PageResponse[AiFundReportListItem]:
        with self._uow_factory() as uow:
            total = uow.ai_fund_reports.count_for_user(user.id, fund_code)
            pages = (total + page_size - 1) // page_size if total else 0
            offset = (page - 1) * page_size
            reports = uow.ai_fund_reports.list_for_user(user.id, fund_code, offset=offset, limit=page_size)
            return PageResponse(
                page=page,
                page_size=page_size,
                total=total,
                pages=pages,
                items=[_to_list_item(report) for report in reports],
            )

    def get_report_detail(self, user: CurrentUser, report_id: int) -> AiFundReportDetailResponse:
        with self._uow_factory() as uow:
            report = uow.ai_fund_reports.get_by_id_for_user(report_id, user.id)
            if report is None:
                raise NotFoundError("report not found")
            return _to_detail_item(report)


def _to_current_user(user: User | CurrentUser) -> CurrentUser:
    if isinstance(user, CurrentUser):
        return user
    return CurrentUser(id=user.id, username=user.username, email=user.email, phone=user.phone, role_id=user.role_id)


def _service_from_session(db: Session) -> AiFundReportService:
    return AiFundReportService(lambda: SqlAlchemyUnitOfWork(lambda: db))


def create_report(db: Session, user: User | CurrentUser, fund_code: str, content: str) -> AiFundReportDetailResponse:
    return _service_from_session(db).create_report(_to_current_user(user), fund_code, content)


def list_reports(
    db: Session,
    user: User | CurrentUser,
    fund_code: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> PageResponse[AiFundReportListItem]:
    return _service_from_session(db).list_reports(_to_current_user(user), fund_code=fund_code, page=page, page_size=page_size)


def get_report_detail(db: Session, user: User | CurrentUser, report_id: int) -> AiFundReportDetailResponse:
    return _service_from_session(db).get_report_detail(_to_current_user(user), report_id)


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
