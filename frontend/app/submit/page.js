'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';
import { postsAPI } from '../../lib/api';
import { getErrorMessage } from '../../lib/errors';
import InlineError from '../../components/InlineError';

export default function Submit() {
  const [formData, setFormData] = useState({
    title: '',
    url: '',
    text: '',
    post_type: 'story'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [authChecked, setAuthChecked] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const authStatus = Cookies.get('auth_status');
    if (!authStatus) {
      router.replace('/login?next=/submit');
      return;
    }
    setAuthChecked(true);
  }, [router]);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // Validate that either URL or text is provided
    if (!formData.url && !formData.text) {
      setError('Please provide either a URL or text content.');
      setLoading(false);
      return;
    }

    try {
      await postsAPI.createPost(formData);
      router.push('/');
    } catch (error) {
      setError(getErrorMessage(error, 'Failed to submit post. Please try again.'));
    } finally {
      setLoading(false);
    }
  };

  if (!authChecked) {
    return null;
  }

  return (
    <table border="0" cellPadding="0" cellSpacing="0" width="50%">
      <tbody>
        <tr>
          <td className="title pb-2.5 submit-title-cell">Submit</td>
        </tr>
        <tr>
          <td>
            <InlineError message={error} />

            <form onSubmit={handleSubmit} className="hn-form submit-form">
              <table border="0" cellPadding="0" cellSpacing="0" className="hn-form-table submit-table">
                <tbody>
                  <tr>
                    <td className="hn-form-label submit-label">Title:</td>
                    <td className="submit-field">
                      <input
                        type="text"
                        name="title"
                        value={formData.title}
                        onChange={handleChange}
                        className="submit-input"
                        required
                      />
                    </td>
                  </tr>
                  <tr>
                    <td className="hn-form-label submit-label">URL:</td>
                    <td className="submit-field">
                      <input
                        type="url"
                        name="url"
                        value={formData.url}
                        onChange={handleChange}
                        placeholder="https://example.com"
                        className="submit-input"
                      />
                      <div className="submit-helper">
                        Leave blank to submit a text post
                      </div>
                    </td>
                  </tr>
                  <tr>
                    <td className="hn-form-label submit-label">Text:</td>
                    <td className="submit-field">
                      <textarea
                        name="text"
                        value={formData.text}
                        onChange={handleChange}
                        className="comment-box submit-textarea"
                        placeholder="Text (optional if URL is provided)"
                      />
                    </td>
                  </tr>
                  <tr>
                    <td className="hn-form-label submit-label">Type:</td>
                    <td className="submit-field">
                      <select
                        name="post_type"
                        value={formData.post_type}
                        onChange={handleChange}
                        className="submit-select"
                      >
                        <option value="story">story</option>
                        <option value="ask">ask</option>
                        <option value="show">show</option>
                        <option value="job">job</option>
                      </select>
                    </td>
                  </tr>
                  <tr>
                    <td></td>
                    <td className="submit-field">
                      <button
                        type="submit"
                        disabled={loading}
                        className="comment-submit submit-button"
                      >
                        {loading ? 'Submitting...' : 'Submit'}
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </form>
          </td>
        </tr>
      </tbody>
    </table>
  );
}
