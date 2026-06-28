import { useState, useEffect, useCallback } from 'react';
import { Chat } from '../types';
import { getChats, toggleChat, syncChats } from '../services/api';

export function useChats() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncLoading, setSyncLoading] = useState(false);
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
      setChats((prev) =>
        prev.map((chat) =>
          chat.chat_id === chatId ? { ...chat, auto_enabled: enabled } : chat
        )
      );
      await toggleChat(chatId, enabled);
    } catch (err) {
      setChats((prev) =>
        prev.map((chat) =>
          chat.chat_id === chatId ? { ...chat, auto_enabled: !enabled } : chat
        )
      );
      setError(err instanceof Error ? err.message : 'Toggle failed');
    }
  }, []);

  const syncWithTelegram = useCallback(async () => {
    try {
      setSyncLoading(true);
      setError(null);
      const result = await syncChats();
      setChats(result.chats);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sync failed');
      throw err;
    } finally {
      setSyncLoading(false);
    }
  }, []);

  // Carga inicial una sola vez
  useEffect(() => {
    fetchChats();
  }, [fetchChats]);

  return { chats, loading, syncLoading, error, toggleAuto, refresh: fetchChats, syncWithTelegram };
}
