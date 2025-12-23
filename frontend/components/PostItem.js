'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { postsAPI } from '../lib/api';

export default function PostItem({ post, onVote }) {
  const [userVote, setUserVote] = useState(0);
  const [score, setScore] = useState(post.score);

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
      // Update score locally (in real app, might refetch or use websocket)
      setScore(prev => prev + (voteType === 1 ? 1 : -1) - (userVote === 1 ? 1 : userVote === -1 ? -1 : 0));
      if (onVote) onVote();
    } catch (error) {
      alert('Failed to vote. Please try again.');
    }
  };

  const timeAgo = (date) => {
    const now = new Date();
    const postDate = new Date(date);
    const diffInSeconds = Math.floor((now - postDate) / 1000);

    if (diffInSeconds < 60) return `${diffInSeconds} seconds ago`;
    const diffInMinutes = Math.floor(diffInSeconds / 60);
    if (diffInMinutes < 60) return `${diffInMinutes} minutes ago`;
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours} hours ago`;
    const diffInDays = Math.floor(diffInHours / 24);
    return `${diffInDays} days ago`;
  };

  return (
    <div className="hn-post">
      <div style={{ marginBottom: '2px' }}>
        <span
          className={`hn-vote-arrow up ${userVote === 1 ? 'voted' : ''}`}
          onClick={() => handleVote(1)}
          style={{ color: userVote === 1 ? '#ff6600' : '#828282' }}
        >
          ▲
        </span>
        <span
          className={`hn-vote-arrow down ${userVote === -1 ? 'voted' : ''}`}
          onClick={() => handleVote(-1)}
          style={{ color: userVote === -1 ? '#0000ff' : '#828282' }}
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
        {post.url && (
          <span className="hn-post-meta" style={{ marginLeft: '4px' }}>
            ({new URL(post.url).hostname})
          </span>
        )}
      </div>
      <div className="hn-post-meta">
        {score} points by{' '}
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