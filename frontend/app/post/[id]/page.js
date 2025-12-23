'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Cookies from 'js-cookie';
import CommentItem from '../../../components/CommentItem';
import { postsAPI, commentsAPI, authAPI } from '../../../lib/api';

const safeHostname = (url) => {
  if (!url) return null;
  try {
    return new URL(url).hostname;
  } catch (error) {
    return null;
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

const pointsLabel = (score) => (score === 1 ? 'point' : 'points');

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

  useEffect(() => {
    const token = Cookies.get('access_token');
    setIsLoggedIn(!!token);
    if (token) {
      authAPI.me().then((res) => {
        setCurrentUser(res.data);
      }).catch(() => {
        setCurrentUser(null);
      });
    }
  }, []);

  useEffect(() => {
    if (id) {
      fetchPost();
      fetchComments();
    }
  }, [id]);

  const fetchPost = async () => {
    try {
      const response = await postsAPI.getPost(id);
      setPost(response.data);
    } catch (error) {
      console.error('Failed to fetch post:', error);
    }
  };

  const fetchComments = async () => {
    try {
      const response = await commentsAPI.getComments(id);
      setComments(response.data);
    } catch (error) {
      console.error('Failed to fetch comments:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCommentSubmit = async (e) => {
    e.preventDefault();
    if (!commentText.trim()) return;
    const token = Cookies.get('access_token');
    if (!token) {
      router.replace(`/login?next=/post/${id}`);
      return;
    }

    setSubmittingComment(true);
    try {
      await commentsAPI.createComment(id, { text: commentText });
      setCommentText('');
      fetchComments(); // Refresh comments
    } catch (error) {
      alert('Failed to post comment. Please try again.');
    } finally {
      setSubmittingComment(false);
    }
  };

  const handleReply = async (parentId, text) => {
    const token = Cookies.get('access_token');
    if (!token) {
      router.replace(`/login?next=/post/${id}`);
      return;
    }
    try {
      await commentsAPI.createComment(id, { text, parent_id: parentId });
      fetchComments(); // Refresh comments
    } catch (error) {
      alert('Failed to post reply. Please try again.');
    }
  };

  const handleVote = async (voteType) => {
    try {
      await postsAPI.vote(id, { vote_type: voteType });
      fetchPost();
    } catch (error) {
      alert('Failed to vote. Please try again.');
    }
  };

  if (loading) {
    return <div className="hn-loading">Loading...</div>;
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
                  <span id={`unv_${post.id}`}></span> |{' '}
                  <a href={`/post/${post.id}`}>discuss</a>
                </span>
              </td>
            </tr>
            <tr className="spacer" style={{ height: '5px' }}></tr>
          </tbody>
      </table>

      <br />

      <table border="0" cellPadding="0" cellSpacing="0">
        <tbody>
          <tr>
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
                onReply={handleReply}
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
