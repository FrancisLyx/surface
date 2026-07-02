import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Protocol, TypeVar

EventT = TypeVar("EventT")
EventHandler = Callable[[object], Awaitable[None]]

logger = logging.getLogger(__name__)


class EventBus(Protocol):
    def register(
        self, event_type: type[EventT], handler: Callable[[EventT], Awaitable[None]]
    ) -> None: ...

    async def publish(self, event: object) -> None: ...


class InProcessEventBus:
    """Serial, failure-isolated in-process event bus for non-critical side effects."""

    def __init__(self) -> None:
        self._handlers: dict[type[object], list[EventHandler]] = defaultdict(list)

    def register(
        self, event_type: type[EventT], handler: Callable[[EventT], Awaitable[None]]
    ) -> None:
        self._handlers[event_type].append(handler)  # type: ignore[arg-type]

    async def publish(self, event: object) -> None:
        for handler in self._handlers.get(type(event), []):
            try:
                await handler(event)
            except Exception:
                logger.exception(
                    "event handler failed", extra={"event_type": type(event).__name__}
                )
