'use client';

import { useState, useEffect } from 'react';
import Cookies from 'js-cookie';

const timeAgo = (date) => {
  const now = new Date();
  const commentDate = new Date(date);
  const diffInSeconds = Math.floor((now - commentDate) / 1000);

  if (diffInSeconds < 60) return `${diffInSeconds} seconds ago`;
  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) return `${diffInMinutes} minutes ago`;
  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) return `${diffInHours} hours ago`;
  const diffInDays = Math.floor(diffInHours / 24);
  return `${diffInDays} days ago`;
};

export default function CommentItem({ comment, depth = 0, onReply }) {
  const [showReplyForm, setShowReplyForm] = useState(false);
  const [replyText, setReplyText] = useState('');
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const token = Cookies.get('access_token');
    setIsLoggedIn(!!token);
  }, []);

  const handleReply = async () => {
    if (!replyText.trim()) return;
    await onReply(comment.id, replyText);
    setReplyText('');
    setShowReplyForm(false);
  };

  return (
    <>
      <tr className="comtr">
        <td className="ind" style={{ paddingLeft: `${depth * 40}px` }}></td>
        <td className="default">
          <div className="comhead">
            <a href={`/user/${comment.username}`} className="hnuser">
              {comment.username}
            </a>
            {' '}
            <span className="age" title={new Date(comment.created_at).toISOString()}>
              <a href={`/post/${comment.post_id}?id=${comment.id}`}>{timeAgo(comment.created_at)}</a>
            </span>
            {' '}
            {isLoggedIn ? (
              <a
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  setShowReplyForm(!showReplyForm);
                }}
              >
                reply
              </a>
            ) : (
              <a href={`/login?next=/post/${comment.post_id}`}>reply</a>
            )}
          </div>
          <div className="comment">
            {comment.text}
          </div>

          {isLoggedIn && (
            <div className={`reply-form ${showReplyForm ? 'show' : ''}`}>
              <textarea
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
                className="reply-textarea"
                placeholder="Write a reply..."
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

      {comment.replies && comment.replies.map((reply) => (
        <CommentItem
          key={reply.id}
          comment={reply}
          depth={depth + 1}
          onReply={onReply}
        />
      ))}
    </>
  );
}
