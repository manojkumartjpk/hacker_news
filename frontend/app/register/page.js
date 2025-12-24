'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { authAPI } from '../../lib/api';
import { getErrorMessage } from '../../lib/errors';

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
  const [success, setSuccess] = useState('');
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
    setSuccess('');

    try {
      const passwordCheck = checkPasswordStrength(formData.password);
      if (!passwordCheck.valid) {
        setError(passwordCheck.message);
        setLoading(false);
        return;
      }
      await authAPI.register(formData);
      setSuccess('Account created. Redirecting to login...');
      setTimeout(() => {
        router.push('/login');
      }, 1200);
    } catch (error) {
      setError(getErrorMessage(error, 'Registration failed. Please try again.'));
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
    if (password.length < 9) {
      return { valid: false, message: 'Password must be at least 9 characters.' };
    }
    if (!/[A-Z]/.test(password)) {
      return { valid: false, message: 'Password must include at least one uppercase letter.' };
    }
    if (!/[0-9]/.test(password)) {
      return { valid: false, message: 'Password must include at least one number.' };
    }
    if (!/[^A-Za-z0-9]/.test(password)) {
      return { valid: false, message: 'Password must include at least one special character.' };
    }
    return { valid: true, message: 'Password strength: strong.' };
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
          <td className="title" style={{ paddingBottom: '10px' }}>Create account</td>
        </tr>
        <tr>
          <td>
            {error && (
              <div className="hn-error">
                {error}
              </div>
            )}
            {success && (
              <div className="hn-success">
                {success}
              </div>
            )}

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
                    <td className="hn-form-label">Email:</td>
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
                    <td className="hn-form-label">Password:</td>
                    <td>
                      <input
                        type="password"
                        name="password"
                        value={formData.password}
                        onChange={handlePasswordChange}
                        title="At least 9 characters, 1 uppercase, 1 number, 1 special character"
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
                        {loading ? 'Creating...' : 'Create account'}
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
