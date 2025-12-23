'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Cookies from 'js-cookie';
import { notificationsAPI } from '../lib/api';

export default function Header() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    const token = Cookies.get('access_token');
    setIsLoggedIn(!!token);

    if (token) {
      fetchUnreadCount();
    }
  }, []);

  const fetchUnreadCount = async () => {
    try {
      const response = await notificationsAPI.getUnreadCount();
      setUnreadCount(response.data.unread_count);
    } catch (error) {
      console.error('Failed to fetch unread count:', error);
    }
  };

  const handleLogout = () => {
    Cookies.remove('access_token');
    setIsLoggedIn(false);
    setUnreadCount(0);
    window.location.href = '/';
  };

  return (
    <header className="hn-header">
      <table className="hn-table">
        <tbody>
          <tr>
            <td style={{ paddingRight: '4px' }}>
              <Link href="/" className="hn-title">
                Hacker News
              </Link>
            </td>
            <td className="hn-nav">
              <Link href="/">new</Link>
              {' | '}
              <Link href="/?sort=top">top</Link>
              {' | '}
              {isLoggedIn ? (
                <>
                  <Link href="/submit">submit</Link>
                  {' | '}
                  <Link href="/notifications">
                    notifications{unreadCount > 0 && ` (${unreadCount})`}
                  </Link>
                  {' | '}
                  <button onClick={handleLogout} style={{ color: '#ffffff', textDecoration: 'none' }}>
                    logout
                  </button>
                </>
              ) : (
                <>
                  <Link href="/login">login</Link>
                  {' | '}
                  <Link href="/register">register</Link>
                </>
              )}
            </td>
          </tr>
        </tbody>
      </table>
    </header>
  );
}