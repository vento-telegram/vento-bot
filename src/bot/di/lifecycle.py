from contextlib import asynccontextmanager
from typing import AsyncIterator

from bot.di.container import Container


@asynccontextmanager
async def container_lifecycle() -> AsyncIterator[None]:
    _container = Container()
    _container.wire(modules=["bot.main"], packages=["bot"])
    try:
        yield
    finally:
        _container.unwire()
