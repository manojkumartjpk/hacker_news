'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';
import { authAPI } from '../../lib/api';

export default function Login() {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
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

    try {
      const response = await authAPI.login(formData);
      Cookies.set('access_token', response.data.access_token, { expires: 1/24 }); // 1 hour
      router.push('/');
    } catch (error) {
      setError(error.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ margin: '20px auto', maxWidth: '400px' }}>
      <h1 style={{ fontSize: '14pt', marginBottom: '20px' }}>Login</h1>
      
      {error && (
        <div style={{ color: '#ff0000', marginBottom: '10px', fontSize: '10pt' }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="hn-form">
        <table className="hn-table">
          <tbody>
            <tr>
              <td style={{ fontSize: '10pt', paddingRight: '10px' }}>username:</td>
              <td>
                <input
                  type="text"
                  name="username"
                  value={formData.username}
                  onChange={handleChange}
                  style={{ width: '200px' }}
                  required
                />
              </td>
            </tr>
            <tr>
              <td style={{ fontSize: '10pt', paddingRight: '10px' }}>password:</td>
              <td>
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
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
                  {loading ? 'Logging in...' : 'login'}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </form>

      <div style={{ marginTop: '20px', fontSize: '10pt' }}>
        <Link href="/register" style={{ color: '#ff6600' }}>Create account</Link>
      </div>
    </div>
  );
}