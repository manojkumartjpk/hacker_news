import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { act } from 'react';
import FeedList from '../components/FeedList';
import { postsAPI } from '../lib/api';
import Cookies from 'js-cookie';

let replace;
let searchParamsValue = '';

jest.mock('../lib/api', () => ({
  postsAPI: {
    getPosts: jest.fn(),
    vote: jest.fn(),
  },
}));

jest.mock('js-cookie', () => ({
  get: jest.fn(),
}));

jest.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(searchParamsValue),
  usePathname: () => '/news',
  useRouter: () => ({ replace }),
}));

jest.mock('../lib/format', () => ({
  safeHostname: jest.requireActual('../lib/format').safeHostname,
  timeAgo: () => '1 hour ago',
  pointsLabel: jest.requireActual('../lib/format').pointsLabel,
  commentsLabel: jest.requireActual('../lib/format').commentsLabel,
}));

describe('FeedList', () => {
  beforeEach(() => {
    replace = jest.fn();
    searchParamsValue = '';
    postsAPI.getPosts.mockResolvedValue({
      data: [
        {
          id: 1,
          title: 'Hello Feed',
          url: 'https://example.com',
          text: null,
          post_type: 'story',
          score: 3,
          comment_count: 0,
          user_id: 1,
          username: 'alice',
          created_at: '2024-01-01T00:00:00Z',
        },
      ],
    });
  });

  it('renders posts after loading', async () => {
    Cookies.get.mockReturnValue('token');
    render(<FeedList />);

    expect(screen.getByText('Loading...')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText('Hello Feed')).toBeInTheDocument());
    expect(screen.getByText('More')).toBeInTheDocument();
  });

  it('falls back to default sort when invalid', async () => {
    Cookies.get.mockReturnValue('token');
    searchParamsValue = 'sort=invalid';
    render(<FeedList defaultSort="top" />);

    await waitFor(() => expect(postsAPI.getPosts).toHaveBeenCalled());
    expect(postsAPI.getPosts).toHaveBeenCalledWith(expect.objectContaining({ sort: 'top' }));
  });

  it('defaults to page 1 when page param is invalid', async () => {
    Cookies.get.mockReturnValue('token');
    searchParamsValue = 'p=not-a-number';
    render(<FeedList />);

    await waitFor(() => expect(screen.getByText('Hello Feed')).toBeInTheDocument());
    expect(screen.getByText('More').getAttribute('href')).toBe('/news?p=2');
  });

  it('adds post_type when provided', async () => {
    Cookies.get.mockReturnValue('token');
    render(<FeedList postType="show" />);

    await waitFor(() => expect(postsAPI.getPosts).toHaveBeenCalled());
    expect(postsAPI.getPosts).toHaveBeenCalledWith(
      expect.objectContaining({ post_type: 'show' }),
    );
  });

  it('includes sort param in More link when non-default', async () => {
    Cookies.get.mockReturnValue('token');
    searchParamsValue = 'sort=top';
    render(<FeedList defaultSort="new" />);

    await waitFor(() => expect(screen.getByText('Hello Feed')).toBeInTheDocument());
    expect(screen.getByText('More').getAttribute('href')).toBe('/news?p=2&sort=top');
  });

  it('redirects to login when voting while logged out', async () => {
    Cookies.get.mockReturnValue(undefined);
    render(<FeedList />);

    await waitFor(() => expect(screen.getByText('Hello Feed')).toBeInTheDocument());
    await userEvent.click(screen.getByTitle('upvote'));

    expect(replace).toHaveBeenCalledWith('/login?next=%2Fnews&vote=1&post=1');
    expect(postsAPI.vote).not.toHaveBeenCalled();
  });

  it('preserves query string when redirecting for votes', async () => {
    Cookies.get.mockReturnValue(undefined);
    searchParamsValue = 'sort=top&p=2';
    render(<FeedList />);

    await waitFor(() => expect(screen.getByText('Hello Feed')).toBeInTheDocument());
    await userEvent.click(screen.getByTitle('downvote'));

    expect(replace).toHaveBeenCalledWith('/login?next=%2Fnews%3Fsort%3Dtop%26p%3D2&vote=-1&post=1');
  });

  it('shows the error message when fetch fails', async () => {
    Cookies.get.mockReturnValue('token');
    postsAPI.getPosts.mockRejectedValueOnce(new Error('boom'));
    render(<FeedList />);

    await waitFor(() => expect(screen.getByText('boom')).toBeInTheDocument());
  });

  it('renders job empty message when no posts', async () => {
    Cookies.get.mockReturnValue('token');
    searchParamsValue = 'p=2';
    postsAPI.getPosts.mockResolvedValueOnce({ data: [] });
    render(<FeedList postType="job" />);

    await waitFor(() => {
      expect(screen.getByText('No more job listings.')).toBeInTheDocument();
    });
  });

  it('renders job empty message for first page', async () => {
    Cookies.get.mockReturnValue('token');
    postsAPI.getPosts.mockResolvedValueOnce({ data: [] });
    render(<FeedList postType="job" />);

    await waitFor(() => {
      expect(screen.getByText('No job listings found.')).toBeInTheDocument();
    });
  });

  it('renders ask empty message when no posts', async () => {
    Cookies.get.mockReturnValue('token');
    postsAPI.getPosts.mockResolvedValueOnce({ data: [] });
    render(<FeedList postType="ask" />);

    await waitFor(() => {
      expect(screen.getByText('No ask posts found.')).toBeInTheDocument();
    });
  });

  it('renders ask empty message for later pages', async () => {
    Cookies.get.mockReturnValue('token');
    searchParamsValue = 'p=2';
    postsAPI.getPosts.mockResolvedValueOnce({ data: [] });
    render(<FeedList postType="ask" />);

    await waitFor(() => {
      expect(screen.getByText('No more ask posts.')).toBeInTheDocument();
    });
  });

  it('renders show empty message when no posts and page > 1', async () => {
    Cookies.get.mockReturnValue('token');
    searchParamsValue = 'p=2';
    postsAPI.getPosts.mockResolvedValueOnce({ data: [] });
    render(<FeedList postType="show" />);

    await waitFor(() => {
      expect(screen.getByText('No more show posts.')).toBeInTheDocument();
    });
  });

  it('renders show empty message for first page', async () => {
    Cookies.get.mockReturnValue('token');
    postsAPI.getPosts.mockResolvedValueOnce({ data: [] });
    render(<FeedList postType="show" />);

    await waitFor(() => {
      expect(screen.getByText('No show posts found.')).toBeInTheDocument();
    });
  });

  it('renders generic empty message for page > 1', async () => {
    Cookies.get.mockReturnValue('token');
    searchParamsValue = 'p=2';
    postsAPI.getPosts.mockResolvedValueOnce({ data: [] });
    render(<FeedList />);

    await waitFor(() => {
      expect(screen.getByText('No more posts.')).toBeInTheDocument();
    });
  });

  it('renders generic empty message for first page', async () => {
    Cookies.get.mockReturnValue('token');
    postsAPI.getPosts.mockResolvedValueOnce({ data: [] });
    render(<FeedList />);

    await waitFor(() => {
      expect(screen.getByText('No posts found.')).toBeInTheDocument();
    });
  });

  it('shows vote error when logged in', async () => {
    const user = userEvent.setup();
    Cookies.get.mockReturnValue('token');
    postsAPI.vote.mockRejectedValueOnce(new Error('vote failed'));
    render(<FeedList />);

    await waitFor(() => expect(screen.getByText('Hello Feed')).toBeInTheDocument());
    await act(async () => {
      await user.click(screen.getByTitle('upvote'));
    });

    await waitFor(() => {
      expect(screen.getByText('vote failed')).toBeInTheDocument();
    });
  });

  it('handles downvote when logged in', async () => {
    const user = userEvent.setup();
    Cookies.get.mockReturnValue('token');
    postsAPI.vote.mockResolvedValueOnce({ data: {} });
    render(<FeedList />);

    await waitFor(() => expect(screen.getByText('Hello Feed')).toBeInTheDocument());
    await act(async () => {
      await user.click(screen.getByTitle('downvote'));
    });
    expect(postsAPI.vote).toHaveBeenCalledWith(1, { vote_type: -1 });
  });

  it('renders job metadata without score', async () => {
    Cookies.get.mockReturnValue('token');
    postsAPI.getPosts.mockResolvedValueOnce({
      data: [
        {
          id: 2,
          title: 'Job Post',
          url: 'https://example.com',
          text: null,
          post_type: 'job',
          score: 0,
          comment_count: 0,
          user_id: 1,
          username: 'alice',
          created_at: '2024-01-01T00:00:00Z',
        },
      ],
    });
    render(<FeedList postType="job" />);

    await waitFor(() => expect(screen.getByText('Job Post')).toBeInTheDocument());
    expect(screen.queryByText(/points/)).not.toBeInTheDocument();
  });

  it('renders comment count when present', async () => {
    Cookies.get.mockReturnValue('token');
    postsAPI.getPosts.mockResolvedValueOnce({
      data: [
        {
          id: 3,
          title: 'Commented',
          url: null,
          text: 'Body',
          post_type: 'story',
          score: 2,
          comment_count: 2,
          user_id: 1,
          username: 'alice',
          created_at: '2024-01-01T00:00:00Z',
        },
      ],
    });
    render(<FeedList />);

    await waitFor(() => expect(screen.getByText('Commented')).toBeInTheDocument());
    expect(screen.getByText('2 comments')).toBeInTheDocument();
  });

  it('hides hostname when url is invalid', async () => {
    Cookies.get.mockReturnValue('token');
    postsAPI.getPosts.mockResolvedValueOnce({
      data: [
        {
          id: 4,
          title: 'Invalid URL',
          url: 'not-a-url',
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
    render(<FeedList />);

    await waitFor(() => expect(screen.getByText('Invalid URL')).toBeInTheDocument());
    expect(screen.queryByText(/\(/)).not.toBeInTheDocument();
  });
});
