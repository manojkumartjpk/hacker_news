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
  const [usernameStatus, setUsernameStatus] = useState('');
  const [passwordHint, setPasswordHint] = useState('');
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
    setUsernameStatus('');

    try {
      const passwordCheck = checkPasswordStrength(formData.password);
      if (!passwordCheck.valid) {
        setError(passwordCheck.message);
        setLoading(false);
        return;
      }
      await authAPI.register(formData);
      router.push('/login');
    } catch (error) {
      setError(error.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleUsernameBlur = async () => {
    if (!formData.username.trim()) {
      setUsernameStatus('');
      return;
    }
    try {
      const response = await authAPI.usernameAvailable(formData.username.trim());
      setUsernameStatus(response.data.available ? 'available' : 'taken');
    } catch (error) {
      setUsernameStatus('');
    }
  };

  const checkPasswordStrength = (password) => {
    if (password.length < 8) {
      return { valid: false, message: 'Password must be at least 8 characters.' };
    }
    if (!/[A-Za-z]/.test(password) || !/[0-9]/.test(password)) {
      return { valid: false, message: 'Password must include letters and numbers.' };
    }
    return { valid: true, message: 'Password strength: good.' };
  };

  const handlePasswordChange = (e) => {
    handleChange(e);
    const result = checkPasswordStrength(e.target.value);
    setPasswordHint(result.message);
  };

  return (
    <table border="0" cellPadding="0" cellSpacing="0">
      <tbody>
        <tr>
          <td className="title" style={{ paddingBottom: '10px' }}>create account</td>
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
                        onBlur={handleUsernameBlur}
                        title="Pick a unique username"
                        style={{ width: '200px' }}
                        required
                      />
                    </td>
                    <td className="hn-form-status">
                      {usernameStatus === 'taken' && (
                        <span className="hn-error">taken</span>
                      )}
                      {usernameStatus === 'available' && (
                        <span className="hn-success">available</span>
                      )}
                    </td>
                  </tr>
                  <tr>
                    <td className="hn-form-label">email:</td>
                    <td>
                      <input
                        type="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        title="Enter a valid email address"
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
                        onChange={handlePasswordChange}
                        title="At least 8 characters with letters and numbers"
                        style={{ width: '200px' }}
                        required
                      />
                    </td>
                    <td className="hn-form-status">
                      {passwordHint && (
                        <span className={passwordHint.includes('good') ? 'hn-success' : 'hn-error'}>
                          {passwordHint.replace('Password strength: ', '')}
                        </span>
                      )}
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
                        {loading ? 'creating...' : 'create account'}
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </form>

            <div style={{ marginTop: '20px' }}>
              <Link href="/login" style={{ color: '#ff6600' }}>login</Link>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  );
}
