import { useState, useEffect, useCallback } from 'react';
import { Chat } from '../types';
import { getChats, toggleChat } from '../services/api';

export function useChats() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchChats = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getChats();
      setChats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  const toggleAuto = useCallback(async (chatId: number, enabled: boolean) => {
    try {
      // Optimistic update
      setChats((prev) =>
        prev.map((chat) =>
          chat.chat_id === chatId ? { ...chat, auto_enabled: enabled } : chat
        )
      );

      await toggleChat(chatId, enabled);
    } catch (err) {
      // Rollback on error
      setChats((prev) =>
        prev.map((chat) =>
          chat.chat_id === chatId ? { ...chat, auto_enabled: !enabled } : chat
        )
      );
      setError(err instanceof Error ? err.message : 'Toggle failed');
    }
  }, []);

  useEffect(() => {
    fetchChats();
    const interval = setInterval(fetchChats, 5000); // Poll every 5s
    return () => clearInterval(interval);
  }, [fetchChats]);

  return { chats, loading, error, toggleAuto, refresh: fetchChats };
}
