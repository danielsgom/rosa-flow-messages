import React from 'react';
import { Chat, Photo } from '../types';
import { ToggleSwitch } from './ToggleSwitch';

interface ChatItemProps {
  chat: Chat;
  allPhotos: Photo[];
  assignedCount: number;
  onToggle: (chatId: number, enabled: boolean) => void;
  onManagePhotos: (chatId: number) => void;
  onToggleVip: (chatId: number, isVip: boolean) => void;
  onViewHistory: (chatId: number) => void;
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

export const ChatItem: React.FC<ChatItemProps> = ({
  chat, assignedCount, onToggle, onManagePhotos, onToggleVip, onViewHistory,
}) => {
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
          {chat.is_vip && (
            <span
              title="VIP"
              className="inline-flex items-center px-1.5 py-0.5 rounded-md text-[10px] font-bold bg-amber-100 text-amber-700 flex-shrink-0"
            >
              ★ VIP
            </span>
          )}
          {chat.username && (
            <span className="text-xs text-rosa-500 font-medium flex-shrink-0">
              @{chat.username}
            </span>
          )}
          <span className="text-[10px] text-gray-400 flex-shrink-0 font-medium ml-auto">
            {timeLabel}
          </span>
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
        </div>

        {/* Stats row: conversations + cost */}
        <div className="flex items-center gap-3 mt-1">
          {chat.total_conversations > 0 && (
            <span className="text-[10px] text-gray-400">
              {chat.total_conversations} conv.
            </span>
          )}
          {chat.total_cost_usd > 0 && (
            <span className="text-[10px] text-gray-400">
              ${chat.total_cost_usd.toFixed(3)}
            </span>
          )}
        </div>
      </div>

      {/* Toggle + action buttons */}
      <div className="flex flex-col items-center gap-2 flex-shrink-0 pt-1">
        {/* Auto toggle */}
        <div className="flex flex-col items-center gap-1">
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

        {/* VIP toggle */}
        <button
          onClick={() => onToggleVip(chat.chat_id, !chat.is_vip)}
          title={chat.is_vip ? 'Quitar VIP' : 'Marcar como VIP'}
          className={`p-1.5 rounded-lg transition-colors ${
            chat.is_vip
              ? 'bg-amber-100 text-amber-600 hover:bg-amber-200'
              : 'hover:bg-gray-100 text-gray-400 hover:text-amber-500'
          }`}
        >
          <svg className="w-4 h-4" fill={chat.is_vip ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
          </svg>
        </button>

        {/* Photos button */}
        <button
          onClick={() => onManagePhotos(chat.chat_id)}
          title="Gestionar fotos de este chat"
          className="relative p-1.5 rounded-lg hover:bg-rosa-50 text-gray-400 hover:text-rosa-500 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          {assignedCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 rounded-full bg-rosa-500 text-white text-[8px] font-bold flex items-center justify-center">
              {assignedCount}
            </span>
          )}
        </button>

        {/* History button */}
        <button
          onClick={() => onViewHistory(chat.chat_id)}
          title="Ver historial de conversaciones"
          className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </button>
      </div>
    </div>
  );
};
