"""
Database Configuration for Fair Hiring System
Async PostgreSQL with SQLAlchemy 2.0
"""
import os
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

# Load environment variables
# Load environment variables from root directory
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

# Database URL from environment — no hardcoded password fallback
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Please configure your PostgreSQL connection string."
    )

# Fix for Render/Heroku which provides 'postgres://' but asyncpg needs 'postgresql+asyncpg://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Fix for Neon/Supabase: asyncpg expects 'ssl=' instead of 'sslmode='
if "sslmode=" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("sslmode=", "ssl=")

# asyncpg does not accept channel_binding keyword
if "channel_binding=" in DATABASE_URL:
    import re
    DATABASE_URL = re.sub(r'[?&]channel_binding=[^&]+', '', DATABASE_URL)
    if "?" not in DATABASE_URL and "&" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("&", "?", 1)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Import Base from models (will be imported when models are loaded)
Base = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database - create all tables with retry logic
    """
    from app.models import Base
    import asyncio
    
    max_retries = 5
    retry_delay = 5
    
    for attempt in range(1, max_retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("✓ Database initialized successfully")
            return
        except Exception as e:
            if attempt == max_retries:
                print(f"✗ Failed to initialize database after {max_retries} attempts: {e}")
                raise
            print(f"⚠ Database connection attempt {attempt} failed, retrying in {retry_delay}s... ({e})")
            await asyncio.sleep(retry_delay)


async def close_db():
    """
    Close database connections
    """
    await engine.dispose()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session for use in background tasks or outside of request context.
    This is similar to get_db() but doesn't handle commit/rollback automatically.
    The caller is responsible for commit/rollback.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
