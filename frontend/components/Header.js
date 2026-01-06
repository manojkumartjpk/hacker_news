'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, usePathname } from 'next/navigation';
import Link from 'next/link';
import Cookies from 'js-cookie';
import { notificationsAPI, authAPI } from '../lib/api';

export default function Header() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const sortParam = searchParams.get('sort') || 'new';
  const sort = ['new', 'past'].includes(sortParam) ? sortParam : 'new';

  useEffect(() => {
    const authStatus = Cookies.get('auth_status');
    setIsLoggedIn(!!authStatus);

    if (authStatus) {
      fetchUnreadCount();
    }
  }, [pathname]);

  const fetchUnreadCount = async () => {
    try {
      const response = await notificationsAPI.getUnreadCount();
      setUnreadCount(response.data.unread_count);
    } catch (error) {
      console.error('Failed to fetch unread count:', error);
    }
  };

  const handleLogout = async () => {
    try {
      await authAPI.logout();
    } catch (error) {
      console.error('Failed to logout:', error);
    }
    Cookies.remove('auth_status');
    Cookies.remove('csrf_token');
    setIsLoggedIn(false);
    setUnreadCount(0);
    window.location.href = '/';
  };

  return (
    <tr>
      <td className="bg-[#ff6600] p-[2px]">
        <table border="0" cellPadding="0" cellSpacing="0" width="100%" className="w-full">
          <tbody>
            <tr>
              <td className="w-[18px] pr-1">
                <a href="/">
                  <img
                    src="https://news.ycombinator.com/y18.svg"
                    width="18"
                    height="18"
                    className="border border-white block"
                    alt="Hacker News"
                  />
                </a>
              </td>
              <td className="leading-[12pt] h-[10px]">
                <span className="pagetop">
                  <b className="hnname">
                    <a href="/">Hacker News</a>
                  </b>
                  <a href="/" className={pathname === '/' && sort === 'new' ? 'topsel' : ''}>new</a> |{' '}
                  <a href="/?sort=past" className={pathname === '/' && sort === 'past' ? 'topsel' : ''}>past</a> |{' '}
                  <a href="/comments" className={pathname === '/comments' ? 'topsel' : ''}>comments</a> |{' '}
                  <a href="/ask" className={pathname === '/ask' ? 'topsel' : ''}>ask</a> |{' '}
                  <a href="/show" className={pathname === '/show' ? 'topsel' : ''}>show</a> |{' '}
                  <a href="/jobs" className={pathname === '/jobs' ? 'topsel' : ''}>jobs</a> |{' '}
                  <a href="/submit" className={pathname === '/submit' ? 'topsel' : ''}>submit</a>
                </span>
              </td>
              <td className="hn-nav-right text-right pr-1 align-top">
                <span className="pagetop">
                  {isLoggedIn ? (
                    <>
                      <a href="/notifications">
                        {unreadCount > 0 && `(${unreadCount}) `}
                        notifications
                      </a>
                      {' | '}
                      <a
                        href="#"
                        onClick={(e) => {
                          e.preventDefault();
                          handleLogout();
                        }}
                      >
                        logout
                      </a>
                    </>
                  ) : (
                    <a href="/login">login</a>
                  )}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </td>
    </tr>
  );
}
