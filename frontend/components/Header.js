'use client';

import { useState, useEffect, useRef } from 'react';
import { useSearchParams, usePathname } from 'next/navigation';
import Link from 'next/link';
import Cookies from 'js-cookie';
import { notificationsAPI, authAPI } from '../lib/api';

export default function Header() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const lastUnreadFetchRef = useRef(0);
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const sortParam = searchParams.get('sort') || 'new';
  const sort = ['new', 'past'].includes(sortParam) ? sortParam : 'new';
  const UNREAD_FETCH_TTL_MS = 5 * 60 * 1000;

  useEffect(() => {
    const authStatus = Cookies.get('auth_status');
    setIsLoggedIn(!!authStatus);

    if (authStatus) {
      maybeFetchUnreadCount();
    }
  }, [pathname]);

  const maybeFetchUnreadCount = async () => {
    const now = Date.now();
    if (now - lastUnreadFetchRef.current < UNREAD_FETCH_TTL_MS) {
      return;
    }
    lastUnreadFetchRef.current = now;

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
              <td className="w-[18px] pr-[4px]">
                <Link href="/">
                  <img
                    src="https://news.ycombinator.com/y18.svg"
                    className="border border-white block h-[20px] w-[20px] max-w-none"
                    alt="Hacker News"
                  />
                </Link>
              </td>
              <td className="leading-[12pt] h-[10px]">
                <span className="pagetop">
                  <b className="hnname">
                    <Link href="/">Hacker News</Link>
                  </b>
                  <Link href="/" className={pathname === '/' && sort === 'new' ? 'topsel' : ''}>new</Link> |{' '}
                  <Link href="/?sort=past" className={pathname === '/' && sort === 'past' ? 'topsel' : ''}>past</Link> |{' '}
                  <Link href="/comments" className={pathname === '/comments' ? 'topsel' : ''}>comments</Link> |{' '}
                  <Link href="/ask" className={pathname === '/ask' ? 'topsel' : ''}>ask</Link> |{' '}
                  <Link href="/show" className={pathname === '/show' ? 'topsel' : ''}>show</Link> |{' '}
                  <Link href="/jobs" className={pathname === '/jobs' ? 'topsel' : ''}>jobs</Link> |{' '}
                  <Link href="/submit" className={pathname === '/submit' ? 'topsel' : ''}>submit</Link>
                </span>
              </td>
              <td className="hn-nav-right text-right pr-1 align-top">
                <span className="pagetop">
                  {isLoggedIn ? (
                    <>
                      <Link href="/notifications">
                        {unreadCount > 0 && `(${unreadCount}) `}
                        notifications
                      </Link>
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
