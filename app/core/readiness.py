import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass


DependencyChecker = Callable[[], Awaitable[None]]


@dataclass(slots=True)
class DependencyStatus:
    status: str = "unknown"
    message: str | None = None
    core: bool = True


class ReadinessState:
    def __init__(self) -> None:
        self._dependencies: dict[str, DependencyStatus] = {}

    def mark_ok(self, name: str, *, core: bool = True) -> None:
        self._dependencies[name] = DependencyStatus(
            status="ok", message=None, core=core
        )

    def mark_failed(self, name: str, message: str, *, core: bool = True) -> None:
        self._dependencies[name] = DependencyStatus(
            status="failed", message=message, core=core
        )

    def is_ready(self) -> bool:
        core_dependencies = [item for item in self._dependencies.values() if item.core]
        return bool(core_dependencies) and all(
            item.status == "ok" for item in core_dependencies
        )

    def snapshot(self) -> dict[str, object]:
        return {
            "status": "ok" if self.is_ready() else "degraded",
            "dependencies": {
                name: {
                    "status": item.status,
                    "message": item.message,
                }
                for name, item in self._dependencies.items()
            },
        }


async def monitor_readiness(
    state: ReadinessState,
    checkers: dict[str, DependencyChecker],
    *,
    interval_seconds: float = 5.0,
    timeout_seconds: float = 3.0,
) -> None:
    while True:
        for name, checker in checkers.items():
            try:
                await asyncio.wait_for(checker(), timeout=timeout_seconds)
            except Exception as exc:
                state.mark_failed(name, str(exc))
            else:
                state.mark_ok(name)
        await asyncio.sleep(interval_seconds)
