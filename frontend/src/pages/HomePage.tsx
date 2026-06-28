import React from 'react';
import { useChats } from '../hooks/useChats';
import { ChatList } from '../components/ChatList';

export const HomePage: React.FC = () => {
  const { chats, loading, syncLoading, error, toggleAuto, syncWithTelegram } = useChats();

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Rosa Flow</h1>
            <p className="text-sm text-gray-500 mt-1">
              Gestiona tus conversaciones de Telegram con IA
            </p>
          </div>
          <button
            onClick={syncWithTelegram}
            disabled={syncLoading}
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              syncLoading
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-rosa-600 text-white hover:bg-rosa-700 active:bg-rosa-800 shadow-sm'
            }`}
          >
            {syncLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b border-white" />
                Sincronizando...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Sincronizar
              </>
            )}
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow-sm p-4">
            <p className="text-2xl font-semibold text-rosa-600">{chats.length}</p>
            <p className="text-xs text-gray-500">Chats</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-4">
            <p className="text-2xl font-semibold text-green-600">
              {chats.filter((c) => c.auto_enabled).length}
            </p>
            <p className="text-xs text-gray-500">Auto activo</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-4">
            <p className="text-2xl font-semibold text-gray-600">
              {chats.filter((c) => c.conversation_status === 'active').length}
            </p>
            <p className="text-xs text-gray-500">Activas</p>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Chat List */}
        <ChatList chats={chats} onToggle={toggleAuto} loading={loading || syncLoading} />
      </div>
    </div>
  );
};
