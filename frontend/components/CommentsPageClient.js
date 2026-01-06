'use client';

import { useState, useEffect } from 'react';
import React from 'react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import Cookies from 'js-cookie';
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
  const [commentVotes, setCommentVotes] = useState({});
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();
  const { page, skip } = getPagination(searchParams, COMMENTS_PER_PAGE);
  const nextUrl = `${pathname}${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  useEffect(() => {
    fetchComments();
  }, [page]);

  useEffect(() => {
    const authStatus = Cookies.get('auth_status');
    setIsLoggedIn(!!authStatus);
  }, []);

  useEffect(() => {
    if (!isLoggedIn || comments.length === 0) {
      setCommentVotes({});
      return;
    }
    const ids = comments.map((comment) => comment.id);
    const fetchVotes = async () => {
      try {
        const response = await commentsAPI.getVotesBulk(ids);
        const voteMap = response.data.reduce((accumulator, vote) => {
          accumulator[vote.comment_id] = vote.vote_type;
          return accumulator;
        }, {});
        setCommentVotes(voteMap);
      } catch (voteError) {
        setCommentVotes({});
      }
    };
    fetchVotes();
  }, [comments, isLoggedIn]);

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

  const handleUnvote = async (commentId) => {
    try {
      setError('');
      await commentsAPI.unvote(commentId);
      setCommentVotes((prev) => ({ ...prev, [commentId]: 0 }));
    } catch (voteError) {
      setError(getErrorMessage(voteError, 'Failed to remove vote. Please try again.'));
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
    <table border="0" cellPadding="0" cellSpacing="0" className="comment-table">
      <tbody>
        {comments.map((comment) => (
          <React.Fragment key={comment.id}>
            {(() => {
              const isDeleted = !!comment.is_deleted;
              const displayText = isDeleted ? 'comment has been deleted' : comment.text;
              return (
            <tr className="athing">
              <td className="votelinks align-top comment-vote-cell">
                <center>
                  {commentVotes[comment.id] === 1 || isDeleted ? (
                    <div className="votearrow invisible"></div>
                  ) : (
                    <a
                      href="#"
                      onClick={async (event) => {
                        event.preventDefault();
                        if (!isLoggedIn) {
                          router.replace(`/login?next=${encodeURIComponent(nextUrl)}&vote=1&comment=${comment.id}`);
                          return;
                        }
                        try {
                          await commentsAPI.vote(comment.id, { vote_type: 1 });
                          setCommentVotes((prev) => ({ ...prev, [comment.id]: 1 }));
                        } catch (voteError) {
                          setError(getErrorMessage(voteError, 'Failed to vote. Please try again.'));
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
                    <span className="navs">
                      {isLoggedIn && commentVotes[comment.id] === 1 && !isDeleted && (
                        <>
                          {' '}
                          |{' '}
                          <a
                            href="#"
                            onClick={(event) => {
                              event.preventDefault();
                              handleUnvote(comment.id);
                            }}
                          >
                            unvote
                          </a>
                        </>
                      )}
                      {comment.parent_id && (
                        <>
                          {' '}
                          | <a href={`/post/${comment.post_id}?id=${comment.parent_id}`}>parent</a>
                        </>
                      )}
                      {' '}
                      | <a href={`/post/${comment.post_id}?id=${comment.id}`}>context</a>
                      <span className="onstory">
                        {' '}
                        | on: <a href={`/post/${comment.post_id}`}>{comment.post_title}</a>
                      </span>
                    </span>
                  </span>
                </div>
                <div className="comment">
                  {displayText}
                </div>
              </td>
            </tr>
              );
            })()}
            <tr className="spacer h-[15px]"></tr>
          </React.Fragment>
        ))}
        <tr className="spacer h-[10px]"></tr>
        <tr>
          <td></td>
          <td className="title">
            <a href={`/comments?p=${page + 1}`} className="morelink" rel="next">More</a>
          </td>
        </tr>
      </tbody>
    </table>
  );
}
