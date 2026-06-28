import React from 'react';
import { Chat } from '../types';
import { ToggleSwitch } from './ToggleSwitch';

interface ChatItemProps {
  chat: Chat;
  onToggle: (chatId: number, enabled: boolean) => void;
}

function timeAgo(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  const diffHr = Math.floor(diffMs / 3600000);
  const diffDay = Math.floor(diffMs / 86400000);

  if (diffMin < 1) return 'ahora';
  if (diffMin < 60) return `${diffMin}m`;
  if (diffHr < 24) return `${diffHr}h`;
  if (diffDay < 7) return `${diffDay}d`;
  return date.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' });
}

function getInitials(chat: Chat): string {
  if (chat.full_name) return chat.full_name.charAt(0).toUpperCase();
  return (chat.name || '?').charAt(0).toUpperCase();
}

function getDisplayName(chat: Chat): string {
  return chat.full_name || chat.name || 'Sin nombre';
}

export const ChatItem: React.FC<ChatItemProps> = ({ chat, onToggle }) => {
  const isActive = chat.conversation_status === 'active';
  const timeLabel = timeAgo(chat.last_message_at);

  return (
    <div className="flex items-start gap-3 p-4 bg-white rounded-xl shadow-sm hover:shadow-md transition-all duration-200 border border-gray-100 cursor-default">
      {/* Avatar */}
      <div className="relative flex-shrink-0 mt-0.5">
        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-rosa-400 to-rosa-600 flex items-center justify-center text-white font-bold text-lg shadow-sm">
          {getInitials(chat)}
        </div>
        {/* Active/Closed indicator dot */}
        <div
          className={`absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 rounded-full border-2 border-white ${
            isActive ? 'bg-green-500' : 'bg-gray-400'
          }`}
        />
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0 pt-0.5">
        {/* Header line: Name + badges + time */}
        <div className="flex items-center gap-2 min-w-0">
          <h3 className="text-sm font-semibold text-gray-900 truncate">
            {getDisplayName(chat)}
          </h3>
          {chat.username && (
            <span className="text-xs text-rosa-500 font-medium flex-shrink-0">
              @{chat.username}
            </span>
          )}
        </div>

        {/* Status badge */}
        <div className="flex items-center gap-2 mt-1">
          <span
            className={`inline-flex items-center px-1.5 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider ${
              isActive
                ? 'bg-green-100 text-green-700'
                : 'bg-gray-100 text-gray-500'
            }`}
          >
            {isActive ? 'Activa' : 'Cerrada'}
          </span>
          {!isActive && (
            <span className="text-[10px] text-gray-400">
              (volver a escribir la reactiva)
            </span>
          )}
        </div>

        {/* Message preview and time */}
        <div className="flex items-center gap-2 mt-1.5">
          <p className="text-xs text-gray-500 truncate flex-1 min-w-0">
            {chat.last_message_preview || 'Sin mensajes aún'}
          </p>
          <span className="text-[10px] text-gray-400 flex-shrink-0 font-medium">
            {timeLabel}
          </span>
        </div>
      </div>

      {/* Toggle */}
      <div className="flex flex-col items-center gap-1 flex-shrink-0 pt-1">
        <ToggleSwitch
          enabled={chat.auto_enabled}
          onChange={() => onToggle(chat.chat_id, !chat.auto_enabled)}
        />
        <span className={`text-[9px] font-medium uppercase tracking-wider ${
          chat.auto_enabled ? 'text-rosa-600' : 'text-gray-400'
        }`}>
          {chat.auto_enabled ? 'On' : 'Off'}
        </span>
      </div>
    </div>
  );
};
