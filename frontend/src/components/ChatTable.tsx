import React from 'react';
import { Chat, Photo } from '../types';
import { ChatTableRow } from './ChatTableRow';

interface ChatTableProps {
  chats: Chat[];
  allPhotos: Photo[];
  assignedCountMap: Record<number, number>;
  onToggle: (chatId: number, enabled: boolean) => void;
  onManagePhotos: (chatId: number) => void;
  onToggleVip: (chatId: number, isVip: boolean) => void;
  onViewHistory: (chatId: number) => void;
  loading?: boolean;
}

export const ChatTable: React.FC<ChatTableProps> = ({
  chats,
  allPhotos,
  assignedCountMap,
  onToggle,
  onManagePhotos,
  onToggleVip,
  onViewHistory,
  loading,
}) => {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-rosa-600" />
      </div>
    );
  }

  if (chats.length === 0) {
    return (
      <div className="text-center py-20 px-4 bg-white rounded-xl border border-gray-100">
        <div className="w-14 h-14 mx-auto mb-4 rounded-full bg-rosa-50 flex items-center justify-center">
          <span className="text-2xl">💬</span>
        </div>
        <h3 className="text-gray-700 font-medium text-sm">No hay conversaciones</h3>
        <p className="text-gray-400 text-xs mt-1 max-w-xs mx-auto">
          Pulsa Sincronizar para cargar los chats de Telegram, o espera a recibir un mensaje.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50/80">
              <th className="px-4 py-3 text-left text-[11px] font-semibold text-gray-500 uppercase tracking-wider">
                Usuario
              </th>
              <th className="px-4 py-3 text-left text-[11px] font-semibold text-gray-500 uppercase tracking-wider">
                Estado / Auto
              </th>
              <th className="px-4 py-3 text-left text-[11px] font-semibold text-gray-500 uppercase tracking-wider">
                Último mensaje
              </th>
              <th className="px-4 py-3 text-center text-[11px] font-semibold text-gray-500 uppercase tracking-wider">
                Hace
              </th>
              <th className="px-4 py-3 text-right text-[11px] font-semibold text-gray-500 uppercase tracking-wider">
                Convs / €
              </th>
              <th className="px-4 py-3 text-center text-[11px] font-semibold text-gray-500 uppercase tracking-wider">
                Fotos
              </th>
              <th className="px-4 py-3 text-center text-[11px] font-semibold text-gray-500 uppercase tracking-wider">
                Acciones
              </th>
            </tr>
          </thead>
          <tbody>
            {chats.map((chat) => (
              <ChatTableRow
                key={chat.chat_id}
                chat={chat}
                allPhotos={allPhotos}
                assignedCount={assignedCountMap[chat.chat_id] ?? 0}
                onToggle={onToggle}
                onManagePhotos={onManagePhotos}
                onToggleVip={onToggleVip}
                onViewHistory={onViewHistory}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
