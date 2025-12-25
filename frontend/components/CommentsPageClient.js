'use client';

import { useState, useEffect } from 'react';
import React from 'react';
import { useSearchParams } from 'next/navigation';
import { commentsAPI } from '../lib/api';
import { timeAgo } from '../lib/format';
import { getErrorMessage } from '../lib/errors';
import InlineError from './InlineError';
import { getPagination } from '../lib/pagination';

const COMMENTS_PER_PAGE = 30;

export default function CommentsPageClient() {
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const searchParams = useSearchParams();
  const { page, skip } = getPagination(searchParams, COMMENTS_PER_PAGE);

  useEffect(() => {
    fetchComments();
  }, [page]);

  const fetchComments = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await commentsAPI.getRecentComments({ limit: COMMENTS_PER_PAGE, skip });
      setComments(response.data);
    } catch (error) {
      setError(getErrorMessage(error, 'Failed to fetch comments.'));
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="hn-loading">Loading...</div>;
  }

  if (error) {
    return <InlineError message={error} />;
  }

  if (!comments.length) {
    const emptyMessage = page > 1 ? 'No more comments.' : 'No comments found.';
    return <div className="hn-loading">{emptyMessage}</div>;
  }

  return (
    <table border="0" cellPadding="0" cellSpacing="0">
      <tbody>
        {comments.map((comment) => (
          <React.Fragment key={comment.id}>
            <tr className="athing">
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
                  <a href={`/post/${comment.post_id}?id=${comment.id}`}>context</a>
                  {' | '}
                  {comment.parent_id && (
                    <>
                      <a href={`/post/${comment.post_id}?id=${comment.parent_id}`}>parent</a>
                      {' | '}
                    </>
                  )}
                  <span className="on">
                    on: <a href={`/post/${comment.post_id}`}>{comment.post_title}</a>
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
          <td className="title">
            <a href={`/comments?p=${page + 1}`}>More</a>
          </td>
        </tr>
      </tbody>
    </table>
  );
}
