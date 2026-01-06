'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { postsAPI } from '../lib/api';
import { safeHostname, timeAgo } from '../lib/format';
import { getErrorMessage } from '../lib/errors';

export default function PostItem({ post, onVote }) {
  const [userVote, setUserVote] = useState(0);
  const [points, setPoints] = useState(post.points);
  const hostname = safeHostname(post.url);

  useEffect(() => {
    fetchUserVote();
  }, [post.id]);

  const fetchUserVote = async () => {
    try {
      const response = await postsAPI.getVote(post.id);
      setUserVote(response.data.vote_type);
    } catch (error) {
      // User not logged in or error
    }
  };

  const handleVote = async (voteType) => {
    try {
      await postsAPI.vote(post.id, { vote_type: voteType });
      setUserVote(voteType);
      // Update points locally (in real app, might refetch or use websocket)
      setPoints(prev => prev + (voteType === 1 ? 1 : -1) - (userVote === 1 ? 1 : userVote === -1 ? -1 : 0));
      if (onVote) onVote();
    } catch (error) {
      alert(getErrorMessage(error, 'Failed to vote. Please try again.'));
    }
  };

  return (
    <div className="hn-post">
      <div className="mb-0.5">
        <span
          className={`hn-vote-arrow up ${userVote === 1 ? 'voted-up' : ''}`}
          onClick={() => handleVote(1)}
        >
          ▲
        </span>
        <span
          className={`hn-vote-arrow down ${userVote === -1 ? 'voted-down' : ''}`}
          onClick={() => handleVote(-1)}
        >
          ▼
        </span>
        <span className="hn-post-title">
          {post.url ? (
            <a href={post.url} target="_blank" rel="noopener noreferrer">
              {post.title}
            </a>
          ) : (
            <Link href={`/post/${post.id}`}>
              {post.title}
            </Link>
          )}
        </span>
        {post.url && hostname && (
          <span className="hn-post-domain">
            ({hostname})
          </span>
        )}
      </div>
      <div className="hn-post-meta">
        {points} points by{' '}
        <Link href={`/user/${post.username}`} className="hn-comment-link">
          {post.username}
        </Link>{' '}
        {timeAgo(post.created_at)}{' '}
        <span className="hn-comment-link">|</span>{' '}
        <Link href={`/post/${post.id}`} className="hn-comment-link">
          discuss
        </Link>
      </div>
    </div>
  );
}
