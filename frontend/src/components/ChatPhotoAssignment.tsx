import React, { useEffect, useState, useCallback } from 'react';
import { Photo } from '../types';
import { getChatPhotos, setChatPhotos } from '../services/api';

interface Props {
  chatId: number;
  chatName: string;
  allPhotos: Photo[];
  onClose: () => void;
}

export const ChatPhotoAssignment: React.FC<Props> = ({ chatId, chatName, allPhotos, onClose }) => {
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getChatPhotos(chatId)
      .then((data) => setSelected(new Set(data.assigned_filenames)))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [chatId]);

  const toggle = useCallback(
    async (filename: string) => {
      const next = new Set(selected);
      if (next.has(filename)) next.delete(filename);
      else next.add(filename);
      setSelected(next);
      setSaving(true);
      try {
        await setChatPhotos(chatId, Array.from(next));
      } catch (e) {
        console.error(e);
        setSelected(selected); // revert on error
      } finally {
        setSaving(false);
      }
    },
    [chatId, selected],
  );

  const enabledPhotos = allPhotos.filter((p) => p.enabled);
  const assignedCount = selected.size;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <div>
            <h2 className="text-base font-semibold text-gray-900">Fotos asignadas</h2>
            <p className="text-xs text-gray-500 mt-0.5 truncate max-w-[220px]">{chatName}</p>
          </div>
          <div className="flex items-center gap-3">
            {saving && <span className="text-xs text-rosa-500 animate-pulse">Guardando…</span>}
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors text-gray-500"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Info pill */}
        <div className="px-5 pt-3">
          <p className="text-xs text-gray-500">
            {assignedCount === 0
              ? 'Sin asignación — se usarán todas las fotos habilitadas'
              : `${assignedCount} foto${assignedCount !== 1 ? 's' : ''} asignada${assignedCount !== 1 ? 's' : ''} a este chat`}
          </p>
        </div>

        {/* Photo grid */}
        <div className="px-5 py-4">
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-rosa-500" />
            </div>
          ) : enabledPhotos.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-8">
              No hay fotos habilitadas todavía
            </p>
          ) : (
            <div className="grid grid-cols-3 gap-2">
              {enabledPhotos.map((photo) => {
                const isSelected = selected.has(photo.filename);
                return (
                  <button
                    key={photo.filename}
                    onClick={() => toggle(photo.filename)}
                    className={`relative rounded-xl overflow-hidden border-2 transition-all flex flex-col ${
                      isSelected
                        ? 'border-rosa-500 ring-2 ring-rosa-200'
                        : 'border-transparent hover:border-gray-300'
                    }`}
                  >
                    <div className="aspect-square w-full relative">
                      <img
                        src={photo.url}
                        alt={photo.filename}
                        className="w-full h-full object-cover"
                      />
                      {isSelected && (
                        <div className="absolute inset-0 bg-rosa-500/20 flex items-center justify-center">
                          <div className="w-6 h-6 rounded-full bg-rosa-500 flex items-center justify-center shadow">
                            <svg className="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                            </svg>
                          </div>
                        </div>
                      )}
                    </div>
                    {photo.caption && (
                      <div className="bg-white px-1.5 py-1 text-left">
                        <p className="text-[9px] text-gray-500 leading-tight line-clamp-2">{photo.caption}</p>
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 pb-4 flex justify-between items-center">
          <button
            onClick={() => {
              setSelected(new Set());
              setChatPhotos(chatId, []).catch(console.error);
            }}
            className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
          >
            Limpiar selección
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-rosa-600 text-white text-sm font-medium rounded-lg hover:bg-rosa-700 transition-colors"
          >
            Listo
          </button>
        </div>
      </div>
    </div>
  );
};
