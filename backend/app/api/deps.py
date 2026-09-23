"""Shared FastAPI dependencies."""
from dataclasses import dataclass

from fastapi import Query

from app.core.database import get_db

__all__ = ["get_db", "PageParams", "get_page_params"]


@dataclass
class PageParams:
    page: int
    page_size: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def get_page_params(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PageParams:
    return PageParams(page=page, page_size=page_size)
