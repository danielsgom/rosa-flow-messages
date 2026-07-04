import React, { useEffect, useRef, useState } from 'react';
import { deletePhoto, getPhotos, togglePhoto, updatePhotoCaption, uploadPhoto } from '../services/api';
import { Photo } from '../types';
import { ToggleSwitch } from './ToggleSwitch';

export const PhotoManager: React.FC<{ onPhotosChange?: (photos: Photo[]) => void }> = ({ onPhotosChange }) => {
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [collapsed, setCollapsed] = useState(false);
  const [captionEdits, setCaptionEdits] = useState<Record<string, string>>({});
  const [savingCaption, setSavingCaption] = useState<Set<string>>(new Set());
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchPhotos = async () => {
    try {
      const data = await getPhotos();
      setPhotos(data.photos);
      onPhotosChange?.(data.photos);
      setCaptionEdits(Object.fromEntries(data.photos.map(p => [p.filename, p.caption ?? ''])));
      setError(null);
    } catch (e) {
      setError('No se pudieron cargar las fotos');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchPhotos(); }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const photo = await uploadPhoto(file);
      setPhotos(prev => [...prev, photo]);
      setCaptionEdits(prev => ({ ...prev, [photo.filename]: photo.caption ?? '' }));
    } catch (e) {
      setError('Error al subir la foto');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (filename: string) => {
    if (!window.confirm(`Eliminar ${filename}?`)) return;
    try {
      await deletePhoto(filename);
      setPhotos(prev => prev.filter(p => p.filename !== filename));
    } catch {
      setError('Error al eliminar la foto');
    }
  };

  const handleToggle = async (photo: Photo) => {
    try {
      const updated = await togglePhoto(photo.filename, !photo.enabled);
      setPhotos(prev => prev.map(p => p.filename === updated.filename ? updated : p));
    } catch {
      setError('Error al cambiar el estado de la foto');
    }
  };

  const handleSaveCaption = async (filename: string) => {
    const currentPhoto = photos.find(p => p.filename === filename);
    const newCaption = captionEdits[filename]?.trim() || null;
    const oldCaption = currentPhoto?.caption ?? null;
    if (newCaption === oldCaption) return;
    setSavingCaption(prev => new Set(prev).add(filename));
    try {
      const updated = await updatePhotoCaption(filename, newCaption);
      setPhotos(prev => prev.map(p => p.filename === updated.filename ? updated : p));
    } catch {
      setError('Error al guardar el caption');
    } finally {
      setSavingCaption(prev => { const s = new Set(prev); s.delete(filename); return s; });
    }
  };

  const enabledCount = photos.filter(p => p.enabled).length;

  return (
    <div className="bg-white rounded-lg shadow-sm overflow-hidden">
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 cursor-pointer select-none"
        onClick={() => setCollapsed(c => !c)}
      >
        <div className="flex items-center gap-2">
          <span className="text-base font-semibold text-gray-800">Fotos del canal</span>
          <span className="text-xs bg-rosa-100 text-rosa-700 rounded-full px-2 py-0.5 font-medium">
            {enabledCount} de {photos.length} activas
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={e => { e.stopPropagation(); fileInputRef.current?.click(); }}
            disabled={uploading}
            className="text-xs px-3 py-1.5 rounded-lg bg-rosa-600 text-white hover:bg-rosa-700 disabled:opacity-50 transition-colors"
          >
            {uploading ? 'Subiendo…' : '+ Subir foto'}
          </button>
          <svg
            className={`w-4 h-4 text-gray-400 transition-transform ${collapsed ? '' : 'rotate-180'}`}
            fill="none" stroke="currentColor" viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleUpload}
      />

      {!collapsed && (
        <div className="border-t border-gray-100 px-4 py-4">
          {error && (
            <div className="mb-3 text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-rosa-600" />
            </div>
          ) : photos.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-6">
              No hay fotos. Sube la primera para que Rosa empiece a mandarlas.
            </p>
          ) : (
            <div className="grid grid-cols-3 gap-3 sm:grid-cols-4">
              {photos.map(photo => (
                <div
                  key={photo.filename}
                  className={`relative rounded-lg overflow-hidden border transition-all ${
                    photo.enabled ? 'border-rosa-200' : 'border-gray-200 opacity-50 grayscale'
                  }`}
                >
                  {/* Thumbnail */}
                  <div className="aspect-square bg-gray-100">
                    <img
                      src={photo.url}
                      alt={photo.filename}
                      className="w-full h-full object-cover"
                      loading="lazy"
                    />
                  </div>

                  {/* Caption input */}
                  <div className="px-2 pt-1.5 bg-white">
                    <input
                      type="text"
                      value={captionEdits[photo.filename] ?? ''}
                      placeholder="Describe la foto…"
                      maxLength={200}
                      className="w-full text-[10px] text-gray-600 placeholder-gray-300 bg-transparent border-0 border-b border-gray-100 focus:border-rosa-300 focus:outline-none pb-0.5"
                      onChange={e => setCaptionEdits(prev => ({ ...prev, [photo.filename]: e.target.value }))}
                      onBlur={() => handleSaveCaption(photo.filename)}
                      onKeyDown={e => { if (e.key === 'Enter') { e.currentTarget.blur(); } }}
                    />
                    {savingCaption.has(photo.filename) && (
                      <span className="text-[9px] text-rosa-400 animate-pulse">guardando…</span>
                    )}
                  </div>

                  {/* Footer */}
                  <div className="bg-white px-2 py-1.5 flex items-center justify-between gap-1">
                    <ToggleSwitch
                      enabled={photo.enabled}
                      onChange={() => handleToggle(photo)}
                    />
                    <button
                      onClick={() => handleDelete(photo.filename)}
                      className="text-gray-400 hover:text-red-500 transition-colors"
                      title="Eliminar"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>

                  {/* Status badge */}
                  <div className={`absolute top-1 right-1 text-xs rounded px-1 py-0.5 font-medium ${
                    photo.enabled
                      ? 'bg-green-500 text-white'
                      : 'bg-gray-400 text-white'
                  }`}>
                    {photo.enabled ? 'ON' : 'OFF'}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
