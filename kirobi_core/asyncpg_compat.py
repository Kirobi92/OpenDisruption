from __future__ import annotations

from types import SimpleNamespace
from typing import Any


async def _missing_create_pool(*_args: Any, **_kwargs: Any) -> Any:
    raise RuntimeError("asyncpg.create_pool unavailable in this environment")


def ensure_asyncpg_compat(asyncpg_module: Any) -> Any:
    if not hasattr(asyncpg_module, "create_pool"):
        asyncpg_module.create_pool = _missing_create_pool

    if not hasattr(asyncpg_module, "Pool"):
        asyncpg_module.Pool = type("Pool", (), {})

    if not hasattr(asyncpg_module, "Record"):
        asyncpg_module.Record = dict

    if not hasattr(asyncpg_module, "UndefinedTableError"):
        asyncpg_module.UndefinedTableError = type("UndefinedTableError", (Exception,), {})

    if not hasattr(asyncpg_module, "exceptions"):
        asyncpg_module.exceptions = SimpleNamespace()

    if not hasattr(asyncpg_module.exceptions, "UndefinedColumnError"):
        asyncpg_module.exceptions.UndefinedColumnError = type(
            "UndefinedColumnError",
            (Exception,),
            {},
        )

    return asyncpg_module
