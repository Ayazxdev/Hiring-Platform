import asyncio
from app.db import async_session_maker
from app.models import Company, Job
from sqlalchemy import select
from datetime import datetime

async def seed():
    async with async_session_maker() as db:
        # Check if dummy company exists
        q = await db.execute(select(Company).where(Company.email == "test@company.com"))
        company = q.scalar_one_or_none()
        
        if not company:
            company = Company(
                name="Test Corporation",
                email="test@company.com",
                password_hash="nosig" # Not needed for this test
            )
            db.add(company)
            await db.commit()
            await db.refresh(company)
            print(f"Created company: {company.name} (ID: {company.id})")
        else:
            print(f"Company already exists (ID: {company.id})")
            
        # Check if dummy job exists
        q_job = await db.execute(select(Job).where(Job.title == "Frontend Engineer", Job.company_id == company.id))
        job = q_job.scalar_one_or_none()
        
        if not job:
            job = Job(
                company_id=company.id,
                title="Frontend Engineer",
                description="Develop core interface systems with high-fidelity interaction models.",
                published=True
            )
            db.add(job)
            await db.commit()
            await db.refresh(job)
            print(f"Created job: {job.title} (ID: {job.id})")
        else:
            print(f"Job already exists (ID: {job.id})")

if __name__ == "__main__":
    asyncio.run(seed())
