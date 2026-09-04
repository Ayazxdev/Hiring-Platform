import asyncio
import os
import json
from sqlalchemy import update
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:1234@localhost:5432/fair_hiring"
)

async def seed_job_reqs():
    engine = create_async_engine(DATABASE_URL)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    
    import sys
    sys.path.append(os.getcwd())
    from app.models import Job
    
    reqs = {
        "core": ["Python", "JavaScript", "TypeScript", "SQL"],
        "frameworks": ["FastAPI", "React", "Node.js"],
        "tools": ["Git", "Docker"]
    }
    
    async with AsyncSessionLocal() as session:
        print(f"Seeding Job ID 1 with requirements: {json.dumps(reqs, indent=2)}")
        stmt = update(Job).where(Job.id == 1).values(required_skills=reqs)
        await session.execute(stmt)
        await session.commit()
        print("Job requirements updated successfully.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_job_reqs())
