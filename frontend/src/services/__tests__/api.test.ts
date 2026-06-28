import { describe, it, expect, vi } from 'vitest';
import { getChats, toggleChat } from '../api';

describe('api', () => {
  it('getChats returns chats', async () => {
    const mockChats = [
      { chat_id: 1, name: 'Test', last_message_preview: '', last_message_at: '', auto_enabled: true, conversation_status: 'active' },
    ];
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockChats,
    } as Response);

    const result = await getChats();
    expect(result).toEqual(mockChats);
  });

  it('getChats throws on error', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      statusText: 'Server Error',
    } as Response);

    await expect(getChats()).rejects.toThrow('Failed to fetch chats');
  });

  it('toggleChat returns updated chat', async () => {
    const mockChat = { chat_id: 1, auto_enabled: true, conversation_status: 'active' };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockChat,
    } as Response);

    const result = await toggleChat(1, true);
    expect(result).toEqual(mockChat);
  });
});
