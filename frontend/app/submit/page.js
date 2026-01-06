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
    <table border="0" cellPadding="0" cellSpacing="0">
      <tbody>
        <tr>
          <td className="title pb-2.5">Submit</td>
        </tr>
        <tr>
          <td>
            <InlineError message={error} />

            <form onSubmit={handleSubmit} className="hn-form">
              <table border="0" cellPadding="0" cellSpacing="0" className="hn-form-table">
                <tbody>
                  <tr>
                    <td className="hn-form-label">Title:</td>
                    <td>
                      <input
                        type="text"
                        name="title"
                        value={formData.title}
                        onChange={handleChange}
                        className="w-full"
                        required
                      />
                    </td>
                  </tr>
                  <tr>
                    <td className="hn-form-label">URL:</td>
                    <td>
                      <input
                        type="url"
                        name="url"
                        value={formData.url}
                        onChange={handleChange}
                        placeholder="https://example.com"
                        className="w-full"
                      />
                      <div className="text-[8pt] text-[#828282] mt-0.5">
                        Leave blank to submit a text post
                      </div>
                    </td>
                  </tr>
                  <tr>
                    <td className="hn-form-label">Text:</td>
                    <td>
                      <textarea
                        name="text"
                        value={formData.text}
                        onChange={handleChange}
                        className="comment-box"
                        placeholder="Text (optional if URL is provided)"
                      />
                    </td>
                  </tr>
                  <tr>
                    <td className="hn-form-label">Type:</td>
                    <td>
                      <select
                        name="post_type"
                        value={formData.post_type}
                        onChange={handleChange}
                        className="w-[200px]"
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
                    <td>
                      <button
                        type="submit"
                        disabled={loading}
                        className="mt-2.5"
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
