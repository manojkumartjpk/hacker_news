'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { authAPI } from '../../lib/api';

export default function Register() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
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
      await authAPI.register(formData);
      router.push('/login');
    } catch (error) {
      setError(error.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <table border="0" cellPadding="0" cellSpacing="0">
      <tbody>
        <tr>
          <td className="title" style={{ paddingBottom: '10px' }}>Create Account</td>
        </tr>
        <tr>
          <td>
            {error && (
              <div className="hn-error">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="hn-form">
              <table border="0" cellPadding="0" cellSpacing="0">
                <tbody>
                  <tr>
                    <td style={{ paddingRight: '10px' }}>username:</td>
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
                    <td style={{ paddingRight: '10px' }}>email:</td>
                    <td>
                      <input
                        type="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        style={{ width: '200px' }}
                        required
                      />
                    </td>
                  </tr>
                  <tr>
                    <td style={{ paddingRight: '10px' }}>password:</td>
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
                        {loading ? 'Creating...' : 'create account'}
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </form>

            <div style={{ marginTop: '20px' }}>
              <Link href="/login" style={{ color: '#ff6600' }}>Login</Link>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  );
}
