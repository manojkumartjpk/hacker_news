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

const toISODate = (date) => date.toISOString().slice(0, 10);

const parseDayParam = (value) => {
  if (!value) {
    return null;
  }
  const parsed = new Date(`${value}T00:00:00Z`);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }
  return parsed;
};

const addUtcDays = (date, delta) => (
  new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate() + delta))
);

const addUtcMonths = (date, delta) => (
  new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth() + delta, date.getUTCDate()))
);

const addUtcYears = (date, delta) => (
  new Date(Date.UTC(date.getUTCFullYear() + delta, date.getUTCMonth(), date.getUTCDate()))
);

const formatUtcDate = (date) => (
  new Intl.DateTimeFormat('en-US', {
    timeZone: 'UTC',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(date)
);

export default function FeedList({ defaultSort = 'new', postType = null }) {
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();
  const sortParam = searchParams.get('sort') || defaultSort;
  const sort = ['new', 'past'].includes(sortParam) ? sortParam : defaultSort;
  const dayParam = searchParams.get('day');
  const { page, skip } = getPagination(searchParams, POSTS_PER_PAGE);

  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [error, setError] = useState('');
  const [userVotes, setUserVotes] = useState({});

  useEffect(() => {
    fetchPosts();
  }, [sort, page, postType, dayParam]);

  useEffect(() => {
    const authStatus = Cookies.get('auth_status');
    setIsLoggedIn(!!authStatus);
  }, []);

  useEffect(() => {
    if (!isLoggedIn || posts.length === 0) {
      setUserVotes({});
      return;
    }
    const fetchVotes = async () => {
      try {
        const response = await postsAPI.getVotesBulk(posts.map((post) => post.id));
        const entries = response.data.map(({ post_id, vote_type }) => [post_id, vote_type]);
        setUserVotes(Object.fromEntries(entries));
      } catch (error) {
        // Ignore vote lookup failures to keep the feed usable.
      }
    };
    fetchVotes();
  }, [isLoggedIn, posts]);

  const fetchPosts = async () => {
    try {
      setLoading(true);
      setError('');
      const params = { sort, limit: POSTS_PER_PAGE, skip };
      if (sort === 'past' && dayParam) {
        params.day = dayParam;
      }
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

  const handleVote = async (postId) => {
    if (!isLoggedIn) {
      const nextUrl = `${pathname}${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
      router.replace(`/login?next=${encodeURIComponent(nextUrl)}&vote=1&post=${postId}`);
      return;
    }
    try {
      setError('');
      await postsAPI.vote(postId, { vote_type: 1 });
      setUserVotes((prev) => ({ ...prev, [postId]: 1 }));
      fetchPosts();
    } catch (error) {
      setError(getErrorMessage(error, 'Failed to vote. Please try again.'));
    }
  };

  const handleUnvote = async (postId) => {
    try {
      setError('');
      await postsAPI.unvote(postId);
      setUserVotes((prev) => ({ ...prev, [postId]: 0 }));
      fetchPosts();
    } catch (error) {
      setError(getErrorMessage(error, 'Failed to remove vote. Please try again.'));
    }
  };

  if (loading) {
    return <div className="hn-loading">Loading...</div>;
  }

  if (error) {
    return <InlineError message={error} />;
  }

  const parsedDay = parseDayParam(dayParam);
  const selectedDay = sort === 'past'
    ? (parsedDay || (posts[0]?.created_at ? new Date(posts[0].created_at) : null))
    : null;
  const selectedDayIso = selectedDay ? toISODate(selectedDay) : null;
  const pastHeader = sort === 'past' && selectedDay ? (
    <div className="hn-past-header">
      <div className="text-hn-gray">Stories from {formatUtcDate(selectedDay)} (UTC)</div>
      <div className="hn-past-nav">
        Go back a{' '}
        <a href={`${pathname}?sort=past&day=${toISODate(addUtcDays(selectedDay, -1))}`}>day</a>,{' '}
        <a href={`${pathname}?sort=past&day=${toISODate(addUtcMonths(selectedDay, -1))}`}>month</a>, or{' '}
        <a href={`${pathname}?sort=past&day=${toISODate(addUtcYears(selectedDay, -1))}`}>year</a>. Go forward a{' '}
        <a href={`${pathname}?sort=past&day=${toISODate(addUtcDays(selectedDay, 1))}`}>day</a>.
      </div>
    </div>
  ) : null;

  if (!posts.length) {
    const isMore = page > 1;
    const emptyMessage = postType === 'job'
      ? (isMore ? 'No more job listings.' : 'No job listings found.')
      : postType === 'ask'
        ? (isMore ? 'No more ask posts.' : 'No ask posts found.')
        : postType === 'show'
          ? (isMore ? 'No more show posts.' : 'No show posts found.')
          : (isMore ? 'No more posts.' : 'No posts found.');
    return (
      <>
        {pastHeader}
        <div className="hn-loading">{emptyMessage}</div>
      </>
    );
  }

  return (
    <>
      {pastHeader}
      <table border="0" cellPadding="0" cellSpacing="0">
        <tbody>
          {posts.map((post, index) => {
            const hostname = safeHostname(post.url);
            const rank = (page - 1) * POSTS_PER_PAGE + index + 1;
            const userVote = userVotes[post.id] || 0;
            return (
              <React.Fragment key={post.id}>
                <tr className="athing submission">
                  <td className="title align-top text-right">
                    <span className="rank">{rank}.</span>
                  </td>
                  <td className="votelinks align-top">
                    <center>
                      {userVote === 1 ? (
                        <div className="votearrow invisible"></div>
                      ) : (
                        <a
                          id={`up_${post.id}`}
                          href="#"
                          onClick={(e) => {
                            e.preventDefault();
                            handleVote(post.id);
                          }}
                        >
                          <div className="votearrow" title="upvote"></div>
                        </a>
                      )}
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
                          <span className="points" id={`points_${post.id}`}>{post.points} {pointsLabel(post.points)}</span> by{' '}
                          <a href={`/user/${post.username}`} className="hnuser">
                            {post.username}
                          </a>{' '}
                          <span className="age" title={new Date(post.created_at).toISOString()}>
                            <a href={`/post/${post.id}`}>{timeAgo(post.created_at)}</a>
                          </span>{' '}
                          {isLoggedIn && userVote === 1 && (
                            <>
                              |{' '}
                              <a
                                href="#"
                                onClick={(e) => {
                                  e.preventDefault();
                                  handleUnvote(post.id);
                                }}
                              >
                                unvote
                              </a>{' '}
                            </>
                          )}
                          |{' '}
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
                <tr className="spacer h-[5px]"></tr>
              </React.Fragment>
            );
          })}
          <tr className="spacer h-[10px]"></tr>
          <tr>
            <td colSpan="2"></td>
            <td className="title">
              <a
                href={`${pathname}?p=${page + 1}${sort !== defaultSort ? `&sort=${sort}` : ''}${
                  sort === 'past' && selectedDayIso ? `&day=${encodeURIComponent(selectedDayIso)}` : ''
                }`}
              >
                More
              </a>
            </td>
          </tr>
        </tbody>
      </table>
    </>
  );
}
