import React from 'react';
import { Chat } from '../types';
import { ToggleSwitch } from './ToggleSwitch';

interface ChatItemProps {
  chat: Chat;
  onToggle: (chatId: number, enabled: boolean) => void;
}

export const ChatItem: React.FC<ChatItemProps> = ({ chat, onToggle }) => {
  const isActive = chat.conversation_status === 'active';

  return (
    <div className="flex items-center gap-4 p-4 hover:bg-gray-50 transition-colors">
      {/* Avatar */}
      <div className="w-10 h-10 rounded-full bg-rosa-500 flex items-center justify-center text-white font-semibold text-sm flex-shrink-0">
        {chat.name.charAt(0).toUpperCase()}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-medium text-gray-900 truncate">
            {chat.name || 'Unknown'}
          </h3>
          <span
            className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
              isActive
                ? 'bg-green-100 text-green-800'
                : 'bg-gray-100 text-gray-600'
            }`}
          >
            {isActive ? 'Activa' : 'Cerrada'}
          </span>
        </div>
        <p className="text-sm text-gray-500 truncate mt-0.5">
          {chat.last_message_preview || 'Sin mensajes'}
        </p>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3 flex-shrink-0">
        <span className="text-xs text-gray-400">
          Auto
        </span>
        <ToggleSwitch
          enabled={chat.auto_enabled}
          onChange={() => onToggle(chat.chat_id, !chat.auto_enabled)}
        />
      </div>
    </div>
  );
};
