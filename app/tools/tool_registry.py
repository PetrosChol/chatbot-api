import logging
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.tools.statement_builders.movies_statement_builder import (
    build_cinemas_statement,
)
from app.tools.statement_builders.performances_statement_builder import (
    build_performances_statement,
)
from app.tools.statement_builders.outages_statement_builder import (
    build_outages_statement,
)
from app.tools.statement_builders.hospital_shifts_statement_builder import (
    build_hospital_shifts_statement,
)
from app.tools.statement_builders.thessaloniki_history_statement_builder import (
    query_thessaloniki_history,
)

logger = logging.getLogger(__name__)


async def run_cinemas(params: Dict[str, Any], db: AsyncSession) -> Any:
    stmt = build_cinemas_statement(**params)
    result = await db.execute(stmt)
    return result.all()


async def run_performances(params: Dict[str, Any], db: AsyncSession) -> Any:
    stmt = build_performances_statement(**params)
    result = await db.execute(stmt)
    return result.all()


async def run_outages(params: Dict[str, Any], db: AsyncSession) -> Any:
    stmt = build_outages_statement(**params)
    result = await db.execute(stmt)
    return result.scalars().all()


async def run_hospital_shifts(params: Dict[str, Any], db: AsyncSession) -> Any:
    stmt = build_hospital_shifts_statement(**params)
    result = await db.execute(stmt)
    return result.scalars().all()


async def run_history(params: Dict[str, Any], db: AsyncSession) -> Any:
    search_query = params.get("search_query", "")

    logger.info(f"Εκτέλεση run_history με search_query (αγνοείται): '{search_query}'")

    history_text = await query_thessaloniki_history(search_query)

    if history_text is None:
        logger.warning("Η ανάκτηση του ιστορικού κειμένου απέτυχε ή επέστρεψε None.")
        return "Δεν ήταν δυνατή η ανάκτηση των ιστορικών πληροφοριών."

    return history_text


TOOL_REGISTRY: Dict[str, Any] = {
    "cinemas": run_cinemas,
    "performances": run_performances,
    "outages": run_outages,
    "hospital_shifts": run_hospital_shifts,
    "history": run_history,
}
