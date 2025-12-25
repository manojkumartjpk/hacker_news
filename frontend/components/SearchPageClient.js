'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import React from 'react';
import { postsAPI } from '../lib/api';
import { commentsLabel, pointsLabel, safeHostname, timeAgo } from '../lib/format';
import { getErrorMessage } from '../lib/errors';

const RESULTS_PER_PAGE = 30;

export default function SearchPageClient() {
  const searchParams = useSearchParams();
  const query = searchParams.get('q') || '';
  const pageParam = Number.parseInt(searchParams.get('p') || '1', 10);
  const page = Number.isNaN(pageParam) || pageParam < 1 ? 1 : pageParam;

  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchResults();
  }, [query, page]);

  const fetchResults = async () => {
    if (!query.trim()) {
      setPosts([]);
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      setError('');
      const skip = (page - 1) * RESULTS_PER_PAGE;
      const response = await postsAPI.searchPosts({ q: query, skip, limit: RESULTS_PER_PAGE });
      setPosts(response.data);
    } catch (error) {
      setError(getErrorMessage(error, 'Failed to fetch search results.'));
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="hn-loading">Loading...</div>;
  }

  if (error) {
    return <div className="hn-error">{error}</div>;
  }

  if (!posts.length) {
    return <div className="hn-loading">No results found.</div>;
  }

  const handleVote = async (postId, voteType) => {
    try {
      setError('');
      await postsAPI.vote(postId, { vote_type: voteType });
      fetchResults();
    } catch (error) {
      setError(getErrorMessage(error, 'Failed to vote. Please try again.'));
    }
  };

  return (
    <table border="0" cellPadding="0" cellSpacing="0">
      <tbody>
        {posts.map((post, index) => {
          const hostname = safeHostname(post.url);
          const rank = (page - 1) * RESULTS_PER_PAGE + index + 1;
          return (
            <React.Fragment key={post.id}>
              <tr className="athing submission">
                <td style={{ textAlign: 'right', verticalAlign: 'top' }} className="title">
                  <span className="rank">{rank}.</span>
                </td>
                <td style={{ verticalAlign: 'top' }} className="votelinks">
                  <center>
                    <a
                      id={`up_${post.id}`}
                      href="#"
                      onClick={(e) => {
                        e.preventDefault();
                        handleVote(post.id, 1);
                      }}
                    >
                      <div className="votearrow" title="upvote"></div>
                    </a>
                  </center>
                </td>
                <td className="title">
                  <span className="titleline">
                    {post.url ? (
                      <a href={post.url} target="_blank" rel="noopener noreferrer">
                        {post.title}
                      </a>
                    ) : (
                      <a href={`/post/${post.id}`}>
                        {post.title}
                      </a>
                    )}
                    {hostname && (
                      <span className="sitebit comhead">
                        {' '}
                        (
                        <a href={`from?site=${hostname}`}>
                          <span className="sitestr">{hostname}</span>
                        </a>
                        )
                      </span>
                    )}
                  </span>
                </td>
              </tr>
              <tr>
                <td colSpan="2"></td>
                <td className="subtext">
                  <span className="subline">
                    <span className="score" id={`score_${post.id}`}>{post.score} {pointsLabel(post.score)}</span> by{' '}
                    <a href={`/user/${post.username}`} className="hnuser">
                      {post.username}
                    </a>{' '}
                    <span className="age" title={new Date(post.created_at).toISOString()}>
                      <a href={`/post/${post.id}`}>{timeAgo(post.created_at)}</a>
                    </span>{' '}
                    <span id={`unv_${post.id}`}></span> |{' '}
                    <a href={`/post/${post.id}`}>
                      {post.comment_count > 0
                        ? `${post.comment_count} ${commentsLabel(post.comment_count)}`
                        : 'discuss'}
                    </a>
                  </span>
                </td>
              </tr>
              <tr className="spacer" style={{ height: '5px' }}></tr>
            </React.Fragment>
          );
        })}
        <tr className="spacer" style={{ height: '10px' }}></tr>
        <tr>
          <td colSpan="2"></td>
          <td className="title">
            <a href={`/search?q=${encodeURIComponent(query)}&p=${page + 1}`}>More</a>
          </td>
        </tr>
      </tbody>
    </table>
  );
}
