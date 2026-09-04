from sqlalchemy.ext.asyncio import AsyncSession
from app.models import AuditLog

async def log_event(db: AsyncSession, actor: str, action: str, meta: dict):
    db.add(AuditLog(actor=actor, action=action, meta=meta))
    await db.commit()
