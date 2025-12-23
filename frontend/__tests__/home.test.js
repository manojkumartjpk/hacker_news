import { render, screen, waitFor } from '@testing-library/react';
import Home from '../app/page';

jest.mock('../lib/api', () => ({
  postsAPI: {
    getPosts: jest.fn(() => Promise.resolve({ data: [] })),
  },
}));

jest.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(''),
}));

describe('Home page', () => {
  it('renders the more link after loading', async () => {
    render(<Home />);
    await waitFor(() => {
      expect(screen.getByText('more')).toBeInTheDocument();
    });
  });
});
