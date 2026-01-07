'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import Cookies from 'js-cookie';
import CommentItem from '../../../components/CommentItem';
import { postsAPI, commentsAPI, authAPI } from '../../../lib/api';
import { pointsLabel, safeHostname, timeAgo } from '../../../lib/format';
import { getErrorMessage } from '../../../lib/errors';
import InlineError from '../../../components/InlineError';

const collectCommentIds = (commentList) => {
  const ids = [];
  const stack = [...commentList];
  while (stack.length) {
    const current = stack.pop();
    if (!current) continue;
    ids.push(current.id);
    if (current.replies && current.replies.length) {
      stack.push(...current.replies);
    }
  }
  return ids;
};

export default function PostDetail() {
  const { id } = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const focusedCommentId = searchParams.get('id');
  const [post, setPost] = useState(null);
  const [comments, setComments] = useState([]);
  const [commentVotes, setCommentVotes] = useState({});
  const [loading, setLoading] = useState(true);
  const [commentText, setCommentText] = useState('');
  const [submittingComment, setSubmittingComment] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [postError, setPostError] = useState('');
  const [commentsError, setCommentsError] = useState('');
  const [userVote, setUserVote] = useState(0);

  useEffect(() => {
    // Read the auth token on the client to decide if we can show comment controls.
    const authStatus = Cookies.get('auth_status');
    setIsLoggedIn(!!authStatus);
    if (authStatus) {
      authAPI.me().then((res) => {
        setCurrentUser(res.data);
      }).catch(() => {
        setCurrentUser(null);
        setIsLoggedIn(false);
      });
    }
  }, []);

  useEffect(() => {
    if (id) {
      // Fetch post and comments when the route param is available.
      fetchPost();
      fetchComments();
    }
  }, [id]);

  useEffect(() => {
    if (!focusedCommentId) return;
    const target = document.getElementById(`comment-${focusedCommentId}`);
    if (target) {
      target.scrollIntoView({ block: 'center' });
    }
  }, [comments, focusedCommentId]);

  useEffect(() => {
    if (!isLoggedIn) {
      setCommentVotes({});
      return;
    }
    const ids = collectCommentIds(comments);
    if (ids.length === 0) {
      setCommentVotes({});
      return;
    }
    const fetchCommentVotes = async () => {
      try {
        const response = await commentsAPI.getVotesBulk(ids);
        const voteMap = response.data.reduce((accumulator, vote) => {
          accumulator[vote.comment_id] = vote.vote_type;
          return accumulator;
        }, {});
        setCommentVotes(voteMap);
      } catch (error) {
        setCommentVotes({});
      }
    };
    fetchCommentVotes();
  }, [comments, isLoggedIn]);

  useEffect(() => {
    if (!id || !isLoggedIn) {
      setUserVote(0);
      return;
    }
    const fetchVote = async () => {
      try {
        const response = await postsAPI.getVote(id);
        setUserVote(response.data.vote_type);
      } catch (error) {
        // Ignore vote lookup failures.
      }
    };
    fetchVote();
  }, [id, isLoggedIn]);

  const fetchPost = async () => {
    try {
      setPostError('');
      const response = await postsAPI.getPost(id);
      setPost(response.data);
    } catch (error) {
      setPost(null);
      setPostError(getErrorMessage(error, 'Failed to fetch post.'));
    }
  };

  const fetchComments = async () => {
    try {
      setCommentsError('');
      const response = await commentsAPI.getComments(id);
      setComments(response.data);
    } catch (error) {
      setComments([]);
      setCommentsError(getErrorMessage(error, 'Failed to fetch comments.'));
    } finally {
      setLoading(false);
    }
  };

  const handleCommentSubmit = async (e) => {
    e.preventDefault();
    if (!commentText.trim()) return;
    const authStatus = Cookies.get('auth_status');
    if (!authStatus) {
      // Send the user to login and return to this post afterward.
      router.replace(`/login?next=/post/${id}`);
      return;
    }

    setSubmittingComment(true);
    try {
      await commentsAPI.createComment(id, { text: commentText });
      setCommentText('');
      fetchComments(); // Refresh comments
    } catch (error) {
      setCommentsError(getErrorMessage(error, 'Failed to post comment. Please try again.'));
    } finally {
      setSubmittingComment(false);
    }
  };

  const redirectToLogin = () => {
    router.replace(`/login?next=/post/${id}`);
  };

  const handleVote = async (voteType) => {
    try {
      await postsAPI.vote(id, { vote_type: voteType });
      setUserVote(voteType);
      fetchPost();
    } catch (error) {
      setPostError(getErrorMessage(error, 'Failed to vote. Please try again.'));
    }
  };

  const handleUnvote = async () => {
    try {
      await postsAPI.unvote(id);
      setUserVote(0);
      fetchPost();
    } catch (error) {
      setPostError(getErrorMessage(error, 'Failed to remove vote. Please try again.'));
    }
  };

  if (loading) {
    return <div className="hn-loading">Loading...</div>;
  }

  if (postError) {
    return <InlineError message={postError} />;
  }

  if (!post) {
    return <div className="hn-loading">Post not found</div>;
  }

  const hostname = safeHostname(post.url);

  return (
    <>
      <table border="0" cellPadding="0" cellSpacing="0" className="fatitem">
        <tbody>
          <tr className="athing submission">
            <td className="votelinks" valign="top">
              <center>
                {userVote === 1 ? (
                  <div className="votearrow invisible"></div>
                ) : (
                  <a
                    id={`up_${post.id}`}
                    href="#"
                    onClick={(e) => {
                      e.preventDefault();
                      handleVote(1);
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
                  <span>{post.title}</span>
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
            <td colSpan="1"></td>
            <td className="subtext">
              <span className="subline">
                <span className="points" id={`points_${post.id}`}>{post.points} {pointsLabel(post.points)}</span> by{' '}
                <a href={`/user/${post.username}`} className="hnuser">
                  {post.username}
                </a>{' '}
                <span className="age" title={new Date(post.created_at).toISOString()}>
                  {timeAgo(post.created_at)}
                </span>{' '}
                {isLoggedIn && userVote === 1 && (
                  <>
                    |{' '}
                    <a
                      href="#"
                      onClick={(e) => {
                        e.preventDefault();
                        handleUnvote();
                      }}
                    >
                      unvote
                    </a>{' '}
                  </>
                )}
                |{' '}
                <a href={`/post/${post.id}`}>discuss</a>
              </span>
            </td>
          </tr>
          <tr>
            <td colSpan="1"></td>
            <td>
              <div className="toptext"></div>
            </td>
          </tr>
          <tr className="spacer h-[6px]"></tr>
          <tr>
            <td colSpan="1"></td>
            <td>
              <form onSubmit={handleCommentSubmit}>
                <textarea
                  value={commentText}
                  onChange={isLoggedIn ? (e) => setCommentText(e.target.value) : undefined}
                  onFocus={!isLoggedIn ? redirectToLogin : undefined}
                  onClick={!isLoggedIn ? redirectToLogin : undefined}
                  onKeyDown={!isLoggedIn ? (e) => {
                    e.preventDefault();
                    redirectToLogin();
                  } : undefined}
                  readOnly={!isLoggedIn}
                  className="comment-box"
                  rows={8}
                  cols={80}
                  wrap="virtual"
                  placeholder=""
                />
                <br />
                <br />
                <input
                  type="submit"
                  value={submittingComment ? 'Posting...' : 'add comment'}
                  disabled={submittingComment}
                  className="comment-submit"
                />
              </form>
            </td>
          </tr>
        </tbody>
      </table>

      <br />

      <InlineError message={commentsError} />

      {comments.length > 0 && (
        <div className="comment-tree-wrap">
          <table border="0" cellPadding="0" cellSpacing="0" className="comment-tree">
            <tbody>
              {comments.map((comment) => (
                <CommentItem
                  key={comment.id}
                  comment={comment}
                  onRefresh={fetchComments}
                  currentUser={currentUser}
                  commentVotes={commentVotes}
                  focusedCommentId={focusedCommentId}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {comments.length === 0 && (
        <div className="text-center py-5 text-[#828282] text-[10pt]">
          No comments yet.
        </div>
      )}
    </>
  );
}
