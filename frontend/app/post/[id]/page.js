'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Cookies from 'js-cookie';
import CommentItem from '../../../components/CommentItem';
import { postsAPI, commentsAPI, authAPI } from '../../../lib/api';
import { pointsLabel, safeHostname, timeAgo } from '../../../lib/format';
import { getErrorMessage } from '../../../lib/errors';
import InlineError from '../../../components/InlineError';

export default function PostDetail() {
  const { id } = useParams();
  const router = useRouter();
  const [post, setPost] = useState(null);
  const [comments, setComments] = useState([]);
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
      <table border="0" cellPadding="0" cellSpacing="0">
        <tbody>
          <tr className="athing submission">
            <td style={{ textAlign: 'right', verticalAlign: 'top' }} className="title">
              <span className="rank"></span>
            </td>
            <td style={{ verticalAlign: 'top' }} className="votelinks">
              <center>
                {userVote === 1 ? (
                  <div className="votearrow" style={{ visibility: 'hidden' }}></div>
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
            <td colSpan="2"></td>
            <td className="subtext">
                <span className="subline">
                  <span className="score" id={`score_${post.id}`}>{post.score} {pointsLabel(post.score)}</span> by{' '}
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
            <tr className="spacer" style={{ height: '5px' }}></tr>
          </tbody>
      </table>

      <br />

      <InlineError message={commentsError} />

      <table border="0" cellPadding="0" cellSpacing="0">
        <tbody>
          <tr className="comment-form-row">
            <td style={{ textAlign: 'right', verticalAlign: 'top' }} className="title">
              <span className="rank">&nbsp;</span>
            </td>
            <td style={{ verticalAlign: 'top' }} className="votelinks">
              <center>
                <div className="votearrow" style={{ visibility: 'hidden' }}></div>
              </center>
            </td>
            <td>
              {isLoggedIn ? (
                <>
                  <textarea
                    value={commentText}
                    onChange={(e) => setCommentText(e.target.value)}
                    className="comment-box"
                    placeholder=""
                  />
                  <br />
                  <button
                    onClick={handleCommentSubmit}
                    disabled={submittingComment}
                    className="comment-submit"
                  >
                    {submittingComment ? 'Posting...' : 'add comment'}
                  </button>
                </>
              ) : (
                <div className="subtext">
                  <a href={`/login?next=/post/${id}`}>Login</a> to add a comment.
                </div>
              )}
            </td>
          </tr>
        </tbody>
      </table>

      <br />

      {comments.length > 0 && (
        <table border="0" cellPadding="0" cellSpacing="0">
          <tbody>
            {comments.map((comment) => (
              <CommentItem
                key={comment.id}
                comment={comment}
                onRefresh={fetchComments}
                currentUser={currentUser}
              />
            ))}
          </tbody>
        </table>
      )}

      {comments.length === 0 && (
        <div style={{ textAlign: 'center', padding: '20px', color: '#828282', fontSize: '10pt' }}>
          No comments yet.
        </div>
      )}
    </>
  );
}
