'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';
import { postsAPI } from '../../lib/api';

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
    const token = Cookies.get('access_token');
    if (!token) {
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
      setError(error.response?.data?.detail || 'Failed to submit post. Please try again.');
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
          <td className="title" style={{ paddingBottom: '10px' }}>Submit</td>
        </tr>
        <tr>
          <td>
            {error && (
              <div className="hn-error">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="hn-form">
              <table border="0" cellPadding="0" cellSpacing="0" className="hn-form-table">
                <tbody>
                  <tr>
                    <td style={{ paddingRight: '10px', verticalAlign: 'top' }}>title:</td>
                    <td>
                      <input
                        type="text"
                        name="title"
                        value={formData.title}
                        onChange={handleChange}
                        style={{ width: '100%' }}
                        required
                      />
                    </td>
                  </tr>
                  <tr>
                    <td style={{ paddingRight: '10px', verticalAlign: 'top' }}>url:</td>
                    <td>
                      <input
                        type="url"
                        name="url"
                        value={formData.url}
                        onChange={handleChange}
                        placeholder="https://example.com"
                        style={{ width: '100%' }}
                      />
                      <div style={{ fontSize: '8pt', color: '#828282', marginTop: '2px' }}>
                        Leave blank to submit a text post
                      </div>
                    </td>
                  </tr>
                  <tr>
                    <td style={{ paddingRight: '10px', verticalAlign: 'top' }}>text:</td>
                    <td>
                      <textarea
                        name="text"
                        value={formData.text}
                        onChange={handleChange}
                        placeholder="Text content (optional if URL is provided)"
                        style={{ width: '100%', height: '100px' }}
                      />
                    </td>
                  </tr>
                  <tr>
                    <td style={{ paddingRight: '10px', verticalAlign: 'top' }}>type:</td>
                    <td>
                      <select
                        name="post_type"
                        value={formData.post_type}
                        onChange={handleChange}
                        style={{ width: '200px' }}
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
                        style={{ marginTop: '10px' }}
                      >
                        {loading ? 'Submitting...' : 'submit'}
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
