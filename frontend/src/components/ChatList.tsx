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
      <div className="flex items-center justify-center py-16">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-rosa-600"></div>
      </div>
    );
  }

  if (chats.length === 0) {
    return (
      <div className="text-center py-16 px-4">
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-rosa-50 flex items-center justify-center">
          <span className="text-2xl">💬</span>
        </div>
        <h3 className="text-gray-700 font-medium text-sm">No hay conversaciones aún</h3>
        <p className="text-gray-400 text-xs mt-1 max-w-xs mx-auto leading-relaxed">
          Las conversaciones aparecerán cuando alguien te escriba por Telegram. Asegúrate de que el backend esté corriendo y conectado.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {chats.map((chat) => (
        <ChatItem key={chat.chat_id} chat={chat} onToggle={onToggle} />
      ))}
    </div>
  );
};
