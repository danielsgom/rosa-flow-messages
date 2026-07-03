import { useState, useEffect, useCallback, useMemo } from 'react';
import { Chat } from '../types';
import { getChats, toggleChat, syncChats, setVip } from '../services/api';

export function useChats() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncLoading, setSyncLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchChats = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getChats();
      setChats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      // Keep existing chats on error — don't reset to empty
    } finally {
      setLoading(false);
    }
  }, []);

  const filteredChats = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return chats;
    return chats.filter(
      (c) =>
        (c.full_name ?? c.name).toLowerCase().includes(q) ||
        (c.username ?? '').toLowerCase().includes(q) ||
        (c.last_message_preview ?? '').toLowerCase().includes(q),
    );
  }, [chats, searchQuery]);

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

  const toggleVip = useCallback(async (chatId: number, isVip: boolean) => {
    try {
      setChats((prev) =>
        prev.map((chat) =>
          chat.chat_id === chatId ? { ...chat, is_vip: isVip } : chat
        )
      );
      await setVip(chatId, isVip);
    } catch (err) {
      setChats((prev) =>
        prev.map((chat) =>
          chat.chat_id === chatId ? { ...chat, is_vip: !isVip } : chat
        )
      );
      setError(err instanceof Error ? err.message : 'VIP toggle failed');
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

  return {
    chats,
    filteredChats,
    searchQuery,
    setSearchQuery,
    loading,
    syncLoading,
    error,
    toggleAuto,
    toggleVip,
    refresh: fetchChats,
    syncWithTelegram,
  };
}
