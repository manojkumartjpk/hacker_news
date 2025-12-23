'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { notificationsAPI } from '../../lib/api';

export default function Notifications() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const response = await notificationsAPI.getNotifications({ limit: 50 });
      setNotifications(response.data);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (id) => {
    try {
      await notificationsAPI.markAsRead(id);
      setNotifications(notifications.map(n => 
        n.id === id ? { ...n, read: true } : n
      ));
    } catch (error) {
      console.error('Failed to mark as read:', error);
    }
  };

  const timeAgo = (date) => {
    const now = new Date();
    const notifDate = new Date(date);
    const diffInSeconds = Math.floor((now - notifDate) / 1000);

    if (diffInSeconds < 60) return `${diffInSeconds} seconds ago`;
    const diffInMinutes = Math.floor(diffInSeconds / 60);
    if (diffInMinutes < 60) return `${diffInMinutes} minutes ago`;
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours} hours ago`;
    const diffInDays = Math.floor(diffInHours / 24);
    return `${diffInDays} days ago`;
  };

  if (loading) {
    return <div className="hn-loading">Loading...</div>;
  }

  return (
    <table border="0" cellPadding="0" cellSpacing="0">
      <tbody>
        <tr>
          <td className="title" style={{ paddingBottom: '10px' }}>Notifications</td>
        </tr>
        <tr>
          <td>
            {notifications.length > 0 ? (
              <table border="0" cellPadding="0" cellSpacing="0">
                <tbody>
                  {notifications.map((notification) => (
                    <tr key={notification.id}>
                      <td style={{ padding: '4px 0' }}>
                        <div style={{ fontSize: '10pt', marginBottom: '2px' }}>
                          {notification.message}
                        </div>
                        <div style={{ fontSize: '8pt', color: '#828282' }}>
                          {timeAgo(notification.created_at)}
                          {!notification.read && (
                            <span style={{ marginLeft: '8px' }}>
                              <button
                                onClick={() => markAsRead(notification.id)}
                                style={{ color: '#ff6600', textDecoration: 'none', fontSize: '8pt' }}
                              >
                                [mark as read]
                              </button>
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div style={{ textAlign: 'center', padding: '20px', color: '#828282', fontSize: '10pt' }}>
                No notifications yet.
              </div>
            )}
          </td>
        </tr>
      </tbody>
    </table>
  );
}
