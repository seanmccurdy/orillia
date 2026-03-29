from __future__ import annotations

import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from nova_act import SecurityOptions
from nova_act.asyncio import NovaAct as AsyncNovaAct


def security_options_for(url: str) -> SecurityOptions | None:
    if url.startswith("file://"):
        path = url.removeprefix("file://")
        directory = os.path.dirname(path)
        return SecurityOptions(allowed_file_open_paths=[f"{directory}/*"])
    return None


@asynccontextmanager
async def nova_session(
    url: str,
    *,
    screen_width: int = 1440,
    screen_height: int = 900,
) -> AsyncIterator[AsyncNovaAct]:
    kwargs: dict = {
        "starting_page": url,
        "headless": True,
        "tty": False,
        "screen_width": screen_width,
        "screen_height": screen_height,
    }
    security = security_options_for(url)
    if security:
        kwargs["security_options"] = security

    async with AsyncNovaAct(**kwargs) as nova:
        yield nova
