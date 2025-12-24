export const safeHostname = (url) => {
  if (!url) return null;
  try {
    return new URL(url).hostname;
  } catch (error) {
    return null;
  }
};

export const timeAgo = (date) => {
  const now = new Date();
  const parsedDate = new Date(date);
  const diffInSeconds = Math.floor((now - parsedDate) / 1000);

  if (diffInSeconds < 60) return `${diffInSeconds} seconds ago`;
  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) return `${diffInMinutes} minutes ago`;
  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) return `${diffInHours} hours ago`;
  const diffInDays = Math.floor(diffInHours / 24);
  return `${diffInDays} days ago`;
};

export const pointsLabel = (score) => (score === 1 ? 'point' : 'points');
export const commentsLabel = (count) => (count === 1 ? 'comment' : 'comments');
