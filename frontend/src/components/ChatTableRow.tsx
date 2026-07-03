import React from 'react';
import { Chat, Photo } from '../types';
import { ToggleSwitch } from './ToggleSwitch';

interface ChatTableRowProps {
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

export const ChatTableRow: React.FC<ChatTableRowProps> = ({
  chat,
  assignedCount,
  onToggle,
  onManagePhotos,
  onToggleVip,
  onViewHistory,
}) => {
  const isActive = chat.conversation_status === 'active';

  return (
    <tr className="hover:bg-rosa-50/30 transition-colors group border-b border-gray-50 last:border-0">

      {/* Col: Usuario */}
      <td className="px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="relative flex-shrink-0">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-rosa-400 to-rosa-600 flex items-center justify-center text-white text-xs font-bold shadow-sm">
              {getInitials(chat)}
            </div>
            <div
              className={`absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-white ${
                isActive ? 'bg-green-400' : 'bg-gray-300'
              }`}
            />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="font-medium text-gray-900 text-sm truncate max-w-[200px]">
                {getDisplayName(chat)}
              </span>
              {chat.is_vip && (
                <span className="inline-flex text-[9px] font-bold px-1.5 py-0.5 rounded bg-amber-100 text-amber-600 flex-shrink-0 leading-none">
                  ★ VIP
                </span>
              )}
            </div>
            {chat.username && (
              <span className="text-[11px] text-gray-400">@{chat.username}</span>
            )}
          </div>
        </div>
      </td>

      {/* Col: Estado */}
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <span
            className={`text-[10px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wide flex-shrink-0 ${
              isActive ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
            }`}
          >
            {isActive ? 'Activa' : 'Cerrada'}
          </span>
          <ToggleSwitch
            size="sm"
            enabled={chat.auto_enabled}
            onChange={() => onToggle(chat.chat_id, !chat.auto_enabled)}
          />
        </div>
      </td>

      {/* Col: Último mensaje */}
      <td className="px-4 py-3 max-w-0 w-full">
        <p className="text-xs text-gray-500 truncate">
          {chat.last_message_preview || '—'}
        </p>
      </td>

      {/* Col: Hace */}
      <td className="px-4 py-3 text-center whitespace-nowrap">
        <span className="text-[11px] text-gray-400">{timeAgo(chat.last_message_at)}</span>
      </td>

      {/* Col: Convs / Coste */}
      <td className="px-4 py-3 text-right whitespace-nowrap">
        {chat.total_conversations > 0 ? (
          <>
            <span className="text-[11px] text-gray-600 font-medium">
              {chat.total_conversations}
            </span>
            <span className="text-[10px] text-gray-400 ml-0.5">conv</span>
          </>
        ) : (
          <span className="text-[11px] text-gray-300">—</span>
        )}
        {chat.total_cost_usd > 0 && (
          <div className="text-[10px] text-gray-400">${chat.total_cost_usd.toFixed(3)}</div>
        )}
      </td>

      {/* Col: Fotos */}
      <td className="px-4 py-3 text-center">
        <button
          onClick={() => onManagePhotos(chat.chat_id)}
          title="Gestionar fotos asignadas"
          className="inline-flex items-center gap-1 text-[11px] text-gray-500 hover:text-rosa-600 transition-colors px-1.5 py-1 rounded hover:bg-rosa-50"
        >
          <span>📸</span>
          <span>{assignedCount > 0 ? assignedCount : '—'}</span>
        </button>
      </td>

      {/* Col: Acciones */}
      <td className="px-4 py-3">
        <div className="flex items-center justify-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={() => onToggleVip(chat.chat_id, !chat.is_vip)}
            title={chat.is_vip ? 'Quitar VIP' : 'Marcar VIP'}
            className={`p-1.5 rounded-md text-sm transition-colors ${
              chat.is_vip
                ? 'text-amber-500 hover:bg-amber-50 opacity-100'
                : 'text-gray-400 hover:text-amber-500 hover:bg-amber-50'
            }`}
          >
            ★
          </button>
          <button
            onClick={() => onViewHistory(chat.chat_id)}
            title="Ver historial de conversaciones"
            className="p-1.5 rounded-md text-gray-400 hover:text-blue-500 hover:bg-blue-50 transition-colors text-sm"
          >
            🕐
          </button>
        </div>
        {/* VIP star siempre visible si está marcado */}
        {chat.is_vip && (
          <button
            onClick={() => onToggleVip(chat.chat_id, false)}
            title="Quitar VIP"
            className="flex items-center justify-center w-full text-amber-500 text-sm group-hover:hidden"
          >
            ★
          </button>
        )}
      </td>
    </tr>
  );
};
