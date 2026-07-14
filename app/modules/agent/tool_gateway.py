import asyncio
from collections.abc import Callable
from typing import Any, Protocol

from app.core.current_user import CurrentUser
from app.modules.fund.favorite_service import FundFavoriteService
from app.modules.fund.public import FundQueryFacade
from app.modules.fund.schemas import FundProfileRequest, FundValueRequest
from app.modules.strategy import service as strategy_service
from app.modules.strategy.schemas import MarketScriptKey


class AgentToolGateway(Protocol):
    async def execute(
        self, tool_name: str, args: dict[str, Any], user: CurrentUser | None
    ) -> dict[str, Any]: ...


class DefaultAgentToolGateway:
    def __init__(
        self,
        fund_query_factory: Callable[[], FundQueryFacade] = FundQueryFacade,
        fund_favorite_service: FundFavoriteService | None = None,
    ) -> None:
        self._fund_query_factory = fund_query_factory
        self._fund_favorite_service = fund_favorite_service

    async def execute(
        self, tool_name: str, args: dict[str, Any], user: CurrentUser | None
    ) -> dict[str, Any]:
        if tool_name == "get_fund_value":
            # akshare 为同步阻塞调用，丢线程池以便多个工具真正并发
            return await asyncio.to_thread(
                self._get_fund_value, str(args.get("fund_code") or "")
            )
        if tool_name == "get_fund_profile":
            return await asyncio.to_thread(
                self._get_fund_profile, str(args.get("fund_code") or "")
            )
        if tool_name == "get_fund_nav_trend_summary":
            return await asyncio.to_thread(
                self._get_fund_nav_trend_summary, str(args.get("fund_code") or "")
            )
        if tool_name == "get_favorite_fund_list":
            return await self._get_favorite_fund_list(user)
        if tool_name == "get_market_structure_watch_points":
            return await asyncio.to_thread(
                self._get_market_structure_watch_points,
                args.get("market_script_key"),
            )
        if tool_name == "get_market_structure_discipline_advice":
            return await asyncio.to_thread(
                self._get_market_structure_discipline_advice,
                args.get("market_script_key"),
            )
        if tool_name == "get_market_structure_tool_context":
            return await asyncio.to_thread(self._get_market_structure_tool_context)
        if tool_name == "search_strategy_etfs":
            return await asyncio.to_thread(
                self._search_strategy_etfs,
                str(args.get("keyword") or ""),
                int(args.get("limit") or 10),
            )
        return {"error": f"unsupported tool: {tool_name}"}

    def _get_fund_value(self, fund_code: str) -> dict[str, Any]:
        result = self._fund_query_factory().get_fund_value(
            FundValueRequest(fund_code=fund_code, source="auto")
        )
        return result.model_dump()

    def _get_fund_profile(self, fund_code: str) -> dict[str, Any]:
        from datetime import date

        result = self._fund_query_factory().get_fund_profile(
            FundProfileRequest(symbol=fund_code, year=str(date.today().year))
        )
        payload = result.model_dump()
        payload["holdings"] = payload["holdings"][:10]
        payload["industry_allocations"] = payload["industry_allocations"][:10]
        return payload

    def _get_fund_nav_trend_summary(self, fund_code: str) -> dict[str, Any]:
        return self._fund_query_factory().get_fund_nav_trend_summary(fund_code)

    async def _get_favorite_fund_list(self, user: CurrentUser | None) -> dict[str, Any]:
        if user is None:
            return {"error": "current user is required"}
        if self._fund_favorite_service is None:
            return {"error": "favorite fund service is not configured"}

        items = await self._fund_favorite_service.list_favorite_fund_options(user)
        return {
            "total": len(items),
            "items": [
                {
                    "fund_code": item.fund_code,
                    "fund_name": item.fund_name,
                    "fund_type": item.fund_type,
                }
                for item in items
            ],
        }

    def _get_market_structure_watch_points(
        self, market_script_key: object | None
    ) -> dict[str, Any]:
        result = strategy_service.get_market_structure_watch_points(
            _normalize_market_script_key(market_script_key)
        )
        return _dump_tool_result(result)

    def _get_market_structure_discipline_advice(
        self, market_script_key: object | None
    ) -> dict[str, Any]:
        result = strategy_service.get_market_structure_discipline_advice(
            _normalize_market_script_key(market_script_key)
        )
        return _dump_tool_result(result)

    def _get_market_structure_tool_context(self) -> dict[str, Any]:
        return _dump_tool_result(strategy_service.get_market_structure_tool_context())

    def _search_strategy_etfs(self, keyword: str, limit: int) -> dict[str, Any]:
        result = strategy_service.search_strategy_etfs(keyword=keyword, limit=limit)
        return _dump_tool_result(result)


def _normalize_market_script_key(value: object | None) -> MarketScriptKey | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text in {
        "domestic_story",
        "overseas_earnings",
        "hard_tech_siphon",
        "rotation_other",
        "unknown",
    }:
        return text  # type: ignore[return-value]
    return None


def _dump_tool_result(result: object) -> dict[str, Any]:
    if hasattr(result, "model_dump"):
        return result.model_dump()  # type: ignore[no-any-return]
    if isinstance(result, dict):
        return result
    return {"value": result}
