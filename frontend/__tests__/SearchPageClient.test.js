import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { act } from 'react';
import SearchPageClient from '../components/SearchPageClient';
import { postsAPI } from '../lib/api';

let searchParamsValue = '';

jest.mock('../lib/api', () => ({
  postsAPI: {
    searchPosts: jest.fn(),
    vote: jest.fn(),
  },
}));

jest.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(searchParamsValue),
}));

jest.mock('../lib/format', () => ({
  safeHostname: jest.requireActual('../lib/format').safeHostname,
  commentsLabel: () => 'comments',
  pointsLabel: () => 'points',
  timeAgo: () => '1 hour ago',
}));

describe('SearchPageClient', () => {
  beforeEach(() => {
    searchParamsValue = '';
    postsAPI.searchPosts.mockResolvedValue({ data: [] });
    postsAPI.vote.mockResolvedValue({ data: {} });
  });

  it('shows empty state when query is blank', async () => {
    render(<SearchPageClient />);
    await waitFor(() => {
      expect(screen.getByText('No results found.')).toBeInTheDocument();
    });
    expect(postsAPI.searchPosts).not.toHaveBeenCalled();
  });

  it('renders search results', async () => {
    searchParamsValue = 'q=hello';
    postsAPI.searchPosts.mockResolvedValueOnce({
      data: [
        {
          id: 1,
          title: 'Hello HN',
          url: 'https://example.com',
          text: null,
          post_type: 'story',
          score: 2,
          comment_count: 1,
          user_id: 1,
          username: 'alice',
          created_at: '2024-01-01T00:00:00Z',
        },
      ],
    });

    render(<SearchPageClient />);
    await waitFor(() => expect(screen.getByText('Hello HN')).toBeInTheDocument());
    expect(screen.getByText(/example\.com/)).toBeInTheDocument();
  });

  it('shows error when search fails', async () => {
    searchParamsValue = 'q=oops';
    postsAPI.searchPosts.mockRejectedValueOnce(new Error('boom'));
    render(<SearchPageClient />);
    await waitFor(() => expect(screen.getByText('boom')).toBeInTheDocument());
  });

  it('votes and refreshes results', async () => {
    const user = userEvent.setup();
    searchParamsValue = 'q=vote';
    postsAPI.searchPosts.mockResolvedValue({
      data: [
        {
          id: 2,
          title: 'Vote me',
          url: 'https://example.com',
          text: null,
          post_type: 'story',
          score: 1,
          comment_count: 0,
          user_id: 1,
          username: 'alice',
          created_at: '2024-01-01T00:00:00Z',
        },
      ],
    });

    render(<SearchPageClient />);
    await waitFor(() => expect(screen.getByText('Vote me')).toBeInTheDocument());
    await act(async () => {
      await user.click(screen.getByTitle('upvote'));
    });

    await waitFor(() => {
      expect(postsAPI.vote).toHaveBeenCalledWith(2, { vote_type: 1 });
      expect(postsAPI.searchPosts).toHaveBeenCalled();
    });
  });
});
