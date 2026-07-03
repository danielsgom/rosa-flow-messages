import React, { useState, useEffect, useCallback } from 'react';
import { ChatTable } from '../components/ChatTable';
import { PhotoManager } from '../components/PhotoManager';
import { ChatPhotoAssignment } from '../components/ChatPhotoAssignment';
import { CostModal } from '../components/CostModal';
import { ChatHistoryModal } from '../components/ChatHistoryModal';
import { useChats } from '../hooks/useChats';
import { Photo } from '../types';
import { getPhotos, getChatPhotos } from '../services/api';

export const HomePage: React.FC = () => {
  const {
    chats,
    filteredChats,
    searchQuery,
    setSearchQuery,
    loading,
    syncLoading,
    error,
    toggleAuto,
    toggleVip,
    syncWithTelegram,
  } = useChats();

  // Track whether a sync has been done in this session (to show DB banner)
  const [hasSynced, setHasSynced] = useState(false);

  const handleSync = useCallback(async () => {
    await syncWithTelegram();
    setHasSynced(true);
  }, [syncWithTelegram]);

  // Photos pool
  const [allPhotos, setAllPhotos] = useState<Photo[]>([]);
  useEffect(() => {
    getPhotos().then((d) => setAllPhotos(d.photos)).catch(console.error);
  }, []);

  // Assigned counts per chat (for the badge)
  const [assignedCountMap, setAssignedCountMap] = useState<Record<number, number>>({});
  useEffect(() => {
    if (chats.length === 0) return;
    Promise.all(
      chats.map((c) =>
        getChatPhotos(c.chat_id)
          .then((d) => ({ id: c.chat_id, count: d.assigned_filenames.length }))
          .catch(() => ({ id: c.chat_id, count: 0 })),
      ),
    ).then((results) => {
      const map: Record<number, number> = {};
      results.forEach(({ id, count }) => { map[id] = count; });
      setAssignedCountMap(map);
    });
  }, [chats]);

  // Photo assignment modal
  const [photoAssignChatId, setPhotoAssignChatId] = useState<number | null>(null);
  const photoAssignChat = chats.find((c) => c.chat_id === photoAssignChatId) ?? null;

  const handleAssignmentClose = useCallback(() => {
    // Refresh badge count for the edited chat
    if (photoAssignChatId !== null) {
      getChatPhotos(photoAssignChatId)
        .then((d) => setAssignedCountMap((prev) => ({ ...prev, [photoAssignChatId]: d.assigned_filenames.length })))
        .catch(console.error);
    }
    setPhotoAssignChatId(null);
  }, [photoAssignChatId]);

  // Cost modal
  const [showCostModal, setShowCostModal] = useState(false);

  // VIP filter applied on top of search results
  const [vipOnly, setVipOnly] = useState(false);
  const visibleChats = vipOnly ? filteredChats.filter((c) => c.is_vip) : filteredChats;

  // History modal
  const [historyChatId, setHistoryChatId] = useState<number | null>(null);
  const historyChat = chats.find((c) => c.chat_id === historyChatId) ?? null;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-[1400px] mx-auto px-6 py-5">

        {/* ── Header ── */}
        <div className="flex items-center gap-4 mb-5 flex-wrap">

          {/* Title */}
          <div className="flex-shrink-0">
            <h1 className="text-xl font-bold text-gray-900">Rosa Flow</h1>
            <p className="text-xs text-gray-400 leading-none mt-0.5">Panel de conversaciones</p>
          </div>

          {/* Stats pills */}
          <div className="flex items-center gap-2 ml-2">
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-white border border-gray-200 text-gray-600 shadow-sm">
              <span className="font-bold text-rosa-600">{chats.length}</span> chats
            </span>
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-white border border-gray-200 text-gray-600 shadow-sm">
              <span className="font-bold text-green-600">{chats.filter((c) => c.auto_enabled).length}</span> auto
            </span>
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-white border border-gray-200 text-gray-600 shadow-sm">
              <span className="font-bold text-amber-500">{chats.filter((c) => c.is_vip).length}</span> VIP
            </span>
          </div>

          {/* Search bar — flex-1 */}
          <div className="flex-1 min-w-[200px] max-w-sm relative">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none"
              fill="none" stroke="currentColor" viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder="Buscar por nombre, @usuario o mensaje…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-8 py-2 text-sm bg-white border border-gray-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-rosa-300 focus:border-transparent placeholder-gray-400"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 text-xs font-bold"
              >
                ✕
              </button>
            )}
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2 ml-auto flex-shrink-0">
            {/* VIP filter */}
            <button
              onClick={() => setVipOnly((v) => !v)}
              className={`inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors border ${
                vipOnly
                  ? 'bg-amber-100 border-amber-300 text-amber-700'
                  : 'bg-white border-gray-200 text-gray-500 hover:border-amber-300 hover:text-amber-600'
              }`}
            >
              <svg className="w-3.5 h-3.5" fill={vipOnly ? 'currentColor' : 'none'} stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
              </svg>
              Solo VIP
            </button>

            {/* Cost */}
            <button
              onClick={() => setShowCostModal(true)}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium text-gray-600 hover:bg-gray-100 border border-gray-200 transition-colors bg-white"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Gasto
            </button>

            {/* Sync */}
            <button
              onClick={handleSync}
              disabled={syncLoading}
              className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all shadow-sm ${
                syncLoading
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-rosa-600 text-white hover:bg-rosa-700 active:bg-rosa-800'
              }`}
            >
              {syncLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b border-rosa-300" />
                  Sincronizando…
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
        </div>

        {/* ── DB banner ── */}
        {!hasSynced && chats.length > 0 && !loading && (
          <div className="mb-4 flex items-center gap-2 px-3 py-2 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-600">
            <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Mostrando {chats.length} chats guardados — pulsa Sincronizar para actualizar
          </div>
        )}

        {/* ── Error ── */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* ── Search result count ── */}
        {searchQuery && (
          <p className="text-xs text-gray-500 mb-2">
            {visibleChats.length} resultado{visibleChats.length !== 1 ? 's' : ''} para &ldquo;{searchQuery}&rdquo;
            {vipOnly && <span className="ml-1 text-amber-600">· solo VIP</span>}
          </p>
        )}

        {/* ── Chat Table ── */}
        <ChatTable
          chats={visibleChats}
          allPhotos={allPhotos}
          assignedCountMap={assignedCountMap}
          onToggle={toggleAuto}
          onManagePhotos={(chatId) => setPhotoAssignChatId(chatId)}
          onToggleVip={(chatId, isVip) => toggleVip(chatId, isVip)}
          onViewHistory={(chatId) => setHistoryChatId(chatId)}
          loading={loading || syncLoading}
        />

        {/* ── Photo Manager ── */}
        <div className="mt-6">
          <PhotoManager onPhotosChange={(photos) => setAllPhotos(photos)} />
        </div>
      </div>

      {/* Modals */}
      {photoAssignChatId !== null && photoAssignChat && (
        <ChatPhotoAssignment
          chatId={photoAssignChatId}
          chatName={photoAssignChat.full_name ?? photoAssignChat.name}
          allPhotos={allPhotos}
          onClose={handleAssignmentClose}
        />
      )}
      {showCostModal && <CostModal onClose={() => setShowCostModal(false)} />}
      {historyChatId !== null && historyChat && (
        <ChatHistoryModal
          chatId={historyChatId}
          chatName={historyChat.full_name ?? historyChat.name}
          onClose={() => setHistoryChatId(null)}
        />
      )}
    </div>
  );
};
