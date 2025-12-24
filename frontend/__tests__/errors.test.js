import { getErrorMessage } from '../lib/errors';

describe('getErrorMessage', () => {
  it('prefers API detail when available', () => {
    const error = { response: { data: { detail: 'API error' } } };
    expect(getErrorMessage(error)).toBe('API error');
  });

  it('falls back to message', () => {
    const error = { message: 'Network error' };
    expect(getErrorMessage(error)).toBe('Network error');
  });

  it('uses default fallback when nothing else exists', () => {
    expect(getErrorMessage(null, 'Fallback')).toBe('Fallback');
  });
});
