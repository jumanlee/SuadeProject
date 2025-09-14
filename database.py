from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncIterator


#plannned workflow:
#1)AsyncSession asks the engine for a connection.
#2)the engine hands it one from the pool.
#3)query runs on that connection
#4)when the session is closed (end of async with), the connection is returned to the pool for reuse

DATABASE_URL = "postgresql+asyncpg://app:app@localhost:5432/suade"

#th engine creates a connection pool object. This pool is responsible for opening and holding the actual TCP connections to postgres
engine = create_async_engine(
    DATABASE_URL,
    #how many connections to keep in the pool, worker will maintain a pool of 10 persistent DB connections
    pool_size=10,      
    #how many EXTRA connections to allow if pool is full, so if more than 10 requests hit the DB at once, it can temporarily open up to 20 mor     
    max_overflow=20,

    #test the connection before giving it out of the pool
    pool_pre_ping=True  
)

class Base(DeclarativeBase):
    pass

#builds AsyncSession objects, don’t want to make AsyncSession directly every time, instead, configure once here, factory for making sessions
AsyncSessionLocal = async_sessionmaker(
     #by default, when we call session.commit(), SQLAlchemy expires all ORM objects in that session, but we don't want automatic clearing, so set it to false, as this is for API in this case, potentially stale returned objects are fine. The session is about to close anyway
    engine, 
    expire_on_commit=False, 
    class_=AsyncSession,)

#runs once at app startup, create tables from models
async def init_models() -> None:
    #engine begin opens a connection with a transaction
    async with engine.begin() as conn:
        #conn.run_sync enables call sync functions on the async connection
        #Base.metadata.create_all checks the models defined with Base as their base class and creates any tables that don't already exist in the DB
        await conn.run_sync(Base.metadata.create_all)

#per-request dependency, exactly one yield
async def get_session() -> AsyncIterator[AsyncSession]:
    #AsyncSessionLocal() returns a context manager: AsyncSession object, which manages the transaction.
    async with AsyncSessionLocal() as session:
        yield session




