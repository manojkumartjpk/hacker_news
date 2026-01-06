from sqlalchemy import DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class CommentVote(Base):
    __tablename__ = "comment_votes"
    __table_args__ = (UniqueConstraint("user_id", "comment_id", name="uq_comment_votes_user_comment"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id"))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="comment_votes")
    comment: Mapped["Comment"] = relationship(back_populates="votes")
