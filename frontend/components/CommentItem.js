'use client';

import { useState, useEffect } from 'react';
import Cookies from 'js-cookie';
import { useRouter } from 'next/navigation';
import { commentsAPI } from '../lib/api';
import { timeAgo } from '../lib/format';
import { getErrorMessage } from '../lib/errors';

const MAX_NESTING = 5; // Prevent runaway nesting in deep reply threads.

export default function CommentItem({ comment, depth = 0, onReply, onRefresh, currentUser }) {
  const [showReplyForm, setShowReplyForm] = useState(false);
  const [replyText, setReplyText] = useState('');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(comment.text);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const router = useRouter();

  useEffect(() => {
    // Client-side auth check to toggle reply/vote affordances.
    const authStatus = Cookies.get('auth_status');
    setIsLoggedIn(!!authStatus);
  }, []);

  const handleReply = async () => {
    if (!replyText.trim()) return;
    await onReply(comment.id, replyText);
    setReplyText('');
    setShowReplyForm(false);
  };

  const handleEditSave = async () => {
    if (!editText.trim()) return;
    try {
      await commentsAPI.updateComment(comment.id, { text: editText });
      setIsEditing(false);
      if (onRefresh) {
        onRefresh();
      }
    } catch (error) {
      alert(getErrorMessage(error, 'Failed to update comment. Please try again.'));
    }
  };

  const handleDelete = async () => {
    try {
      await commentsAPI.deleteComment(comment.id);
      setShowDeleteConfirm(false);
      if (onRefresh) {
        onRefresh();
      }
    } catch (error) {
      alert(getErrorMessage(error, 'Failed to delete comment. Please try again.'));
    }
  };

  return (
    <>
      <tr className="comtr">
        <td className="default" style={{ paddingLeft: `${depth * 40}px` }}>
          <span className="comment-votelinks">
            <a
              href="#"
              onClick={async (e) => {
                e.preventDefault();
                if (!isLoggedIn) {
                  // Preserve context so the user returns to the same comment after login.
                  router.replace(`/login?next=/post/${comment.post_id}&vote=1&comment=${comment.id}`);
                  return;
                }
                try {
                  await commentsAPI.vote(comment.id, { vote_type: 1 });
                } catch (error) {
                  alert(getErrorMessage(error, 'Failed to vote. Please try again.'));
                }
              }}
            >
              <div className="votearrow" title="upvote"></div>
            </a>
          </span>
          <div className="comhead">
            <a href={`/user/${comment.username}`} className="hnuser">
              {comment.username}
            </a>
            {' '}
            <span className="age" title={new Date(comment.created_at).toISOString()}>
              <a href={`/post/${comment.post_id}?id=${comment.id}`}>{timeAgo(comment.created_at)}</a>
            </span>
            {' '}
            {isLoggedIn && depth < MAX_NESTING ? (
              <a
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  setShowReplyForm(!showReplyForm);
                }}
              >
                reply
              </a>
            ) : !isLoggedIn ? (
              <a href={`/login?next=/post/${comment.post_id}`}>reply</a>
            ) : null}
            {currentUser?.id === comment.user_id && (
              <>
                {' | '}
                <a
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    setIsEditing(!isEditing);
                    setShowDeleteConfirm(false);
                  }}
                >
                  edit
                </a>
                {' | '}
                <a
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    setShowDeleteConfirm(!showDeleteConfirm);
                    setIsEditing(false);
                  }}
                >
                  delete
                </a>
              </>
            )}
          </div>
          {isEditing ? (
            <div className="comment-edit">
              <div className="hn-form-label reply-label">Text:</div>
              <textarea
                value={editText}
                onChange={(e) => setEditText(e.target.value)}
                className="comment-box"
              />
              <div className="reply-buttons">
                <button
                  onClick={handleEditSave}
                  className="reply-submit"
                >
                  update
                </button>
                <button
                  onClick={() => setIsEditing(false)}
                  className="reply-cancel"
                >
                  cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="comment">
              {comment.text}
            </div>
          )}

          {showDeleteConfirm && (
            <div className="comment-delete">
              <div className="hn-form-label reply-label">Do you want this to be deleted?</div>
              <div className="reply-buttons">
                <button onClick={handleDelete} className="reply-submit">Yes</button>
                <button onClick={() => setShowDeleteConfirm(false)} className="reply-cancel">No</button>
              </div>
            </div>
          )}

          {isLoggedIn && (
            <div className={`reply-form ${showReplyForm ? 'show' : ''}`}>
              <div className="hn-form-label reply-label">Reply:</div>
              <textarea
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
                className="comment-box"
                placeholder=""
              />
              <div className="reply-buttons">
                <button
                  onClick={handleReply}
                  className="reply-submit"
                >
                  reply
                </button>
                <button
                  onClick={() => setShowReplyForm(false)}
                  className="reply-cancel"
                >
                  cancel
                </button>
              </div>
            </div>
          )}
        </td>
      </tr>

      {/* Recursive render for nested replies. */}
      {comment.replies && depth < MAX_NESTING && comment.replies.map((reply) => (
        <CommentItem
          key={reply.id}
          comment={reply}
          depth={depth + 1}
          onReply={onReply}
          onRefresh={onRefresh}
          currentUser={currentUser}
        />
      ))}
    </>
  );
}
