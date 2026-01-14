from sqlalchemy import Integer, ForeignKey, CheckConstraint, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class CommentAncestor(Base):
    __tablename__ = "comment_ancestors"
    __table_args__ = (
        UniqueConstraint(
            "ancestor_post_id",
            "ancestor_comment_id",
            "descendant_comment_id",
            name="uq_comment_ancestors_ancestor_descendant",
        ),
        CheckConstraint(
            "(ancestor_post_id IS NOT NULL AND ancestor_comment_id IS NULL) OR "
            "(ancestor_post_id IS NULL AND ancestor_comment_id IS NOT NULL)",
            name="ck_comment_ancestors_one_ancestor",
        ),
        Index("ix_comment_ancestors_descendant", "descendant_comment_id"),
        Index("ix_comment_ancestors_ancestor_comment", "ancestor_comment_id"),
        Index("ix_comment_ancestors_ancestor_post", "ancestor_post_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    ancestor_post_id: Mapped[int | None] = mapped_column(ForeignKey("posts.id"), nullable=True)
    ancestor_comment_id: Mapped[int | None] = mapped_column(ForeignKey("comments.id"), nullable=True)
    descendant_comment_id: Mapped[int] = mapped_column(ForeignKey("comments.id"))
    depth: Mapped[int] = mapped_column(Integer, default=0)
