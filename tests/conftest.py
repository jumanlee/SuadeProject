import os

#ensure DB URL is set BEFORE importing engine/app.
#inside Docker, the Postgres hostname is "db".
os.environ["DATABASE_URL"] = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://app:app@db:5432/suade"
)

import pytest
import asyncio
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
import pytest_asyncio
from asgi_lifespan import LifespanManager

# #IMPORTANT: set env BEFORE importing engine so engine picks it up
# #ensure that tests hit the mapped Postgres on localhost:5432
# os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://app:app@localhost:5432/suade")

from database import engine, Base
import models.models
from main import app

#autouse means run this fixture automatically even if the test doesn’t request it, scope="session" means run once per test session
@pytest_asyncio.fixture(autouse=True, scope="session")
async def ensure_tables_created():
    #Fastapi's startup hook (triggered by httpx.AsyncClient with lifespan="on") will create tables later, not here.
    async with engine.begin() as conn:
        #only to ensure engine is live, if not, would raise error, and test would stop. This is important to ensure the DB is up before running tests
        #this creates a trivial conn.run_sync(lambda conn: None), the actual table creation happens later when the Fastapi app starts up in the test client
        # await conn.run_sync(lambda conn: None)  
        await conn.run_sync(Base.metadata.create_all)
    yield

@pytest_asyncio.fixture
#building a fake HTTP client to test the api endpoints without uvicorn. Note this shouldn't be run atuomatically, hence no autouse, must be requested by functions.
async def client():
    #fake server: ASGITransport with lifespan so @app.on_event("startup") runs
    #ASGITransport httpx transport layer that lets us call an ASGI app e.g. fastapi directly in memory, without networking
    #lifespan="on" ensures fastapi’s startup/shutdown events (e.g. @app.on_event("startup")) are triggered
    # transport = ASGITransport(app=app, lifespan="on")

    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        #fake client
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

@pytest_asyncio.fixture(autouse=True)
async def db_cleanup():
    #clean tables before each test, order matters due to foreign keys due to restrictions
    async with engine.begin() as conn:
        #delete child first, then parents, avoid TRUNCATE CASCADE for safety
        await conn.execute(text("DELETE FROM transactions;"))
        await conn.execute(text("DELETE FROM users;"))
        await conn.execute(text("DELETE FROM products;"))
    yield