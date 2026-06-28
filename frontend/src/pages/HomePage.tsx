import React from 'react';
import { useChats } from '../hooks/useChats';
import { ChatList } from '../components/ChatList';

export const HomePage: React.FC = () => {
  const { chats, loading, error, toggleAuto } = useChats();

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Rosa Flow</h1>
          <p className="text-sm text-gray-500 mt-1">
            Gestiona tus conversaciones de Telegram con IA
          </p>
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
        <ChatList chats={chats} onToggle={toggleAuto} loading={loading} />
      </div>
    </div>
  );
};
