from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import City, Dma, Pipe


async def is_city_table_empty(db_session: AsyncSession):
    query = select(City.id.isnot(None))
    query = select(exists(query))
    result = await db_session.execute(query)
    table_exists = result.scalars().one()
    return not (table_exists)


async def is_dma_table_empty(db_session: AsyncSession):
    query = select(Dma.dma_id.isnot(None))
    query = select(exists(query))
    result = await db_session.execute(query)
    table_exists = result.scalars().one()
    return not (table_exists)


async def is_pipes_table_empty(db_session: AsyncSession):
    query = select(Pipe.pipe_id.isnot(None))
    query = select(exists(query))
    result = await db_session.execute(query)
    table_exists = result.scalars().one()
    return not (table_exists)
