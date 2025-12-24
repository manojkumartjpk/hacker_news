import pytest
from fastapi import HTTPException

from auth import get_password_hash
from models import User, Post, Comment, CommentVote
from schemas import VoteCreate, CommentVoteCreate
from services.vote_service import VoteService
from services.comment_vote_service import CommentVoteService


@pytest.mark.unit
def test_vote_service_rejects_missing_post(db_session):
    with pytest.raises(HTTPException):
        VoteService.vote_on_post(db_session, 999, VoteCreate(vote_type=1), 1)


@pytest.mark.unit
def test_get_user_vote_on_post_missing_post(db_session):
    with pytest.raises(HTTPException):
        VoteService.get_user_vote_on_post(db_session, 999, 1)


@pytest.mark.unit
def test_comment_vote_score(db_session):
    user = User(username="voter", email="voter@example.com", hashed_password=get_password_hash("Password1!"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    post = Post(title="Post", url=None, text="Body", post_type="story", user_id=user.id)
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)

    comment = Comment(text="Comment", user_id=user.id, post_id=post.id, parent_id=None)
    db_session.add(comment)
    db_session.commit()
    db_session.refresh(comment)

    assert CommentVoteService.get_comment_score(db_session, comment.id) == 0

    db_session.add(CommentVote(user_id=user.id, comment_id=comment.id, vote_type=1))
    db_session.commit()

    assert CommentVoteService.get_comment_score(db_session, comment.id) == 1


@pytest.mark.unit
def test_comment_vote_rejects_missing_comment(db_session):
    with pytest.raises(HTTPException):
        CommentVoteService.vote_on_comment(
            db_session,
            999,
            CommentVoteCreate(vote_type=1),
            1,
        )
