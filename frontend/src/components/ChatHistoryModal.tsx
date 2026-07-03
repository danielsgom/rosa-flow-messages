import React, { useEffect, useState } from 'react';
import { ChatHistory, ConversationHistory } from '../types';
import { getChatHistory } from '../services/api';

interface Props {
  chatId: number;
  chatName: string;
  onClose: () => void;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('es-ES', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

function statusBadge(status: string) {
  const classes =
    status === 'active'
      ? 'bg-green-100 text-green-700'
      : status === 'closing'
      ? 'bg-yellow-100 text-yellow-700'
      : 'bg-gray-100 text-gray-500';
  return (
    <span className={`inline-flex px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${classes}`}>
      {status}
    </span>
  );
}

export const ChatHistoryModal: React.FC<Props> = ({ chatId, chatName, onClose }) => {
  const [history, setHistory] = useState<ChatHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getChatHistory(chatId)
      .then(setHistory)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [chatId]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <div>
            <h2 className="text-base font-semibold text-gray-900">Historial de conversaciones</h2>
            <p className="text-xs text-gray-500 mt-0.5">{chatName}</p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-5 py-4">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-rosa-600" />
            </div>
          )}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
              {error}
            </div>
          )}
          {history && history.conversations.length === 0 && (
            <p className="text-center text-gray-400 text-sm py-12">
              No hay conversaciones registradas aún.
            </p>
          )}
          {history && history.conversations.length > 0 && (
            <div className="space-y-3">
              {history.conversations.map((conv: ConversationHistory) => (
                <div
                  key={conv.id}
                  className="border border-gray-100 rounded-xl p-4 hover:border-rosa-200 transition-colors"
                >
                  {/* Conv header */}
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      {statusBadge(conv.status)}
                      <span className="text-xs text-gray-500">{formatDate(conv.started_at)}</span>
                    </div>
                    <span className="text-xs font-semibold text-rosa-600 flex-shrink-0">
                      ${conv.cost_usd.toFixed(4)}
                    </span>
                  </div>

                  {/* Stats row */}
                  <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                    <span>
                      <span className="font-medium text-gray-700">{conv.turn_count}</span>
                      {conv.max_turns ? ` / ${conv.max_turns}` : ''} turnos
                    </span>
                    {conv.photos.length > 0 && (
                      <span>
                        <span className="font-medium text-gray-700">{conv.photos.length}</span> foto
                        {conv.photos.length !== 1 ? 's' : ''}
                      </span>
                    )}
                    {conv.ended_at && (
                      <span>Cerrada {formatDate(conv.ended_at)}</span>
                    )}
                  </div>

                  {/* Photo thumbnails */}
                  {conv.photos.length > 0 && (
                    <div className="flex gap-1.5 mt-3 flex-wrap">
                      {conv.photos.map((filename) => (
                        <img
                          key={filename}
                          src={`/api/photos/${encodeURIComponent(filename)}/file`}
                          alt={filename}
                          className="w-10 h-10 rounded-lg object-cover border border-gray-200"
                        />
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer stats */}
        {history && (
          <div className="px-5 py-3 border-t border-gray-100 flex items-center justify-between">
            <span className="text-xs text-gray-500">
              {history.total_conversations} conversacion{history.total_conversations !== 1 ? 'es' : ''}
            </span>
            <span className="text-xs font-medium text-gray-700">
              Total: ${history.conversations.reduce((s, c) => s + c.cost_usd, 0).toFixed(4)}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
