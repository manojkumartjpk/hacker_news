import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { act } from 'react';
import CommentItem from '../components/CommentItem';
import Cookies from 'js-cookie';
import { commentsAPI } from '../lib/api';

let replace;

jest.mock('js-cookie', () => ({
  get: jest.fn(),
}));

jest.mock('../lib/api', () => ({
  commentsAPI: {
    updateComment: jest.fn(),
    deleteComment: jest.fn(),
    vote: jest.fn(),
    unvote: jest.fn(),
  },
}));

jest.mock('next/navigation', () => ({
  useRouter: () => ({ replace }),
}));

jest.mock('../lib/format', () => ({
  timeAgo: () => '1 hour ago',
}));

describe('CommentItem', () => {
  const baseComment = {
    id: 10,
    text: 'Hello comment',
    user_id: 1,
    post_id: 5,
    parent_id: null,
    created_at: '2024-01-01T00:00:00Z',
    username: 'alice',
    replies: [],
  };

  beforeEach(() => {
    replace = jest.fn();
    commentsAPI.updateComment.mockClear();
    commentsAPI.deleteComment.mockClear();
    commentsAPI.vote.mockClear();
    commentsAPI.unvote.mockClear();
    commentsAPI.updateComment.mockResolvedValue({ data: {} });
    commentsAPI.deleteComment.mockResolvedValue({ data: {} });
    commentsAPI.vote.mockResolvedValue({ data: {} });
    commentsAPI.unvote.mockResolvedValue({ data: {} });
  });

  it('redirects to login when voting while logged out', async () => {
    const user = userEvent.setup();
    Cookies.get.mockReturnValue(undefined);

    render(
      <table>
        <tbody>
          <CommentItem comment={baseComment} currentUser={{ id: 2 }} />
        </tbody>
      </table>,
    );

    await act(async () => {
      await user.click(screen.getByTitle('upvote'));
    });
    expect(replace).toHaveBeenCalledWith('/login?next=/post/5&vote=1&comment=10');
    expect(commentsAPI.vote).not.toHaveBeenCalled();
  });

  it('allows the owner to edit a comment', async () => {
    const user = userEvent.setup();
    Cookies.get.mockReturnValue('token');

    render(
      <table>
        <tbody>
          <CommentItem comment={baseComment} currentUser={{ id: 1 }} />
        </tbody>
      </table>,
    );

    await act(async () => {
      await user.click(screen.getByRole('link', { name: 'edit' }));
    });
    const editForm = screen.getByText('Text:').parentElement;
    const editBox = within(editForm).getByRole('textbox');
    await act(async () => {
      await user.clear(editBox);
      await user.type(editBox, 'Updated text');
      await user.click(screen.getByRole('button', { name: 'update' }));
    });

    await waitFor(() => {
      expect(commentsAPI.updateComment).toHaveBeenCalledWith(10, { text: 'Updated text' });
    });
  });

  it('shows login link for reply when logged out', () => {
    Cookies.get.mockReturnValue(undefined);

    render(
      <table>
        <tbody>
          <CommentItem comment={baseComment} currentUser={{ id: 2 }} />
        </tbody>
      </table>,
    );

    expect(screen.getByRole('link', { name: 'reply' })).toHaveAttribute('href', '/login?next=/reply/10');
  });

  it('hides reply link when max depth reached', () => {
    Cookies.get.mockReturnValue('token');

    render(
      <table>
        <tbody>
          <CommentItem comment={baseComment} currentUser={{ id: 2 }} depth={5} />
        </tbody>
      </table>,
    );

    expect(screen.queryByRole('link', { name: 'reply' })).not.toBeInTheDocument();
  });

  it('links to reply page when logged in', () => {
    Cookies.get.mockReturnValue('token');

    render(
      <table>
        <tbody>
          <CommentItem comment={baseComment} currentUser={{ id: 2 }} />
        </tbody>
      </table>,
    );

    expect(screen.getByRole('link', { name: 'reply' })).toHaveAttribute('href', '/reply/10');
  });

  it('allows the owner to delete a comment', async () => {
    const user = userEvent.setup();
    Cookies.get.mockReturnValue('token');

    render(
      <table>
        <tbody>
          <CommentItem comment={baseComment} currentUser={{ id: 1 }} />
        </tbody>
      </table>,
    );

    await act(async () => {
      await user.click(screen.getByRole('link', { name: 'delete' }));
    });
    const confirmButton = await screen.findByRole('button', { name: 'Yes' });
    await act(async () => {
      await user.click(confirmButton);
    });

    await waitFor(() => {
      expect(commentsAPI.deleteComment).toHaveBeenCalledWith(10);
    });
  });

  it('cancels delete confirmation', async () => {
    const user = userEvent.setup();
    Cookies.get.mockReturnValue('token');

    render(
      <table>
        <tbody>
          <CommentItem comment={baseComment} currentUser={{ id: 1 }} />
        </tbody>
      </table>,
    );

    await act(async () => {
      await user.click(screen.getByRole('link', { name: 'delete' }));
    });
    const confirmContainer = screen.getByText('Do you want this to be deleted?').parentElement;
    await act(async () => {
      await user.click(within(confirmContainer).getByRole('button', { name: 'No' }));
    });

    expect(screen.queryByText('Do you want this to be deleted?')).not.toBeInTheDocument();
  });

  it('calls onRefresh after edit and delete', async () => {
    const user = userEvent.setup();
    Cookies.get.mockReturnValue('token');
    const onRefresh = jest.fn();

    render(
      <table>
        <tbody>
          <CommentItem comment={baseComment} currentUser={{ id: 1 }} onRefresh={onRefresh} />
        </tbody>
      </table>,
    );

    await act(async () => {
      await user.click(screen.getByRole('link', { name: 'edit' }));
    });
    const editForm = await screen.findByText('Text:');
    const editContainer = editForm.parentElement;
    const editBox = within(editContainer).getByRole('textbox');
    await act(async () => {
      await user.clear(editBox);
      await user.type(editBox, 'Updated text');
      await user.click(within(editContainer).getByRole('button', { name: 'update' }));
    });

    await waitFor(() => expect(onRefresh).toHaveBeenCalledTimes(1));

    await act(async () => {
      await user.click(screen.getByRole('link', { name: 'delete' }));
    });
    const confirmButton = await screen.findByRole('button', { name: 'Yes' });
    await act(async () => {
      await user.click(confirmButton);
    });
    await waitFor(() => expect(onRefresh).toHaveBeenCalledTimes(2));
  });

  it('alerts on edit, delete, and vote errors', async () => {
    const user = userEvent.setup();
    const alertSpy = jest.spyOn(window, 'alert').mockImplementation(() => {});
    Cookies.get.mockReturnValue('token');
    commentsAPI.updateComment.mockRejectedValueOnce(new Error('edit failed'));
    commentsAPI.deleteComment.mockRejectedValueOnce(new Error('delete failed'));
    commentsAPI.vote.mockRejectedValueOnce(new Error('vote failed'));

    render(
      <table>
        <tbody>
          <CommentItem comment={baseComment} currentUser={{ id: 1 }} />
        </tbody>
      </table>,
    );

    await act(async () => {
      await user.click(screen.getByRole('link', { name: 'edit' }));
    });
    const editForm = await screen.findByText('Text:');
    const editContainer = editForm.parentElement;
    const editBox = within(editContainer).getByRole('textbox');
    await act(async () => {
      await user.clear(editBox);
      await user.type(editBox, 'Updated text');
      await user.click(within(editContainer).getByRole('button', { name: 'update' }));
    });

    await act(async () => {
      await user.click(screen.getByRole('link', { name: 'delete' }));
    });
    const confirmButton = await screen.findByRole('button', { name: 'Yes' });
    await act(async () => {
      await user.click(confirmButton);
    });

    await act(async () => {
      await user.click(screen.getByTitle('upvote'));
    });

    await waitFor(() => {
      expect(alertSpy).toHaveBeenCalled();
    });
    alertSpy.mockRestore();
  });

  it('does not update when edit text is empty and can cancel', async () => {
    const user = userEvent.setup();
    Cookies.get.mockReturnValue('token');

    render(
      <table>
        <tbody>
          <CommentItem comment={baseComment} currentUser={{ id: 1 }} />
        </tbody>
      </table>,
    );

    await act(async () => {
      await user.click(screen.getByRole('link', { name: 'edit' }));
    });
    const initialCalls = commentsAPI.updateComment.mock.calls.length;
    const editForm = await screen.findByText('Text:');
    const editContainer = editForm.parentElement;
    const editBox = within(editContainer).getByRole('textbox');
    await act(async () => {
      await user.clear(editBox);
      await user.click(within(editContainer).getByRole('button', { name: 'update' }));
    });

    expect(commentsAPI.updateComment.mock.calls.length).toBe(initialCalls);

    await act(async () => {
      await user.click(within(editContainer).getByRole('button', { name: 'cancel' }));
    });

    expect(screen.queryByText('Text:')).not.toBeInTheDocument();
  });

  it('toggles edit cancel action', async () => {
    const user = userEvent.setup();
    Cookies.get.mockReturnValue('token');

    render(
      <table>
        <tbody>
          <CommentItem comment={baseComment} currentUser={{ id: 1 }} />
        </tbody>
      </table>,
    );

    await act(async () => {
      await user.click(screen.getByRole('link', { name: 'edit' }));
    });
    const editForm = await screen.findByText('Text:');
    const editContainer = editForm.parentElement;
    await act(async () => {
      await user.click(within(editContainer).getByRole('button', { name: 'cancel' }));
    });
    expect(screen.queryByText('Text:')).not.toBeInTheDocument();
  });

  it('renders nested replies', () => {
    Cookies.get.mockReturnValue('token');
    const nestedComment = {
      ...baseComment,
      replies: [
        {
          id: 11,
          text: 'Nested',
          user_id: 2,
          post_id: 5,
          parent_id: 10,
          created_at: '2024-01-01T00:00:00Z',
          username: 'bob',
          replies: [],
        },
      ],
    };

    render(
      <table>
        <tbody>
          <CommentItem comment={nestedComment} currentUser={{ id: 1 }} />
        </tbody>
      </table>,
    );

    expect(screen.getByText('Nested')).toBeInTheDocument();
  });
});
