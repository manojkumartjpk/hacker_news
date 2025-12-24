import { safeHostname, timeAgo, pointsLabel, commentsLabel } from '../lib/format';

describe('format helpers', () => {
  it('parses safeHostname for valid URLs', () => {
    expect(safeHostname('https://example.com/path')).toBe('example.com');
  });

  it('returns null for invalid URLs', () => {
    expect(safeHostname('not a url')).toBeNull();
    expect(safeHostname('')).toBeNull();
  });

  it('formats timeAgo for minutes and days', () => {
    const now = Date.now();
    const minutesAgo = new Date(now - 5 * 60 * 1000).toISOString();
    const daysAgo = new Date(now - 2 * 24 * 60 * 60 * 1000).toISOString();
    expect(timeAgo(minutesAgo)).toContain('minutes ago');
    expect(timeAgo(daysAgo)).toContain('days ago');
  });

  it('formats timeAgo for hours', () => {
    const now = Date.now();
    const hoursAgo = new Date(now - 3 * 60 * 60 * 1000).toISOString();
    expect(timeAgo(hoursAgo)).toContain('hours ago');
  });

  it('formats timeAgo for seconds', () => {
    const now = Date.now();
    const secondsAgo = new Date(now - 10 * 1000).toISOString();
    expect(timeAgo(secondsAgo)).toContain('seconds ago');
  });

  it('formats labels correctly', () => {
    expect(pointsLabel(1)).toBe('point');
    expect(pointsLabel(2)).toBe('points');
    expect(commentsLabel(1)).toBe('comment');
    expect(commentsLabel(3)).toBe('comments');
  });
});
