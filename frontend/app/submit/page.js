'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { postsAPI } from '../../lib/api';

export default function Submit() {
  const [formData, setFormData] = useState({
    title: '',
    url: '',
    text: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

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

  return (
    <div style={{ margin: '20px auto', maxWidth: '600px' }}>
      <h1 style={{ fontSize: '14pt', marginBottom: '20px' }}>Submit</h1>
      
      {error && (
        <div style={{ color: '#ff0000', marginBottom: '10px', fontSize: '10pt' }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="hn-form">
        <table className="hn-table">
          <tbody>
            <tr>
              <td style={{ fontSize: '10pt', paddingRight: '10px', verticalAlign: 'top' }}>title:</td>
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
              <td style={{ fontSize: '10pt', paddingRight: '10px', verticalAlign: 'top' }}>url:</td>
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
              <td style={{ fontSize: '10pt', paddingRight: '10px', verticalAlign: 'top' }}>text:</td>
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
    </div>
  );
}