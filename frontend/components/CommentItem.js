'use client';

import { useState, useEffect } from 'react';
import Cookies from 'js-cookie';
import { useRouter } from 'next/navigation';
import { commentsAPI } from '../lib/api';
import { timeAgo } from '../lib/format';
import { getErrorMessage } from '../lib/errors';

const INDENT_WIDTH = 40;

export default function CommentItem({
  comment,
  depth = 0,
  onRefresh,
  currentUser,
  commentVotes = {},
  focusedCommentId = null,
}) {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(comment.text);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [userVote, setUserVote] = useState(0);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const router = useRouter();
  const isFocused = Number(focusedCommentId) === Number(comment.id);
  const isDeleted = !!comment.is_deleted;
  const displayText = isDeleted ? 'comment has been deleted' : comment.text;
  const hasParent = comment.parent_id !== null && comment.parent_id !== undefined;
  const rootId = comment.root_id ?? null;
  const prevId = comment.prev_id ?? null;
  const nextId = comment.next_id ?? null;

  useEffect(() => {
    // Client-side auth check to toggle reply/vote affordances.
    const authStatus = Cookies.get('auth_status');
    setIsLoggedIn(!!authStatus);
  }, []);

  useEffect(() => {
    if (!isLoggedIn) {
      setUserVote(0);
      return;
    }
    setUserVote(commentVotes[comment.id] ?? 0);
  }, [comment.id, commentVotes, isLoggedIn]);

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
      <tr className={`athing comtr${isFocused ? ' focused' : ''}`} id={`comment-${comment.id}`}>
        <td>
          <table border="0" cellPadding="0" cellSpacing="0">
            <tbody>
              <tr>
                <td className="ind" data-indent={depth}>
                  <span
                    className="indent-spacer"
                    style={{ width: depth * INDENT_WIDTH }}
                    aria-hidden="true"
                  />
                </td>
                <td className="votelinks" valign="top">
                  <center>
                    {userVote === 1 || isDeleted ? (
                      <div className="votearrow invisible"></div>
                    ) : (
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
                            setUserVote(1);
                            if (onRefresh) {
                              onRefresh();
                            }
                          } catch (error) {
                            alert(getErrorMessage(error, 'Failed to vote. Please try again.'));
                          }
                        }}
                      >
                        <div className="votearrow" title="upvote"></div>
                      </a>
                    )}
                  </center>
                </td>
                <td className="default">
                  <div className="comment-headline">
                    <span className="comhead">
                      <a href={`/user/${comment.username}`} className="hnuser">
                        {comment.username}
                      </a>
                      {' '}
                      <span className="age" title={new Date(comment.created_at).toISOString()}>
                        <a href={`/post/${comment.post_id}?id=${comment.id}`}>{timeAgo(comment.created_at)}</a>
                      </span>
                      {' '}
                      <span className="navs">
                        {isLoggedIn && userVote !== 0 && !isDeleted && (
                          <>
                            <a
                              href="#"
                              onClick={async (e) => {
                                e.preventDefault();
                                try {
                                  await commentsAPI.unvote(comment.id);
                                  setUserVote(0);
                                  if (onRefresh) {
                                    onRefresh();
                                  }
                                } catch (error) {
                                  alert(getErrorMessage(error, 'Failed to remove vote. Please try again.'));
                                }
                              }}
                            >
                              unvote
                            </a>
                          </>
                        )}
                        {hasParent && (
                          <>
                            {' | '}
                            <a href={`#comment-${comment.parent_id}`}>parent</a>
                          </>
                        )}
                        {rootId && rootId !== comment.id && (
                          <>
                            {' | '}
                            <a href={`#comment-${rootId}`}>root</a>
                          </>
                        )}
                        {prevId && (
                          <>
                            {' | '}
                            <a href={`#comment-${prevId}`}>prev</a>
                          </>
                        )}
                        {nextId && (
                          <>
                            {' | '}
                            <a href={`#comment-${nextId}`}>next</a>
                          </>
                        )}
                        {' '}
                        <button
                          type="button"
                          className="comment-toggle"
                          aria-expanded={!isCollapsed}
                          onClick={() => setIsCollapsed((prev) => !prev)}
                        >
                          [{isCollapsed ? '+' : '–'}]
                        </button>
                      </span>
                    </span>
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
          ) : !isCollapsed ? (
            <>
              <div className="comment">
                {displayText}
              </div>
              <div className="comment-actions">
                {isLoggedIn ? (
                  <a href={`/reply/${comment.id}`}>reply</a>
                ) : !isLoggedIn ? (
                  <a href={`/login?next=/reply/${comment.id}`}>reply</a>
                ) : null}
                {currentUser?.id === comment.user_id && !isDeleted && (
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
            </>
          ) : null}

          {showDeleteConfirm && (
            <div className="comment-delete">
              <div className="hn-form-label reply-label">Do you want this to be deleted?</div>
              <div className="reply-buttons">
                <button onClick={handleDelete} className="reply-submit">Yes</button>
                <button onClick={() => setShowDeleteConfirm(false)} className="reply-cancel">No</button>
              </div>
            </div>
          )}
                </td>
              </tr>
            </tbody>
          </table>
        </td>
      </tr>

      {/* Recursive render for nested replies. */}
      {!isCollapsed && comment.replies && comment.replies.map((reply) => (
        <CommentItem
          key={reply.id}
          comment={reply}
          depth={depth + 1}
          onRefresh={onRefresh}
          currentUser={currentUser}
          commentVotes={commentVotes}
          focusedCommentId={focusedCommentId}
        />
      ))}
    </>
  );
}
