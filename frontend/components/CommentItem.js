'use client';

import { useState } from 'react';
import Link from 'next/link';

export default function CommentItem({ comment, depth = 0, onReply }) {
  const [showReplyForm, setShowReplyForm] = useState(false);
  const [replyText, setReplyText] = useState('');

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

  const handleReply = async () => {
    if (!replyText.trim()) return;
    await onReply(comment.id, replyText);
    setReplyText('');
    setShowReplyForm(false);
  };

  const indentClass = depth > 0 ? `ml-${Math.min(depth * 4, 16)} border-l-2 border-gray-200 pl-4` : '';

  return (
    <div className={`py-2 ${indentClass}`}>
      <div className="text-sm text-gray-600 mb-1">
        <Link href={`/user/${comment.username}`} className="font-medium hover:underline">
          {comment.username}
        </Link>
        {' '}
        {timeAgo(comment.created_at)}
      </div>
      <div className="text-gray-800 mb-2">{comment.text}</div>
      <div className="text-xs text-gray-500">
        <button
          onClick={() => setShowReplyForm(!showReplyForm)}
          className="hover:underline mr-4"
        >
          reply
        </button>
      </div>
      
      {showReplyForm && (
        <div className="mt-2">
          <textarea
            value={replyText}
            onChange={(e) => setReplyText(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded text-sm"
            rows="3"
            placeholder="Write a reply..."
          />
          <div className="mt-2 space-x-2">
            <button
              onClick={handleReply}
              className="px-3 py-1 bg-orange-500 text-white text-sm rounded hover:bg-orange-600"
            >
              Reply
            </button>
            <button
              onClick={() => setShowReplyForm(false)}
              className="px-3 py-1 bg-gray-300 text-gray-700 text-sm rounded hover:bg-gray-400"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
      
      {comment.replies && comment.replies.map(reply => (
        <CommentItem
          key={reply.id}
          comment={reply}
          depth={depth + 1}
          onReply={onReply}
        />
      ))}
    </div>
  );
}