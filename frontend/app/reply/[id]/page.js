'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Cookies from 'js-cookie';
import { commentsAPI } from '../../../lib/api';
import { timeAgo } from '../../../lib/format';
import { getErrorMessage } from '../../../lib/errors';
import InlineError from '../../../components/InlineError';

export default function ReplyPage() {
  const { id } = useParams();
  const router = useRouter();
  const [comment, setComment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [replyText, setReplyText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const authStatus = Cookies.get('auth_status');
    setIsLoggedIn(!!authStatus);
  }, []);

  useEffect(() => {
    if (!id) return;
    const fetchComment = async () => {
      try {
        setLoading(true);
        setError('');
        const response = await commentsAPI.getComment(id);
        setComment(response.data);
      } catch (error) {
        setError(getErrorMessage(error, 'Failed to fetch comment.'));
      } finally {
        setLoading(false);
      }
    };
    fetchComment();
  }, [id]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!replyText.trim() || !comment) return;
    const authStatus = Cookies.get('auth_status');
    if (!authStatus) {
      router.replace(`/login?next=/reply/${id}`);
      return;
    }
    try {
      setSubmitting(true);
      setError('');
      await commentsAPI.createComment(comment.post_id, { text: replyText, parent_id: comment.id });
      setReplyText('');
      router.push(`/post/${comment.post_id}?id=${comment.id}`);
    } catch (error) {
      setError(getErrorMessage(error, 'Failed to post reply. Please try again.'));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="hn-loading">Loading...</div>;
  }

  if (error) {
    return <InlineError message={error} />;
  }

  if (!comment) {
    return <div className="hn-loading">Comment not found</div>;
  }

  const displayText = comment.is_deleted ? 'comment has been deleted' : comment.text;

  return (
    <>
      <table border="0" cellPadding="0" cellSpacing="0">
        <tbody>
          <tr className="athing">
            <td className="title align-top text-right">
              <span className="rank">&nbsp;</span>
            </td>
            <td className="votelinks align-top">
              <center>
                <div className="votearrow invisible"></div>
              </center>
            </td>
            <td className="title">
              <span className="comhead">
                <a href={`/user/${comment.username}`} className="hnuser">
                  {comment.username}
                </a>{' '}
                <span className="age" title={new Date(comment.created_at).toISOString()}>
                  <a href={`/post/${comment.post_id}?id=${comment.id}`}>{timeAgo(comment.created_at)}</a>
                </span>{' '}
                {comment.parent_id && (
                  <>
                    | <a href={`/post/${comment.post_id}?id=${comment.parent_id}`}>parent</a>{' '}
                  </>
                )}
                | <a href={`/post/${comment.post_id}?id=${comment.id}`}>context</a>{' '}
                | on: <a href={`/post/${comment.post_id}`}>{comment.post_title}</a>
              </span>
              <div className="comment">{displayText}</div>
            </td>
          </tr>
          <tr className="spacer h-[6px]"></tr>
          <tr className="comment-form-row">
            <td className="title align-top text-right">
              <span className="rank">&nbsp;</span>
            </td>
            <td className="votelinks align-top">
              <center>
                <div className="votearrow invisible"></div>
              </center>
            </td>
            <td>
              {isLoggedIn ? (
                <>
                  <textarea
                    value={replyText}
                    onChange={(e) => setReplyText(e.target.value)}
                    className="comment-box"
                    placeholder=""
                  />
                  <br />
                  <button
                    onClick={handleSubmit}
                    disabled={submitting}
                    className="comment-submit"
                  >
                    {submitting ? 'Posting...' : 'reply'}
                  </button>
                </>
              ) : (
                <div className="subtext">
                  <a href={`/login?next=/reply/${comment.id}`}>Login</a> to reply.
                </div>
              )}
            </td>
          </tr>
        </tbody>
      </table>
    </>
  );
}
