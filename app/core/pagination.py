from math import ceil
from typing import Generic, Sequence, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageResponse(BaseModel, Generic[T]):
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页条数")
    total: int = Field(description="总条数")
    pages: int = Field(description="总页数")
    items: list[T] = Field(description="当前页数据")


def paginate(items: Sequence[T], page: int, page_size: int) -> PageResponse[T]:
    total = len(items)
    pages = ceil(total / page_size) if total else 0
    start = (page - 1) * page_size
    end = start + page_size

    return PageResponse(
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
        items=list(items[start:end]),
    )
