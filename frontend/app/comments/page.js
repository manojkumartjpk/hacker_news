'use client';

import { useState, useEffect } from 'react';
import React from 'react';
import { useSearchParams } from 'next/navigation';
import { commentsAPI } from '../../lib/api';

const COMMENTS_PER_PAGE = 30;

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

export default function CommentsPage() {
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const searchParams = useSearchParams();
  const pageParam = Number.parseInt(searchParams.get('p') || '1', 10);
  const page = Number.isNaN(pageParam) || pageParam < 1 ? 1 : pageParam;

  useEffect(() => {
    fetchComments();
  }, [page]);

  const fetchComments = async () => {
    try {
      setLoading(true);
      const skip = (page - 1) * COMMENTS_PER_PAGE;
      const response = await commentsAPI.getRecentComments({ limit: COMMENTS_PER_PAGE, skip });
      setComments(response.data);
    } catch (error) {
      console.error('Failed to fetch comments:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="hn-loading">Loading...</div>;
  }

  if (!comments.length) {
    const emptyMessage = page > 1 ? 'No more comments.' : 'No comments found.';
    return <div className="hn-loading">{emptyMessage}</div>;
  }

  return (
    <table border="0" cellPadding="0" cellSpacing="0">
      <tbody>
        {comments.map((comment, index) => (
          <React.Fragment key={comment.id}>
            <tr className="athing">
              <td style={{ textAlign: 'right', verticalAlign: 'top' }} className="title">
                <span className="rank">{index + 1}.</span>
              </td>
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
                  <span className="on">
                    | on: <a href={`/post/${comment.post_id}`}>{comment.post_title}</a>
                  </span>
                </div>
                <div className="comment">
                  {comment.text}
                </div>
              </td>
            </tr>
            <tr className="spacer" style={{ height: '10px' }}></tr>
          </React.Fragment>
        ))}
        <tr className="spacer" style={{ height: '10px' }}></tr>
        <tr>
          <td colSpan="2"></td>
          <td className="title">
            <a href={`/comments?p=${page + 1}`}>More</a>
          </td>
        </tr>
      </tbody>
    </table>
  );
}
