'use client';

import { useState, useEffect } from 'react';
import { notificationsAPI } from '../../lib/api';
import { timeAgo } from '../../lib/format';
import { getErrorMessage } from '../../lib/errors';
import InlineError from '../../components/InlineError';

export default function Notifications() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await notificationsAPI.getNotifications({ limit: 50 });
      setNotifications(response.data);
    } catch (error) {
      setError(getErrorMessage(error, 'Failed to fetch notifications.'));
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
      setError(getErrorMessage(error, 'Failed to mark notification as read.'));
    }
  };

  if (loading) {
    return <div className="hn-loading">Loading...</div>;
  }

  if (error) {
    return <InlineError message={error} />;
  }

  return (
    <table border="0" cellPadding="0" cellSpacing="0">
      <tbody>
        <tr>
          <td className="title pb-2.5">Notifications</td>
        </tr>
        <tr>
          <td>
            {notifications.length > 0 ? (
              <table border="0" cellPadding="0" cellSpacing="0">
                <tbody>
                  {notifications.map((notification) => (
                    <tr key={notification.id}>
                      <td className="py-1">
                        <div className="text-[10pt] mb-0.5">
                          {notification.message}
                        </div>
                        <div className="text-[8pt] text-[#828282]">
                          {timeAgo(notification.created_at)}
                          {!notification.read && (
                            <span className="ml-2">
                              <button
                                onClick={() => markAsRead(notification.id)}
                                className="text-[#ff6600] no-underline text-[8pt]"
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
              <div className="text-center py-5 text-[#828282] text-[10pt]">
                No notifications yet.
              </div>
            )}
          </td>
        </tr>
      </tbody>
    </table>
  );
}
