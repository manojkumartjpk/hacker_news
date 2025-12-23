from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(300), index=True)
    url: Mapped[str] = mapped_column(String(500), nullable=True)  # URL or text post
    text: Mapped[str] = mapped_column(Text, nullable=True)  # For text posts
    score: Mapped[int] = mapped_column(Integer, default=0)  # Cached score from votes
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="posts")
    comments: Mapped[list["Comment"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    votes: Mapped[list["Vote"]] = relationship(back_populates="post", cascade="all, delete-orphan")