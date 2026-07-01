import { Chat, Photo } from '../types';

const API_BASE = '/api';

export async function getChats(): Promise<Chat[]> {
  const response = await fetch(`${API_BASE}/chats`);
  if (!response.ok) {
    throw new Error(`Failed to fetch chats: ${response.statusText}`);
  }
  return response.json();
}

export async function toggleChat(chatId: number, enabled: boolean): Promise<Chat> {
  const response = await fetch(`${API_BASE}/chats/${chatId}/toggle`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ enabled }),
  });
  if (!response.ok) {
    throw new Error(`Failed to toggle chat: ${response.statusText}`);
  }
  return response.json();
}

export interface SyncResult {
  synced: number;
  total: number;
  chats: Chat[];
}

export async function syncChats(): Promise<SyncResult> {
  const response = await fetch(`${API_BASE}/chats/sync`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error(`Failed to sync chats: ${response.statusText}`);
  }
  return response.json();
}

// ---------------------------------------------------------------------------
// Photo API
// ---------------------------------------------------------------------------

export async function getPhotos(): Promise<{ total: number; photos: Photo[] }> {
  const response = await fetch(`${API_BASE}/photos`);
  if (!response.ok) throw new Error(`Failed to fetch photos: ${response.statusText}`);
  return response.json();
}

export async function uploadPhoto(file: File): Promise<Photo> {
  const form = new FormData();
  form.append('file', file);
  const response = await fetch(`${API_BASE}/photos`, { method: 'POST', body: form });
  if (!response.ok) throw new Error(`Failed to upload photo: ${response.statusText}`);
  return response.json();
}

export async function deletePhoto(filename: string): Promise<void> {
  const response = await fetch(`${API_BASE}/photos/${encodeURIComponent(filename)}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error(`Failed to delete photo: ${response.statusText}`);
}

export async function togglePhoto(filename: string, enabled: boolean): Promise<Photo> {
  const response = await fetch(`${API_BASE}/photos/${encodeURIComponent(filename)}/toggle`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ enabled }),
  });
  if (!response.ok) throw new Error(`Failed to toggle photo: ${response.statusText}`);
  return response.json();
}
