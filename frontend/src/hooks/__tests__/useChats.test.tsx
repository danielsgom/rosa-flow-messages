import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useChats } from '../useChats';

describe('useChats', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches chats on mount', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [],
    } as Response);

    const { result } = renderHook(() => useChats());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.chats).toEqual([]);
  });

  it('handles fetch error', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      statusText: 'Error',
    } as Response);

    const { result } = renderHook(() => useChats());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.error).toBeDefined();
  });
});
