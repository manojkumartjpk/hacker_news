import { render, screen, waitFor } from '@testing-library/react';
import Home from '../app/page';

jest.mock('../lib/api', () => ({
  postsAPI: {
    getPosts: jest.fn(() => Promise.resolve({ data: [] })),
  },
}));

jest.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(''),
  usePathname: () => '/',
  useRouter: () => ({ replace: jest.fn() }),
}));

describe('Home page', () => {
  it('renders the empty state when no posts are returned', async () => {
    render(<Home />);
    await waitFor(() => {
      expect(screen.getByText('No posts found.')).toBeInTheDocument();
    });
  });
});
