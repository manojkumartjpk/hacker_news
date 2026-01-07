from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class QueuedWrite(Base):
    __tablename__ = "queued_write_requests"

    request_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
