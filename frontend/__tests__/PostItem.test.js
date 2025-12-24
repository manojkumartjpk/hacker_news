import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { act } from 'react';
import PostItem from '../components/PostItem';
import { postsAPI } from '../lib/api';

jest.mock('../lib/api', () => ({
  postsAPI: {
    getVote: jest.fn(),
    vote: jest.fn(),
  },
}));

jest.mock('../lib/format', () => ({
  safeHostname: jest.requireActual('../lib/format').safeHostname,
  timeAgo: () => '1 hour ago',
}));

describe('PostItem', () => {
  beforeEach(() => {
    postsAPI.getVote.mockResolvedValue({ data: { vote_type: 0 } });
    postsAPI.vote.mockResolvedValue({ data: {} });
  });

  it('renders post title and hostname', async () => {
    const post = {
      id: 1,
      title: 'Hello HN',
      url: 'https://example.com',
      text: null,
      post_type: 'story',
      score: 10,
      comment_count: 0,
      user_id: 1,
      username: 'alice',
      created_at: '2024-01-01T00:00:00Z',
    };

    render(<PostItem post={post} />);

    await waitFor(() => expect(postsAPI.getVote).toHaveBeenCalledWith(1));
    expect(screen.getByText('Hello HN')).toBeInTheDocument();
    expect(screen.getByText(/example\.com/)).toBeInTheDocument();
  });

  it('upvotes and updates score locally', async () => {
    const user = userEvent.setup();
    const post = {
      id: 2,
      title: 'Vote me',
      url: 'https://example.com',
      text: null,
      post_type: 'story',
      score: 10,
      comment_count: 0,
      user_id: 1,
      username: 'alice',
      created_at: '2024-01-01T00:00:00Z',
    };

    render(<PostItem post={post} />);

    await waitFor(() => expect(postsAPI.getVote).toHaveBeenCalledWith(2));
    await act(async () => {
      await user.click(screen.getByText('▲'));
    });

    await waitFor(() => {
      expect(postsAPI.vote).toHaveBeenCalledWith(2, { vote_type: 1 });
    });

    expect(screen.getByText(/11 points by/i)).toBeInTheDocument();
  });

  it('renders internal link when url is missing', async () => {
    const post = {
      id: 3,
      title: 'Text post',
      url: null,
      text: 'Body',
      post_type: 'story',
      score: 1,
      comment_count: 0,
      user_id: 1,
      username: 'alice',
      created_at: '2024-01-01T00:00:00Z',
    };

    render(<PostItem post={post} />);
    await waitFor(() => expect(postsAPI.getVote).toHaveBeenCalledWith(3));
    expect(screen.getByRole('link', { name: 'Text post' })).toHaveAttribute('href', '/post/3');
    expect(screen.queryByText(/example\.com/)).not.toBeInTheDocument();
  });

  it('alerts when vote fails', async () => {
    const user = userEvent.setup();
    const alertSpy = jest.spyOn(window, 'alert').mockImplementation(() => {});
    postsAPI.vote.mockRejectedValueOnce(new Error('Vote error'));

    const post = {
      id: 4,
      title: 'Vote error',
      url: 'https://example.com',
      text: null,
      post_type: 'story',
      score: 1,
      comment_count: 0,
      user_id: 1,
      username: 'alice',
      created_at: '2024-01-01T00:00:00Z',
    };

    render(<PostItem post={post} />);
    await waitFor(() => expect(postsAPI.getVote).toHaveBeenCalledWith(4));
    await act(async () => {
      await user.click(screen.getByText('▲'));
    });

    await waitFor(() => {
      expect(alertSpy).toHaveBeenCalled();
    });
    alertSpy.mockRestore();
  });

  it('downvotes and calls onVote', async () => {
    const user = userEvent.setup();
    const onVote = jest.fn();
    const post = {
      id: 5,
      title: 'Downvote',
      url: 'https://example.com',
      text: null,
      post_type: 'story',
      score: 5,
      comment_count: 0,
      user_id: 1,
      username: 'alice',
      created_at: '2024-01-01T00:00:00Z',
    };

    render(<PostItem post={post} onVote={onVote} />);
    await waitFor(() => expect(postsAPI.getVote).toHaveBeenCalledWith(5));
    await act(async () => {
      await user.click(screen.getByText('▼'));
    });

    await waitFor(() => {
      expect(postsAPI.vote).toHaveBeenCalledWith(5, { vote_type: -1 });
    });
    expect(onVote).toHaveBeenCalled();
    expect(screen.getByText(/4 points by/i)).toBeInTheDocument();
  });

  it('adjusts score when switching from upvote to downvote', async () => {
    const user = userEvent.setup();
    postsAPI.getVote.mockResolvedValueOnce({ data: { vote_type: 1 } });
    const post = {
      id: 6,
      title: 'Switch vote',
      url: 'https://example.com',
      text: null,
      post_type: 'story',
      score: 10,
      comment_count: 0,
      user_id: 1,
      username: 'alice',
      created_at: '2024-01-01T00:00:00Z',
    };

    render(<PostItem post={post} />);
    await waitFor(() => expect(postsAPI.getVote).toHaveBeenCalledWith(6));
    await act(async () => {
      await user.click(screen.getByText('▼'));
    });

    expect(screen.getByText(/8 points by/i)).toBeInTheDocument();
  });

  it('adjusts score when switching from downvote to upvote', async () => {
    const user = userEvent.setup();
    postsAPI.getVote.mockResolvedValueOnce({ data: { vote_type: -1 } });
    const post = {
      id: 8,
      title: 'Flip vote',
      url: 'https://example.com',
      text: null,
      post_type: 'story',
      score: 10,
      comment_count: 0,
      user_id: 1,
      username: 'alice',
      created_at: '2024-01-01T00:00:00Z',
    };

    render(<PostItem post={post} />);
    await waitFor(() => expect(postsAPI.getVote).toHaveBeenCalledWith(8));
    await act(async () => {
      await user.click(screen.getByText('▲'));
    });

    expect(screen.getByText(/12 points by/i)).toBeInTheDocument();
  });

  it('ignores getVote failures', async () => {
    postsAPI.getVote.mockRejectedValueOnce(new Error('no session'));
    const post = {
      id: 7,
      title: 'No vote',
      url: null,
      text: 'Body',
      post_type: 'story',
      score: 2,
      comment_count: 0,
      user_id: 1,
      username: 'alice',
      created_at: '2024-01-01T00:00:00Z',
    };

    render(<PostItem post={post} />);
    await waitFor(() => expect(postsAPI.getVote).toHaveBeenCalledWith(7));
    expect(screen.getByText('No vote')).toBeInTheDocument();
  });
});
