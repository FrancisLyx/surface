import logging
import time
import uuid

from fastapi import FastAPI, Request

logger = logging.getLogger("app.request")


def register_request_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start_time

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.6f}"
        logger.info(
            "%s %s %s %.6fs request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            process_time,
            request_id,
        )
        return response
