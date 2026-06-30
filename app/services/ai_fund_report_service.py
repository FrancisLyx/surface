from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.api.routes.ai.ai_schema import AiFundReportDetailResponse, AiFundReportListItem
from app.core.pagination import PageResponse
from app.db.models.ai_fund_report import AiFundReport
from app.db.models.user import User


def create_report(db: Session, user: User, fund_code: str, content: str) -> AiFundReport:
    report = AiFundReport(
        user_id=user.id,
        fund_code=fund_code.strip(),
        content=content,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def list_reports(
    db: Session,
    user: User,
    fund_code: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> PageResponse[AiFundReportListItem]:
    filters = [AiFundReport.user_id == user.id]
    normalized_fund_code = fund_code.strip() if fund_code else None
    if normalized_fund_code:
        filters.append(AiFundReport.fund_code == normalized_fund_code)

    where_clause = and_(*filters)
    total = db.scalar(select(func.count()).select_from(AiFundReport).where(where_clause)) or 0
    pages = (total + page_size - 1) // page_size if total else 0
    offset = (page - 1) * page_size
    reports = db.scalars(
        select(AiFundReport)
        .where(where_clause)
        .order_by(AiFundReport.created_at.desc(), AiFundReport.id.desc())
        .offset(offset)
        .limit(page_size)
    ).all()

    return PageResponse(
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
        items=[_to_list_item(report) for report in reports],
    )


def get_report_detail(db: Session, user: User, report_id: int) -> AiFundReportDetailResponse:
    report = db.scalar(
        select(AiFundReport).where(
            AiFundReport.id == report_id,
            AiFundReport.user_id == user.id,
        )
    )
    if report is None:
        raise HTTPException(status_code=404, detail="report not found")

    return AiFundReportDetailResponse(
        id=report.id,
        fund_code=report.fund_code,
        content=report.content,
        created_at=report.created_at.isoformat(),
    )


def _to_list_item(report: AiFundReport) -> AiFundReportListItem:
    return AiFundReportListItem(
        id=report.id,
        fund_code=report.fund_code,
        created_at=report.created_at.isoformat(),
    )
