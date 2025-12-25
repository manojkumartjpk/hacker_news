'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, usePathname, useRouter } from 'next/navigation';
import React from 'react';
import { postsAPI } from '../lib/api';
import Cookies from 'js-cookie';
import { commentsLabel, pointsLabel, safeHostname, timeAgo } from '../lib/format';
import { getErrorMessage } from '../lib/errors';
import InlineError from './InlineError';
import { getPagination } from '../lib/pagination';

const POSTS_PER_PAGE = 30;

export default function FeedList({ defaultSort = 'new', postType = null }) {
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();
  const sortParam = searchParams.get('sort') || defaultSort;
  const sort = ['new', 'top', 'best'].includes(sortParam) ? sortParam : defaultSort;
  const { page, skip } = getPagination(searchParams, POSTS_PER_PAGE);

  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchPosts();
  }, [sort, page, postType]);

  useEffect(() => {
    const authStatus = Cookies.get('auth_status');
    setIsLoggedIn(!!authStatus);
  }, []);

  const fetchPosts = async () => {
    try {
      setLoading(true);
      setError('');
      const params = { sort, limit: POSTS_PER_PAGE, skip };
      if (postType) {
        params.post_type = postType;
      }
      const response = await postsAPI.getPosts(params);
      setPosts(response.data);
    } catch (error) {
      setError(getErrorMessage(error, 'Failed to fetch posts.'));
    } finally {
      setLoading(false);
    }
  };

  const handleVote = async (postId, voteType) => {
    if (!isLoggedIn) {
      const nextUrl = `${pathname}${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
      router.replace(`/login?next=${encodeURIComponent(nextUrl)}&vote=${voteType}&post=${postId}`);
      return;
    }
    try {
      setError('');
      await postsAPI.vote(postId, { vote_type: voteType });
      fetchPosts();
    } catch (error) {
      setError(getErrorMessage(error, 'Failed to vote. Please try again.'));
    }
  };

  if (loading) {
    return <div className="hn-loading">Loading...</div>;
  }

  if (error) {
    return <InlineError message={error} />;
  }

  if (!posts.length) {
    const isMore = page > 1;
    const emptyMessage = postType === 'job'
      ? (isMore ? 'No more job listings.' : 'No job listings found.')
      : postType === 'ask'
        ? (isMore ? 'No more ask posts.' : 'No ask posts found.')
        : postType === 'show'
          ? (isMore ? 'No more show posts.' : 'No show posts found.')
          : (isMore ? 'No more posts.' : 'No posts found.');
    return <div className="hn-loading">{emptyMessage}</div>;
  }

  return (
    <table border="0" cellPadding="0" cellSpacing="0">
      <tbody>
        {posts.map((post, index) => {
          const hostname = safeHostname(post.url);
          const rank = (page - 1) * POSTS_PER_PAGE + index + 1;
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
                    <a
                      id={`down_${post.id}`}
                      href="#"
                      onClick={(e) => {
                        e.preventDefault();
                        handleVote(post.id, -1);
                      }}
                    >
                      <div className="votearrow downvote" title="downvote"></div>
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
                    {post.post_type === 'job' ? (
                      <>
                        <span className="age" title={new Date(post.created_at).toISOString()}>
                          <a href={`/post/${post.id}`}>{timeAgo(post.created_at)}</a>
                        </span>
                      </>
                    ) : (
                      <>
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
                      </>
                    )}
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
            <a href={`${pathname}?p=${page + 1}${sort !== defaultSort ? `&sort=${sort}` : ''}`}>More</a>
          </td>
        </tr>
      </tbody>
    </table>
  );
}
