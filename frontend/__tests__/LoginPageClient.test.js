import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { act } from 'react';
import LoginPageClient from '../components/LoginPageClient';
import { authAPI, postsAPI, commentsAPI } from '../lib/api';

let searchParamsValue = '';
let push;

jest.mock('../lib/api', () => ({
  authAPI: {
    login: jest.fn(),
  },
  postsAPI: {
    vote: jest.fn(),
  },
  commentsAPI: {
    vote: jest.fn(),
  },
}));

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push }),
  useSearchParams: () => new URLSearchParams(searchParamsValue),
}));

jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ href, children }) => <a href={href}>{children}</a>,
}));

describe('LoginPageClient', () => {
  beforeEach(() => {
    searchParamsValue = '';
    push = jest.fn();
    authAPI.login.mockResolvedValue({ data: { access_token: 'token' } });
    postsAPI.vote.mockResolvedValue({ data: {} });
    commentsAPI.vote.mockResolvedValue({ data: {} });
  });

  const fillAndSubmit = async () => {
    const user = userEvent.setup();
    await act(async () => {
      await user.type(screen.getByTitle('Enter your username'), 'alice');
      await user.type(screen.getByTitle('Enter your password'), 'Password1!');
      await user.click(screen.getByRole('button', { name: 'Login' }));
    });
  };

  it('logs in and redirects to safe next', async () => {
    searchParamsValue = 'next=/submit';
    render(<LoginPageClient />);
    await fillAndSubmit();

    await waitFor(() => expect(authAPI.login).toHaveBeenCalled());
    expect(push).toHaveBeenCalledWith('/submit');
  });

  it('falls back to home when next is unsafe', async () => {
    searchParamsValue = 'next=https://evil.com';
    render(<LoginPageClient />);
    await fillAndSubmit();

    await waitFor(() => expect(authAPI.login).toHaveBeenCalled());
    expect(push).toHaveBeenCalledWith('/');
  });

  it('executes post vote after login when params are present', async () => {
    searchParamsValue = 'next=/&vote=1&post=9';
    render(<LoginPageClient />);
    await fillAndSubmit();

    await waitFor(() => {
      expect(postsAPI.vote).toHaveBeenCalledWith('9', { vote_type: 1 });
    });
  });

  it('executes comment vote after login when params are present', async () => {
    searchParamsValue = 'next=/&vote=1&comment=4';
    render(<LoginPageClient />);
    await fillAndSubmit();

    await waitFor(() => {
      expect(commentsAPI.vote).toHaveBeenCalledWith('4', { vote_type: 1 });
    });
  });

  it('shows error when login fails', async () => {
    authAPI.login.mockRejectedValueOnce(new Error('Login failed'));
    render(<LoginPageClient />);
    await fillAndSubmit();

    await waitFor(() => {
      expect(screen.getByText('Login failed')).toBeInTheDocument();
    });
  });
});
