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
    <table border="0" cellPadding="0" cellSpacing="0">
      <tbody>
        <tr>
          <td className="title" style={{ paddingBottom: '10px' }}>login</td>
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
                    <td className="hn-form-label">username:</td>
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
                    <td className="hn-form-label">password:</td>
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
                        {loading ? 'logging in...' : 'login'}
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </form>

            <div style={{ marginTop: '20px' }}>
              <Link href="/register" style={{ color: '#ff6600' }}>create account</Link>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  );
}
