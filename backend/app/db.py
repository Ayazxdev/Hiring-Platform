from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
if "sslmode=" in db_url:
    db_url = db_url.replace("sslmode=", "ssl=")
if "channel_binding=" in db_url:
    import re
    db_url = re.sub(r'[?&]channel_binding=[^&]+', '', db_url)
    if "?" not in db_url and "&" in db_url:
        db_url = db_url.replace("&", "?", 1)

# auto-detect DB driver from DATABASE_URL
engine = create_async_engine(
    db_url,
    echo=False,
    future=True,
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
async_session_maker = SessionLocal

class Base(DeclarativeBase):
    pass

async def get_db():
    async with SessionLocal() as session:
        yield session
