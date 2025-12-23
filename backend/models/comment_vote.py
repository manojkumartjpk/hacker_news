from sqlalchemy import Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class CommentVote(Base):
    __tablename__ = "comment_votes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id"))
    vote_type: Mapped[int] = mapped_column(Integer)  # 1 for upvote, -1 for downvote
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="comment_votes")
    comment: Mapped["Comment"] = relationship(back_populates="votes")
