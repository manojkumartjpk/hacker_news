'use client';

export default function InlineError({ message, className = 'hn-error' }) {
  if (!message) {
    return null;
  }

  return <div className={className}>{message}</div>;
}
