from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql+asyncpg://app:app@localhost:5432/suade"


#th engine creates a connection pool object. This pool is responsible for opening and holding the actual TCP connections to postgres
engine = create_async_engine(
    DATABASE_URL,
    #how many connections to keep in the pool, worker will maintain a pool of 10 persistent DB connections
    pool_size=10,      
    #how many EXTRA connections to allow if pool is full, so if more than 10 requests hit the DB at once, it can temporarily open up to 20 mor     
    max_overflow=20,
)

#plannned workflow:
#1)AsyncSession asks the engine for a connection.
#2)the engine hands it one from the pool.
#3)query runs on that connection
#4)when the session is closed (end of async with), the connection is returned to the pool for reuse

AsyncSessionLocal = sessionmaker(
    engine,

    #by default, when we call session.commit(), SQLAlchemy expires all ORM objects in that session, but we don't want automatic clearing, so set it to false, as this is for API in this case, potentially stale returned objects are fine. The session is about to close anyway
    expire_on_commit=False, 
    class_=AsyncSession
)

Base = declarative_base()

async def get_database():
    async with AsyncSessionLocal() as session:
        yield session
