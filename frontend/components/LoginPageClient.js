'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import Cookies from 'js-cookie';
import { authAPI } from '../lib/api';
import { getErrorMessage } from '../lib/errors';
import InlineError from './InlineError';

export default function LoginPageClient() {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();
  const searchParams = useSearchParams();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    if (error) {
      setError('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await authAPI.login(formData);
      Cookies.set('access_token', response.data.access_token, { expires: 1/24 }); // 1 hour
      const next = searchParams.get('next');
      const safeNext = getSafeNext(next);
      const vote = searchParams.get('vote');
      const postId = searchParams.get('post');
      const commentId = searchParams.get('comment');
      if (vote && postId) {
        try {
          await fetchVote(postId, vote);
        } catch (err) {
          // ignore, user can retry vote after redirect
        }
      }
      if (vote && commentId) {
        try {
          await fetchCommentVote(commentId, vote);
        } catch (err) {
          // ignore, user can retry vote after redirect
        }
      }
      if (safeNext) {
        router.push(safeNext);
      } else {
        router.push('/');
      }
    } catch (error) {
      setError(getErrorMessage(error, 'Login failed. Please try again.'));
    } finally {
      setLoading(false);
    }
  };

  const getSafeNext = (next) => {
    if (!next) return null;
    if (next.startsWith('/') && !next.startsWith('//')) {
      return next;
    }
    return null;
  };

  const fetchVote = async (postId, voteType) => {
    const { postsAPI } = await import('../lib/api');
    await postsAPI.vote(postId, { vote_type: Number(voteType) });
  };

  const fetchCommentVote = async (commentId, voteType) => {
    const { commentsAPI } = await import('../lib/api');
    await commentsAPI.vote(commentId, { vote_type: Number(voteType) });
  };

  return (
    <table border="0" cellPadding="0" cellSpacing="0">
      <tbody>
        <tr>
          <td className="title" style={{ paddingBottom: '10px' }}>Login</td>
        </tr>
        <tr>
          <td>
            <InlineError message={error} />

            <form onSubmit={handleSubmit} className="hn-form">
              <table border="0" cellPadding="0" cellSpacing="0" className="hn-form-table">
                <tbody>
                  <tr>
                    <td className="hn-form-label">Username:</td>
                    <td>
                      <input
                        type="text"
                        name="username"
                        value={formData.username}
                        onChange={handleChange}
                        title="Enter your username"
                        style={{ width: '200px' }}
                        required
                      />
                    </td>
                  </tr>
                  <tr>
                    <td className="hn-form-label">Password:</td>
                    <td>
                      <input
                        type="password"
                        name="password"
                        value={formData.password}
                        onChange={handleChange}
                        title="Enter your password"
                        style={{ width: '200px' }}
                        required
                      />
                    </td>
                  </tr>
                  <tr>
                    <td></td>
                    <td>
                      <button
                        type="submit"
                        disabled={loading}
                        style={{ marginTop: '10px' }}
                      >
                        {loading ? 'Logging in...' : 'Login'}
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </form>

            <div style={{ marginTop: '20px' }}>
              <Link href="/register" style={{ color: '#ff6600' }}>Create account</Link>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  );
}
