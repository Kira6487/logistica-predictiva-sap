import asyncio

import httpx
import pytest

from app.core.config import Settings
from app.main import create_app


VERCEL_ORIGIN_REGEX = (
    r"^https://logistica-predictiva(?:-sap)?(?:-[a-z0-9]+)*[.]vercel[.]app$"
)


async def _request_with_origin(origin: str, allowed_origins: tuple[str, ...]) -> httpx.Response:
    application = create_app(
        Settings(
            app_env="production",
            allowed_origins=allowed_origins,
            allowed_origin_regex=VERCEL_ORIGIN_REGEX,
        )
    )
    transport = httpx.ASGITransport(app=application)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get("/health", headers={"Origin": origin})


@pytest.mark.parametrize(
    "origin",
    [
        "https://logistica-predictiva-sap.vercel.app",
        "https://logistica-predictiva-sap-git-main-kira-e800.vercel.app",
        "https://logistica-predictiva-3jjpyoxud-kira-e800.vercel.app",
    ],
)
def test_vercel_origins_are_allowed(origin: str) -> None:
    response = asyncio.run(_request_with_origin(origin, ()))

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


@pytest.mark.parametrize(
    "origin",
    [
        "https://evil.vercel.app",
        "https://logistica-ejemplo.vercel.app",
    ],
)
def test_unrelated_vercel_origins_are_rejected(origin: str) -> None:
    response = asyncio.run(_request_with_origin(origin, ()))

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize("origin", ["http://localhost:5173", "http://127.0.0.1:5173"])
def test_local_origins_remain_allowed(origin: str) -> None:
    response = asyncio.run(
        _request_with_origin(
            origin,
            ("http://localhost:5173", "http://127.0.0.1:5173"),
        )
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
