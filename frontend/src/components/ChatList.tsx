import React from 'react';
import { Chat } from '../types';
import { ChatItem } from './ChatItem';

interface ChatListProps {
  chats: Chat[];
  onToggle: (chatId: number, enabled: boolean) => void;
  loading?: boolean;
}

export const ChatList: React.FC<ChatListProps> = ({ chats, onToggle, loading }) => {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-rosa-600"></div>
      </div>
    );
  }

  if (chats.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 text-sm">No hay conversaciones aún</p>
        <p className="text-gray-400 text-xs mt-1">
          Las conversaciones aparecerán cuando alguien te escriba por Telegram
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm divide-y divide-gray-100">
      {chats.map((chat) => (
        <ChatItem key={chat.chat_id} chat={chat} onToggle={onToggle} />
      ))}
    </div>
  );
};
